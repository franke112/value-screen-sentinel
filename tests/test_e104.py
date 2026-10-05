"""E104: a disagreeing check is re-extracted before it is escalated.

E103 moved the read-back from every figure in advance to the figure that
blinked. Asking for THAT one back was still the read-back the ruling existed
to avoid — the owner's own catch on E103's first full run, where eight
checks disagreed and the report asked for eight read-backs.

So the machine reads the figure again, on a narrow excerpt around the line
the first pass quoted, and:

    two readings AGREE      -> the transcription is settled; the
                               disagreement is CONSTRUCTION and the owner's
    two readings DIFFER     -> the extraction was the problem; the figure
                               WITHDRAWS ITSELF and nothing reaches him

**The test that matters is `test_a_contradicted_figure_withdraws_itself`.**
It is the half that costs the owner nothing, and it is the half that would
silently not happen if the withdrawal were ever dropped.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from vss import manual as M
from vss import reference_figures as RF

MANUAL = Path("config/manual")


def _proposal(value=37.0, quote="Free cash flow 37 185 383 -572 -163"):
    return RF.Proposal("LIAB.ST", "free_cash_flow_reported", "2025-Q3",
                       value=value, scale="millions",
                       page=f"page 25 -- verbatim: {quote}", quote=quote,
                       route=RF.ROUTE_PDF)


def _reply(value, scale="millions", quote="Free cash flow 37"):
    body = json.dumps({"value": value, "scale": scale, "quote": quote})

    class Response:
        def __enter__(self):
            return self

        def __exit__(self, *a):
            return False

        def read(self):
            return json.dumps(
                {"choices": [{"message": {"content": body}}]}).encode()

    return lambda request, timeout=None: Response()


# --- the second pass is INDEPENDENT ---------------------------------------


def test_the_second_pass_is_never_told_the_first_answer(tmp_path: Path):
    """**Clause 2, and it is the whole of the independence.** A second
    reading shown the first is not a second reading."""
    document = tmp_path / "LIAB.ST_2025-Q3_x.txt"
    document.write_text("blah Free cash flow 37 185 383 -572 -163 blah",
                        encoding="utf-8")
    seen = {}

    def transport(request, timeout=None):
        seen["body"] = request.data.decode()
        return _reply(37.0)(request)

    RF.confirm_figure(_proposal(value=37.0), document,
                      transport=transport, api_key="k")
    assert "37 185 383" in seen["body"], "the passage must reach the model"
    payload = json.loads(seen["body"])
    sent = "\n".join(m["content"] for m in payload["messages"])
    # The QUOTE locates the passage; the VALUE must not appear as an answer.
    assert "first pass" not in sent.lower()
    assert "37.0" not in sent
    assert "value" in sent, "it is still asked for a value"


def test_the_quote_only_LOCATES_the_passage():
    text = "x" * 5000 + " Net debt 4,497 4,456 " + "y" * 5000
    passage = RF.narrow_excerpt(text, "Net debt 4,497 4,456")
    assert passage is not None
    assert "Net debt 4,497" in passage
    assert len(passage) <= RF.CONFIRM_WINDOW + 40


def test_a_quote_that_is_not_in_the_document_is_itself_a_finding(tmp_path: Path):
    assert RF.narrow_excerpt("nothing like it here", "Free cash flow 37") is None


def test_a_missing_quote_cannot_locate_anything():
    assert RF.narrow_excerpt("some text", "") is None


def test_a_normalised_quote_still_finds_its_line():
    """The first pass may have collapsed whitespace. A distinctive run of
    words still locates the passage; a bare number never would."""
    text = "prefix " + "z" * 3000 + " Adjusted free cash flow for the period -21 " + "z" * 3000
    assert RF.narrow_excerpt(text, "Adjusted free cash flow -21") is not None


# --- what two readings mean ----------------------------------------------


def test_two_readings_that_agree_settle_the_transcription(tmp_path: Path):
    document = tmp_path / "d.txt"
    document.write_text("Free cash flow 37 185 383", encoding="utf-8")
    result = RF.confirm_figure(_proposal(value=37.0), document,
                               transport=_reply(37.0), api_key="k")
    assert result.agreed and result.conclusive
    assert "CONFIRMED" in result.line()
    assert "CONSTRUCTION" in result.line()


def test_two_readings_that_differ_convict_the_extraction(tmp_path: Path):
    """A wrong column in a multi-column row is exactly this shape: the
    first pass took 37, the second takes 185 from the same line."""
    document = tmp_path / "d.txt"
    document.write_text("Free cash flow 37 185 383", encoding="utf-8")
    result = RF.confirm_figure(_proposal(value=37.0), document,
                               transport=_reply(185.0), api_key="k")
    assert not result.agreed and result.conclusive
    assert "CONTRADICTED" in result.line()
    assert "WITHDRAWN" in result.line()


def test_a_second_pass_that_reads_nothing_does_not_confirm(tmp_path: Path):
    document = tmp_path / "d.txt"
    document.write_text("Free cash flow 37 185 383", encoding="utf-8")
    result = RF.confirm_figure(_proposal(), document,
                               transport=_reply(None), api_key="k")
    assert not result.agreed and not result.conclusive
    assert "NOT CONFIRMED" in result.line()


def test_a_difference_of_SCALE_ALONE_is_not_a_disagreement(tmp_path: Path):
    """Two readings that differ only in the scale they named have not
    disagreed about the line."""
    document = tmp_path / "d.txt"
    document.write_text("Free cash flow 37", encoding="utf-8")
    result = RF.confirm_figure(
        _proposal(value=37.0), document,
        transport=_reply(37_000.0, scale="thousands"), api_key="k")
    assert result.agreed, "37 millions and 37,000 thousands are one figure"


def test_no_api_key_is_NOT_a_confirmation(tmp_path: Path, monkeypatch):
    monkeypatch.delenv("VSS_OPENROUTER_KEY", raising=False)
    document = tmp_path / "d.txt"
    document.write_text("Free cash flow 37", encoding="utf-8")
    result = RF.confirm_figure(_proposal(), document)
    assert not result.agreed and not result.conclusive
    assert "not set" in result.detail


# --- and the figure withdraws itself --------------------------------------


def _store_with(tmp_path: Path, value=37.0, quote="Free cash flow 37 185 383"):
    from tests.test_e103 import _store

    directory = _store(tmp_path)
    text = (directory / "LIAB.ST.yaml").read_text(encoding="utf-8")
    text = RF.insert_figure(
        text, "2025-Q3",
        RF.figure_block("free_cash_flow_reported", _proposal(value, quote)))
    (directory / "LIAB.ST.yaml").write_text(text, encoding="utf-8")
    return directory


def test_a_contradicted_figure_withdraws_itself(tmp_path: Path):
    """**THE ONE THAT MATTERS.** This is the half that costs the owner
    nothing, and the half that would silently not happen if it were
    dropped."""
    directory = _store_with(tmp_path)
    text = (directory / "LIAB.ST.yaml").read_text(encoding="utf-8")
    confirmation = RF.Confirmation("free_cash_flow_reported", "2025-Q3",
                                   37.0, 185.0, detail="the two readings differ")
    withdrawn = RF.withdraw_figure(text, "2025-Q3",
                                   "free_cash_flow_reported", confirmation)
    (directory / "LIAB.ST.yaml").write_text(withdrawn, encoding="utf-8")

    parsed = M.load_manual("LIAB.ST", directory=directory)
    entry = next(e for e in parsed.periods if e.period == "2025-Q3")
    figure = entry.figures["free_cash_flow_reported"]
    assert not figure.present, "a withdrawn figure is not a figure"
    assert "E104 WITHDRAWN" in (figure.source or "")
    assert "first pass read 37" in (figure.page or "")
    assert "second pass read 185" in (figure.page or "")


def test_a_withdrawal_is_a_NAMED_ABSENCE_not_a_deletion(tmp_path: Path):
    """A reader must see that the figure was tried and withdrawn, rather
    than never attempted -- and the next run may try again, because a null
    figure is not `present`."""
    directory = _store_with(tmp_path)
    text = (directory / "LIAB.ST.yaml").read_text(encoding="utf-8")
    out = RF.withdraw_figure(
        text, "2025-Q3", "free_cash_flow_reported",
        RF.Confirmation("free_cash_flow_reported", "2025-Q3", 37.0, 185.0))
    assert "free_cash_flow_reported:" in out
    assert "value: null" in out
    assert out.count("free_cash_flow_reported:") == \
        text.count("free_cash_flow_reported:")


def test_withdrawing_a_figure_that_is_not_there_refuses(tmp_path: Path):
    from tests.test_e103 import _store

    text = (_store(tmp_path) / "LIAB.ST.yaml").read_text(encoding="utf-8")
    with pytest.raises(RF.ReferenceError):
        RF.withdraw_figure(text, "2025-Q3", "net_debt_reported",
                           RF.Confirmation("net_debt_reported", "2025-Q3",
                                           1.0, 2.0))


def test_the_store_still_loads_after_a_withdrawal(tmp_path: Path):
    directory = _store_with(tmp_path)
    text = (directory / "LIAB.ST.yaml").read_text(encoding="utf-8")
    out = RF.withdraw_figure(
        text, "2025-Q3", "free_cash_flow_reported",
        RF.Confirmation("free_cash_flow_reported", "2025-Q3", 37.0, None,
                        detail="the second pass returned no figure"))
    (directory / "LIAB.ST.yaml").write_text(out, encoding="utf-8")
    assert M.load_manual("LIAB.ST", directory=directory).ticker == "LIAB.ST"


# --- a figure the owner VERIFIED is never re-read -------------------------


def test_a_verified_comparator_is_left_alone(tmp_path: Path):
    """SAP.DE and PNDORA.CO are of this kind: both sides are figures the
    owner read by hand, so a second machine reading adds nothing."""
    called = []

    def confirmer(proposal, document, **kwargs):
        called.append(proposal.field)
        return RF.Confirmation(proposal.field, proposal.period,
                               proposal.value, proposal.value, agreed=True)

    # E117 (2026-09-19): SAP never isolates its lease interest, so its FCF0
    # is DATA MISSING and no FCF disagreement forms on the committed store.
    # This test is about E104, not leases: a COPY whose lease declaration
    # reads `yes` forms FCF0 without that leg, and the verified comparator
    # disagrees with it exactly as before.
    copy = tmp_path / "manual"
    copy.mkdir()
    text = (MANUAL / "SAP.DE.yaml").read_text(encoding="utf-8")
    text = text.replace("operating_leases_in_ocf:\n  value: no",
                        "operating_leases_in_ocf:\n  value: yes", 1)
    (copy / "SAP.DE.yaml").write_text(text, encoding="utf-8")
    results, notes = RF.confirm_disagreements(
        "SAP.DE", manual_dir=copy, sources_root=tmp_path,
        confirmer=confirmer)
    assert "free_cash_flow_reported" not in called
    assert any("VERIFIED" in n for n in notes)


def test_a_hand_entered_figure_is_not_re_read_either(tmp_path: Path):
    """E104 re-reads what THIS PROJECT entered. A figure somebody typed is
    not an extraction and a second extraction says nothing about it."""
    from tests.test_e103 import _store

    directory = _store(tmp_path)
    text = (directory / "LIAB.ST.yaml").read_text(encoding="utf-8")
    text = RF.insert_figure(text, "2026-Q2",
                            "      net_debt_reported:\n"
                            # DISAGREES with ours (3,126 since E117 took the
                            # 1,410 of leases out; 4,536 before) by -36%, so
                            # the check FLAGS -- otherwise E104 never reaches
                            # it and the test would pass for the wrong reason.
                            "        value: 2000\n"
                            '        source: "hand, p.25"\n'
                            '        page: "p.25, net debt note"\n'
                            "        status: UNVERIFIED\n")
    (directory / "LIAB.ST.yaml").write_text(text, encoding="utf-8")
    called = []

    def confirmer(proposal, document, **kwargs):
        called.append(proposal.period)
        return RF.Confirmation(proposal.field, proposal.period, 1.0, 1.0,
                               agreed=True)

    _, notes = RF.confirm_disagreements("LIAB.ST", manual_dir=directory,
                                        sources_root=tmp_path,
                                        confirmer=confirmer)
    assert "2026-Q2" not in called
    assert any("entered by hand" in n for n in notes)


# --- the report says three different things ------------------------------


def test_the_report_separates_confirmed_from_withdrawn(tmp_path: Path):
    def confirmer(proposal, document, **kwargs):
        agreed = proposal.period == "2026-Q2"
        return RF.Confirmation(proposal.field, proposal.period,
                               proposal.value,
                               proposal.value if agreed else 999.0,
                               agreed=agreed)

    _, text = RF.report_confirmations(ticker="SAP.DE", manual_dir=MANUAL,
                                      sources_root=tmp_path,
                                      confirmer=confirmer)
    assert "confirmed — CONSTRUCTION, and yours to judge" in text
    assert "withdrawn — the extraction was the problem" in text
    assert "not re-read because you verified them" in text


def test_a_near_miss_is_reported_at_the_precision_that_shows_it():
    """KAR.ST's 2025-Q4 withdrawal printed as "the first pass read 239 and
    the second 239" -- a contradiction that read as an identity, because
    `:,.0f` rounded 238.6 to 239. A summary that hides the difference
    discredits the report rather than the extraction."""
    result = RF.Confirmation("free_cash_flow_reported", "2025-Q4",
                             238.6, 239.0, detail="the two readings differ")
    line = result.line()
    assert "238.6" in line and "239" in line
    assert "read 239 and the second 239" not in line
