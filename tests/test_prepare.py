"""`vss prepare` -- the machine's work before the owner sits down.

Three routes, each a fixture: SEC XBRL (NKE, through the same facts payload
`test_xbrl_annual` uses), Nasdaq Nordic (PNDORA.CO, through `test_nordic`'s
replayed feed and an xlsx appendix with a committed cell map), and a name
with no route (MC.PA). Then the four rules: idempotent, --dry-run writes
nothing, the verification list is exactly the §5 gate's `blocking`, and the
watchlist is never written.
"""

from __future__ import annotations

import json
import shutil
from datetime import datetime
from pathlib import Path

import pytest
import yaml

from test_appendix import FIN, MARGINS, FULL_FIELDS, workbook
from test_earnings import EXTRACTION_JSON, RELEASE, mock_llm
from test_nordic import FEED_OPENER, PANDORA, issuers_file
from test_xbrl_annual import facts as nke_facts

from vss import extract as X
from vss import manual as M
from vss.prepare import run_prepare
from vss.refresh import ROUTE_EDGAR, ROUTE_MANUAL, ROUTE_NORDIC

RUN_TS = datetime(2026, 9, 13, 20, 0, 0).astimezone()

WATCHLIST = """\
tickers:
  - ticker: NKE
    name: NIKE, Inc.
    currency: USD
    status: PIPELINE
    cik: 320187
    dd_at_entry: 0.31
    peak_date: 2026-03-02
  - ticker: PNDORA.CO
    name: Pandora A/S
    currency: DKK
    status: PIPELINE
  - ticker: MC.PA
    name: LVMH
    currency: EUR
    status: PIPELINE
    fv_base: 612.5
    tier: 2
    run_record: reference/run-records/MC.PA-2026-08-30.json
    growth:
      view: reference/growth-views/MC.PA.md
      registered: 2026-08-30
      base: 0.04
      bear: 0.0
      bull: 0.07
  - ticker: ACME.ST
    name: ACME Industries
    currency: SEK
    status: PIPELINE
    quarters:
      - {period: 2025-Q4, revenue: 4140, revenue_yoy: -0.01, op_margin: 0.135, guidance_action: maintained, basis: reported, accounting: gaap}
      - {period: 2026-Q1, revenue: 4130, revenue_yoy: -0.02, op_margin: 0.130, guidance_action: maintained, basis: reported, accounting: gaap}
"""


@pytest.fixture
def repo(tmp_path, monkeypatch):
    monkeypatch.setenv(X.KEY_ENV, "test-key-not-real")
    for d in ("config/manual/maps", "sources", "reports/prepare", "data/cache"):
        (tmp_path / d).mkdir(parents=True)
    (tmp_path / "config" / "watchlist.yaml").write_text(WATCHLIST, encoding="utf-8")
    issuers_file(tmp_path, {"PNDORA.CO": {"market": PANDORA.market, "company": PANDORA.company,
                                          "language": "en"}})
    (tmp_path / "oslo_issuers.yaml").write_text("issuers: {}\n", encoding="utf-8")
    # a Nordic appendix already downloaded, with its manifest row and a cell map
    book = workbook(tmp_path / "sources", {"Financial statements_appendix": FIN,
                                            "Cost, GM, EBIT, EBITDA_appendix": MARGINS},
                    name="PNDORA.CO_2026-Q2_inside-information_2026-08-12_en_a0.xlsx")
    (tmp_path / "config" / "manual" / "maps" / "PNDORA.CO.yaml").write_text(yaml.safe_dump({
        "ticker": "PNDORA.CO", "name": "Pandora A/S", "reporting_currency": "DKK",
        "quote_currency": "DKK", "sector": "Consumer", "reporting_frequency": "quarterly",
        "period_basis": "calendar", "document": "Pandora appendix", "fields": FULL_FIELDS}))
    # a release for ACME.ST, saved as the fetchers name files
    release = tmp_path / "sources" / "ACME.ST_2026-Q2_interim-report_2026-07-20_en_a0.html"
    shutil.copy(RELEASE, release)
    manifest = {"schema": "vss/nordic manifest v1", "note": "", "downloads": [
        {"file": book.name, "ticker": "PNDORA.CO", "period": "2026-Q2", "origin": "nasdaq-nordic",
         "category": "Inside information", "released": "2026-08-12 07:00:00 +0000",
         "disclosure_id": 1457001, "figures_read": False},
        {"file": release.name, "ticker": "ACME.ST", "period": "2026-Q2", "origin": "nasdaq-nordic",
         "category": "Interim report (Q1 and Q3)", "released": "2026-07-20 07:00:00 +0000",
         "disclosure_id": 99, "figures_read": False},
    ]}
    (tmp_path / "sources" / "manifest.json").write_text(json.dumps(manifest, indent=2))
    # the record MC.PA already has: a run record, a briefing, a growth-view file
    (tmp_path / "reference" / "run-records").mkdir(parents=True)
    (tmp_path / "reference" / "run-records" / "MC.PA-2026-08-30.json").write_text("{}")
    (tmp_path / "reports" / "BRIEFING-MC.PA-2026-09-01.md").write_text("# LVMH briefing\n")
    (tmp_path / "reference" / "growth-views").mkdir()
    (tmp_path / "reference" / "growth-views" / "MC.PA.md").write_text(VIEW.replace("ACN", "MC.PA"))
    # NKE has a view FILE but no registered date on its entry
    (tmp_path / "reference" / "growth-views" / "NKE.md").write_text(VIEW.replace("ACN", "NKE"))
    return tmp_path


VIEW = """\
# ACN — growth view
Set by the owner, 2026-08-30, pre-registered under FRAMEWORK-EDITS E28.

Base case FCF growth, 10 years: 4.5%
Bear: 0%
Bull: 7.5%
"""


def run(repo, ticker=None, **kw):
    params = dict(
        ticker=ticker, watchlist_path=repo / "config" / "watchlist.yaml",
        manual_dir=repo / "config" / "manual", sources_root=repo / "sources",
        maps_dir=repo / "config" / "manual" / "maps", reports_dir=repo / "reports" / "prepare",
        db_path=repo / "data" / "vss.sqlite", cache_dir=repo / "data" / "cache",
        issuers_path=repo / "nordic_issuers.yaml", oslo_issuers_path=repo / "oslo_issuers.yaml",
        now=RUN_TS, fetcher=lambda cik: nke_facts(), opener=FEED_OPENER,
        transport=mock_llm(EXTRACTION_JSON.read_text()),
        reader=lambda path, **kw: {}, root=repo,
        views_dir=repo / "reference" / "growth-views")
    params.update(kw)
    return run_prepare(**params)


def loaded(repo, ticker):
    p = repo / "reports" / "prepare" / f"{ticker}-{RUN_TS.date().isoformat()}.json"
    return json.loads(p.read_text(encoding="utf-8"))


# --- the US route ------------------------------------------------------------

def test_us_route_fetches_the_facts_and_writes_a_sec_xbrl_store(repo):
    code, report = run(repo, "NKE")
    store = repo / "config" / "manual" / "NKE.yaml"
    assert store.exists()
    parsed = M.parse_manual(yaml.safe_load(store.read_text()), path=store)
    assert parsed.origin == M.ORIGIN_XBRL
    data = loaded(repo, "NKE")
    assert data["steps"][1]["data"]["route"] == ROUTE_EDGAR
    assert "xbrl.run_xbrl_annual" in data["steps"][3]["reused"]
    assert (repo / "reports" / "prepare" / f"NKE-{RUN_TS.date()}.md").exists()
    assert data["summary"].startswith(("ready for review", "blocked on"))
    assert any(c["name"].startswith("Gate 1 level leg") for c in data["checks"])
    # the frozen leg (E12) is read off the entry, not today's price
    gate1 = next(c for c in data["checks"] if c["name"].startswith("Gate 1 level leg"))
    assert "frozen" in gate1["name"] and "0.31" not in gate1["name"]


def test_us_route_is_idempotent_and_names_the_force_backup(repo):
    run(repo, "NKE")
    store = repo / "config" / "manual" / "NKE.yaml"
    before = store.read_bytes()
    code, report = run(repo, "NKE")
    assert store.read_bytes() == before
    data = loaded(repo, "NKE")
    assert any("not re-filled (pass --force)" in l for l in data["steps"][3]["lines"])
    assert data["llm_calls"] == 0
    run(repo, "NKE", force=True)
    backups = list((repo / "config" / "manual").glob("NKE.yaml.bak-*"))
    assert backups, "--force backs the store up first"
    data = loaded(repo, "NKE")
    assert any("--force" in l and "DISCARDED" in l for l in data["steps"][3]["lines"])


# --- the Nordic route --------------------------------------------------------

def test_nordic_route_lists_the_feed_fills_from_the_appendix_and_downloads_nothing(repo):
    files_before = sorted(p.name for p in (repo / "sources").iterdir())
    code, report = run(repo, "PNDORA.CO")
    data = loaded(repo, "PNDORA.CO")
    assert data["steps"][1]["data"]["route"] == ROUTE_NORDIC
    assert [d["file"] for d in data["documents"]] == ["PNDORA.CO_2026-Q2_inside-information_2026-08-12_en_a0.xlsx"]
    fetch = data["steps"][2]
    assert "nordic.fetch_releases" in fetch["reused"] and "watch.classify" in fetch["reused"]
    assert any("NOT FETCHED" in l and "--period YYYY-Qn" in l for l in fetch["lines"])
    assert any(r["on_file"] for r in fetch["data"]["releases"])   # 1457001 is in the manifest
    assert sorted(p.name for p in (repo / "sources").iterdir()) == files_before
    store = repo / "config" / "manual" / "PNDORA.CO.yaml"
    assert store.exists()
    text = store.read_text()
    assert "origin: nordic-xlsx" in text and "status: VERIFIED" not in text
    assert "appendix.run_appendix" in data["steps"][3]["reused"]
    before = store.read_bytes()
    run(repo, "PNDORA.CO")
    assert store.read_bytes() == before


# --- no route ----------------------------------------------------------------

def test_a_name_with_no_route_says_manual_and_fills_nothing(repo):
    code, report = run(repo, "MC.PA")
    data = loaded(repo, "MC.PA")
    assert data["steps"][1]["data"]["route"] == ROUTE_MANUAL
    assert data["steps"][2]["status"] == "skipped"
    assert any("manual route" in l for l in data["steps"][2]["lines"])
    assert not (repo / "config" / "manual" / "MC.PA.yaml").exists()
    assert "manual download" in report


# --- the LLM path ------------------------------------------------------------

def test_the_earnings_path_runs_with_compare_and_the_calls_are_counted(repo):
    code, report = run(repo, "ACME.ST")
    data = loaded(repo, "ACME.ST")
    assert data["llm_calls_earnings"] == 2, "--compare reads the source twice"
    assert "earnings.run_earnings (--compare)" in data["steps"][3]["reused"]
    assert any(f["field"] == "revenue" and f["status"].startswith("PROPOSED") for f in data["filled"])
    assert data["context"]["one_offs"]["class_c_impact"] is not None or \
        "sentence" in data["context"]["one_offs"]
    assert not (repo / "config" / "manual" / "ACME.ST.yaml").exists(), "the earnings path writes no store"
    assert "the earnings alert, verbatim" in (repo / "reports" / "prepare" / f"ACME.ST-{RUN_TS.date()}.md").read_text()


# --- dry run -----------------------------------------------------------------

def test_dry_run_writes_nothing_anywhere(repo):
    manifest = (repo / "sources" / "manifest.json").read_bytes()
    code, report = run(repo, "NKE", dry_run=True)
    assert "DRY RUN" in report
    assert not (repo / "config" / "manual" / "NKE.yaml").exists()
    assert list((repo / "reports" / "prepare").iterdir()) == []
    assert (repo / "sources" / "manifest.json").read_bytes() == manifest
    assert not (repo / "data" / "vss.sqlite").exists()


# --- the verification list is the gate's ---------------------------------------

def test_verification_list_equals_what_the_section_5_gate_refuses_on(repo):
    run(repo, "NKE")
    store = repo / "config" / "manual" / "NKE.yaml"
    text = store.read_text()
    # un-verify one tagged figure by hand, as a reading that has not been done
    text = text.replace("status: VERIFIED\n        verified_kind: tagged", "status: UNVERIFIED", 1)
    store.write_text(text)
    run(repo, "NKE")
    data = loaded(repo, "NKE")
    parsed = M.load_manual("NKE", directory=repo / "config" / "manual")
    gate = M.gate_on_registered_view(parsed, as_of=RUN_TS.date())
    expected = sorted((f.name, f.period) for f in gate.blocking)
    assert sorted((v["field"], v["period"]) for v in data["verification"]) == expected
    assert (expected == []) == (not any("UNVERIFIED" in c["name"] for c in data["checks"]))
    assert data["blocked_on"] >= len(expected)


# --- the rules ---------------------------------------------------------------

def test_the_watchlist_is_never_written_and_no_decision_field_is_set(repo):
    watchlist = repo / "config" / "watchlist.yaml"
    before = watchlist.read_bytes()
    code, report = run(repo, all_pipeline=True)
    assert watchlist.read_bytes() == before
    for ticker in ("NKE", "PNDORA.CO", "MC.PA", "ACME.ST"):
        assert (repo / "reports" / "prepare" / f"{ticker}-{RUN_TS.date()}.json").exists()
    for store in (repo / "config" / "manual").glob("*.yaml"):
        text = store.read_text()
        for forbidden in ("fv_base:", "tier:", "mbp:", "stop_price:", "status: HELD"):
            assert forbidden not in text
    assert "Never written by this command" in report or code in (0, 1)


def test_every_step_reports_even_when_one_fails(repo):
    def broken(cik):
        raise RuntimeError("SEC is down")
    code, report = run(repo, "NKE", fetcher=broken)
    data = loaded(repo, "NKE")
    names = [s["name"] for s in data["steps"]]
    assert names == ["stands", "route", "fetch", "fill", "compute", "verify", "context"]
    fill = data["steps"][3]
    assert fill["status"] in ("failed", "refused")
    assert any("SEC is down" in l for l in fill["lines"]) or data["refused"]
    assert data["steps"][4]["status"] == "ok"


# --- 1. where this name stands -------------------------------------------------

def test_where_this_name_stands_reads_the_record_and_sets_the_summary(repo):
    code, report = run(repo, "MC.PA")
    data = loaded(repo, "MC.PA")
    st = data["context"]["stands"]
    assert st["status"] == "PIPELINE" and st["playbook_step"] == "pipeline"
    assert st["growth_view"].startswith("growth view registered 2026-08-30: g_base 4.0%")
    assert "fv_base 612.5" in st["fv_base"] and "on disk" in st["run_record"]
    assert st["struck"] == "2026-08-30" and st["verdict_recorded"] is False
    assert st["inconsistent_e27"] is True
    assert any(d["kind"] == "briefing" for d in st["documents"])
    assert st["reviews"] == "reference/reviews/ does not exist"
    assert data["summary"].startswith("already struck 2026-08-30; verdict not recorded -- resume at verdict")
    assert "INCONSISTENT WITH E27" in data["summary"]
    md = (repo / "reports" / "prepare" / f"MC.PA-{RUN_TS.date()}.md").read_text()
    assert md.index("## Where this name stands") < md.index("## Route")
    assert "INCONSISTENT WITH E27" in md


def test_rates_are_hidden_until_the_entry_carries_a_registered_date(repo):
    run(repo, "NKE")
    st = loaded(repo, "NKE")["context"]["stands"]
    assert st["growth_view"].startswith("no growth view registered")
    assert "rates not shown" in st["growth_view"]
    for rate in ("4.5%", "7.5%", "0.045"):
        assert rate not in st["growth_view"]
    assert st["resume_at"] is None
    assert not loaded(repo, "NKE")["summary"].startswith("already struck")


# --- 2. the writer speaks the store's vocabulary, and every write is validated ------

def test_edgar_quarter_names_are_translated_to_the_stores_fields():
    from vss.refresh import store_figures
    figures, dropped = store_figures({"eps": 1, "op_income": 2, "revenue": 3, "weird": 4})
    assert set(figures) == {"diluted_eps", "operating_income", "revenue"}
    assert dropped == ["weird"]


def test_a_block_the_store_refuses_is_never_written(repo):
    from vss.refresh import RefreshError, validated_insert, _period_block
    from test_refresh import FakeFigure
    run(repo, "NKE")
    store = repo / "config" / "manual" / "NKE.yaml"
    original = store.read_text()
    block, _ = _period_block(period="2026-Q1", period_end=__import__("datetime").date(2026, 3, 31),
                             period_basis="calendar", document="d", url="",
                             figures={"eps": FakeFigure(1.0, end="2026-03-31")})
    with pytest.raises(RefreshError) as exc:
        validated_insert(original, block, store)
    assert "unknown figure(s) eps" in str(exc.value)
    assert store.read_text() == original


def test_prepare_appends_diluted_eps_and_the_store_still_loads(repo, monkeypatch):
    from test_refresh import FakeFigure
    from vss import xbrl as XB
    run(repo, "NKE")                      # creates the sec-xbrl store from the annual facts

    class Q:
        # a quarter ENDING AFTER the annual FY2026 window (2026-05-31), or the
        # append path rightly skips it as already covered
        period = "2027-Q1"; period_basis = "fiscal"; balance_sheet_only = False; missing = []
        figures = {"eps": FakeFigure(2.10, end="2026-08-31", tag="us-gaap:EarningsPerShareDiluted"),
                   "revenue": FakeFigure(11_000_000_000, end="2026-08-31")}
    monkeypatch.setattr(XB, "build_quarters", lambda facts, limit=8: [Q()])
    monkeypatch.setattr(XB, "fiscal_year_end_month", lambda facts, *a, **k: 5)
    code, report = run(repo, "NKE")
    store = repo / "config" / "manual" / "NKE.yaml"
    text = store.read_text()
    fill = loaded(repo, "NKE")["steps"][3]["lines"]
    assert "diluted_eps:" in text and "\n      eps:" not in text, fill
    parsed = M.load_manual("NKE", directory=repo / "config" / "manual")   # loads
    assert [p.period for p in parsed.periods] == ["2027-Q1"], fill
    assert parsed.periods[0].figures["diluted_eps"].value == 2.10
    assert any("appended 1 period(s)" in l for l in loaded(repo, "NKE")["steps"][3]["lines"])


# --- 3. no LLM on the sec-xbrl route, and inline XBRL is stripped elsewhere ---------

def test_sec_xbrl_route_skips_the_llm_even_with_a_filed_htm_on_disk(repo):
    doc = repo / "sources" / "NKE_FY2026_annual-report-10k_2026-07-15_en_a0.htm"
    doc.write_text("<html><body><ix:header><ix:hidden>0000320187</ix:hidden></ix:header><p>Revenues 46,398</p></body></html>")
    manifest = json.loads((repo / "sources" / "manifest.json").read_text())
    manifest["downloads"].append({"file": doc.name, "ticker": "NKE", "period": "FY2026",
                                  "origin": "sec-edgar", "form": "10-K", "filed": "2026-07-15"})
    (repo / "sources" / "manifest.json").write_text(json.dumps(manifest))
    run(repo, "NKE")
    data = loaded(repo, "NKE")
    assert data["llm_calls_earnings"] == 0
    assert any("LLM extraction SKIPPED on the sec-xbrl route" in l for l in data["steps"][3]["lines"])
    assert "earnings.run_earnings (--compare)" not in data["steps"][3]["reused"]


def test_inline_xbrl_hidden_header_never_reaches_the_model():
    from vss.source import html_to_text
    html = ("<html><body><div style='display:none'><ix:header><ix:hidden>"
            "<ix:nonNumeric name='dei:EntityCentralIndexKey'>0000906163</ix:nonNumeric></ix:hidden>"
            "<ix:resources><xbrli:context id='c-1'><xbrli:period><xbrli:startDate>2025-01-01"
            "</xbrli:startDate></xbrli:period></xbrli:context></ix:resources></ix:header></div>"
            "<table><tr><td>Revenues</td><td><ix:nonFraction name='us-gaap:Revenues'>1,881,063"
            "</ix:nonFraction></td></tr></table></body></html>")
    text = html_to_text(html)
    assert "1,881,063" in text and "Revenues" in text
    assert "0000906163" not in text and "2025-01-01" not in text and "c-1" not in text
