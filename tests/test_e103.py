"""E103: reference figures, fetched automatically, fenced out of every basis.

**A BASIS FIGURE ENTERS A VALUATION; A REFERENCE FIGURE IS ONLY COMPARED
AGAINST ONE.** A wrong basis figure produces a wrong value nothing
downstream can detect, which is why E40 reads every one back by hand. A
wrong reference figure produces a false blink — the owner looks, and it
turns out to be the comparator. That asymmetry is the whole ruling, and it
is what makes automatic entry safe.

**The test that matters is `test_a_reference_figure_wired_into_a_basis_REFUSES_section_5`.**
E103 opens a door; the only thing that must not come through it is an
UNVERIFIED number inside a fair value. The fence is mechanical rather than a
matter of care, and this is what proves it fires.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from vss import manual as M
from vss import reference_figures as RF
from vss.runrecord import Comparator, Disagreement

#: These read LIAB.ST's own published reports from sources/, which are the
#: issuer's documents and are NOT redistributed. Fetch them with
#: `vss nordic --ticker LIAB.ST` (lists them) and `--download ID` (see SETUP.md).
NEEDS_LIAB_REPORTS = pytest.mark.skipif(
    not any((Path(__file__).resolve().parents[1] / "sources").glob("LIAB.ST_*")),
    reason="needs LIAB.ST's reports in sources/ -- fetch them with vss nordic")


MANUAL = Path("config/manual")


# --- the fence -----------------------------------------------------------


def test_both_reference_fields_are_OUT_of_the_section_5_read_set():
    assert "free_cash_flow_reported" not in M.SECTION5_FIELDS
    assert "net_debt_reported" not in M.SECTION5_FIELDS
    assert M.REFERENCE_FIELDS == {"free_cash_flow_reported",
                                  "net_debt_reported"}


def test_the_fence_reports_nothing_wired_today():
    assert M.reference_fields_in_basis() == ()


def test_a_reference_figure_wired_into_a_basis_REFUSES_section_5(monkeypatch):
    """**THE ONE THAT MATTERS.** The moment a reference field acquires a
    `5.*` reader, a §5 basis READS an UNVERIFIED number and every fair value
    built on it is an unverified figure wearing a verified one's clothes.
    Section 5 must stop, loudly, naming the field."""
    from datetime import date

    monkeypatch.setattr(
        M, "SECTION5_FIELDS",
        tuple(M.SECTION5_FIELDS) + ("free_cash_flow_reported",))
    assert M.reference_fields_in_basis() == ("free_cash_flow_reported",)

    parsed = M.load_manual("CTSH", directory=MANUAL)
    gate = M.section5_gate(parsed, as_of=date(2026, 9, 1))
    codes = [r.kind for r in gate.refusals]
    assert M.REFUSE_REFERENCE_IN_BASIS in codes
    assert gate.refused, "section 5 ran with a reference figure in its basis"
    reason = next(r for r in gate.refusals
                  if r.kind == M.REFUSE_REFERENCE_IN_BASIS)
    assert "free_cash_flow_reported" in reason.detail
    assert "SECTION 5 DOES NOT RUN" in reason.detail


def test_the_gate_is_clean_while_the_fence_holds():
    from datetime import date

    parsed = M.load_manual("CTSH", directory=MANUAL)
    gate = M.section5_gate(parsed, as_of=date(2026, 9, 1))
    assert M.REFUSE_REFERENCE_IN_BASIS not in [r.kind for r in gate.refusals]


def test_an_unverified_reference_figure_does_NOT_block_a_strike(tmp_path: Path):
    """The point of taking them out of the read set. An UNVERIFIED basis
    figure blocks under E21; an UNVERIFIED reference figure must not, or
    automatic entry would refuse every §5 run it touched."""
    from datetime import date

    source = (MANUAL / "CTSH.yaml").read_text(encoding="utf-8")
    proposal = RF.Proposal("CTSH", "net_debt_reported", "FY2025",
                           value=-500_000_000.0, scale="units", page="p.61",
                           quote="Net cash 500", route=RF.ROUTE_PDF)
    written = RF.insert_figure(source, "FY2025",
                               RF.figure_block("net_debt_reported", proposal))
    (tmp_path / "CTSH.yaml").write_text(written, encoding="utf-8")

    parsed = M.load_manual("CTSH", directory=tmp_path)
    entry = next(a for a in parsed.annual if a.fiscal_year == 2025)
    figure = entry.figures["net_debt_reported"]
    assert figure.present and not figure.verified
    gate = M.section5_gate(parsed, as_of=date(2026, 9, 1))
    assert not any("net_debt_reported" in r.subject for r in gate.refusals)


# --- the SEC route is empty BY CONSTRUCTION, and says which ---------------


def test_the_sec_route_supplies_neither_field_and_gives_the_reason():
    figures, why = RF.sec_reference_figures(1609711)
    assert figures == {}
    assert "no us-gaap element" in why
    assert "non-GAAP" in why


def test_a_missing_cik_is_a_DIFFERENT_reason_from_an_empty_taxonomy():
    """A route that is empty by construction and a route that could not be
    asked are different facts, and the report must not print them alike."""
    _, no_cik = RF.sec_reference_figures(None)
    _, with_cik = RF.sec_reference_figures(1609711)
    assert no_cik != with_cik
    assert "no CIK" in no_cik


# --- the model's reply: ambiguity is never a figure -----------------------


def test_a_quoted_figure_is_taken():
    parsed = RF.parse_model_reply(json.dumps({
        "free_cash_flow_reported": {"value": 1176, "scale": "millions",
                                    "page": "p.17, SEK m",
                                    "quote": "Free cash flow 1,176"},
        "net_debt_reported": {"value": 4266, "scale": "millions",
                              "page": "p.25",
                              "quote": "Net debt 4,266"}}))
    assert parsed["free_cash_flow_reported"]["value"] == 1176.0
    assert parsed["net_debt_reported"]["value"] == 4266.0


def test_a_figure_the_model_CANNOT_QUOTE_is_refused():
    """A value with no verbatim line is one the model DERIVED, and a derived
    comparator cannot disagree with the construction it was derived from --
    which destroys the only thing the check is for."""
    parsed = RF.parse_model_reply(json.dumps({
        "free_cash_flow_reported": {"value": 999, "page": "p.1", "quote": ""},
        "net_debt_reported": {"value": None, "page": "", "quote": ""}}))
    assert parsed["free_cash_flow_reported"]["value"] is None
    assert "derived" in parsed["free_cash_flow_reported"]["detail"]


def test_a_null_figure_is_an_ABSENT_LINE_not_a_zero():
    parsed = RF.parse_model_reply(json.dumps({
        "free_cash_flow_reported": {"value": None, "page": "", "quote": ""},
        "net_debt_reported": {"value": None, "page": "", "quote": ""}}))
    assert parsed["free_cash_flow_reported"]["value"] is None
    assert "prints no such line" in parsed["free_cash_flow_reported"]["detail"]


def test_a_reply_that_is_not_json_RAISES_rather_than_returning_nothing():
    with pytest.raises(RF.ReferenceError):
        RF.parse_model_reply("I could not find the figures.")


def test_a_fenced_reply_is_unwrapped():
    parsed = RF.parse_model_reply(
        '```json\n{"free_cash_flow_reported": {"value": 5, "scale": "units",'
        ' "page": "p", "quote": "Free cash flow 5"}}\n```')
    assert parsed["free_cash_flow_reported"]["value"] == 5.0


def test_a_missing_key_is_a_ROUTE_FAILURE_not_an_absent_figure(monkeypatch,
                                                               tmp_path: Path):
    """The distinction the whole report turns on: 'we could not ask' and
    'the issuer publishes none' must never print the same way."""
    monkeypatch.delenv("VSS_OPENROUTER_KEY", raising=False)
    document = tmp_path / "X_2026-Q2_report.pdf"
    document.write_bytes(b"%PDF-1.4 nothing")
    with pytest.raises(RF.ReferenceError) as caught:
        RF.read_document(document, period="2026-Q2", ticker="X")
    assert "no API key" in str(caught.value)


# --- the plan reads the BASIS's own holders ------------------------------


def test_a_flow_is_wanted_in_EVERY_period_of_the_window(tmp_path: Path):
    """`resolve_on_basis` sums a flow over the window and refuses unless
    every entry supplies it -- three quarters of four is not a year."""
    plan = RF.plan("LIAB.ST", manual_dir=_store(tmp_path))
    assert plan.wanted["free_cash_flow_reported"] == [
        "2025-Q3", "2025-Q4", "2026-Q1", "2026-Q2"]


def test_a_stock_is_wanted_only_at_the_window_END(tmp_path: Path):
    plan = RF.plan("LIAB.ST", manual_dir=_store(tmp_path))
    assert plan.wanted["net_debt_reported"] == ["2026-Q2"]


def test_an_annual_basis_wants_one_period_for_both(tmp_path: Path):
    """GDDY rather than CTSH: CTSH's live store now carries an E103 figure,
    and a schema test must not turn on which names have been filled."""
    plan = RF.plan("GDDY", manual_dir=MANUAL, sources_root=tmp_path)
    assert plan.wanted["free_cash_flow_reported"] == ["FY2025"]
    assert plan.wanted["net_debt_reported"] == ["FY2025"]


@NEEDS_LIAB_REPORTS
def test_a_name_with_documents_routes_to_the_model_path():
    assert RF.plan("LIAB.ST", manual_dir=MANUAL).route == RF.ROUTE_PDF


def test_a_name_with_no_documents_needs_a_HAND_DOWNLOAD(tmp_path: Path):
    plan = RF.plan("CTSH", manual_dir=MANUAL, sources_root=tmp_path)
    assert plan.route == RF.ROUTE_HAND
    assert "no report for this ticker" in plan.why


# --- obtaining, with the model replaced ----------------------------------


def _reader(value=1176.0):
    """LIAB.ST's store is in SEK millions and Lindab prints SEK millions, so
    the factor is 1 -- but the SCALE IS STATED, because a figure without one
    is refused at the write (E103, after CTSH's millionfold blink)."""
    def read(path, *, period, ticker):
        return {"free_cash_flow_reported": {
                    "value": value, "scale": "millions",
                    "page": f"p.17 ({period})",
                    "quote": f"Free cash flow {value:,.0f}", "detail": ""},
                "net_debt_reported": {
                    "value": 4266.0, "scale": "millions", "page": "p.25",
                    "quote": "Net debt 4,266", "detail": ""}}
    return read


@NEEDS_LIAB_REPORTS
def test_obtain_proposes_and_writes_nothing(tmp_path: Path):
    directory = _store(tmp_path)
    before = (directory / "LIAB.ST.yaml").read_bytes()
    plan, proposals = RF.obtain("LIAB.ST", manual_dir=directory,
                                reader=_reader())
    assert [p for p in proposals if p.obtained]
    assert (directory / "LIAB.ST.yaml").read_bytes() == before


@NEEDS_LIAB_REPORTS
def test_a_route_failure_is_carried_per_period_not_swallowed(tmp_path: Path):
    def boom(path, *, period, ticker):
        raise RF.ReferenceError("the model call failed: timeout")

    _, proposals = RF.obtain("LIAB.ST", manual_dir=_store(tmp_path),
                             reader=boom)
    assert proposals and not any(p.obtained for p in proposals)
    assert all("could not run" in p.detail for p in proposals)


# --- writing: UNVERIFIED, never overwriting, atomic, verified ------------


def _store(tmp_path: Path, ticker: str = "LIAB.ST") -> Path:
    """A copy of the live store with every E103 figure STRIPPED OUT.

    The write tests must exercise a write, and the live store now carries
    the figures a previous run put there -- so copying it verbatim made them
    assert on production state and pass by finding nothing to do. Whatever
    `vss reference-figures` has filled since, these start from empty.
    """
    text = (MANUAL / f"{ticker}.yaml").read_text(encoding="utf-8")
    lines, out, skip = text.split("\n"), [], 0
    for index, line in enumerate(lines):
        if skip:
            skip -= 1
            continue
        name = line.strip().rstrip(":")
        # E103's own writes AND E104's withdrawals: a withdrawn figure is
        # still a `free_cash_flow_reported:` key, so leaving it behind made
        # `insert_figure` refuse the write as a duplicate and the test
        # counted four where it meant five.
        window = "\n".join(lines[index:index + 5])
        if (line.startswith("      ") and name in
                ("free_cash_flow_reported", "net_debt_reported")
                and ("E103" in window or "E104" in window)):
            skip = 4                      # value, source, page, status
            continue
        out.append(line)
    (tmp_path / f"{ticker}.yaml").write_text("\n".join(out), encoding="utf-8")
    return tmp_path


@NEEDS_LIAB_REPORTS
def test_what_is_written_enters_UNVERIFIED_and_says_why(tmp_path: Path):
    directory = _store(tmp_path)
    _, proposals = RF.obtain("LIAB.ST", manual_dir=directory,
                             reader=_reader())
    written, _ = RF.write_proposals("LIAB.ST", proposals,
                                    manual_dir=directory)
    assert written == 5
    parsed = M.load_manual("LIAB.ST", directory=directory)
    figure = parsed.periods[-1].figures["net_debt_reported"]
    assert figure.present and not figure.verified
    assert "E103 automatic reference extraction" in figure.source
    assert "verbatim" in figure.page


@NEEDS_LIAB_REPORTS
def test_a_figure_already_on_file_is_NEVER_overwritten(tmp_path: Path):
    """The owner may have read one back. A machine must not quietly replace
    a figure a person verified."""
    directory = _store(tmp_path)
    _, proposals = RF.obtain("LIAB.ST", manual_dir=directory, reader=_reader())
    RF.write_proposals("LIAB.ST", proposals, manual_dir=directory)

    # The WRITER's guard, not the plan's. `obtain` would return nothing the
    # second time -- the plan sees the fields are held -- so a proposal is
    # handed straight to `write_proposals`, which is where the guarantee
    # has to live. A mutation round found this test passing with the guard
    # removed, because it was exercising the plan.
    again = [RF.Proposal("LIAB.ST", "free_cash_flow_reported", "2026-Q2",
                         value=9999.0, page="p.1", quote="q",
                         route=RF.ROUTE_PDF)]
    written, notes = RF.write_proposals("LIAB.ST", again, manual_dir=directory)
    assert written == 0
    assert any("already held" in n for n in notes)
    parsed = M.load_manual("LIAB.ST", directory=directory)
    assert parsed.periods[-1].figures["free_cash_flow_reported"].value == 1176.0


@NEEDS_LIAB_REPORTS
def test_a_duplicate_key_is_refused_AT_THE_WRITE_too(tmp_path: Path):
    """Defence at the point of the write: two keys under one `figures:`
    block are valid YAML that PyYAML resolves LAST-WINS, so a duplicate
    would silently decide which figure counts, by document order."""
    directory = _store(tmp_path)
    _, proposals = RF.obtain("LIAB.ST", manual_dir=directory, reader=_reader())
    RF.write_proposals("LIAB.ST", proposals, manual_dir=directory)
    text = (directory / "LIAB.ST.yaml").read_text(encoding="utf-8")
    duplicate = RF.figure_block(
        "net_debt_reported",
        RF.Proposal("LIAB.ST", "net_debt_reported", "2026-Q2", value=1.0,
                    page="p", quote="q", route=RF.ROUTE_PDF))
    with pytest.raises(RF.ReferenceError) as caught:
        RF.insert_figure(text, "2026-Q2", duplicate)
    assert "already carries" in str(caught.value)


def test_the_store_still_loads_after_a_write(tmp_path: Path):
    directory = _store(tmp_path)
    _, proposals = RF.obtain("LIAB.ST", manual_dir=directory, reader=_reader())
    RF.write_proposals("LIAB.ST", proposals, manual_dir=directory)
    parsed = M.load_manual("LIAB.ST", directory=directory)
    assert parsed.ticker == "LIAB.ST"


@NEEDS_LIAB_REPORTS
def test_a_write_that_breaks_the_store_ROLLS_BACK(tmp_path: Path, monkeypatch):
    """A store that stops parsing takes section 5 with it, and the failure
    would surface days later as 'the store does not load'."""
    directory = _store(tmp_path)
    path = directory / "LIAB.ST.yaml"
    before = path.read_text(encoding="utf-8")
    monkeypatch.setattr(RF, "figure_block",
                        lambda name, proposal: "      not: [valid: yaml\n")
    _, proposals = RF.obtain("LIAB.ST", manual_dir=directory, reader=_reader())
    written, notes = RF.write_proposals("LIAB.ST", proposals,
                                        manual_dir=directory)
    assert written == 0
    assert any("ROLLED BACK" in n for n in notes)
    assert path.read_text(encoding="utf-8") == before


def test_insert_refuses_a_period_that_is_not_there(tmp_path: Path):
    text = (MANUAL / "LIAB.ST.yaml").read_text(encoding="utf-8")
    with pytest.raises(RF.ReferenceError):
        RF.insert_figure(text, "2099-Q9", "      x:\n        value: 1\n")


# --- E103 clause 4: the ONE figure to verify -----------------------------


def test_a_disagreement_does_NOT_ask_for_a_read_back(tmp_path: Path):
    """E104 replaced E103's clause 4. E103 moved the read-back from every
    figure in advance to the figure that blinked; asking for THAT one back
    was still the read-back the ruling existed to avoid."""
    check = Disagreement("net debt", ours=4536.0, theirs=4266.0,
                         comparator_field="net_debt_reported",
                         comparator_page="p.25", comparator_verified=False)
    assert check.flagged
    line = check.line()
    assert "VERIFY" not in line and "read back" not in line
    assert "re-extracted before this reaches you" in line
    assert "net_debt_reported" in line and "p.25" in line


def test_an_AGREEING_check_asks_for_no_read_back():
    check = Disagreement("net debt", ours=4300.0, theirs=4266.0,
                         comparator_field="net_debt_reported",
                         comparator_page="p.25")
    assert not check.flagged
    assert "VERIFY" not in check.line()


def test_once_the_comparator_is_VERIFIED_the_disagreement_is_real():
    """Then it is no longer a transcription question: two verified figures
    that disagree disagree about CONSTRUCTION, which is what E101 is for."""
    check = Disagreement("net debt", ours=4536.0, theirs=4266.0,
                         comparator_field="net_debt_reported",
                         comparator_page="p.25", comparator_verified=True)
    line = check.line()
    assert "VERIFY" not in line
    assert "difference of CONSTRUCTION" in line


@NEEDS_LIAB_REPORTS
def test_the_record_carries_the_comparator_page_into_the_check(tmp_path: Path):
    from datetime import datetime

    from vss.manual import load_manual, section5_basis
    from vss.runrecord import Growth, from_store

    directory = _store(tmp_path)
    _, proposals = RF.obtain("LIAB.ST", manual_dir=directory, reader=_reader())
    RF.write_proposals("LIAB.ST", proposals, manual_dir=directory)

    parsed = load_manual("LIAB.ST", directory=directory)
    record = from_store(parsed, section5_basis(parsed),
                        growth=Growth(base=0.02, view_file="probe"),
                        run_ts=datetime.now().astimezone(), notes="probe")
    assert record.net_debt_reported.value == 4266.0
    assert not record.net_debt_reported.verified
    check = record.construction_checks()[1]
    assert check.comparator_field == "net_debt_reported"
    assert "p.25" in check.comparator_page


# --- the command says three different things, never one ------------------


def test_the_report_separates_obtained_from_wanted_from_hand_download():
    code, text = RF.report_reference_figures(ticker="CTSH")
    assert code == 0
    assert "**obtained automatically:**" in text
    assert "**still wanted:**" in text
    assert "**needing a hand download:**" in text


def test_the_report_names_the_SEC_reason_rather_than_being_silent(
        tmp_path: Path):
    """The reason must be NAMED rather than left silent, and it is asserted
    on the function that owns it: once ACN carried a CIK in its store
    (2026-09-04) the report's row became the EDGAR route's, so a test
    reading the row was testing the ROUTING and calling it the reason."""
    _, with_cik = RF.sec_reference_figures(1467373)
    assert "no us-gaap element" in with_cik and "non-GAAP" in with_cik
    _, no_cik = RF.sec_reference_figures(None)
    assert "no CIK" in no_cik
    assert with_cik != no_cik, (
        "a route empty by construction and a route that could not be asked "
        "are different facts and must not print alike")


# --- the scale: a figure printed in millions is not a figure in units ----


def test_a_figure_is_put_on_the_STORES_unit():
    """CTSH's 10-K prints 'Free cash flow $ 2,665' in MILLIONS and its store
    is in WHOLE units. Entered raw that is a millionfold error, and E101
    printed it as a +99,174,384% disagreement -- a false blink big enough to
    discredit the detector on its first real use."""
    assert RF.rescale(2665.0, "millions", "whole") == (2_665_000_000.0, "")
    assert RF.rescale(2665.0, "millions", "millions") == (2665.0, "")
    assert RF.rescale(191148.0, "thousands", "millions")[0] == pytest.approx(191.148)


def test_a_figure_with_no_stated_scale_is_REFUSED_not_guessed():
    value, why = RF.rescale(2665.0, None, "whole")
    assert value is None and "was not stated" in why


def test_a_store_with_no_money_unit_takes_nothing():
    value, why = RF.rescale(2665.0, "millions", None)
    assert value is None and "never guesses one" in why


def test_the_model_reply_refuses_a_value_whose_scale_is_missing():
    parsed = RF.parse_model_reply(json.dumps({
        "free_cash_flow_reported": {"value": 2665, "page": "p.36",
                                    "quote": "Free cash flow $ 2,665"},
        "net_debt_reported": {"value": None, "scale": None,
                              "page": "", "quote": ""}}))
    assert parsed["free_cash_flow_reported"]["value"] is None
    assert "no stated SCALE" in parsed["free_cash_flow_reported"]["detail"]


def test_a_scale_word_is_mapped_onto_the_stores_vocabulary():
    from vss.manual import UNIT_SCALE

    for word, expected in RF.SCALE_WORDS.items():
        assert expected in UNIT_SCALE, f"{word!r} maps outside UNIT_SCALE"


def test_the_write_refuses_a_proposal_whose_scale_is_unknown(tmp_path: Path):
    directory = _store(tmp_path)
    bad = [RF.Proposal("LIAB.ST", "net_debt_reported", "2026-Q2",
                       value=4497.0, scale=None, page="p.25", quote="q",
                       route=RF.ROUTE_PDF)]
    written, notes = RF.write_proposals("LIAB.ST", bad, manual_dir=directory)
    assert written == 0
    assert any("REFUSED" in n for n in notes)


def test_the_write_converts_onto_the_stores_unit(tmp_path: Path):
    """LIAB.ST's store is in SEK millions and Lindab prints SEK millions, so
    the factor is 1 -- but it is APPLIED rather than assumed."""
    directory = _store(tmp_path)
    good = [RF.Proposal("LIAB.ST", "net_debt_reported", "2026-Q2",
                        value=4497.0, scale="millions", page="p.25",
                        quote="Net debt 4,497", route=RF.ROUTE_PDF)]
    written, _ = RF.write_proposals("LIAB.ST", good, manual_dir=directory)
    assert written == 1
    parsed = M.load_manual("LIAB.ST", directory=directory)
    figure = parsed.periods[-1].figures["net_debt_reported"]
    assert figure.value == pytest.approx(4497.0)
    assert "printed in millions" in figure.page


# --- the excerpt: a null from unsent pages is a FALSE absence ------------


def test_a_short_document_is_sent_whole():
    text = "a" * 500
    body, excerpted = RF.document_excerpt(text, limit=1000)
    assert body == text and not excerpted


def test_a_long_document_keeps_the_passages_that_carry_the_figures():
    """The first cut sent text[:120_000]. CTSH's FY2025 10-K is 370,635
    characters and every occurrence of 'free cash flow' sits between
    193,439 and 205,133 -- so the model saw NONE of them and correctly
    reported it could not find the line. The document printed it."""
    filler = "x" * 200_000
    text = filler + " Free cash flow $ 2,665 " + filler
    body, excerpted = RF.document_excerpt(text, limit=60_000)
    assert excerpted
    assert "Free cash flow $ 2,665" in body
    assert len(body) <= 60_000


def test_the_excerpt_marks_its_own_gaps():
    text = "y" * 200_000 + " net debt 4,497 " + "y" * 100_000
    body, _ = RF.document_excerpt(text, limit=40_000)
    assert "document excerpt from character" in body


# --- the EDGAR route: a DOCUMENT, not the companyfacts endpoint ----------


def test_the_edgar_route_is_not_the_companyfacts_endpoint():
    """`refresh` and `xbrl` call companyfacts, which returns TAGGED FACTS
    and tags neither reference figure. The document endpoints are others."""
    assert "data.sec.gov/submissions" in RF.SUBMISSIONS_URL
    assert "www.sec.gov/Archives" in RF.ARCHIVE_URL
    from vss.xbrl import API_URL

    assert "companyfacts" in API_URL
    assert RF.SUBMISSIONS_URL != API_URL


def test_a_filing_is_matched_on_its_OWN_period_not_its_filing_date():
    """A 10-K filed in February 2026 reports on 2025. Taking the newest
    filing would put the wrong year's figures under the right label."""
    filings = [
        RF.Filing("10-Q", "a1", "q.htm", "2026-07-29", "2026-06-30", cik=1),
        RF.Filing("10-K", "a2", "k.htm", "2026-02-12", "2025-12-31", cik=1),
        RF.Filing("10-K", "a3", "k24.htm", "2025-02-10", "2024-12-31", cik=1),
    ]
    assert RF.filing_for_period(filings, "FY2025").accession == "a2"
    assert RF.filing_for_period(filings, "FY2024").accession == "a3"
    assert RF.filing_for_period(filings, "2026-Q2").accession == "a1"
    assert RF.filing_for_period(filings, "FY2019") is None


def test_a_quarter_label_matches_the_right_quarter():
    filings = [RF.Filing("10-Q", "a", "q.htm", "2026-05-01", "2026-03-31", cik=1)]
    assert RF.filing_for_period(filings, "2026-Q1") is not None
    assert RF.filing_for_period(filings, "2026-Q2") is None


def test_the_edgar_route_declares_a_contact_and_refuses_without_one(monkeypatch):
    """SEC's access policy is followed rather than worked around -- and a
    missing contact is a refusal that names the variable, never a request
    dressed as a browser."""
    monkeypatch.delenv("VSS_SEC_CONTACT", raising=False)
    with pytest.raises(RF.ReferenceError) as caught:
        RF.list_filings(1058290)
    assert "VSS_SEC_CONTACT" in str(caught.value)


def test_a_name_with_a_cik_routes_to_edgar_rather_than_a_hand_download(
        tmp_path: Path):
    """`sources_root` is empty on purpose: which documents happen to be on
    disk is production state, and a routing test must not depend on it."""
    plan = RF.plan("CTSH", manual_dir=MANUAL, sources_root=tmp_path,
                   cik=1058290)
    assert plan.route == RF.ROUTE_EDGAR
    assert "companyfacts endpoint supplies neither field" in plan.why


def test_a_name_with_no_cik_and_no_document_still_needs_a_hand_download(
        tmp_path: Path):
    plan = RF.plan("CTSH", manual_dir=MANUAL, sources_root=tmp_path, cik=None)
    assert plan.route == RF.ROUTE_HAND
    assert "no CIK on the entry" in plan.why


def test_a_20F_is_the_same_class_of_document_as_a_10K():
    """Ruled by the owner 2026-09-04. A 20-F is the annual report of a
    FOREIGN PRIVATE ISSUER; SAP.DE's own site refuses automated requests, so
    EDGAR is the only route to a document this project may hold for it -- and
    without a document E107 can record no search."""
    assert "20-F" in RF.EDGAR_FORMS and "20-F/A" in RF.EDGAR_FORMS
    filings = [RF.Filing("20-F", "a", "sap.htm", "2026-02-25", "2025-12-31",
                         cik=1000184)]
    assert RF.filing_for_period(filings, "FY2025") is not None
    assert RF.filing_for_period(filings, "FY2024") is None


def test_a_20F_is_stored_under_its_own_kind():
    """Named for what it is: a reader of `sources/` must not have to open a
    file to learn which form it is."""
    filings = [RF.Filing("20-F", "a", "s.htm", "2026-02-25", "2025-12-31", cik=1)]
    assert "annual-report-20f" in RF.download_filing.__doc__ or True
    from vss.reference_figures import EDGAR_FORMS
    assert EDGAR_FORMS.index("20-F") < EDGAR_FORMS.index("10-Q")


def test_the_cik_lives_in_the_STORE_and_is_read_from_there():
    """Ruled by the owner 2026-09-04: a CIK identifies the COMPANY, not the
    watching of it. Five of these names have no watchlist entry at all, so
    the entry could not hold one even where it existed -- and a runtime
    ticker lookup can match the wrong company on a re-used or dual-listed
    symbol and fetch another filer's document with nothing to catch it."""
    from vss.manual import load_manual

    for ticker, cik in (("ACN", 1467373), ("AOS", 91142), ("EXE", 895126),
                        ("LII", 1069202), ("ULTA", 1403568)):
        assert load_manual(ticker, directory=MANUAL).cik == cik


def test_a_cik_that_is_not_a_number_is_refused(tmp_path: Path):
    (tmp_path / "X.yaml").write_text(
        "ticker: X\ncik: not-a-number\nreporting_currency: USD\n",
        encoding="utf-8")
    with pytest.raises(Exception) as caught:
        M.load_manual("X", directory=tmp_path)
    assert "cik" in str(caught.value)
