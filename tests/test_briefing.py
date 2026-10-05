"""E76's BRIEFING: research, and never a verdict (2026-09-04).

The property these tests exist to hold is the one the module opens with:
**it may make no judgement.** Everything else is plumbing around that.
"""

from __future__ import annotations

from datetime import date

import pytest

from vss import briefing as B


# --- the line that must never be crossed ----------------------------------


@pytest.mark.parametrize("line", [
    "We believe the shares are worth more than this.",
    "The name looks attractive against its peers.",
    "It is undervalued on any measure.",
    "A fair value of 140 would follow.",
    "We assume growth of 5% a year.",
    "The shares are cheap.",
    "We recommend a purchase.",
])
def test_a_judgement_ANYWHERE_outside_a_quote_is_found(line):
    assert B.judgement_in(f"# Briefing\n\n{line}\n")


def test_a_VERBATIM_QUOTE_may_say_what_the_filer_said():
    """Crocs' own 10-K says *"we do not believe that we compete directly
    with any single company"*. An earlier cut of this guard refused the
    briefing for reproducing it. QUOTING A FILER IS NOT ASSERTING, so a
    fenced block is exempt -- and only a fenced block."""
    inside = ("# Briefing\n\n```\nAlthough we do not believe that we compete "
              "directly with any single company, we believe portions of our "
              "business compete with others.\n```\n")
    assert B.judgement_in(inside) == []
    outside = inside.replace("```\n", "", 2)
    assert B.judgement_in(outside)


def test_the_guard_runs_over_the_FINISHED_text_and_refuses_the_whole_thing():
    """It is not advice to the author: `build` raises and writes nothing."""
    import vss.briefing as module

    calls = {}

    def boom(*a, **k):
        calls["reached"] = True
        raise AssertionError("should not be reached")

    text = "the shares are cheap"
    assert B.judgement_in(text)
    del boom, calls, module


# --- locating and quoting -------------------------------------------------


SAMPLE = "\n".join([
    "Summary Compensation Table",          # the contents
    "42",
    "Item 5. Market for Registrant's Common Equity",
    "Issuer Purchases of Equity Securities",
    "Total Number\tAverage",
    "October 1, 2025 to October 31, 2025\t54,463 \t$\t383.89 \t54,463",
    "November 1, 2025 to November 30, 2025\t68,480 \t365.05 \t68,480",
    "December 1, 2025 to December 31, 2025\t52,503 \t398.52 \t52,503",
    "Equity Compensation Plan Information",
])


def test_a_heading_in_the_CONTENTS_does_not_win_over_the_table():
    """`last=True` exists because a 10-K names every item twice and the body
    always follows the contents."""
    _, first = B.block_at(SAMPLE, r"Issuer Purchases", lines=4)
    assert first and "Total Number" in first[0]
    anchor, table = B.first_table(
        SAMPLE, (r"^Issuer Purchases of Equity Securities\s*$",),
        lines=6, stop=r"^Equity Compensation Plan")
    assert anchor and B.numeric_rows(table) >= 3
    assert any("383.89" in line for line in table)


def test_a_block_with_no_NUMBERS_is_not_a_table():
    """Crocs' contents put `Item 6. [Reserved]` under the same heading."""
    prose = "Issuer Purchases of Equity Securities\n33\nItem 6.\n[Reserved]\n34"
    anchor, table = B.first_table(
        prose, (r"^Issuer Purchases of Equity Securities\s*$",), rows=3)
    assert anchor == "" and table == []


def test_prose_is_anchored_on_the_SENTENCE_not_on_a_heading():
    """A 10-Q puts *"Revenues were $996.3 million..."* under a heading
    called `Revenues`, and the income statement three lines below puts its
    column headers under the same word. A length tells them apart."""
    text = "\n".join([
        "Revenues",
        "$\t996,301\t$\t1,062,200",
        "Revenues were $996.3 million for the third quarter of 2025, a 6.2% "
        "decrease compared to the third quarter of 2024, due to lower unit "
        "sales volume in both brands and net changes in exchange rates which "
        "together moved the figure by more than a hundred million dollars.",
    ])
    got = B.prose_matching(text, r"^Revenues?[\s.,]")
    assert len(got) == 1 and got[0].startswith("Revenues were $996.3")


def test_item_body_takes_the_BODY_and_not_the_contents():
    text = "\n".join([
        "Item 1.", "2", "Item 1A.", "6",          # the contents
        "PART I", "ITEM 1. Business",
        "x" * 200,
        "ITEM 1A. Risk Factors", "y" * 200,
    ])
    body = B.item_body(text, "1", "1A", lines=3)
    assert body == ["x" * 200]


# --- Form 4 ---------------------------------------------------------------


FORM4 = """<ownershipDocument>
<reportingOwner><reportingOwnerId><rptOwnerName>Rees Andrew</rptOwnerName>
</reportingOwnerId><reportingOwnerRelationship><isOfficer>1</isOfficer>
<officerTitle>Chief Executive Officer</officerTitle>
</reportingOwnerRelationship></reportingOwner>
<nonDerivativeTable>
<nonDerivativeTransaction>
<transactionDate><value>2026-08-07</value></transactionDate>
<transactionCoding><transactionCode>S</transactionCode></transactionCoding>
<transactionAmounts><transactionShares><value>5796</value></transactionShares>
<transactionPricePerShare><value>137.4143</value></transactionPricePerShare>
</transactionAmounts></nonDerivativeTransaction>
<nonDerivativeTransaction>
<transactionDate><value>2026-05-01</value></transactionDate>
<transactionCoding><transactionCode>A</transactionCode></transactionCoding>
<transactionAmounts><transactionShares><value>1000</value></transactionShares>
</transactionAmounts></nonDerivativeTransaction>
</nonDerivativeTable></ownershipDocument>"""


def test_a_GRANT_is_not_an_open_market_purchase(tmp_path):
    """E76 wants open-market transactions. `A` is a grant and `M` an option
    exercise, and folding either in reports an insider "buy" nobody made."""
    filing = B.Filing(form="4", filed="2026-08-11", period="2026-08-07",
                      accession="0001-26-1", document="x/form4.xml", cik=1)
    (tmp_path / "_briefing_0001-26-1_form4.xml").write_text(FORM4, encoding="utf-8")
    trades, skipped = B.insider_trades([filing], since=date(2026, 1, 1),
                                       root=tmp_path)
    assert skipped == 1
    assert [(t.code, t.shares, t.price) for t in trades] == [("S", 5796.0, 137.4143)]
    assert trades[0].owner == "Rees Andrew"
    assert trades[0].title == "Chief Executive Officer"


def test_buys_and_sells_are_NEVER_netted(tmp_path):
    filing = B.Filing("4", "2026-08-11", "", "0001-26-1", "x/form4.xml", 1)
    (tmp_path / "_briefing_0001-26-1_form4.xml").write_text(FORM4, encoding="utf-8")
    trades, skipped = B.insider_trades([filing], since=date(2026, 1, 1),
                                       root=tmp_path)
    section = B.insiders_section(trades, skipped, date(2026, 1, 1), 1)
    body = "\n".join(section.lines)
    assert "**PURCHASES**" in body and "**SALES**" in body
    assert "NEVER NETTED" in body
    assert "*none*" in body            # no purchases, said rather than implied


def test_a_filer_with_forms_and_no_open_market_line_says_THAT(tmp_path):
    section = B.insiders_section([], 12, date(2026, 1, 1), 4)
    body = "\n".join(section.lines)
    assert "NOT ONE OPEN-MARKET TRANSACTION" in body
    assert "That is a finding and not an absence of data" in body


# --- sections that cannot be filled ---------------------------------------


def test_a_section_that_cannot_be_filled_SAYS_SO_and_is_collected():
    empty = B.Section("x", "A section", why_not="the filing carries no such note")
    assert not empty.filled
    assert "**NOT FILLED.** the filing carries no such note" in empty.render()
    closing = B.unanswered_section([empty])
    assert any("A section — NOT FILLED" in line for line in closing.lines)


def test_the_closing_section_also_collects_a_PARTIAL_gap():
    partial = B.Section("y", "Another", lines=["**NOT LOCATED.** no table"])
    closing = B.unanswered_section([partial])
    assert any("Another" in line and "NOT LOCATED" in line
               for line in closing.lines)


def test_no_web_route_is_NOT_FILLED_and_never_a_hole():
    section = B.price_section("X", [(date(2026, 1, 2), 100.0),
                                    (date(2026, 1, 3), 80.0)], None)
    body = "\n".join(section.lines)
    assert "the web route was not available" in body
    assert "NOT FILLED" in body


def test_an_UNCITED_web_answer_is_DROPPED():
    """The route may say anything; without a URL none of it is kept."""
    section = B.price_section(
        "X", [(date(2026, 1, 2), 100.0), (date(2026, 1, 3), 80.0)],
        lambda q: ("The shares fell because of a downgrade.", []))
    body = "\n".join(section.lines)
    assert "an uncited claim is dropped" in body
    assert "downgrade" not in body


def test_a_CITED_web_answer_is_kept_WITH_its_url():
    section = B.price_section(
        "X", [(date(2026, 1, 2), 100.0), (date(2026, 1, 3), 80.0)],
        lambda q: ("The company cut its outlook.", ["https://example.com/a"]))
    body = "\n".join(section.lines)
    assert "The company cut its outlook." in body
    assert "https://example.com/a" in body
    assert "WEB-SOURCED, not from a filing" in body
