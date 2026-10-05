"""The earnings pipeline: recorded release, mocked LLM, no network.

Covers the four hard constraints:
  * the LLM never decides materiality and never writes prose
  * alerts say POSSIBLE TRIP, never "sell", with the source URL first
  * any failure, null or ambiguity marks the run EXTRACTION UNCERTAIN
  * extracted figures NEVER reach the quarters: block
"""

import json
import sqlite3
from datetime import date, datetime
from pathlib import Path

import pytest

from vss import earnings as E
from vss import extract as X
from vss import rules as R
from vss import source as S
from vss.config import ConfigError

FIXTURES = Path(__file__).resolve().parent / "fixtures" / "earnings"
RELEASE = FIXTURES / "acme-q2-2026-release.html"
EXTRACTION_JSON = FIXTURES / "acme-q2-2026-extraction.json"

RUN_TS = datetime(2026, 7, 24, 22, 30)
AS_OF = date(2026, 7, 24)
URL = "https://acme.example.com/investors/q2-2026"

WATCHLIST = """
tickers:
  - ticker: ACME.ST
    name: ACME Industries
    currency: SEK
    status: HELD
    fv_bull: 420.0    # the exit test C4/E42 runs on (owner, 2026-09-20)
    fv_base: 300.0
    tier: 2
    stop_price: 150.0
    catalyst_date: 2026-07-23
    catalyst_event: Q2 2026 results
    exec_changes: []
    quarters:
      - {period: 2024-Q3, revenue: 4000, revenue_yoy: 0.02, op_margin: 0.140, guidance_action: maintained, basis: reported, accounting: gaap, receivables: 1500, inventory: 1200}
      - {period: 2024-Q4, revenue: 4100, revenue_yoy: 0.02, op_margin: 0.142, guidance_action: maintained, basis: reported, accounting: gaap, receivables: 1520, inventory: 1210}
      - {period: 2025-Q1, revenue: 4200, revenue_yoy: 0.01, op_margin: 0.139, guidance_action: maintained, basis: reported, accounting: gaap, receivables: 1550, inventory: 1220}
      - {period: 2025-Q2, revenue: 4265, revenue_yoy: 0.01, op_margin: 0.141, guidance_action: maintained, basis: reported, accounting: gaap, receivables: 1610, inventory: 1230}
      - {period: 2025-Q3, revenue: 4150, revenue_yoy: -0.01, op_margin: 0.138, guidance_action: cut, basis: reported, accounting: gaap, receivables: 1700, inventory: 1235}
      - {period: 2025-Q4, revenue: 4140, revenue_yoy: -0.01, op_margin: 0.135, guidance_action: maintained, basis: reported, accounting: gaap, receivables: 1800, inventory: 1238}
      - {period: 2026-Q1, revenue: 4130, revenue_yoy: -0.02, op_margin: 0.130, guidance_action: maintained, basis: reported, accounting: gaap, receivables: 1900, inventory: 1239}
"""

NON_HELD = WATCHLIST.replace("status: HELD", "status: WATCH-GATED")


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
    """A transport returning `content` as the assistant message."""
    def transport(request, timeout=None):
        return FakeResponse(json.dumps({"choices": [{"message": {"content": content}}]}))
    return transport


def recorded_llm():
    return mock_llm(EXTRACTION_JSON.read_text())


def fake_fetch(url):
    return S.PrimarySource(url=url, text=S.html_to_text(RELEASE.read_text()),
                           content_type="text/html")


@pytest.fixture(autouse=True)
def api_key(monkeypatch):
    """A key must be present or call_openrouter refuses -- by design.

    The mock transport replaces the network, not the credential check.
    """
    monkeypatch.setenv(X.KEY_ENV, "test-key-not-real")


@pytest.fixture
def project(tmp_path):
    wl = tmp_path / "watchlist.yaml"
    wl.write_text(WATCHLIST)
    return {"watchlist_path": wl, "db_path": tmp_path / "vss.sqlite"}


def run(project, **kw):
    params = dict(ticker="ACME.ST", url=URL, watchlist_path=project["watchlist_path"],
                  db_path=project["db_path"], now=RUN_TS.astimezone(),
                  transport=recorded_llm(), fetcher=fake_fetch)
    params.update(kw)
    return E.run_earnings(**params)


# --- the recorded release ------------------------------------------------


def test_release_flattens_to_text_with_sentences_intact():
    text = S.html_to_text(RELEASE.read_text())
    assert "var tracking" not in text and ".hdr" not in text
    assert "Revenue for the second quarter was SEK 4,120 million" in text


def test_extraction_reads_the_known_figures():
    result = X.parse_response(EXTRACTION_JSON.read_text(), URL, "test-model")
    assert result.figures["revenue"] == 4120.0
    assert result.figures["op_margin"] == pytest.approx(0.120)
    assert result.guidance_action == "cut"
    assert result.basis == "reported"
    assert "4,120 million" in result.sentences["revenue"]


# --- constraint: consensus is manual only --------------------------------


def test_missing_api_key_fails_loud_rather_than_silently_skipping(monkeypatch):
    monkeypatch.delenv(X.KEY_ENV, raising=False)
    with pytest.raises(X.ExtractionError, match="no API key"):
        X.call_openrouter("text", model="m", transport=mock_llm("{}"))


def test_key_is_never_embedded_in_the_source():
    import inspect
    assert "sk-" not in inspect.getsource(X)


def test_eps_consensus_is_not_extractable():
    assert "eps_consensus" not in X.EXTRACTABLE_FIELDS
    assert "eps_consensus" not in X.SYSTEM_PROMPT
    assert "eps_consensus" in X.FORBIDDEN_FIELDS


def test_a_model_returning_consensus_has_it_discarded_and_flagged():
    payload = json.loads(EXTRACTION_JSON.read_text())
    payload["figures"]["eps_consensus"] = {"value": 2.40, "sentence": "analysts expected 2.40"}
    result = X.parse_response(json.dumps(payload), URL, "m")
    assert "eps_consensus" not in result.figures
    assert any("forbidden" in i for i in result.issues)
    assert result.uncertain


def test_provisional_quarter_never_carries_consensus():
    result = X.parse_response(EXTRACTION_JSON.read_text(), URL, "m")
    assert E.provisional_quarter(result, "2026-Q2").eps_consensus is None


def test_rule_4_reports_cannot_evaluate_without_consensus(project):
    _, alert = run(project)
    assert "4.2.4" in alert
    assert "MANUAL ONLY" in alert


# --- constraint: nothing is ever written to quarters: --------------------


def test_run_never_modifies_the_watchlist(project):
    before = project["watchlist_path"].read_bytes()
    run(project)
    assert project["watchlist_path"].read_bytes() == before


def test_no_module_in_the_pipeline_can_write_yaml():
    """Structural guarantee, not a behavioural one."""
    import inspect
    for module in (X, E, S):
        src = inspect.getsource(module)
        assert "yaml.dump" not in src and "safe_dump" not in src
        assert ".write_text(" not in src


def test_proposed_entry_is_labelled_not_written(project):
    _, alert = run(project)
    assert "PROPOSED quarters: ENTRY -- NOT WRITTEN" in alert
    assert "vss will never write this" in alert
    assert "eps_consensus:        # MANUAL ONLY" in alert


# --- constraint: alert wording and ordering ------------------------------


def test_alert_leads_with_the_primary_source_url(project):
    _, alert = run(project)
    body = [l for l in alert.splitlines() if l.strip()]
    url_line = next(i for i, l in enumerate(body) if "PRIMARY SOURCE" in l)
    trip_line = next(i for i, l in enumerate(body) if E.TRIP_HEADLINE in l)
    assert url_line < trip_line
    assert URL in body[url_line]


def test_alert_says_possible_trip_and_never_recommends(project):
    _, alert = run(project)
    assert "4.2 POSSIBLE TRIP - VERIFY AGAINST SOURCE" in alert
    lowered = alert.lower()
    for word in (" sell", "you should", "recommend", "we advise", "exit the position"):
        assert word not in lowered


def test_guidance_cut_trips_rule_3(project):
    """Stored 2025-Q3 cut plus the extracted cut = 2 in trailing 4."""
    _, alert = run(project)
    assert "4.2.3" in alert
    assert "guidance cuts" in alert


def test_trip_carries_its_source_sentence_and_url(project):
    _, alert = run(project)
    assert "lowers its full year 2026 revenue outlook" in alert
    assert alert.count(URL) >= 2   # header plus per-trip attribution


def test_soft_flag_is_separated_from_hard_kills(project):
    _, alert = run(project)
    if "SOFT FLAGS" in alert:
        soft = alert.index("SOFT FLAGS")
        assert "NOT hard kills" in alert[soft:soft + 200]


# --- constraint: fail loud -----------------------------------------------


def test_null_figure_marks_the_run_uncertain(project):
    payload = json.loads(EXTRACTION_JSON.read_text())
    payload["figures"]["revenue"] = {"value": None, "sentence": None}
    _, alert = run(project, transport=mock_llm(json.dumps(payload)))
    assert E.UNCERTAIN_HEADLINE in alert
    missing = next(l for l in alert.splitlines() if "not stated in source:" in l)
    assert "revenue" in missing


def test_model_ambiguity_marks_the_run_uncertain(project):
    payload = json.loads(EXTRACTION_JSON.read_text())
    payload["ambiguities"] = ["revenue could be constant currency"]
    _, alert = run(project, transport=mock_llm(json.dumps(payload)))
    assert E.UNCERTAIN_HEADLINE in alert
    assert "constant currency" in alert


def test_unparseable_model_output_still_alerts(project):
    code, alert = run(project, transport=mock_llm("I think revenue fell a bit."))
    assert E.UNCERTAIN_HEADLINE in alert
    assert "did not return valid JSON" in alert
    assert code == 0   # an alert was still produced


def test_missing_basis_marks_the_run_uncertain(project):
    payload = json.loads(EXTRACTION_JSON.read_text())
    payload["basis"] = None
    _, alert = run(project, transport=mock_llm(json.dumps(payload)))
    assert "basis (reported vs constant-currency) not stated" in alert


def test_unreachable_source_alerts_rather_than_crashing(project):
    def boom(url):
        raise S.SourceError("HTTP 503")
    code, alert = run(project, fetcher=boom)
    assert code == 1
    assert E.UNCERTAIN_HEADLINE in alert and "503" in alert


def test_a_corrupt_pdf_is_refused_loudly():
    """vss reads PDFs now; one it cannot read still fails loudly.

    The refusal never became a shrug: a truncated file yields an error
    naming the file, not empty text that reads like a bad release.
    """
    class PdfResponse(FakeResponse):
        def __init__(self):
            super().__init__("%PDF-1.4 binary")
            self.headers = {"Content-Type": "application/pdf"}
    with pytest.raises(S.SourceError, match="cannot read PDF"):
        S.fetch("https://x.example/r.pdf", opener=lambda r, timeout=None: PdfResponse())


def test_news_host_is_warned_about():
    assert "primary source" in S.looks_like_news("https://www.reuters.com/x")
    assert S.looks_like_news("https://acme.example.com/investors") is None


# --- 4.2 on a candidate: FRAMEWORK Phase 2 VALIDATION --------------------
#
# The same rules are read in two situations. On a name you HOLD, a 4.2
# trip is thesis invalidation; on a candidate it is the validation gate
# that decides whether the name may become a position at all. Refusing
# WATCH-GATED and PIPELINE made it impossible to work a name up to a buy
# decision -- the step 4.2 exists to inform.

PIPELINE_WATCHLIST = WATCHLIST.replace("status: HELD", "status: PIPELINE")


def watchlist_file(tmp_path, text, name="alt.yaml"):
    path = tmp_path / name
    path.write_text(text)
    return path


@pytest.mark.parametrize("status,text", [
    ("WATCH-GATED", NON_HELD),
    ("PIPELINE", PIPELINE_WATCHLIST),
])
def test_a_candidate_is_evaluated_not_refused(project, tmp_path, status, text):
    code, alert = run(project, watchlist_path=watchlist_file(tmp_path, text))
    assert code == 0
    assert E.VALIDATION_HEADLINE in alert
    assert E.TRIP_HEADLINE not in alert
    assert f"**STATUS:** {status}" in alert
    assert "Phase 2 VALIDATION" in alert


def test_a_held_name_keeps_the_thesis_invalidation_wording(project):
    _, alert = run(project)
    assert E.TRIP_HEADLINE in alert
    assert E.VALIDATION_HEADLINE not in alert
    assert "**STATUS:** HELD" in alert
    assert "thesis invalidation" in alert


def test_a_candidate_trip_rejects_the_candidate_rather_than_a_thesis(project, tmp_path):
    _, alert = run(project, watchlist_path=watchlist_file(tmp_path, NON_HELD))
    assert "REJECTS THE CANDIDATE" in alert
    assert "there is no position here yet" in alert


def test_status_changes_the_framing_and_nothing_else(project, tmp_path):
    """Same rules, same figures. Only the words around them differ."""
    _, held = run(project)
    _, watch = run(project, watchlist_path=watchlist_file(tmp_path, NON_HELD))

    def section(alert, title):
        body = alert.split(f"## {title}")[1].split("## ")[0] if f"## {title}" in alert else ""
        return body.strip()

    for title in ("CANNOT EVALUATE", "NO TRIP",
                  "EXTRACTED FIGURES AND THEIR SOURCE SENTENCES",
                  "PROPOSED quarters: ENTRY -- NOT WRITTEN"):
        assert section(held, title) == section(watch, title), title
    # the trip findings themselves are identical -- only the heading moved
    assert section(held, E.TRIP_HEADLINE) == section(watch, E.VALIDATION_HEADLINE)


FRESH_CANDIDATE = """
tickers:
  - ticker: ACME.ST
    name: ACME Industries
    currency: SEK
    status: WATCH-GATED
    fv_base: 300.0
    tier: 2
    stop_price: 150.0
    exec_changes: []
    quarters: []
"""


def test_a_clean_candidate_is_not_told_it_may_buy(project, tmp_path):
    """Clearing 4.2 is one gate of Phase 2, not a decision.

    A candidate with no recorded history is the ordinary case: most
    rules cannot evaluate, none trip, and that is not permission.
    """
    _, alert = run(project, watchlist_path=watchlist_file(tmp_path, FRESH_CANDIDATE))
    assert "No 4.2 rule failed" in alert
    assert "It is not a decision" in alert
    lowered = alert.lower()
    for word in (" buy", "you should", "recommend", "we advise", "enter the position"):
        assert word not in lowered


def test_every_status_in_the_schema_is_accepted(project, tmp_path):
    from vss.rules import VALID_STATUSES

    from vss.rules import INTAKE_REFUSED_KEYS

    for status in VALID_STATUSES:
        text = WATCHLIST.replace("status: HELD", f"status: {status}")
        if status == "INTAKE":
            # E111: an intake is READ, NOT WATCHED, so it carries no entry
            # fact. The fixture's tier and stop belong to a name somebody
            # decided to enter; strip them rather than weaken the refusal.
            text = "\n".join(
                line for line in text.split("\n")
                if not any(line.strip().startswith(f"{k}:")
                           for k in INTAKE_REFUSED_KEYS))
        code, alert = run(project,
                          watchlist_path=watchlist_file(tmp_path, text, f"{status}.yaml"))
        assert code == 0, status
        assert f"**STATUS:** {status}" in alert


# --- shadow mode ---------------------------------------------------------


def test_shadow_is_the_default_and_is_visible(project):
    _, alert = run(project)
    assert "SHADOW MODE" in alert
    assert "nothing sent" in alert


def test_no_shadow_removes_the_banner(project):
    _, alert = run(project, shadow=False)
    assert "SHADOW MODE" not in alert


@pytest.mark.parametrize("shadow,flag", [(True, 1), (False, 0)])
def test_shadow_state_is_recorded_per_row(project, shadow, flag):
    run(project, shadow=shadow)
    conn = sqlite3.connect(project["db_path"])
    rows = conn.execute("SELECT shadow, ticker, trips FROM earnings_runs").fetchall()
    conn.close()
    assert rows[-1][0] == flag
    assert rows[-1][1] == "ACME.ST"


def test_every_run_is_logged_with_its_reasoning(project):
    run(project)
    conn = sqlite3.connect(project["db_path"])
    row = conn.execute(
        "SELECT source_url, model, extraction_uncertain, alert, raw_response "
        "FROM earnings_runs"
    ).fetchone()
    conn.close()
    assert row[0] == URL and row[1]
    assert row[3] and "PRIMARY SOURCE" in row[3]
    assert row[4], "raw model response must be retained for audit"


# --- catalyst proposal ---------------------------------------------------


def test_catalyst_resolved_is_proposed_never_written(project):
    before = project["watchlist_path"].read_bytes()
    _, alert = run(project)
    assert "PROPOSED catalyst_resolved -- NOT WRITTEN" in alert
    assert "catalyst_resolved: 2026-07-24" in alert
    assert project["watchlist_path"].read_bytes() == before


def test_default_model_id_is_vendor_prefixed():
    """OpenRouter ids are vendor/model; a bare name is rejected upstream."""
    assert "/" in X.DEFAULT_MODEL, "OpenRouter model id needs a vendor prefix"
    vendor, _, name = X.DEFAULT_MODEL.partition("/")
    assert vendor and name
    assert X.DEFAULT_MODEL != "deepseek/deepseek-chat", "that is V3, a different model"


def test_model_id_reaches_the_request_body():
    body = X.build_request("some release text", X.DEFAULT_MODEL)
    assert body["model"] == X.DEFAULT_MODEL
    assert body["temperature"] == 0


def test_model_env_override_wins(monkeypatch):
    monkeypatch.setenv(X.MODEL_ENV, "anthropic/some-model")
    captured = {}

    def transport(request, timeout=None):
        captured.update(json.loads(request.data))
        return FakeResponse(json.dumps({"choices": [{"message": {"content": "{}"}}]}))

    X.call_openrouter("text", transport=transport)
    assert captured["model"] == "anthropic/some-model"


def test_rejected_model_id_is_echoed_in_the_error():
    import urllib.error

    def transport(request, timeout=None):
        raise urllib.error.HTTPError(X.API_URL, 400, "Bad Request", {}, None)

    with pytest.raises(X.ExtractionError, match=X.DEFAULT_MODEL.replace("/", "/")):
        X.call_openrouter("text", transport=transport)


# --- bug 1: the source-domain matcher fired on the wrong domain ----------


@pytest.mark.parametrize("url", [
    "https://www.microsoft.com/en-us/investor/earnings/fy-2026-q4/press-release",
    "https://www.sap.com/investors/en/reports.html",
    "https://investors.nike.com/news/news-details/2026/",
    "https://www.lindabgroup.com/en/investors/reports",
    "https://hansabiopharma.com/investors/press-releases/",
    "https://www.unilever.com/investor-relations/results/",
])
def test_known_good_ir_domains_produce_no_warning(url):
    """microsoft.com contains the literal substring 'ft.com'.

    The old matcher tested `host in url`, so every Microsoft IR link was
    reported as a Financial Times article.
    """
    assert S.looks_like_news(url) is None


@pytest.mark.parametrize("url,expected", [
    ("https://www.ft.com/content/abc", "ft.com"),
    ("https://ft.com/content/abc", "ft.com"),
    ("https://finance.yahoo.com/news/x", "yahoo.com"),
    ("https://www.reuters.com/business/x", "reuters.com"),
    ("https://seekingalpha.com/article/x", "seekingalpha.com"),
])
def test_known_aggregators_warn_naming_the_right_domain(url, expected):
    warning = S.looks_like_news(url)
    assert warning is not None
    assert warning.startswith(expected), f"named the wrong domain: {warning}"


def test_matcher_uses_the_hostname_not_the_whole_url():
    """A domain appearing in a query string is not the publisher."""
    assert S.looks_like_news("https://acme.example.com/ir?ref=reuters.com") is None
    assert S.looks_like_news("https://acme.example.com/news/ft.com-coverage") is None


def test_subdomains_of_aggregators_still_warn():
    assert S.looks_like_news("https://markets.ft.com/data") is not None


# --- bug 2: quotes that do not contain the figure ------------------------


@pytest.mark.parametrize("value,sentence,field", [
    (80876, "Accounts receivable, net of allowance for doubtful accounts of "
            "$1,040 and $944", "receivables"),
    (1397, "Inventories", "inventory"),
    (500.0, "Revenue grew strongly in the period.", "revenue"),
    (2.5, "", "eps"),
    (2.5, None, "eps"),
])
def test_quote_without_the_figure_is_unverifiable(value, sentence, field):
    assert X.figure_supported(value, sentence, field) is False


@pytest.mark.parametrize("value,sentence,field", [
    (4120.0, "Revenue was SEK 4,120 million.", "revenue"),
    (-0.034, "a decrease of 3.4 per cent", "revenue_yoy"),
    (0.120, "an operating margin of 12.0 per cent", "op_margin"),
    (2.18, "Earnings per share amounted to SEK 2.18.", "eps"),
    (2.1, "Net debt in relation to EBITDA was 2.1 times.", "net_debt_ebitda"),
    (1980.0, "Accounts receivable increased to SEK 1,980 million", "receivables"),
])
def test_quote_containing_the_figure_is_verifiable(value, sentence, field):
    assert X.figure_supported(value, sentence, field) is True


def test_magnitudes_are_never_reconciled():
    """Inferring that 80.9 billion means 80876 million would be deriving."""
    assert X.figure_supported(80876, "Revenue was $80.9 billion", "revenue") is False


def test_european_and_us_separators_both_accepted():
    assert X.figure_supported(4120.0, "SEK 4,120 million", "revenue")
    assert X.figure_supported(4120.0, "SEK 4.120 miljoner", "revenue")


def test_unverifiable_figure_is_nulled_and_reported(project):
    payload = json.loads(EXTRACTION_JSON.read_text())
    payload["figures"]["receivables"] = {
        "value": 80876,
        "sentence": "Accounts receivable, net of allowance for doubtful accounts "
                    "of $1,040 and $944",
        "source_type": "table", "period_column": "June 30, 2026",
    }
    result = X.parse_response(json.dumps(payload), URL, "m")
    assert result.figures["receivables"] is None
    assert "receivables" in result.unverifiable
    assert any(X.PROVENANCE_UNVERIFIABLE in i for i in result.issues)
    assert result.uncertain


def test_unverifiable_figure_appears_in_the_alert(project):
    payload = json.loads(EXTRACTION_JSON.read_text())
    payload["figures"]["inventory"] = {
        "value": 1397, "sentence": "Inventories",
        "source_type": "table", "period_column": "June 30, 2026",
    }
    _, alert = run(project, transport=mock_llm(json.dumps(payload)))
    assert X.PROVENANCE_UNVERIFIABLE in alert
    assert "1397" in alert and "Inventories" in alert
    assert E.UNCERTAIN_HEADLINE in alert


def test_an_unverifiable_figure_cannot_trip_a_rule(project):
    """A dropped figure is null, so rules report CANNOT EVALUATE, not TRIP."""
    payload = json.loads(EXTRACTION_JSON.read_text())
    for field in ("receivables", "inventory"):
        payload["figures"][field] = {"value": 999999, "sentence": "Balance sheet items"}
    _, alert = run(project, transport=mock_llm(json.dumps(payload)))
    trip_section = alert.split("## SOFT FLAGS")[0]
    assert "4.2.7" not in trip_section or "CANNOT EVALUATE" in alert


# --- period_column -------------------------------------------------------


def test_period_column_is_recorded_and_shown(project):
    payload = json.loads(EXTRACTION_JSON.read_text())
    payload["figures"]["receivables"] = {
        "value": 1980.0,
        "sentence": "Accounts receivable increased to SEK 1,980 million from SEK 1,610 million.",
        "source_type": "table", "period_column": "30 June 2026",
    }
    result = X.parse_response(json.dumps(payload), URL, "m")
    assert result.period_columns["receivables"] == "30 June 2026"
    _, alert = run(project, transport=mock_llm(json.dumps(payload)))
    assert "Column read" in alert and "30 June 2026" in alert


def test_table_figure_without_a_column_is_flagged(project):
    """A balance sheet has two period columns; an unattributed figure says so."""
    payload = json.loads(EXTRACTION_JSON.read_text())
    payload["figures"]["receivables"] = {
        "value": 1980.0,
        "sentence": "Accounts receivable increased to SEK 1,980 million from SEK 1,610 million.",
        "source_type": "table", "period_column": None,
    }
    result = X.parse_response(json.dumps(payload), URL, "m")
    assert any("period_column" in i for i in result.issues)
    _, alert = run(project, transport=mock_llm(json.dumps(payload)))
    assert "NOT RECORDED" in alert


def test_prose_figure_needs_no_column(project):
    result = X.parse_response(EXTRACTION_JSON.read_text(), URL, "m")
    assert not any("period_column" in i for i in result.issues)


def test_prompt_demands_the_number_be_in_the_quote():
    assert "WHEREVER YOU READ THE NUMBER" in X.SYSTEM_PROMPT
    assert "period_column" in X.SYSTEM_PROMPT


# --- prompt: source fidelity, with worked examples -----------------------


def test_prompt_forbids_mixing_table_numbers_with_prose_quotes():
    assert "SOURCE FIDELITY" in X.SYSTEM_PROMPT
    assert "Never mix them." in X.SYSTEM_PROMPT
    assert "PROSE'S OWN PRECISION" in X.SYSTEM_PROMPT


def test_prompt_carries_both_correct_and_wrong_worked_examples():
    prompt = X.SYSTEM_PROMPT
    assert "VALIDATION EXAMPLES" in prompt
    assert "CORRECT -- table citation" in prompt
    assert "CORRECT -- prose citation" in prompt
    assert "WRONG -- mixes sources" in prompt
    # The worked example must itself obey the rule it teaches.
    assert X.figure_supported(90007, "Revenue $90,007 $76,441", "revenue")
    assert X.figure_supported(90000, "Revenue was $90.0 billion and increased 18%.", "revenue")
    assert not X.figure_supported(90007, "Revenue was $90.0 billion and increased 18%.", "revenue")


def test_scale_word_is_a_unit_conversion_not_a_reconciliation():
    """"$90.0 billion" states 90000 millions -- the same quantity."""
    assert X.figure_supported(90000, "Revenue was $90.0 billion", "revenue")
    assert X.figure_supported(90.0, "Revenue was $90.0 billion", "revenue")
    # A DIFFERENT quantity still fails, at any scale.
    assert not X.figure_supported(80876, "Total revenue was $80.9 billion", "revenue")
    assert not X.figure_supported(90007, "Revenue was $90.0 billion", "revenue")


def test_mixed_source_extraction_is_dropped_end_to_end(project):
    """The exact live failure: table number, prose quote."""
    payload = json.loads(EXTRACTION_JSON.read_text())
    payload["figures"]["revenue"] = {
        "value": 90007, "source_type": "prose",
        "sentence": "Revenue was $90.0 billion and increased 18%.",
        "period_column": None,
    }
    result = X.parse_response(json.dumps(payload), URL, "m")
    assert result.figures["revenue"] is None
    assert "revenue" in result.unverifiable


# --- period label: fiscal vs calendar ------------------------------------


def test_prompt_pins_the_period_format_and_basis():
    # Normalise wrapping and case: the prompt is line-wrapped prose.
    flat = " ".join(X.SYSTEM_PROMPT.split()).lower()
    assert "period_basis" in flat
    assert '"yyyy-qn"' in flat
    assert "fiscal q4 2026 ended 30 june 2026" in flat
    assert "calendar q4 2026 is october-december" in flat


def test_period_basis_is_captured():
    result = X.parse_response(EXTRACTION_JSON.read_text(), URL, "m")
    assert result.period_basis == "calendar"
    assert not any("period_basis" in i for i in result.issues)


def test_period_without_a_basis_is_flagged():
    """FY26-Q4 and 2026-Q4 are not the same three months."""
    payload = json.loads(EXTRACTION_JSON.read_text())
    payload["period_basis"] = None
    result = X.parse_response(json.dumps(payload), URL, "m")
    assert any("period_basis" in i for i in result.issues)
    assert result.uncertain


def test_period_basis_reaches_the_proposed_entry(project):
    _, alert = run(project)
    assert "period_basis: calendar" in alert


def test_watchlist_rejects_a_ticker_mixing_fiscal_and_calendar_quarters():
    from vss.config import ConfigError, parse_watchlist
    entry = {
        "ticker": "X", "name": "X", "currency": "USD", "status": "HELD",
        "quarters": [
            {"period": "2026-Q1", "period_basis": "fiscal"},
            {"period": "2026-Q2", "period_basis": "calendar"},
        ],
    }
    with pytest.raises(ConfigError, match="mix period_basis"):
        parse_watchlist({"tickers": [entry]})


def test_watchlist_accepts_a_consistent_basis():
    from vss.config import parse_entry
    entry = parse_entry({
        "ticker": "X", "name": "X", "currency": "USD", "status": "HELD",
        "fv_bull": 140.0,          # a holding carries its exit test (2026-09-20)
        "quarters": [
            {"period": "2026-Q3", "period_basis": "fiscal"},
            {"period": "2026-Q4", "period_basis": "fiscal"},
        ],
    }, 0)
    assert [q.period_basis for q in entry.quarters] == ["fiscal", "fiscal"]


# --- negative claims need provenance too ---------------------------------


def test_guidance_none_without_a_quote_becomes_null():
    """"No guidance action" is a claim about the source."""
    payload = json.loads(EXTRACTION_JSON.read_text())
    payload["guidance_action"] = {"value": "none", "sentence": None}
    result = X.parse_response(json.dumps(payload), URL, "m")
    assert result.guidance_action is None
    assert "guidance_action" in result.unverifiable
    assert any("needs provenance" in i for i in result.issues)


def test_guidance_none_with_a_quote_is_kept():
    payload = json.loads(EXTRACTION_JSON.read_text())
    payload["guidance_action"] = {
        "value": "none",
        "sentence": "The company did not update its full-year outlook.",
    }
    result = X.parse_response(json.dumps(payload), URL, "m")
    assert result.guidance_action == "none"
    assert "guidance_action" not in result.unverifiable


@pytest.mark.parametrize("action", ["cut", "raised", "maintained", "none"])
def test_every_guidance_value_needs_a_quote(action):
    payload = json.loads(EXTRACTION_JSON.read_text())
    payload["guidance_action"] = {"value": action, "sentence": None}
    result = X.parse_response(json.dumps(payload), URL, "m")
    assert result.guidance_action is None


def test_unquoted_guidance_cannot_trip_the_cuts_rule(project):
    """A null guidance_action reports CANNOT EVALUATE, never a trip."""
    payload = json.loads(EXTRACTION_JSON.read_text())
    payload["guidance_action"] = {"value": "cut", "sentence": None}
    _, alert = run(project, transport=mock_llm(json.dumps(payload)))
    assert "4.2.3" in alert
    assert "guidance_action not set" in alert
    assert "needs provenance" in alert


def test_prompt_requires_provenance_for_negative_claims():
    assert "EVERY CLAIM NEEDS PROVENANCE" in X.SYSTEM_PROMPT
    assert "not \"none\"" in X.SYSTEM_PROMPT


# --- PDF primary sources -------------------------------------------------
#
# The fixture is a REAL filing, not a hand-written one: pages 2, 4 and 32
# of Berkshire Hathaway's Form 10-Q for the quarter ended 30 June 2025, a
# public SEC filing. A real statement page carries a hazard an invented
# one does not -- FOUR period columns under a two-line stacked header:
#
#     Second Quarter First Six Months
#     2025 2024 2025 2024
#     Total revenues 92,515 93,653 182,240 183,522
#
# The row contains its figures, so it can evidence them. It cannot say
# WHICH of the four was read -- that is period_column's job, and these
# tests hold both halves of the rule to the PDF path.

PDF_RELEASE = FIXTURES / "berkshire-10q-2025-q2-excerpt.pdf"
PDF_URL = "https://www.berkshirehathaway.com/qtrly/2ndqtr25.pdf"
REVENUE_ROW = "Total revenues 92,515 93,653 182,240 183,522"
INVENTORY_ROW = "Inventories 24,371 24,008"
PERIOD_HEADER = "Second Quarter First Six Months"

PDF_WATCHLIST = """
tickers:
  - ticker: BRK.B
    name: Berkshire Hathaway
    currency: USD
    status: HELD
    fv_bull: 784.0    # the exit test C4/E42 runs on (owner, 2026-09-20)
    fv_base: 560.0
    tier: 1
    stop_price: 380.0
    exec_changes: []
    quarters: []
"""


class BytesResponse:
    """A response carrying raw bytes. A PDF is not text and never was."""

    def __init__(self, payload: bytes, content_type: str):
        self._payload = payload
        self.headers = {"Content-Type": content_type}

    def read(self, size=None):
        return self._payload if size is None else self._payload[:size]

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False


def pdf_opener(payload=None, content_type="application/pdf"):
    data = PDF_RELEASE.read_bytes() if payload is None else payload
    return lambda request, timeout=None: BytesResponse(data, content_type)


def fetch_pdf(url=PDF_URL, **kw):
    return S.fetch(url, opener=pdf_opener(**kw))


def pdf_extraction(figures=None, **overrides):
    """An extraction citing rows that really are in the fixture PDF."""
    payload = {
        "period": {"value": "2025-Q2", "sentence": PERIOD_HEADER},
        "period_basis": "calendar",
        "basis": "reported",
        "accounting": "gaap",
        "guidance_action": {"value": None, "sentence": None},
        "figures": {
            "revenue": {"value": 92515, "source_type": "table",
                        "period_column": "Second Quarter 2025",
                        "sentence": REVENUE_ROW},
            "inventory": {"value": 24371, "source_type": "table",
                          "period_column": "June 30, 2025",
                          "sentence": INVENTORY_ROW},
        },
        "exec_changes": [],
        "ambiguities": [],
    }
    payload["figures"].update(figures or {})
    payload.update(overrides)
    return payload


@pytest.fixture
def pdf_project(tmp_path):
    wl = tmp_path / "watchlist.yaml"
    wl.write_text(PDF_WATCHLIST)
    return {"watchlist_path": wl, "db_path": tmp_path / "vss.sqlite"}


def run_pdf(pdf_project, payload=None, **kw):
    params = dict(
        ticker="BRK.B", url=PDF_URL,
        watchlist_path=pdf_project["watchlist_path"], db_path=pdf_project["db_path"],
        now=RUN_TS.astimezone(),
        transport=mock_llm(json.dumps(payload or pdf_extraction())),
        fetcher=lambda url: fetch_pdf(url),
    )
    params.update(kw)
    return E.run_earnings(**params)


def test_a_pdf_flattens_to_text_with_its_statement_rows_intact():
    source = fetch_pdf()
    assert REVENUE_ROW in source.text
    assert INVENTORY_ROW in source.text
    assert PERIOD_HEADER in source.text


def test_a_pdf_source_says_it_came_out_of_a_pdf():
    """The reader must know the text is a reconstruction of the report."""
    source = fetch_pdf()
    assert any("extracted from a PDF" in w for w in source.warnings)


def test_a_pdf_served_as_a_binary_download_is_still_read():
    """IR hosts serve reports as octet-stream from extensionless URLs."""
    source = S.fetch("https://brk.example/download?doc=17",
                     opener=pdf_opener(content_type="application/octet-stream"))
    assert REVENUE_ROW in source.text


def test_html_is_not_treated_as_a_pdf():
    source = S.fetch("https://acme.example.com/q2",
                     opener=lambda r, timeout=None: BytesResponse(
                         RELEASE.read_bytes(), "text/html"))
    assert "Revenue for the second quarter was SEK 4,120 million" in source.text
    assert not any("PDF" in w for w in source.warnings)


# --- the provenance rule, unchanged, on the PDF path ---------------------


@pytest.mark.parametrize("value", [92515, 93653, 182240, 183522])
def test_a_quoted_statement_row_supports_the_figures_it_contains(value):
    """Containment is what the quote is asked for -- any column satisfies it."""
    assert X.figure_supported(value, REVENUE_ROW, "revenue")


@pytest.mark.parametrize("value", [92514, 92.5, 100000, 92515000])
def test_a_quoted_row_does_not_support_a_figure_it_lacks(value):
    assert not X.figure_supported(value, REVENUE_ROW, "revenue")


def test_a_row_whose_number_did_not_survive_extraction_is_unverifiable():
    """The rule the PDF work must not bend.

    When a PDF's table reconstructs badly the number and its label come
    apart, and the quote is a bare label again. That is PROVENANCE
    UNVERIFIABLE -- the same answer as for any other unevidenced figure.
    """
    assert not X.figure_supported(24371, "Inventories", "inventory")
    assert not X.figure_supported(24371, "Inventories 24,008", "inventory")


# Observed live, extracted from the real Lindab (LIAB.ST) interim report
# for January-June 2026 -- one of the two holdings this feature exists for.
# EIGHT period columns on one row: Q2/26, Q2/25, change, H1/26, H1/25,
# change, rolling twelve months, full year.
LINDAB_SALES_ROW = "Net sales, SEK m 3,306 3,253 2 6,309 6,467 -2 12,696 12,854"
LINDAB_MARGIN_ROW = "Operating margin, % 6.6 8.6 - 6.4 7.9 - 7.8 8.5"


@pytest.mark.parametrize("value,row,field", [
    (3306.0, LINDAB_SALES_ROW, "revenue"),
    (3253.0, LINDAB_SALES_ROW, "revenue"),
    (12696.0, LINDAB_SALES_ROW, "revenue"),
    (0.066, LINDAB_MARGIN_ROW, "op_margin"),
    (0.079, LINDAB_MARGIN_ROW, "op_margin"),
])
def test_a_european_report_row_evidences_its_figures(value, row, field):
    assert X.figure_supported(value, row, field)


@pytest.mark.parametrize("value,row,field", [
    (3300.0, LINDAB_SALES_ROW, "revenue"),
    (0.070, LINDAB_MARGIN_ROW, "op_margin"),
    (3306.0, "Net sales, SEK m", "revenue"),
])
def test_a_european_report_row_evidences_nothing_else(value, row, field):
    assert not X.figure_supported(value, row, field)


@pytest.mark.parametrize("quote", [
    "Sales (SEK m) ",     # the label, on its own line
    "3,",                 # the value, split across two lines by the extractor
    "253",
])
def test_a_garbled_slide_deck_evidences_nothing(quote):
    """Observed live in a real Q2 results deck.

    A slide is not a document: its text comes out as loose labels and
    numbers, and a value can split mid-number. That is the case the PDF
    work must not paper over -- none of these fragments evidences 3,253,
    so the figure is dropped. Rejoining them would be vss deciding what
    the slide said.
    """
    assert not X.figure_supported(3253, quote, "revenue")


def test_a_figure_absent_from_its_quoted_pdf_row_is_dropped(pdf_project):
    payload = pdf_extraction(figures={
        "revenue": {"value": 92999, "source_type": "table",
                    "period_column": "Second Quarter 2025", "sentence": REVENUE_ROW},
    })
    _, alert = run_pdf(pdf_project, payload)
    assert X.PROVENANCE_UNVERIFIABLE in alert
    assert "92999" in alert                    # named as dropped...
    assert "revenue: 92999" not in alert       # ...never proposed
    assert E.UNCERTAIN_HEADLINE in alert


def test_a_pdf_table_figure_with_no_column_named_is_flagged(pdf_project):
    """Four period columns, one row: the quote alone cannot say which."""
    payload = pdf_extraction(figures={
        "revenue": {"value": 92515, "source_type": "table",
                    "period_column": None, "sentence": REVENUE_ROW},
    })
    _, alert = run_pdf(pdf_project, payload)
    assert "NOT RECORDED" in alert
    assert "cannot be attributed" in alert
    assert E.UNCERTAIN_HEADLINE in alert


def test_a_properly_cited_pdf_figure_survives_with_its_column(pdf_project):
    code, alert = run_pdf(pdf_project)
    assert code == 0
    assert "revenue: 92515.0" in alert
    assert "inventory: 24371.0" in alert
    assert "`Second Quarter 2025`" in alert
    assert "SOURCE WARNINGS" in alert and "extracted from a PDF" in alert
    assert PDF_URL in alert


def test_a_pdf_run_still_writes_nothing_to_the_watchlist(pdf_project):
    before = pdf_project["watchlist_path"].read_bytes()
    _, alert = run_pdf(pdf_project)
    assert pdf_project["watchlist_path"].read_bytes() == before
    assert "PROPOSED quarters: ENTRY -- NOT WRITTEN" in alert


# --- PDFs vss cannot read fail loudly ------------------------------------


@pytest.mark.parametrize("code", [401, 403, 429])
def test_a_host_refusing_robots_points_at_the_door_that_is_open(code):
    """sap.com 403s an automated fetch of its own quarterly statement.

    vss does not answer that by impersonating a browser. It says so and
    names the escape hatch, which now reads the PDF as well as --url does.
    """
    import urllib.error

    def opener(request, timeout=None):
        raise urllib.error.HTTPError(PDF_URL, code, "Forbidden", {}, None)

    with pytest.raises(S.SourceError, match="--text-file"):
        S.fetch(PDF_URL, opener=opener)


def test_an_ordinary_http_failure_gets_no_such_hint():
    import urllib.error

    def opener(request, timeout=None):
        raise urllib.error.HTTPError(PDF_URL, 503, "Unavailable", {}, None)

    with pytest.raises(S.SourceError, match="HTTP 503") as caught:
        S.fetch(PDF_URL, opener=opener)
    assert "--text-file" not in str(caught.value)


def test_a_scanned_pdf_is_refused_rather_than_read_as_empty():
    """A scan has no text layer. Empty text would read like a bad release."""
    import io

    pypdf = pytest.importorskip("pypdf")
    writer = pypdf.PdfWriter()
    writer.add_blank_page(width=595, height=842)
    buffer = io.BytesIO()
    writer.write(buffer)
    with pytest.raises(S.SourceError, match="no extractable text"):
        S.fetch(PDF_URL, opener=pdf_opener(payload=buffer.getvalue()))


def _encrypted_pdf(**passwords) -> bytes:
    import io

    pypdf = pytest.importorskip("pypdf")
    writer = pypdf.PdfWriter(clone_from=str(PDF_RELEASE))
    writer.encrypt(**passwords)
    buffer = io.BytesIO()
    writer.write(buffer)
    return buffer.getvalue()


def test_a_permissions_encrypted_pdf_is_still_read():
    """IR PDFs are routinely encrypted with an empty password.

    They are readable by anyone; the encryption restricts printing and
    copying. Refusing on `is_encrypted` alone would reject real filings.
    """
    raw = _encrypted_pdf(user_password="", owner_password="owner")
    source = S.fetch(PDF_URL, opener=pdf_opener(payload=raw))
    assert REVENUE_ROW in source.text


def test_an_aes_encrypted_pdf_is_read():
    """SAP's quarterly statement is AES-encrypted with an empty password.

    pypdf decrypts AES only with its crypto extra installed; without it
    the real SAP PDF fails with "cryptography>=3.1 is required". That is
    why requirements.txt asks for pypdf[crypto] rather than bare pypdf.
    """
    raw = _encrypted_pdf(user_password="", owner_password="owner",
                         algorithm="AES-256")
    source = S.fetch(PDF_URL, opener=pdf_opener(payload=raw))
    assert REVENUE_ROW in source.text


def test_a_password_protected_pdf_is_refused():
    raw = _encrypted_pdf(user_password="letmein")
    with pytest.raises(S.SourceError, match="password-protected"):
        S.fetch(PDF_URL, opener=pdf_opener(payload=raw))


def test_a_pdf_may_be_larger_than_a_press_release(monkeypatch):
    """A filing runs to tens of pages. The HTML cap would refuse one."""
    monkeypatch.setattr(S, "MAX_BYTES", 1_000)
    assert S.MAX_PDF_BYTES > S.MAX_BYTES
    assert REVENUE_ROW in fetch_pdf().text
    with pytest.raises(S.SourceError, match="exceeds 1000 bytes"):
        S.fetch("https://acme.example.com/q2",
                opener=lambda r, timeout=None: BytesResponse(
                    RELEASE.read_bytes(), "text/html"))


def test_an_oversized_pdf_is_still_refused(monkeypatch):
    monkeypatch.setattr(S, "MAX_PDF_BYTES", 1_000)
    with pytest.raises(S.SourceError, match="exceeds 1000 bytes"):
        fetch_pdf()


# --- a PDF saved to disk takes the same path -----------------------------


def test_a_local_pdf_is_read_and_carries_both_warnings():
    """Where the file came from and how its text was recovered are two facts."""
    source = S.read_text_file(PDF_RELEASE)
    assert REVENUE_ROW in source.text
    assert any("not fetched" in w for w in source.warnings)
    assert any("extracted from a PDF" in w for w in source.warnings)


@pytest.mark.parametrize("name,body", [
    ("release.txt", b"Revenue for the second quarter was SEK 4,120 million."),
    ("release.pdf", None),          # None = the real fixture PDF's bytes
])
def test_a_relative_path_is_read_and_recorded_absolutely(tmp_path, monkeypatch,
                                                         name, body):
    """`--text-file q3.htm` crashed: as_uri() refuses a relative path.

    The path is resolved on the way in, so the URL recorded as the
    primary source names one unambiguous file however the caller typed
    it -- a relative path is not a provenance record once the working
    directory moves.
    """
    (tmp_path / name).write_bytes(body if body is not None else PDF_RELEASE.read_bytes())
    monkeypatch.chdir(tmp_path)

    source = S.read_text_file(name)          # relative, exactly as typed

    assert source.url == (tmp_path / name).resolve().as_uri()
    assert source.url.startswith("file:///")
    assert source.text
    assert str(tmp_path) in source.warnings[0]


def test_a_relative_path_survives_the_whole_command(project, tmp_path, monkeypatch):
    saved = tmp_path / "q3.htm"
    saved.write_bytes(RELEASE.read_bytes())
    monkeypatch.chdir(tmp_path)
    code, alert = run(project, url=None, text_file="q3.htm")
    assert code == 0
    assert f"**PRIMARY SOURCE:** {saved.resolve().as_uri()}" in alert


def test_a_missing_relative_path_still_fails_loudly(tmp_path, monkeypatch):
    """Resolving must not turn a missing file into a readable one."""
    monkeypatch.chdir(tmp_path)
    with pytest.raises(S.SourceError, match="no such file"):
        S.read_text_file("nope.htm")


def test_a_dotted_path_names_the_file_it_actually_read(tmp_path, monkeypatch):
    (tmp_path / "release.txt").write_text("Revenue was SEK 4,120 million.")
    nested = tmp_path / "sub"
    nested.mkdir()
    monkeypatch.chdir(nested)
    source = S.read_text_file("../release.txt")
    assert source.url == (tmp_path / "release.txt").resolve().as_uri()
    assert ".." not in source.url


def test_a_local_text_file_is_unchanged_by_the_pdf_path(tmp_path):
    saved = tmp_path / "release.txt"
    saved.write_text("Revenue was SEK 4,120 million.")
    source = S.read_text_file(saved)
    assert source.content_type == "text/plain"
    assert not any("PDF" in w for w in source.warnings)


# --- whitespace inside a number means two different things ---------------


@pytest.mark.parametrize("value,row", [
    # Swedish grouping: the space is the thousands separator.
    (4120.0, "Nettoomsättning 4 120 4 265"),
    (4265.0, "Nettoomsättning 4 120 4 265"),
    (1234567.0, "Nettoomsättning 1 234 567 1 198 004"),
    # US grouping: the space is the gap between two period columns.
    (24371.0, INVENTORY_ROW),
    (24008.0, INVENTORY_ROW),
])
def test_both_readings_of_a_space_are_offered(value, row):
    """A flattened row cannot say which convention its spaces follow.

    "4 120" is one number in Stockholm and two columns in Omaha, and the
    text does not say which. Both readings are candidates -- the quote
    contains the figure under one of them either way.
    """
    assert X.figure_supported(value, row, "revenue")


@pytest.mark.parametrize("value", [41204.0, 412.0, 20426.0])
def test_a_number_no_reading_produces_is_not_supported(value):
    """Joining runs the separator rule allows, not any two digits."""
    assert not X.figure_supported(value, "Nettoomsättning 4 120 4 265", "revenue")


def test_a_fragment_of_a_space_grouped_number_is_accepted():
    """Documented, not defended.

    Reading "4 120" as two columns makes 4 and 120 candidates as well as
    4120. Nothing in a flattened row distinguishes a fragment from a
    column, so this check does not try: it asks only whether the quote
    contains the figure. WHICH column it sits in is period_column's
    question, and a tabular figure without one is flagged regardless.
    """
    assert X.figure_supported(120.0, "Nettoomsättning 4 120 4 265", "revenue")


# --- the unit contract: the extractor emits fractions ---------------------
#
# The live bug: the model reported op_margin 6.6 for a 6.6% margin, the
# watchlist took it, and 4.2.2 -- which multiplies by 10,000 for basis
# points -- read 660%. Both sides now obey SPEC.md section 2; this is the
# extractor's side of it.


def figure_payload(field, **node):
    payload = json.loads(EXTRACTION_JSON.read_text())
    payload["figures"][field] = node
    return payload


def test_the_prompt_states_the_unit_contract():
    assert "UNITS" in X.SYSTEM_PROMPT
    assert "FRACTION, never as a percentage" in X.SYSTEM_PROMPT
    assert "6.6 per cent" in X.SYSTEM_PROMPT and "0.066" in X.SYSTEM_PROMPT
    # and says which fields are NOT fractions
    assert "net_debt_ebitda is a multiple" in X.SYSTEM_PROMPT


@pytest.mark.parametrize("field,value", [
    ("op_margin", 6.6),
    ("op_margin", 15.1),
    ("revenue_yoy", 2.0),
    ("revenue_yoy", -7.0),
])
def test_a_percentage_valued_ratio_is_dropped_not_scaled(field, value):
    """6.6 could be a misreported 6.6% or a genuine 660%. Neither is chosen."""
    payload = figure_payload(field, value=value, source_type="prose",
                             sentence=f"the figure was {value} percent")
    result = X.parse_response(json.dumps(payload), URL, "m")
    assert result.figures[field] is None
    assert field in result.out_of_band
    assert result.out_of_band[field]["value"] == value
    assert any(X.UNIT_ERROR in i for i in result.issues)
    assert result.uncertain


def test_the_unit_error_reaches_the_alert_and_the_proposed_entry(project):
    payload = figure_payload("op_margin", value=6.6, source_type="prose",
                             sentence="an operating margin of 6.6 percent")
    _, alert = run(project, transport=mock_llm(json.dumps(payload)))
    assert X.UNIT_ERROR in alert
    assert "op_margin: 6.6" not in alert.split("```yaml")[1]
    assert E.UNCERTAIN_HEADLINE in alert


def test_a_fraction_survives_and_its_percent_quote_still_evidences_it():
    """0.066 quoted as "6.6 percent" is the same quantity, correctly cited."""
    payload = figure_payload("op_margin", value=0.066, source_type="prose",
                             sentence="an operating margin of 6.6 percent")
    result = X.parse_response(json.dumps(payload), URL, "m")
    assert result.figures["op_margin"] == 0.066
    assert "op_margin" not in result.out_of_band
    assert "op_margin" not in result.unverifiable


def test_a_real_lindab_margin_row_supports_the_fraction():
    row = "Operating margin, % 6.6 8.6 - 6.4 7.9 - 7.8 8.5"
    assert X.figure_supported(0.066, row, "op_margin")
    assert not X.figure_supported(6.6 / 1000, row, "op_margin")


def test_net_debt_ebitda_is_not_banded_as_a_fraction():
    """A multiple is not a ratio field: 2.7x is 2.7 and must survive."""
    payload = figure_payload("net_debt_ebitda", value=2.7, source_type="table",
                             period_column="Q2 2026",
                             sentence="Net debt/EBITDA 2.7 2.6")
    result = X.parse_response(json.dumps(payload), URL, "m")
    assert result.figures["net_debt_ebitda"] == 2.7


# --- adjusted versus reported --------------------------------------------


def test_the_prompt_prefers_the_unadjusted_figure():
    assert "ADJUSTED versus REPORTED" in X.SYSTEM_PROMPT
    assert "TAKE THE UNADJUSTED FIGURE" in X.SYSTEM_PROMPT
    assert '"measure": "adjusted"' in X.SYSTEM_PROMPT
    # the worked example is Lindab's own Q4 2025 divergence
    assert "6.5 percent" in X.SYSTEM_PROMPT and "3.1 percent" in X.SYSTEM_PROMPT


def test_the_prompt_ties_a_december_year_end_to_calendar_quarters():
    assert "31 DECEMBER" in X.SYSTEM_PROMPT
    assert "calendar" in X.SYSTEM_PROMPT


def test_an_adjusted_figure_is_kept_but_declared():
    """Some reports state nothing else. Taking it silently is the problem."""
    payload = figure_payload("op_margin", value=0.065, measure="adjusted",
                             source_type="prose",
                             sentence="an adjusted operating margin of 6.5 percent")
    result = X.parse_response(json.dumps(payload), URL, "m")
    assert result.figures["op_margin"] == 0.065
    assert result.measures["op_margin"] == "adjusted"
    assert any("ADJUSTED measure" in i for i in result.issues)
    assert result.uncertain


def test_a_reported_measure_raises_nothing():
    payload = figure_payload("op_margin", value=0.031, measure="reported",
                             source_type="prose",
                             sentence="the operating margin was 3.1 percent")
    result = X.parse_response(json.dumps(payload), URL, "m")
    assert result.measures["op_margin"] == "reported"
    assert not any("ADJUSTED" in i for i in result.issues)


def test_the_alert_names_every_adjusted_figure(project):
    payload = figure_payload("op_margin", value=0.065, measure="adjusted",
                             source_type="prose",
                             sentence="an adjusted operating margin of 6.5 percent")
    _, alert = run(project, transport=mock_llm(json.dumps(payload)))
    assert "ADJUSTED MEASURES TAKEN" in alert
    assert "**adjusted**" in alert
    assert "written against the REPORTED figure" in alert


# --- --compare: two runs, one source -------------------------------------


def mock_llm_sequence(*contents):
    """A transport returning a different assistant message per call."""
    remaining = list(contents)

    def transport(request, timeout=None):
        content = remaining.pop(0) if remaining else contents[-1]
        return FakeResponse(json.dumps({"choices": [{"message": {"content": content}}]}))
    return transport


def test_two_agreeing_runs_keep_every_figure(project):
    same = EXTRACTION_JSON.read_text()
    _, alert = run(project, compare=True,
                   transport=mock_llm_sequence(same, same))
    assert "TWO RUNS AGREED" in alert
    assert X.EXTRACTION_DISAGREEMENT not in alert
    assert "revenue: 4120.0" in alert


def test_agreement_is_not_called_verification(project):
    """Both runs read the same text with the same model."""
    same = EXTRACTION_JSON.read_text()
    _, alert = run(project, compare=True, transport=mock_llm_sequence(same, same))
    assert "corroboration, not" in alert
    assert "both can be wrong together" in alert


def test_a_figure_the_runs_disagree_on_is_nulled_and_both_shown(project):
    """Lindab Q4 2025: 6.5% adjusted on one run, 3.1% reported on the next."""
    first = figure_payload("op_margin", value=0.065, measure="adjusted",
                           source_type="prose",
                           sentence="an adjusted operating margin of 6.5 percent")
    second = figure_payload("op_margin", value=0.031, measure="reported",
                            source_type="prose",
                            sentence="the operating margin was 3.1 percent")
    _, alert = run(project, compare=True,
                   transport=mock_llm_sequence(json.dumps(first), json.dumps(second)))
    assert X.EXTRACTION_DISAGREEMENT in alert
    assert "0.065" in alert and "0.031" in alert
    assert "op_margin: 0.065" not in alert and "op_margin: 0.031" not in alert
    assert E.UNCERTAIN_HEADLINE in alert


@pytest.mark.parametrize("claim,first,second", [
    ("period_basis", "fiscal", "calendar"),
    ("basis", "reported", "constant_currency"),
    ("accounting", "gaap", "non_gaap"),
    ("period", "2025-Q4", "2026-Q1"),
])
def test_a_claim_the_runs_disagree_on_is_nulled(claim, first, second):
    a = X.parse_response(json.dumps({**json.loads(EXTRACTION_JSON.read_text()),
                                     claim: first} if claim != "period" else
                                    {**json.loads(EXTRACTION_JSON.read_text()),
                                     "period": {"value": first, "sentence": "x"}}),
                         URL, "m")
    b = X.parse_response(json.dumps({**json.loads(EXTRACTION_JSON.read_text()),
                                     claim: second} if claim != "period" else
                                    {**json.loads(EXTRACTION_JSON.read_text()),
                                     "period": {"value": second, "sentence": "x"}}),
                         URL, "m")
    merged = X.agreement(a, b)
    assert getattr(merged, claim) is None
    assert claim in merged.disagreements
    assert merged.disagreements[claim] == {"first": first, "second": second}


def test_a_figure_both_runs_agree_on_keeps_its_value():
    payload = EXTRACTION_JSON.read_text()
    merged = X.agreement(X.parse_response(payload, URL, "m"),
                         X.parse_response(payload, URL, "m"))
    assert merged.figures["revenue"] == 4120.0
    assert merged.disagreements == {}
    assert merged.compared is True


def test_the_same_figure_from_a_different_column_keeps_the_number():
    """Corroborated number, uncorroborated attribution -- said, not dropped."""
    first = figure_payload("inventory", value=1240.0, source_type="table",
                           period_column="Q2 2026",
                           sentence="Inventories 1,240 1,230")
    second = figure_payload("inventory", value=1240.0, source_type="table",
                            period_column="30 June 2026",
                            sentence="Inventories 1,240 1,230")
    merged = X.agreement(X.parse_response(json.dumps(first), URL, "m"),
                         X.parse_response(json.dumps(second), URL, "m"))
    assert merged.figures["inventory"] == 1240.0
    assert "inventory" not in merged.disagreements
    assert any("attribution does not" in i for i in merged.issues)


def test_both_raw_responses_are_kept_for_audit(project):
    first = json.dumps(figure_payload("op_margin", value=0.065, measure="adjusted",
                                      sentence="6.5 percent", source_type="prose"))
    second = json.dumps(figure_payload("op_margin", value=0.031, measure="reported",
                                       sentence="3.1 percent", source_type="prose"))
    run(project, compare=True, transport=mock_llm_sequence(first, second))
    conn = sqlite3.connect(project["db_path"])
    raw = conn.execute("SELECT raw_response FROM earnings_runs").fetchone()[0]
    conn.close()
    assert "SECOND RUN" in raw
    assert "0.065" in raw and "0.031" in raw


def test_compare_is_off_by_default(project):
    """One call, one reading, no claim of corroboration."""
    _, alert = run(project)
    assert "TWO RUNS AGREED" not in alert


def test_the_disagreement_reaches_the_sqlite_reasons(project):
    first = json.dumps(figure_payload("eps", value=2.18, sentence="EPS was SEK 2.18",
                                      source_type="prose"))
    second = json.dumps(figure_payload("eps", value=2.81, sentence="EPS was SEK 2.81",
                                       source_type="prose"))
    run(project, compare=True, transport=mock_llm_sequence(first, second))
    conn = sqlite3.connect(project["db_path"])
    reasons = conn.execute("SELECT uncertainty_reasons FROM earnings_runs").fetchone()[0]
    conn.close()
    assert X.EXTRACTION_DISAGREEMENT in reasons and "eps" in reasons


def test_a_proposed_entry_its_own_loader_would_reject_says_so(project):
    """One definition of valid, asked before pasting rather than after."""
    payload = json.loads(EXTRACTION_JSON.read_text())
    payload["figures"]["op_margin"] = {
        "value": 0.065, "measure": "adjusted", "source_type": "prose",
        "sentence": "an adjusted operating margin of 6.5 percent"}
    payload["figures"]["op_income"] = {
        "value": 97.0, "measure": "reported", "source_type": "prose",
        "sentence": "Operating profit amounted to SEK 97 m"}
    payload["figures"]["revenue"] = {
        "value": 3134.0, "measure": "reported", "source_type": "prose",
        "sentence": "Net sales were SEK 3,134 m"}
    _, alert = run(project, transport=mock_llm(json.dumps(payload)))
    assert "THIS ENTRY WILL NOT LOAD" in alert
    assert "do not describe one measure" in alert
    assert "Do not fix it by editing the number" in alert


def test_a_clean_entry_carries_no_such_warning(project):
    _, alert = run(project)
    assert "THIS ENTRY WILL NOT LOAD" not in alert


def test_the_loader_and_the_proposer_share_one_check():
    from vss.config import ConfigError, parse_watchlist, unit_problem
    bad = {"period": "2026-Q2", "revenue": 3134.0, "op_income": 97.0,
           "op_margin": 0.065}
    assert unit_problem(bad) is not None
    with pytest.raises(ConfigError, match="do not describe one measure"):
        parse_watchlist({"tickers": [{"ticker": "X.ST", "name": "X", "currency": "SEK",
                                      "status": "HELD", "quarters": [bad]}]})


def test_agreement_does_not_overstate_when_the_runs_read_different_columns(project):
    """They agreed on 2.3; one read it from a quarter column, one from a date."""
    first = figure_payload("net_debt_ebitda", value=2.3, source_type="table",
                           period_column="2024 Jul-Sep",
                           sentence="Net debt/EBITDA 2.3 2.1")
    second = figure_payload("net_debt_ebitda", value=2.3, source_type="table",
                            period_column="Sep 30, 2024",
                            sentence="Net debt/EBITDA 2.3 2.1")
    _, alert = run(project, compare=True,
                   transport=mock_llm_sequence(json.dumps(first), json.dumps(second)))
    assert "TWO RUNS AGREED ON EVERY FIGURE" in alert
    assert "did not agree on WHERE" in alert
    assert "2024 Jul-Sep" in alert and "Sep 30, 2024" in alert
    assert "net_debt_ebitda: 2.3" in alert      # the figure still stands


# --- what --compare found on a real run ----------------------------------


def test_a_claim_is_read_in_either_shape_the_model_sends():
    """Found live: one run sent "gaap", the next {"value": "gaap", ...}.

    The parser understood only the bare string, so --compare saw two
    different values and nulled three correct claims about Lindab's
    2025-Q4. A stylistic difference is not a disagreement.
    """
    payload = json.loads(EXTRACTION_JSON.read_text())
    payload["accounting"] = {"value": "gaap", "sentence": "prepared in accordance with IFRS"}
    payload["basis"] = "reported"
    result = X.parse_response(json.dumps(payload), URL, "m")
    assert result.accounting == "gaap"
    assert result.basis == "reported"
    assert "IFRS" in result.sentences["accounting"]


def test_the_two_shapes_no_longer_read_as_a_disagreement():
    bare = json.loads(EXTRACTION_JSON.read_text())
    bare["accounting"] = "gaap"
    wrapped = json.loads(EXTRACTION_JSON.read_text())
    wrapped["accounting"] = {"value": "GAAP", "sentence": "in accordance with IFRS"}
    merged = X.agreement(X.parse_response(json.dumps(bare), URL, "m"),
                         X.parse_response(json.dumps(wrapped), URL, "m"))
    assert merged.accounting == "gaap"
    assert "accounting" not in merged.disagreements


@pytest.mark.parametrize("claim,value", [
    ("accounting", "ifrs"),          # a real answer, an invalid watchlist value
    ("basis", "actual"),
    ("period_basis", "quarterly"),
])
def test_a_claim_outside_its_vocabulary_is_dropped(claim, value):
    payload = json.loads(EXTRACTION_JSON.read_text())
    payload[claim] = value
    result = X.parse_response(json.dumps(payload), URL, "m")
    assert getattr(result, claim) is None
    assert any(claim in i and "not one of" in i for i in result.issues)


def test_an_invalid_guidance_action_is_dropped_too():
    payload = json.loads(EXTRACTION_JSON.read_text())
    payload["guidance_action"] = {"value": "reiterated", "sentence": "reiterated its outlook"}
    result = X.parse_response(json.dumps(payload), URL, "m")
    assert result.guidance_action is None
    assert any("not one of" in i for i in result.issues)


def test_a_dropped_claim_never_reaches_the_proposed_entry(project):
    payload = json.loads(EXTRACTION_JSON.read_text())
    payload["accounting"] = "ifrs"
    _, alert = run(project, transport=mock_llm(json.dumps(payload)))
    block = alert.split("```yaml")[1]
    assert "accounting: ifrs" not in block
    assert "accounting: " in block


# --- a table row must survive flattening as a ROW ------------------------
#
# Found on NIKE's saved EDGAR exhibits. Two separate faults made the
# provenance rule impossible to satisfy from a real statement table:
# cells were joined with nothing between them, and a cell holding a
# <div> broke the row across two lines.

EDGAR_ROW = """<table><tr>
  <td><div>TOTAL NIKE, INC. EARNINGS BEFORE INTEREST AND TAXES</div></td>
  <td>1,392</td><td>1,900</td><td>-27</td><td>%</td>
</tr></table>"""


def test_a_statement_row_flattens_to_one_line():
    line = S.html_to_text(EDGAR_ROW).strip()
    assert "\n" not in line, f"row split across lines: {line!r}"
    assert "TOTAL NIKE, INC. EARNINGS BEFORE INTEREST AND TAXES" in line
    assert "1,392" in line and "1,900" in line


def test_the_flattened_row_evidences_the_figure_it_contains():
    """Joined cells read as 1,3921,900 -- a number the row does not state."""
    line = S.html_to_text(EDGAR_ROW).strip()
    assert X.figure_supported(1392.0, line, "op_income")
    assert X.figure_supported(1900.0, line, "op_income")
    # the figure the extractor actually took, from a different line
    assert not X.figure_supported(1416.0, line, "op_income")
    assert not X.figure_supported(1392000.0, line, "op_income")


def test_cells_are_separated_even_without_a_wrapping_div():
    line = S.html_to_text("<table><tr><td>Revenues</td><td>12,354</td>"
                          "<td>12,354</td></tr></table>").strip()
    assert line == "Revenues 12,354 12,354"


def test_two_rows_stay_two_lines():
    text = S.html_to_text("<table><tr><td>A</td><td>1</td></tr>"
                          "<tr><td>B</td><td>2</td></tr></table>")
    assert [l.strip() for l in text.splitlines() if l.strip()] == ["A 1", "B 2"]


def test_prose_outside_a_table_still_breaks_into_lines():
    text = S.html_to_text("<p>First sentence.</p><p>Second sentence.</p>")
    assert [l.strip() for l in text.splitlines() if l.strip()] == \
        ["First sentence.", "Second sentence."]


# --- --text-file must flatten markup, exactly as --url does --------------


def test_a_saved_html_release_is_flattened_not_handed_over_raw(tmp_path):
    """The two paths diverged: --url flattened, --text-file did not.

    A saved EDGAR exhibit reached the model as 286KB of tag soup, and
    the figures extracted from it were whatever survived that.
    """
    saved = tmp_path / "exhibit.htm"
    saved.write_text("<DOCUMENT><TYPE>EX-99.1<TEXT>" + RELEASE.read_text())
    source = S.read_text_file(saved)
    assert "<div" not in source.text and "<table" not in source.text
    assert "Revenue for the second quarter was SEK 4,120 million" in source.text
    assert source.content_type == "text/html"


def test_a_plain_text_release_is_left_alone(tmp_path):
    saved = tmp_path / "release.txt"
    saved.write_text("Revenue grew <1% in the quarter.")
    source = S.read_text_file(saved)
    assert source.text == "Revenue grew <1% in the quarter."
    assert source.content_type == "text/plain"


def test_both_entry_points_flatten_identically(tmp_path):
    html = RELEASE.read_text()
    saved = tmp_path / "release.htm"
    saved.write_text(html)

    class R:
        headers = {"Content-Type": "text/html"}
        def read(self, size=None): return html.encode("utf-8")
        def __enter__(self): return self
        def __exit__(self, *exc): return False

    fetched = S.fetch("https://acme.example.com/q2", opener=lambda r, timeout=None: R())
    assert S.read_text_file(saved).text == fetched.text


def test_the_unseparated_reading_of_a_row_is_still_offered():
    """Documented: "1,392 1,900" also reads as one unseparated number.

    Harmless -- 1,3921,900 is a quantity nobody claims -- and it is the
    same both-conventions logic that lets a Swedish "4 120" read as one
    number. Pinned so a future tightening is a decision, not a surprise.
    """
    line = S.html_to_text(EDGAR_ROW).strip()
    assert X.figure_supported(13921900.0, line, "op_income")


def test_a_dropped_name_reads_as_a_candidate_not_a_thesis(project, tmp_path):
    """4.2 on a rejected name is still validation -- there is no position."""
    from vss.rules import VALID_STATUSES
    assert "DROPPED" in E.CANDIDATE_STATUSES
    assert set(E.CANDIDATE_STATUSES) == set(VALID_STATUSES) - {"HELD"}
    wl = watchlist_file(tmp_path, WATCHLIST.replace("status: HELD", "status: DROPPED"))
    _, alert = run(project, watchlist_path=wl)
    assert E.VALIDATION_HEADLINE in alert
    assert "**STATUS:** DROPPED" in alert


# --- a figure stated in another quarter's filing --------------------------
#
# SAP's Q2 2024 restructuring of -631 appears in the Q2 2025 statement's
# comparative column and nowhere in the Q2 2024 release, because the line
# was not broken out at the time. Reading it there, and recording THAT
# document as its source, is more honest than attributing it to a release
# that does not contain it.


def test_the_prompt_defines_what_a_class_c_impact_is():
    """None of ten SAP runs captured a restructuring line: it was never
    defined, so the model had nothing to recognise."""
    assert "FIELD NOTE -- class_c_impact" in X.SYSTEM_PROMPT
    assert "QUANTIFIED ONE-OFF" in X.SYSTEM_PROMPT
    assert "restructuring charge" in X.SYSTEM_PROMPT


def test_the_prompt_fixes_the_sign_convention_both_ways():
    assert "A charge is NEGATIVE" in X.SYSTEM_PROMPT
    assert "-2242" in X.SYSTEM_PROMPT          # SAP Q1 2024, a charge
    assert "+52" in X.SYSTEM_PROMPT            # SAP Q3 2024, a release


def test_the_prompt_forbids_deriving_a_one_off_from_the_adjusted_gap():
    assert "Never infer\none from the gap" in X.SYSTEM_PROMPT


def test_no_target_period_leaves_the_request_untouched():
    body = X.build_request("some release text", X.DEFAULT_MODEL)
    assert body["messages"][1]["content"] == "some release text"


def test_a_target_period_instructs_the_comparative_column():
    body = X.build_request("some release text", X.DEFAULT_MODEL,
                           target_period="2024-Q2")
    content = body["messages"][1]["content"]
    assert content.startswith("TARGET PERIOD: 2024-Q2")
    assert "COMPARATIVE column" in content
    assert "may be this document's OWN period" in content
    assert "NEVER report another period's figure under this label" in content
    assert content.endswith("some release text")
    # the system prompt is untouched, so every other rule still applies
    assert body["messages"][0]["content"] == X.SYSTEM_PROMPT


def test_the_targeted_period_labels_the_proposed_entry(project):
    """The document is about 2025-Q2; the row proposed is 2024-Q2."""
    payload = json.loads(EXTRACTION_JSON.read_text())
    payload["period"] = {"value": "2024-Q2", "sentence": "Q2 2024 comparative"}
    payload["figures"]["class_c_impact"] = {
        "value": -631, "source_type": "table", "measure": "reported",
        "period_column": "Q2 2024",
        "sentence": "Restructuring -18 -631 -97"}
    _, alert = run(project, target_period="2024-Q2",
                   transport=mock_llm(json.dumps(payload)))
    assert "- period: 2024-Q2" in alert
    assert "class_c_impact: -631.0" in alert
    assert "`Q2 2024`" in alert                 # the column is on the record


def test_a_targeted_run_records_the_document_it_read(project):
    """Provenance is the filing that CONTAINS the figure, not the quarter's
    own release."""
    payload = json.loads(EXTRACTION_JSON.read_text())
    payload["period"] = {"value": "2024-Q2", "sentence": "Q2 2024 comparative"}
    _, alert = run(project, target_period="2024-Q2", url="https://sap.example/q2-2025",
                   transport=mock_llm(json.dumps(payload)))
    assert "**PRIMARY SOURCE:** https://sap.example/q2-2025" in alert
    assert "- period: 2024-Q2" in alert


def test_a_positive_one_off_keeps_its_sign(project):
    """SAP's Q3 2024 restructuring is a release: +52, not a charge."""
    payload = json.loads(EXTRACTION_JSON.read_text())
    payload["figures"]["class_c_impact"] = {
        "value": 52, "source_type": "table", "measure": "reported",
        "period_column": "Q3 2024", "sentence": "Restructuring 18 52 -66"}
    _, alert = run(project, transport=mock_llm(json.dumps(payload)))
    assert "class_c_impact: 52.0" in alert


def test_the_target_period_survives_a_compare_run(project):
    payload = json.loads(EXTRACTION_JSON.read_text())
    payload["period"] = {"value": "2024-Q2", "sentence": "comparative"}
    body = json.dumps(payload)
    _, alert = run(project, target_period="2024-Q2", compare=True,
                   transport=mock_llm_sequence(body, body))
    assert "- period: 2024-Q2" in alert
    assert "TWO RUNS AGREED" in alert


# --- --period targets a column, not a vintage of document -----------------
#
# The instruction first said the target period was "probably" a
# comparative column in a document about a later quarter. That was false
# half the time and load-bearing when false: SAP's 2024-Q3 restructuring
# credit of +52 sits in its OWN statement, beside a 2023 column reading
# 36, and a nudge toward "the comparative" points straight at the wrong
# number. Both modes are pinned here so the assumption cannot return.


@pytest.mark.parametrize("period", ["2024-Q3", "2026-Q1"])
def test_the_instruction_commits_to_neither_mode(period):
    content = X.build_request("text", X.DEFAULT_MODEL,
                              target_period=period)["messages"][1]["content"]
    assert f"TARGET PERIOD: {period}" in content
    assert "may be this document's OWN period" in content
    assert "COMPARATIVE column" in content
    # it must not assert which of the two this document is
    assert "probably" not in content.lower()
    assert f"column is {period}" in content      # the text wraps mid-phrase


def test_targeting_a_documents_own_quarter_keeps_that_quarter(project):
    """The document is about 2024-Q3 and the target is 2024-Q3."""
    payload = json.loads(EXTRACTION_JSON.read_text())
    payload["period"] = {"value": "2024-Q3", "sentence": "Q3 2024"}
    payload["figures"]["class_c_impact"] = {
        "value": 52, "source_type": "table", "measure": "reported",
        "period_column": "Q3 2024", "sentence": "Restructuring 52 36 43"}
    _, alert = run(project, target_period="2024-Q3",
                   transport=mock_llm(json.dumps(payload)))
    assert "- period: 2024-Q3" in alert
    assert "class_c_impact: 52.0" in alert
    assert "`Q3 2024`" in alert


def test_the_neighbouring_column_is_not_what_gets_recorded(project):
    """`Restructuring 52 36 43` holds 2024 and 2023. Only one is 2024-Q3.

    If the model reports the neighbour, the quote still contains it and
    the provenance check cannot object -- the column is the only thing
    that distinguishes them, which is why --period requires it.
    """
    payload = json.loads(EXTRACTION_JSON.read_text())
    payload["period"] = {"value": "2024-Q3", "sentence": "Q3 2024"}
    payload["figures"]["class_c_impact"] = {
        "value": 36, "source_type": "table", "measure": "reported",
        "period_column": "Q3 2023", "sentence": "Restructuring 52 36 43"}
    _, alert = run(project, target_period="2024-Q3",
                   transport=mock_llm(json.dumps(payload)))
    assert "class_c_impact: 36.0" in alert
    assert "`Q3 2023`" in alert, "the column read must be visible on the record"


def test_a_credit_survives_a_block_of_charges(project):
    """+52 sits among negatives; nothing may normalise it to a charge."""
    payload = json.loads(EXTRACTION_JSON.read_text())
    payload["figures"]["class_c_impact"] = {
        "value": 52, "source_type": "table", "measure": "reported",
        "period_column": "Q3 2024", "sentence": "Restructuring 52 36 43"}
    result = X.parse_response(json.dumps(payload), URL, "m")
    assert result.figures["class_c_impact"] == 52.0
    assert "class_c_impact" not in result.unverifiable
    assert "class_c_impact" not in result.out_of_band
