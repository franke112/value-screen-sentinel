"""reporting_frequency, period labels, the overlap guard and half-year windows.

A half-yearly reporter publishes half as many observations as a quarterly
one over the same span. These tests pin three things:

  * the schema: quarterly|half_yearly per ticker, YYYY-H1/H2/FY labels,
    and the kind of label a ticker may hold;
  * the OVERLAP GUARD: no two loaded periods of one ticker may cover the
    same month -- finest resolution stays, coarser goes, never both -- in
    the loader (fatal) and in `vss earnings` (admit / displace / reject);
  * the 4.2 windows: stated in quarters by FRAMEWORK, counted in
    half-years for a half_yearly name, converted by TIME (8 -> 4, 4 -> 2,
    2 -> 1), with the YoY look-back at 2 periods instead of 4.
"""

import json
from datetime import date, datetime
from pathlib import Path

import pytest

from vss import earnings as E
from vss import extract as X
from vss import rules as R
from vss import source as S
from vss.config import ConfigError, parse_entry, parse_watchlist

FIXTURES = Path(__file__).resolve().parent / "fixtures" / "earnings"
RELEASE = FIXTURES / "acme-q2-2026-release.html"
EXTRACTION_JSON = FIXTURES / "acme-q2-2026-extraction.json"
AS_OF = date(2026, 8, 22)


# =========================== period label helpers ==========================


@pytest.mark.parametrize("label,months", [
    ("2025-Q1", 3), ("2025-Q4", 3), ("2025-H1", 6), ("2025-H2", 6), ("2025-FY", 12),
])
def test_period_months_by_kind(label, months):
    assert R.period_months(label) == months


@pytest.mark.parametrize("bad", ["2025-Q5", "2025-H3", "2025-FY1", "25-Q1", "2025Q1", "", None, "2025-q1"])
def test_malformed_labels_are_not_periods(bad):
    assert R.period_parts(bad) is None


@pytest.mark.parametrize("a,b,overlap", [
    ("2025-Q1", "2025-H1", True),     # H1 contains Q1
    ("2025-Q2", "2025-H1", True),
    ("2025-Q3", "2025-H1", False),    # H1 stops in June
    ("2025-Q3", "2025-H2", True),
    ("2024-Q3", "2024-FY", True),     # FY contains every quarter
    ("2025-H1", "2025-FY", True),
    ("2025-H2", "2025-FY", True),
    ("2025-H1", "2025-H2", False),    # the two halves tile the year
    ("2025-H1", "2026-H1", False),    # different years never overlap
    ("2025-FY", "2026-FY", False),
    ("2025-Q1", "2025-Q2", False),
])
def test_overlap_is_about_shared_months(a, b, overlap):
    assert R.periods_overlap(a, b) is overlap
    assert R.periods_overlap(b, a) is overlap


def test_sort_key_orders_halves_and_years_chronologically():
    labels = ["2026-H1", "2025-H2", "2025-H1", "2024-FY"]
    assert sorted(labels, key=R.period_sort_key) == ["2024-FY", "2025-H1", "2025-H2", "2026-H1"]


def test_overlap_problem_names_the_coarse_label_to_remove():
    problem = R.overlap_problem(["2025-H1", "2025-FY"])
    assert problem is not None
    assert "2025-FY contains 2025-H1" in problem
    assert "remove 2025-FY" in problem


def test_tiling_halves_have_no_overlap_problem():
    assert R.overlap_problem(["2024-H1", "2024-H2", "2025-H1", "2025-H2"]) is None


# ============================== windows ====================================


@pytest.mark.parametrize("quarters,ppy,expected", [
    (8, 4, 8), (4, 4, 4), (2, 4, 2), (3, 4, 3),     # quarterly: identity
    (8, 2, 4), (4, 2, 2), (2, 2, 1), (3, 2, 2),     # half-yearly: by time, ceil, min 1
])
def test_windows_convert_by_time(quarters, ppy, expected):
    assert R.periods_for(quarters, ppy) == expected


def test_period_unit_words():
    assert R.period_unit(4) == "quarters"
    assert R.period_unit(2) == "half-years"


# ============================ the loader ==================================


def entry(**overrides):
    raw = {"ticker": "HALF.AS", "name": "Half Yearly NV", "currency": "EUR", "status": "WATCH-GATED"}
    raw.update(overrides)
    return raw


def doc(*entries):
    return {"tickers": list(entries)}


def half(period, **kw):
    base = {"period": period, "basis": "reported", "accounting": "gaap"}
    base.update(kw)
    return base


def test_reporting_frequency_defaults_to_quarterly():
    e = parse_entry(entry(), 0)
    assert e.reporting_frequency == "quarterly"


@pytest.mark.parametrize("value", ["half_yearly", "HALF_YEARLY", " quarterly "])
def test_reporting_frequency_is_normalised(value):
    e = parse_entry(entry(reporting_frequency=value), 0)
    assert e.reporting_frequency == value.strip().lower()


def test_unknown_reporting_frequency_fails_the_run():
    with pytest.raises(ConfigError, match="reporting_frequency must be one of"):
        parse_watchlist(doc(entry(reporting_frequency="monthly")))


def test_half_yearly_ticker_loads_h1_h2_and_fy_labels():
    e = parse_entry(entry(reporting_frequency="half_yearly",
                          quarters=[half("2024-FY"), half("2025-H1"), half("2025-H2")]), 0)
    assert [q.period for q in e.quarters] == ["2024-FY", "2025-H1", "2025-H2"]


def test_half_yearly_ticker_rejects_a_quarterly_label():
    with pytest.raises(ConfigError, match="3-month period but the ticker reports half_yearly"):
        parse_watchlist(doc(entry(reporting_frequency="half_yearly",
                                  quarters=[half("2025-Q1")])))


def test_quarterly_ticker_rejects_a_half_year_label():
    with pytest.raises(ConfigError, match="6-month period but the ticker reports quarterly"):
        parse_watchlist(doc(entry(quarters=[half("2025-H1")])))


def test_quarterly_ticker_rejects_a_full_year_label():
    with pytest.raises(ConfigError, match="12-month period but the ticker reports quarterly"):
        parse_watchlist(doc(entry(quarters=[half("2025-FY")])))


def test_the_overlap_guard_refuses_h1_beside_fy_of_the_same_year():
    with pytest.raises(ConfigError, match="2025-FY contains 2025-H1"):
        parse_watchlist(doc(entry(reporting_frequency="half_yearly",
                                  quarters=[half("2025-H1"), half("2025-FY")])))


def test_the_overlap_guard_refuses_fy_then_h2_too():
    """Order does not matter to the guard: listing FY first still overlaps H2."""
    with pytest.raises(ConfigError, match="overlap"):
        parse_watchlist(doc(entry(reporting_frequency="half_yearly",
                                  quarters=[half("2025-FY"), half("2025-H2")])))


def test_the_overlap_guard_message_says_keep_the_finest():
    with pytest.raises(ConfigError, match="keeps the finest resolution and never holds both"):
        parse_watchlist(doc(entry(reporting_frequency="half_yearly",
                                  quarters=[half("2025-H1"), half("2025-FY")])))


def test_a_lone_fy_loads_when_no_half_exists():
    """The reverse case: only the coarse figures exist, so the coarse period stays."""
    e = parse_entry(entry(reporting_frequency="half_yearly",
                          quarters=[half("2024-FY"), half("2025-H1")]), 0)
    assert [q.period for q in e.quarters] == ["2024-FY", "2025-H1"]


def test_halves_must_be_listed_oldest_first_by_span_not_by_string():
    with pytest.raises(ConfigError, match="oldest first"):
        parse_watchlist(doc(entry(reporting_frequency="half_yearly",
                                  quarters=[half("2025-H2"), half("2025-H1")])))


def test_a_quarterly_history_is_unchanged_by_the_guard():
    e = parse_entry(entry(quarters=[half(f"2025-Q{i}") for i in (1, 2, 3, 4)]), 0)
    assert len(e.quarters) == 4
    assert e.reporting_frequency == "quarterly"


def test_shipped_example_watchlist_still_loads():
    import yaml
    path = Path(__file__).resolve().parents[1] / "config" / "watchlist.example.yaml"
    entries = parse_watchlist(yaml.safe_load(path.read_text()))
    assert all(e.reporting_frequency == "quarterly" for e in entries)


# ======================= half-year windows in the rules ====================

HALVES = [f"20{y}-H{h}" for y in (23, 24, 25, 26) for h in (1, 2)]


def halves(n=6, **series):
    """n half-years oldest-first; each kwarg is a per-period list or scalar."""
    out = []
    for i in range(n):
        kw = {"basis": "reported", "accounting": "gaap"}
        for key, val in series.items():
            kw[key] = val[i] if isinstance(val, (list, tuple)) else val
        out.append(R.Quarter(period=HALVES[i], **kw))
    return out


def test_evaluate_rejects_an_unknown_frequency():
    with pytest.raises(ValueError, match="reporting_frequency"):
        R.evaluate_hard_kills([], [], AS_OF, reporting_frequency="monthly")


def test_half_yearly_rule_names_say_half_years_and_converted_counts():
    names = {r.rule: r.name for r in R.evaluate_hard_kills(halves(), [], AS_OF, "half_yearly")}
    # E30 names the basis 4.2.1 read. These halves carry no organic rate,
    # so it falls back to reported and says so.
    assert names["4.2.1"] == \
        "Revenue declining 1+ consecutive half-years (YoY, reported)"
    assert names["4.2.3"] == "2+ guidance cuts within trailing 2 half-years"
    assert names["4.2.4"] == "3+ EPS misses within trailing 4 half-years"
    assert names["4.2.7"].endswith("for 1+ half-years")
    assert names["4.3.soft"] == "Revenue declining 2+ consecutive half-years (sequential)"


def test_quarterly_rule_names_are_unchanged():
    names = {r.rule: r.name for r in R.evaluate_hard_kills([], [], AS_OF)}
    assert names["4.2.1"] == "Revenue declining 2+ consecutive quarters (YoY)"
    assert names["4.2.3"] == "2+ guidance cuts within trailing 4 quarters"
    assert names["4.2.4"] == "3+ EPS misses within trailing 8 quarters"
    assert names["4.2.7"] == "Receivables or inventory growing > 1.5x revenue growth for 2+ quarters"
    assert names["4.3.soft"] == "Revenue declining 3+ consecutive quarters (sequential)"


def test_one_half_year_of_yoy_decline_trips_4_2_1_on_a_half_yearly_name():
    """Two quarters are six months; so is one half-year. The literal span."""
    qs = halves(6, revenue_yoy=[0.03] * 5 + [-0.01])
    assert R.revenue_decline_kill(qs, 2).state == R.TRIP
    # the same six months on a quarterly name would need two observations
    assert R.revenue_decline_kill(qs, 4).state == R.NO_TRIP


def test_yoy_margin_comparison_looks_back_two_halves():
    """2025-H2 vs 2024-H2: index -2, not -4 (the list runs 2023-H1 .. 2025-H2)."""
    qs = halves(6, op_margin=[0.20, 0.21, 0.20, 0.21, 0.20, 0.17],
                revenue_yoy=[0.02] * 5 + [-0.01])
    r = R.margin_compression_kill(qs, 2)
    assert r.state == R.TRIP                      # 0.21 -> 0.17 = 400bps, revenue down
    assert "2024-H2 op margin 21.00%" in " ".join(r.figures)
    # on a quarterly look-back (index -4) the comparator would be 2023-H2 at 0.21 too,
    # but the rule would demand 5 periods of history first
    assert R.margin_compression_kill(qs[-4:], 4).state == R.CANNOT_EVALUATE


def test_margin_rule_needs_three_halves_not_five():
    r = R.margin_compression_kill(halves(2, op_margin=0.2, revenue_yoy=0.0), 2)
    assert r.state == R.CANNOT_EVALUATE and "needs 3 half-years" in r.detail


def test_guidance_window_is_two_halves():
    qs = halves(6, guidance_action=["maintained", "maintained", "cut", "cut", "maintained", "maintained"])
    # trailing 2 half-years hold no cut -> no trip; a 4-period window (the
    # quarterly count) would reach back to both cuts
    assert R.guidance_cuts_kill(qs, 2).state == R.NO_TRIP
    assert R.guidance_cuts_kill(qs, 4).state == R.TRIP


def test_eps_window_is_four_halves():
    qs = halves(6, eps=[1.0] * 6, eps_consensus=[1.1, 1.1, 1.1, 0.9, 0.9, 0.9])
    # misses sit in the oldest three; the trailing 4 half-years hold one
    assert R.eps_misses_kill(qs, 2).state == R.NO_TRIP
    assert R.eps_misses_kill(qs, 4).state == R.TRIP        # 8-quarter window sees all three


def test_working_capital_needs_three_halves_and_reads_one():
    qs = halves(3, revenue_yoy=[0.02, 0.02, 0.02], receivables=[100, 100, 110], inventory=[50, 50, 50])
    r = R.working_capital_kill(qs, 2)
    assert r.state == R.TRIP                      # +10% receivables vs +2% revenue, one half-year
    assert R.working_capital_kill(qs, 4).state == R.CANNOT_EVALUATE


def test_sequential_soft_flag_needs_two_declines_on_halves():
    qs = halves(3, revenue=[100, 99, 98])
    assert R.sequential_decline_soft_flag(qs, 2).state == R.TRIP
    assert R.sequential_decline_soft_flag(qs, 4).state == R.CANNOT_EVALUATE


def test_year_ago_is_matched_by_label_not_position():
    """A gap in the history must not pair 2026-Q2 with 2025-Q1."""
    qs = [R.Quarter(period=p, basis="reported", accounting="gaap", revenue_yoy=0.05,
                    op_margin=m, receivables=rv, inventory=iv)
          for p, m, rv, iv in (("2025-Q1", 0.10, 100, 50), ("2025-Q3", 0.20, 100, 50),
                               ("2025-Q4", 0.20, 100, 50), ("2026-Q1", 0.20, 100, 50),
                               ("2026-Q2", 0.20, 100, 50))]
    # 2025-Q2 is missing: positional look-back would land on 2025-Q1 (0.10) and
    # report 1,000bps of EXPANSION against a quarter that is not the year-ago.
    assert R._year_ago(qs, 4, 4) is None
    r = R.margin_compression_kill(qs, 4)
    assert r.state == R.CANNOT_EVALUATE and "no year-ago period" in r.detail


def test_a_full_year_beside_halves_never_becomes_a_half_years_comparator():
    qs = [R.Quarter(period=p, basis="reported", accounting="gaap", revenue_yoy=0.02, op_margin=0.18)
          for p in ("2024-FY", "2025-FY", "2026-H1")]
    assert R._year_ago(qs, 2, 2) is None            # 2025-H1 is not loaded
    assert R.margin_compression_kill(qs, 2).state == R.CANNOT_EVALUATE


def test_label_matching_agrees_with_position_on_a_contiguous_history():
    qs = halves(6, op_margin=0.2, revenue_yoy=0.01)
    assert R._year_ago(qs, 5, 2).period == "2024-H2"
    assert R._year_ago(qs, 4, 2).period == "2024-H1"


# ============================ admission (earnings) =========================


def test_admit_rejects_a_malformed_label():
    a = R.admit_period(["2025-H1"], "PROVISIONAL", "half_yearly")
    assert not a.admitted and "not a label" in a.reason


def test_admit_rejects_the_wrong_kind_for_the_frequency():
    a = R.admit_period(["2025-H1"], "2025-Q3", "half_yearly")
    assert not a.admitted and "reports half_yearly" in a.reason
    b = R.admit_period(["2025-Q1"], "2025-H1", "quarterly")
    assert not b.admitted and "reports quarterly" in b.reason


def test_a_reread_displaces_the_stored_row_instead_of_sitting_beside_it():
    a = R.admit_period(["2025-Q4", "2026-Q1", "2026-Q2"], "2026-Q2", "quarterly")
    assert a.admitted and a.displaced == ("2026-Q2",)
    assert "in place of the stored entry" in a.reason


def test_a_coarser_period_over_a_finer_one_is_rejected():
    a = R.admit_period(["2025-H1"], "2025-FY", "half_yearly")
    assert not a.admitted and "2025-H1, which is finer" in a.reason


def test_a_finer_period_displaces_the_coarser_and_says_to_remove_it():
    a = R.admit_period(["2024-FY", "2025-FY"], "2025-H1", "half_yearly")
    assert a.admitted and a.displaced == ("2025-FY",)
    assert "REMOVED" in a.reason


def test_a_non_overlapping_period_is_simply_admitted():
    a = R.admit_period(["2025-H1", "2025-H2"], "2026-H1", "half_yearly")
    assert a.admitted and a.displaced == ()


# ------------------------ through `vss earnings` -------------------------

HALF_WATCHLIST = """
tickers:
  - ticker: HALF.AS
    name: Half Yearly NV
    currency: EUR
    status: HELD
    fv_bull: 140.0    # the exit test C4/E42 runs on (owner, 2026-09-20)
    stop_price: 40.0
    reporting_frequency: half_yearly
    exec_changes: []
    quarters:
      - {period: 2024-H1, revenue: 8000, revenue_yoy: 0.02, op_margin: 0.160, guidance_action: maintained, basis: reported, accounting: gaap, receivables: 3000, inventory: 2000}
      - {period: 2024-H2, revenue: 8100, revenue_yoy: 0.02, op_margin: 0.162, guidance_action: maintained, basis: reported, accounting: gaap, receivables: 3050, inventory: 2020}
      - {period: 2025-H1, revenue: 8200, revenue_yoy: 0.025, op_margin: 0.165, guidance_action: cut, basis: reported, accounting: gaap, receivables: 3100, inventory: 2040}
      - {period: 2025-H2, revenue: 8300, revenue_yoy: 0.025, op_margin: 0.166, guidance_action: maintained, basis: reported, accounting: gaap, receivables: 3150, inventory: 2060}
"""

QUARTERLY_WATCHLIST = """
tickers:
  - ticker: ACME.ST
    name: ACME Industries
    currency: SEK
    status: HELD
    fv_bull: 140.0    # the exit test C4/E42 runs on (owner, 2026-09-20)
    stop_price: 150.0
    exec_changes: []
    quarters:
      - {period: 2025-Q3, revenue: 4150, revenue_yoy: 0.01, op_margin: 0.138, guidance_action: maintained, basis: reported, accounting: gaap}
      - {period: 2025-Q4, revenue: 4140, revenue_yoy: 0.01, op_margin: 0.135, guidance_action: maintained, basis: reported, accounting: gaap}
      - {period: 2026-Q1, revenue: 4130, revenue_yoy: 0.01, op_margin: 0.130, guidance_action: maintained, basis: reported, accounting: gaap}
      - {period: 2026-Q2, revenue: 4120, revenue_yoy: 0.01, op_margin: 0.120, guidance_action: cut, basis: reported, accounting: gaap}
"""


class FakeResponse:
    def __init__(self, payload):
        self._payload = payload.encode("utf-8")
        self.headers = {"Content-Type": "application/json"}

    def read(self, *args):
        return self._payload

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False


def mock_llm(content):
    def transport(request, timeout=None):
        return FakeResponse(json.dumps({"choices": [{"message": {"content": content}}]}))
    return transport


def fake_fetch(url):
    return S.PrimarySource(url=url, text=S.html_to_text(RELEASE.read_text()),
                           content_type="text/html")


@pytest.fixture(autouse=True)
def api_key(monkeypatch):
    monkeypatch.setenv(X.KEY_ENV, "test-key-not-real")


def payload_for(period):
    payload = json.loads(EXTRACTION_JSON.read_text())
    payload["period"] = {"value": period, "sentence": f"the {period} column"}
    return json.dumps(payload)


def run(tmp_path, watchlist, ticker, period, **kw):
    wl = tmp_path / "watchlist.yaml"
    wl.write_text(watchlist)
    params = dict(ticker=ticker, url="https://example.com/r", watchlist_path=wl,
                  db_path=tmp_path / "vss.sqlite",
                  now=datetime(2026, 8, 22, 9, 0).astimezone(),
                  transport=mock_llm(payload_for(period)), fetcher=fake_fetch)
    params.update(kw)
    return E.run_earnings(**params)


def test_a_reread_of_a_loaded_quarter_is_not_counted_twice(tmp_path):
    """The SAP Q2 2026 artefact: one cut, loaded and re-read, read as two."""
    _, alert = run(tmp_path, QUARTERLY_WATCHLIST, "ACME.ST", "2026-Q2")
    assert "already loaded: this re-read is evaluated in place" in alert
    assert "2 guidance cuts" not in alert
    assert "1 guidance cut(s)" in alert


def test_a_quarter_offered_to_a_half_yearly_ticker_is_rejected_not_proposed(tmp_path):
    _, alert = run(tmp_path, HALF_WATCHLIST, "HALF.AS", "2026-Q1")
    assert "## OVERLAP GUARD" in alert
    assert "PERIOD REJECTED -- NOT PROPOSED, NOT EVALUATED" in alert
    assert "reports half_yearly, which stores H1/H2/FY periods only" in alert
    assert "REJECTED BY THE OVERLAP GUARD" in alert
    assert "- period: 2026-Q1" not in alert          # no YAML block to paste
    assert "counted in half-years" in alert


def test_a_full_year_over_loaded_halves_is_rejected(tmp_path):
    _, alert = run(tmp_path, HALF_WATCHLIST, "HALF.AS", "2025-FY")
    assert "PERIOD REJECTED" in alert
    assert "2025-H1, 2025-H2, which is finer" in alert
    assert "- period: 2025-FY" not in alert


def test_a_new_half_year_is_admitted_and_evaluated_in_half_year_windows(tmp_path):
    _, alert = run(tmp_path, HALF_WATCHLIST, "HALF.AS", "2026-H1")
    assert "Period 2026-H1 admitted: 2026-H1 overlaps nothing loaded" in alert
    assert "- period: 2026-H1" in alert
    # the fixture's guidance_action is "cut": trailing 2 half-years = 2025-H2 (maintained) + 2026-H1 (cut) = 1 cut
    assert "2+ guidance cuts within trailing 2 half-years" in alert
    assert "1 guidance cut(s)" in alert


def test_a_finer_half_over_a_loaded_full_year_displaces_it(tmp_path):
    wl = HALF_WATCHLIST.replace(
        "      - {period: 2025-H1, revenue: 8200, revenue_yoy: 0.025, op_margin: 0.165, guidance_action: cut, basis: reported, accounting: gaap, receivables: 3100, inventory: 2040}\n"
        "      - {period: 2025-H2, revenue: 8300, revenue_yoy: 0.025, op_margin: 0.166, guidance_action: maintained, basis: reported, accounting: gaap, receivables: 3150, inventory: 2060}\n",
        "      - {period: 2025-FY, revenue: 16500, revenue_yoy: 0.025, op_margin: 0.165, guidance_action: cut, basis: reported, accounting: gaap, receivables: 3150, inventory: 2060}\n")
    _, alert = run(tmp_path, wl, "HALF.AS", "2025-H1")
    assert "Period 2025-H1 admitted" in alert
    assert "Displaced for this evaluation: 2025-FY" in alert
    assert "must be REMOVED from the watchlist before this entry is pasted" in alert
    assert "- period: 2025-H1" in alert


def test_a_bad_target_period_is_refused_before_any_extraction(tmp_path):
    with pytest.raises(ConfigError, match="--period must look like"):
        run(tmp_path, HALF_WATCHLIST, "HALF.AS", "2026-H1", target_period="2026-S1")


def test_target_period_accepts_half_year_labels(tmp_path):
    _, alert = run(tmp_path, HALF_WATCHLIST, "HALF.AS", "2026-H1", target_period="2026-H1")
    assert "- period: 2026-H1" in alert


def test_the_prompt_tells_the_model_about_half_year_labels():
    assert '"YYYY-H1" or "YYYY-H2"' in X.SYSTEM_PROMPT
    assert '"YYYY-FY"' in X.SYSTEM_PROMPT
    body = X.build_request("text", X.DEFAULT_MODEL, target_period="2025-H1")
    assert "YYYY-H1/H2 a six-month half-year" in body["messages"][1]["content"]
