"""HANDOFF B: the LLM pre-fill from PDF pages. Synthetic page texts and
canned model replies through the transport; no model, no real report."""
from __future__ import annotations

import io
import json
from pathlib import Path

import pytest
import yaml

from vss import pdfdraft as P
from vss import source as S
from vss.manual import parse_manual

FIX = json.loads((Path(__file__).parent / "fixtures" / "pdfdraft" / "pages.json").read_text())
PAGES = [tuple(p) for p in FIX["pages"]]
COL = "01/04/2026 30/06/2026"
UNIT = "Amounts in SEK thousands"


def e(value, row, page, column=COL, unit=UNIT):
    return {"value": value, "row": row, "column": column, "unit": unit, "page": page}


GOOD = {
    "revenue": e(743232, "Net sales 743,232 650,100 1,401,000", 5),
    "operating_income": e(81500, "Operating profit 81,500 70,200 150,300", 5),
    "op_margin": e(11.0, "Operating margin, % 11.0 10.8 10.7", 5),
    "net_income": e(60100, "Profit for the period 60,100 52,000 111,000", 5),
    "diluted_eps": e(1.80, "Earnings per share after dilution 1.80 1.55 3.31", 5),
    "cash_and_equivalents": e(210400, "Cash and cash equivalents 210,400 180,300", 6,
                              column="30/06/2026"),
    "operating_cash_flow": e(95300, "Cash flow from operating activities 95,300 80,000 170,000", 8),
    "capex_ppe": e(-12400, "Investments in tangible fixed assets -12,400 -9,000 -20,000", 8),
    "capex_intangibles": e(0, "Investments in intangible assets 0 -1,000 -500", 8),
    "lease_payments_capital": e(-6256, "Amortisation of lease liabilities -6,256 -5,900 -12,000", 8),
}


class _Resp(io.BytesIO):
    def __enter__(self):
        return self

    def __exit__(self, *a):
        return False


def transport_for(*replies):
    queue = list(replies)

    def opener(request, timeout=None):
        body = {"choices": [{"message": {"content": json.dumps({"fields": queue.pop(0)})}}]}
        return _Resp(json.dumps(body).encode())
    return opener


@pytest.fixture
def pdf(tmp_path, monkeypatch):
    p = tmp_path / "EXM.ST_2026-Q2_interim-report-q1-and-q3_2026-08-25_en_a0.pdf"
    p.write_bytes(b"%PDF-1.7 synthetic")
    monkeypatch.setattr(S, "pdf_pages", lambda raw, where: PAGES)
    return p


def _run(pdf, first, second=None):
    return P.run(pdf, ticker="EXM.ST", target="2026-Q2", model="test/model", api_key="k",
                 transport=transport_for(first, second if second is not None else first))


def test_the_locator_takes_the_group_statements_not_prose_or_the_parent():
    assert P.locate(PAGES) == [5, 6, 8]


def test_good_figures_pass_and_the_draft_is_unverified(pdf, tmp_path):
    r = _run(pdf, GOOD)
    g = r.gated
    assert g.money_unit == "thousands"
    assert g.figures["revenue"]["value"] == 743232 and "op_margin" not in g.figures
    assert g.figures["capex_ppe"]["value"] == -12400
    assert "zero" in g.dropped["capex_intangibles"]                       # a zero
    text = P.draft_yaml("EXM.ST", "Exempel AB", "SEK", r, pdf=pdf, target="2026-Q2",
                        run_ts=P.datetime(2026, 11, 7))
    doc = yaml.safe_load(text)
    parsed = parse_manual(doc, path=Path("x.yaml"))
    assert parsed.origin == "llm-pdf" and doc["money_unit"] == "thousands"
    figs = doc["periods"][0]["figures"]
    assert all(f["status"] == "UNVERIFIED" for f in figs.values())
    assert figs["revenue"]["page"].startswith("LLM-PDF p.5, row 'Net sales 743,232")
    assert len(r.record["responses_sha256"]) == 2 and r.record["model"] == "test/model"
    target = P.write("EXM.ST", text, r.record, directory=tmp_path / "drafts")
    assert (tmp_path / "drafts" / "EXM.ST.llm-pdf.run.json").exists() and target.exists()


def test_a_disagreement_drops_the_field(pdf):
    other = dict(GOOD, revenue=e(743233, "Net sales 743,232 650,100 1,401,000", 5))
    r = _run(pdf, GOOD, other)
    assert "revenue" not in r.gated.figures and "disagree" in r.gated.dropped["revenue"]


def test_a_year_to_date_column_is_not_the_quarter(pdf):
    bad = dict(GOOD, operating_cash_flow=e(170000, "Cash flow from operating activities 95,300 80,000 170,000", 8,
                                            column="01/01/2026 30/06/2026"))
    r = _run(pdf, bad)
    assert "operating_cash_flow" not in r.gated.figures
    assert "2026-01-01..2026-06-30" in r.gated.dropped["operating_cash_flow"]


def test_a_unit_not_quoted_from_the_page_drops_the_field(pdf):
    bad = dict(GOOD, net_income=e(60100, "Profit for the period 60,100 52,000 111,000", 5,
                                  unit="Amounts in SEK millions"))
    r = _run(pdf, bad)
    assert "net_income" not in r.gated.figures and "unit sentence" in r.gated.dropped["net_income"]


def test_a_missing_quote_and_a_value_not_in_the_row(pdf):
    bad = dict(GOOD,
               total_equity=e(455000, "Total equity attributable 455,000", 6, column="30/06/2026"),
               total_assets=e(1020000, "Total assets 1,020,500 950,000", 6, column="30/06/2026"))
    r = _run(pdf, bad)
    assert "not on page 6" in r.gated.dropped["total_equity"]
    assert "not among the row's numbers" in r.gated.dropped["total_assets"]


def test_a_row_from_a_page_not_sent_or_the_parent_company(pdf):
    bad = dict(GOOD, operating_cash_flow=e(1000, "Cash flow from operating activities 1,000 2,000", 9))
    r = _run(pdf, bad)
    assert "was not among the pages sent" in r.gated.dropped["operating_cash_flow"]


def test_the_margin_check_drops_revenue_and_operating_income(pdf):
    bad = dict(GOOD, op_margin=e(1.1, "Operating margin, % 11.0 10.8 10.7", 5))
    # 1.1 is not in the row: dropped before the check, so the pair stands
    assert "revenue" in _run(pdf, bad).gated.figures
    worse = dict(GOOD, operating_income=e(70200, "Operating profit 81,500 70,200 150,300", 5))
    r = _run(pdf, worse)
    assert "revenue" not in r.gated.figures and "unit check" in r.gated.dropped["revenue"]


def test_an_outflow_printed_positive_is_not_flipped(pdf):
    bad = dict(GOOD, capex_ppe=e(12400, "Investments in tangible fixed assets -12,400 -9,000 -20,000", 8))
    r = _run(pdf, bad)
    assert "capex_ppe" not in r.gated.figures


def test_the_column_names_the_target():
    assert P.column_names_target("Apr–Jun 2026", "2026-Q2") is None
    assert P.column_names_target("Jan–Jun 2026", "2026-Q2")
    assert P.column_names_target("Q2 2026", "2026-Q2") is None
    assert P.column_names_target("2025", "2025-FY") is None
    assert P.column_names_target("Q4 2025", "2025-FY")
    assert P.column_names_target("Apr-Jun 2025", "2026-Q2")


LIVE_Q = """ticker: EXM.ST
name: Exempel AB
reporting_currency: SEK
money_unit: thousands
share_unit: whole
origin: manual

periods:
  - period: 2026-Q1
    period_end: 2026-03-31
    period_basis: calendar
    document: "Q1 report"
    url: "sources/q1.pdf"
    figures:
      revenue:
        value: 700000
        page: "p.5 'Net sales 700,000'"
        status: VERIFIED
  # the Q3 report comes in November
  - period: 2026-Q3
    period_end: 2026-09-30
    period_basis: calendar
    document: "Q3 report"
    url: "sources/q3.pdf"
    figures:
      revenue:
        value: 760000
        page: "p.5 'Net sales 760,000'"
        status: VERIFIED
"""


def test_a_period_draft_merges_in_order_and_never_overwrites(pdf, tmp_path):
    from vss import draft
    r = _run(pdf, GOOD)
    text = P.draft_yaml("EXM.ST", "Exempel AB", "SEK", r, pdf=pdf, target="2026-Q2",
                        run_ts=P.datetime(2026, 11, 7))
    m = tmp_path / "manual"
    P.write("EXM.ST", text, r.record, directory=m / "drafts")
    (m / "EXM.ST.yaml").write_text(LIVE_Q)
    res = draft.merge_draft("EXM.ST", origin="llm-pdf", manual_dir=m, backup_dir=tmp_path / "bak")
    doc = yaml.safe_load((m / "EXM.ST.yaml").read_text())
    assert [p["period"] for p in doc["periods"]] == ["2026-Q1", "2026-Q2", "2026-Q3"]
    assert res.added_years == ["2026-Q2"]
    assert "# the Q3 report comes in November" in (m / "EXM.ST.yaml").read_text()
    parse_manual(doc, path=m / "EXM.ST.yaml")


def test_the_number_as_the_model_writes_it():
    assert P.number("881,712") == 881712 and P.number("1 079 808") == 1079808
    assert P.number(881712) == 881712 and P.number("-6,256") == -6256
    assert P.number("1,80") == 1.8 and P.number("(1,711)") == -1711
    assert P.number("1,2345") is None and P.number("n/a") is None and P.number(True) is None


def test_two_spellings_of_one_number_agree(pdf):
    other = dict(GOOD, revenue=e("743,232", "Net sales 743,232 650,100 1,401,000", 5))
    r = _run(pdf, GOOD, other)
    assert r.gated.figures["revenue"]["value"] == 743232


def test_a_balance_sheet_column_is_the_period_end():
    assert P.column_names_target("30/06/2026", "2026-Q2", instant=True) is None
    assert P.column_names_target("Jun 30, 2026", "2026-Q2", instant=True) is None
    assert P.column_names_target("30/06/2025", "2026-Q2", instant=True)
    assert P.column_names_target("31/12/2026", "2026-Q2", instant=True)
    assert P.column_names_target("30/06/2026", "2026-Q2")        # not for a flow line
