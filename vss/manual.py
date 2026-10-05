"""Manually entered fundamentals, for the companies no endpoint serves.

WHY THIS EXISTS. `vss xbrl` reads a filer's own tagged facts from
data.sec.gov and every figure arrives attached to its tag, its context
period and an accession number. Most of the store cannot be asked: on the
2026-08-21 screener run 347 of the 533 filter-1 candidates carry a
foreign listing suffix, and for most of a Nordic or continental list
there is no SEC endpoint at all. A FOREIGN SUFFIX IS NOT ITSELF THE
TEST -- a foreign private issuer files a 20-F and does have a CIK, which
is how SAP.DE and UNA.AS (CIK 217410) had their section 5 inputs built
from SEC XBRL, so `vss xbrl --cik` is the first thing to try. This module
is for the remainder: the names with no CIK to try, for which the
FRAMEWORK section 5 chain has no input at all and the ranking key has
only whatever the quote vendor happened to return.

This module is the third source, beside the vendor and the SEC: figures
the OWNER read out of the company's own report and typed in, each one
carrying the document and page it was read from and a flag saying
whether it has been checked back against that page.

WHAT IT IS NOT. It is not a valuation model. Section 5's three methods
stay where they are -- in the owner's hands, in a per-name workbook.
This module supplies section 5's INPUTS and REFUSES to hand over a
figure nobody has verified. It computes no fair value, and it must not
grow one.

THE THREE THINGS A HAND-TYPED FIGURE CAN GET WRONG, and what stops each:

  * THE UNIT. A margin typed as 6.6 instead of 0.066, or a statement
    read in thousands beside one read in millions. `config.unit_problem`
    is asked the same question the watchlist asks it, and the scale
    check compares the same field ACROSS periods, which is the only
    place a whole-file unit mix is visible.
  * THE AGE. Figures from accounts that closed two years ago divided
    into a price from today. The newest period end decides STALE, on
    the same limit `fundamentals.py` uses.
  * THE PERIOD. A gross profit from 2025 over total assets from 2024 is
    not a ratio. Every ratio section 5 forms is taken from ONE period
    entry and is DATA MISSING when a leg is absent from it -- never
    back-filled from the period next door.

Those are the same three the SEC path is held to. The fourth is new,
and is the reason for the status flag: a figure can simply be typed
wrong, and no arithmetic can see it. Only a second read of the page
can, so the file records whether that read has happened.
"""

from __future__ import annotations

import re

import logging
from dataclasses import dataclass, field, replace
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Any, Iterable, Mapping, Sequence

import yaml

from .config import ConfigError, unit_problem
from .fundamentals import (
    FIELD_NO_DATA,
    FIELD_OK,
    MAX_REPORT_AGE_DAYS,
    FieldValue,
    SeriesPoint,
    TickerFundamentals,
)
from .prices import STATUS_OK, STATUS_STALE
from .rules import (
    DEFAULT_REPORTING_FREQUENCY,
    MAX_CLOSE_AGE_DAYS,
    PERIOD_KINDS_BY_FREQUENCY,
    SCALE_JUMP_FACTOR,
    VALID_PERIOD_BASIS,
    VALID_REPORTING_FREQUENCIES,
    overlap_problem,
    period_kind_allowed,
    period_months,
    period_parts,
    period_span,
    period_sort_key,
)

log = logging.getLogger(__name__)

#: Where filled files live, one per ticker: config/manual/PNDORA.CO.yaml.
#: Beside watchlist.yaml because it is the same kind of thing -- a file
#: the owner writes and the tool only ever reads.
MANUAL_DIR = Path("config/manual")
TEMPLATE_PATH = MANUAL_DIR / "TEMPLATE.yaml"

#: The origin string this path stamps on everything it produces. The
#: vendor path and the SEC path have their own; a reader of any output
#: must never have to work out which one a figure came from.
ORIGIN = "manual"

#: Origins a manual file may declare. `manual` is a figure the owner read
#: off a page and typed. `nordic-xlsx` is a figure lifted from a cell of
#: the issuer's own figures appendix through a committed cell->field map
#: (vss/appendix.py) -- a different provenance, weaker than a tagged fact
#: and stronger than a reading of a PDF, and it is named rather than
#: folded into the other.
ORIGIN_XLSX = "nordic-xlsx"
#: `sec-xbrl` is a figure written by `vss xbrl --annual` out of a filer's
#: own tagged facts at data.sec.gov. It is named `sec-xbrl` and not `xbrl`
#: because ESEF packages are XBRL too -- Eiffage files one -- and a reader
#: must be able to tell which registry a figure came out of.
#:
#: It is the STRONGEST provenance in this schema, and it is still a
#: manual file: WHICH TAG answers which field was a decision, and that
#: decision lives in `vss/xbrl.py`'s ANNUAL_FIELDS table where it can be
#: diffed and argued with, the same way `config/manual/maps/` holds the
#: appendix path's.
ORIGIN_XBRL = "sec-xbrl"
VALID_ORIGINS: tuple[str, ...] = (ORIGIN, ORIGIN_XLSX, ORIGIN_XBRL)

#: What each origin is, in one line, for the head of the report. A reader
#: must never have to infer how a figure got into the file.
ORIGIN_PROSE: dict[str, str] = {
    ORIGIN: ("Every figure below was read out of a company report BY HAND "
             "and typed into `{path}`. No endpoint served it, no model "
             "extracted it and nothing here computed it."),
    ORIGIN_XLSX: ("Every figure below was lifted from a CELL of the issuer's "
                  "own figures appendix into `{path}`, through the committed "
                  "cell-to-field map in `config/manual/maps/`. A cell is a "
                  "number, not a reconstruction -- but WHICH cell was a "
                  "decision, and the map is where that decision is written "
                  "down and reviewed. No model read it and nothing was "
                  "derived, summed or inferred."),
    ORIGIN_XBRL: ("Every figure below arrived from the filer's own tagged "
                  "facts at data.sec.gov into `{path}`, each one carrying "
                  "the us-gaap tag it was filed under, the context period "
                  "it covers and the accession number of the filing that "
                  "reported it. Nobody typed it and no model read it. What "
                  "WAS a decision is which tag answers which field, and "
                  "that decision is in `vss/xbrl.py` rather than in this "
                  "file."),
}

#: How each origin stands against the other two, in one sentence. Kept per
#: origin rather than written once into the report, because the sentence
#: that is true of a hand-read figure -- "weaker than the SEC path's tagged
#: facts" -- is FALSE of a figure that IS one of those tagged facts.
ORIGIN_CONTRAST: dict[str, str] = {
    ORIGIN: ("That is a weaker provenance than the SEC path's tagged facts "
             "and a different one from the vendor path's quote summary, "
             "which is why the origin is stated on every line rather than "
             "assumed."),
    ORIGIN_XLSX: ("That is a weaker provenance than the SEC path's tagged "
                  "facts and a different one from the vendor path's quote "
                  "summary, which is why the origin is stated on every line "
                  "rather than assumed."),
    ORIGIN_XBRL: ("That is the SEC path's own tagged facts, written into "
                  "this schema so section 5 reads them through the same "
                  "validation, the same E21 gate and the same basis "
                  "machinery every other name gets -- not a shortcut past "
                  "any of them. The origin is stated on every line rather "
                  "than assumed."),
}

#: A figure is VERIFIED once it has been read back against the page named
#: beside it. UNVERIFIED is the state a figure is entered in, and it is
#: what section 5 refuses on. It is NOT the same state as absent: an
#: unverified figure is a number somebody entered, and the report names
#: it, its period and its page, so there is something to go and check.
STATUS_VERIFIED = "VERIFIED"
STATUS_UNVERIFIED = "UNVERIFIED"
VALID_FIGURE_STATUSES = (STATUS_UNVERIFIED, STATUS_VERIFIED)
#: E85: a leg the reader searched a WHOLE report for and did not find. Not
#: a figure and not a zero: it enters the bridge at nil, and the search --
#: document, scope, date -- is what the record carries. Never set by the
#: `status:` key; the `not_presented:` block produces it.
STATUS_NOT_PRESENTED = "NOT PRESENTED"

#: E40: WHAT A VERIFIED FLAG STANDS ON, in three kinds. `tagged` is
#: verification BY PROVENANCE -- tag + accession + filing date, the XBRL
#: path's own page line, regenerable by the same path. `cross_document` is
#: a read-back against a SECOND document. `same_page` is a read-back
#: against the page the figure was entered from -- the weakest claim, and
#: the one every flag set before E40 was, so it is what a VERIFIED figure
#: that names no kind is read as. The gate accepts all three; the report
#: prints the kind beside every figure.
KIND_TAGGED = "tagged"
KIND_CROSS_DOCUMENT = "cross_document"
KIND_SAME_PAGE = "same_page"
#: E78 (2026-08-30): a ZERO that stands on the issuer's own sentence -- "no
#: interest-bearing debt", "defined contribution only" -- quoted verbatim on
#: the figure's `statement:`. An absence is stated once, in one place, and
#: has no roll-forward or component sum to reconcile against, so E40's
#: second read is a standard nothing can meet; this kind settles that a
#: stated nothing is not a number. Accepted ONLY on a zero carrying E25's
#: `caption` or `note` form, and only with the sentence.
KIND_CAPTION_STATEMENT = "caption_statement"
VERIFIED_KINDS = (KIND_TAGGED, KIND_CROSS_DOCUMENT, KIND_SAME_PAGE,
                  KIND_CAPTION_STATEMENT)


class ManualError(ConfigError):
    """Any problem with a manual file. Always fatal to the command.

    A ConfigError, deliberately: a malformed hand-entered file is the
    same kind of failure as a malformed watchlist, and `vss` already
    exits 2 on those rather than skipping the entry and carrying on.
    """


# --- the schema -----------------------------------------------------------
#
# One entry per fiscal period, and one figure per line of the accounts.
# The field list is NOT a wish list. Every name below is read by code, or
# by a formula on the section 5 valuation sheet, and the `reads` column
# says which. Adding a line because it would be interesting to have is
# how a schema stops describing what the tool needs.


@dataclass(frozen=True)
class FieldSpec:
    name: str
    #: money    -- an amount in the reporting currency, one scale per file
    #: ratio    -- a FRACTION, never a percentage (SPEC.md section 2)
    #: per_share-- an amount per share
    #: count    -- a number of shares, in the file's own share unit
    #: multiple -- a multiple, e.g. 2.7x is 2.7
    kind: str
    #: What reads it. "rank" = the E6 ranking key; "5.1A/B/C", "5.3" =
    #: the section 5 chain; "check" = a validation check and nothing else;
    #: "measured" = a figure that is REPORTED AND DECIDES NOTHING (E123's
    #: debt to total capitalisation, in E7's and E63's shape). Nothing
    #: outside section 5 is read by it, and `startswith("5.")` is what
    #: keeps it out of the section 5 chain.
    reads: tuple[str, ...]
    note: str = ""
#: E26: a total the issuer presents in TWO CAPTIONS and never totals is
#: DATA MISSING, and both components are named in the file's comment. The
#: same reasoning as E23's refusal to add a split leg to a combined line:
#: adding two presented captions into one schema field is a sum no rule
#: authorises.
TOTAL_NOT_STATED = (
    "\nWHERE THE ISSUER PRESENTS THIS IN TWO CAPTIONS AND STATES NO TOTAL, "
    "THE FIELD IS THEIR SUM under E71 (2026-08-30) WHERE THE ISSUER ITSELF "
    "TREATS THEM AS ONE QUANTITY -- a note that presents them as one line, a "
    "reconciliation elsewhere in the filing, or a subtotal that includes "
    "both -- with every component and its page named on the field. Where "
    "that evidence is absent the field is DATA MISSING (E26) and both "
    "components are named in the file's comment. BETS-B.ST is the case: its "
    "balance sheet carries `Lease liabilities` twice, current and "
    "non-current -- 18.9 and 4.3 at 2026-06-30 -- and totals them nowhere, "
    "and its annual report's note 30 presents the one liability as a total, "
    "so the two are added (23.2). Where the issuer DOES state the total, as "
    "Pandora does in note 7, that stated total is the figure and the parts "
    "are memo.")

#: E22: a share count is the COUNT, stated. Written once and appended to
#: all three count fields -- one rule, three fields, and no chance of the
#: three drifting apart in prose.
STATED_COUNT_ONLY = (
    "\nA COUNT IS THE COUNT, AS STATED (E22). Share capital divided by a "
    "par value is NOT a count, and a treasury holding stated in money is "
    "NOT a count. Neither may be entered here, at any basis. Where the "
    "accounts state no count at the window's end, this field is DATA "
    "MISSING and stays so -- the error such a derivation makes is usually "
    "small, and a small error is still an error entering by a door the "
    "framework otherwise keeps shut.")



FIELDS: tuple[FieldSpec, ...] = (
    # --- read by the ranking key, through the store's own line names ----
    FieldSpec("revenue", "money", ("rank", "5.1B", "check"),
              "Total Revenue. The ranking key's share-class fingerprint "
              "matches on it; the unit check divides op_income by it."),
    FieldSpec("gross_profit", "money", ("rank",),
              "The E6 quality leg's numerator. An absent line is DATA "
              "MISSING -- a bank presents no such concept and that is not "
              "a zero."),
    FieldSpec("operating_income", "money", ("rank", "5.1B", "check"),
              "The operating profit AS THE STATEMENT PRESENTS IT. Enters "
              "the store as `Total Operating Income As Reported`, the top "
              "of the E6 alias chain, because a hand-read figure comes "
              "from the as-filed line by construction. EBITDA is NEVER a "
              "substitute (FRAMEWORK-EDITS E5)."),
    FieldSpec("total_assets", "money", ("rank",),
              "The E6 quality leg's denominator."),
    FieldSpec("income_before_taxes", "money", ("5.3",),
              "INCOME BEFORE INCOME TAXES as the statement prints it -- the "
              "line immediately above the tax charge. Read by ONE thing: "
              "E126 step 2, Gate 3's coverage numerator where the filer "
              "states no subtotal before financing cost. NVR: 'Income "
              "before taxes 1,761,932'; H&R Block, which has printed no "
              "operating subtotal since fiscal 2014.\n"
              "IT IS NOT A VALUATION LEG AND NOTHING IN SECTION 5 READS IT. "
              "E126 names the two lines its numerator may use -- this one "
              "and `finance_costs_period` -- and forbids every other "
              "reconstruction: not EBITDA (E5 stands), not gross profit "
              "less SG&A, not revenue less cost of sales, not segment "
              "subtotals summed, and not a note's interest INCURRED."),
    FieldSpec("captive_finance_debt", "money", ("measured",),
              "E124: the debt of a CAPTIVE FINANCE SUBSIDIARY, where the "
              "balance sheet presents it as its own caption beside the "
              "operating borrowings (PulteGroup: 'Financial Services debt "
              "532,338' beside 'Notes payable 1,631,098'). Read for ONE "
              "purpose and it DECIDES NOTHING: E123 prints debt to total "
              "capitalisation on TWO bases, with and without it, and the "
              "SPREAD between them is the information. It is NOT a leg of "
              "net debt and nothing in section 5 reads it.\n"
              "IT CANNOT BE REACHED BY TAG. PulteGroup's line is absent "
              "from the SEC companyfacts API under EVERY namespace "
              "(searched 2026-09-20, us-gaap, dei and srt, by exact value): "
              "the filer tags it with a custom element the API does not "
              "expose. So the figure comes FROM THE FILING or the second "
              "line reads DATA MISSING -- never omitted, because an omitted "
              "line and a zero look identical in a packet."),
    FieldSpec("total_equity", "money", ("measured",),
              "TOTAL EQUITY as the balance sheet presents it, including any "
              "non-controlling interest where the caption does. Read for ONE "
              "purpose and it DECIDES NOTHING: E123's measured figure, DEBT "
              "TO TOTAL CAPITALISATION, printed with no threshold attached "
              "where Gate 3's FCF and leverage limbs are DATA MISSING "
              "because the operating asset is inventory. It is NOT a leg of "
              "net debt, of the flow, or of any valuation: nothing in "
              "section 5 reads it. A STOCK -- the caption on one date, never "
              "summed across quarters."),
    FieldSpec("net_ppe", "money", ("rank",),
              "Net property, plant and equipment. Read for ONE purpose: "
              "one of the four figures the share-class fingerprint matches "
              "on. No leg of the key divides by it."),
    # --- section 5.1 C: the cash the reverse DCF discounts --------------
    FieldSpec("operating_cash_flow", "money", ("5.1C",),
              "Net cash from operating activities, AFTER tax. Where the "
              "statement presents it before tax (Unilever does), enter the "
              "pre-tax line and the tax paid instead and leave this blank."),
    FieldSpec("operating_cash_flow_pretax", "money", ("5.1C",),
              "Only for a statement that presents operating cash flow "
              "BEFORE income tax."),
    FieldSpec("income_tax_paid", "money", ("5.1C",),
              "As filed, an outflow, so negative. Pairs with "
              "operating_cash_flow_pretax."),
    FieldSpec("capex_ppe", "money", ("5.1C",),
              "Purchases of property, plant and equipment. Outflow, negative."),
    FieldSpec("capex_intangibles", "money", ("5.1C",),
              "Purchases of intangible assets. Outflow, negative."),
    FieldSpec("capex_combined", "money", ("5.1C",),
              "THE ONE LINE, where the issuer prints one (E23). Betsson's "
              "interims print `Investments in intangibles/tangibles` and never "
              "split it; its annual report does split it. Outflow, negative.\n"
              "A STATED FIGURE, NOT A SUM: this is the line as printed, and it "
              "is never entered by adding two figures together. WHERE THE "
              "ISSUER PRINTS THE SPLIT, LEAVE THIS BLANK -- section 5 reads "
              "`capex_ppe` + `capex_intangibles` whenever BOTH resolve at the "
              "basis, and this field only when they do not. Never both, and "
              "never one separate line added to this one."),
    FieldSpec("proceeds_from_disposals_ppe", "money", ("5.1C",),
              "Disposal proceeds, where the company's own FCF line nets "
              "them against capex."),
    FieldSpec("lease_payments_capital", "money", ("5.1C",),
              "Capital element of lease rentals, in FINANCING (IFRS 16.50(b); "
              "ASC 842 finance leases). E117 (2026-09-19): for an IFRS 16 "
              "filer FCF0 DEDUCTS it, with `lease_interest_paid` -- rent is "
              "an operating cost and the lease liability has left net debt. "
              "A US GAAP filer's finance lease principal is NOT deducted: "
              "finance leases stay in net debt (E117 clause 3)."),
    FieldSpec("lease_interest_paid", "money", ("5.1C",),
              "E117: the INTEREST paid on lease liabilities by an IFRS 16 "
              "filer, a POSITIVE MAGNITUDE. FCF0 deducts it beside "
              "`lease_payments_capital` whatever the filer's interest "
              "classification, so the total lease cash outflow is charged "
              "once. Where only IFRS 16.53(b)'s interest EXPENSE is stated, "
              "the page says so. Never read for a US GAAP filer."),
    FieldSpec("operating_lease_liabilities", "money", ("5.1C",),
              "E117: the OPERATING lease liability at the balance-sheet date "
              "(`us-gaap:OperatingLeaseLiability`), the part of "
              "`lease_liabilities` that LEAVES net debt because its rent is "
              "in the flow. What remains of `lease_liabilities` -- finance "
              "leases -- stays in (E117 clause 3). A US GAAP filer only: an "
              "IFRS 16 filer has one lessee model and its whole lease "
              "liability leaves net debt."),
    FieldSpec("operating_lease_payments", "money", ("5.1C",),
              "E70: the CASH PAID FOR OPERATING LEASES that a US GAAP "
              "filer's operating cash flow ALREADY BEARS (ASC 842-20-45-5(a); "
              "`us-gaap:OperatingLeasePayments`, 'cash paid for amounts "
              "included in the measurement of operating lease liabilities'). "
              "FCF0 ADDS IT BACK where `operating_leases_in_ocf: yes`, "
              "because the lease liability in net debt already charges the "
              "obligation; the interest inside the single lease payment "
              "follows the filer's interest rule (E34). A POSITIVE MAGNITUDE. "
              "Never read where `operating_leases_in_ocf: no` (IFRS 16: the "
              "principal is in financing and the flow never bore it)."),
    FieldSpec("net_interest_paid", "money", ("5.1C",),
              "INTEREST PAID LESS INTEREST RECEIVED, from the CASH FLOW "
              "statement -- what was paid, not what was charged.\n"
              "FCF BASIS 3 DEDUCTS IT ONLY WHERE THE FILER'S OPERATING CASH "
              "FLOW IS PRE-INTEREST. That precondition was missing from this "
              "note and its absence is an ERROR OF ARITHMETIC, not of "
              "wording: IAS 7.31-34 lets a filer put interest paid in "
              "operating OR in financing, and ASC 230 puts it in operating "
              "ALWAYS. Where it is inside operating cash flow the figure is "
              "ALREADY BORNE by `operating_cash_flow`, so deducting it here "
              "charges the same interest a second time and UNDERSTATES the "
              "company. Measured on Lindab's R12M to 2026-06-30 -- interest "
              "paid 211, received 10, both inside its operating cash flow "
              "(interim p.17) -- basis 3 takes the fair value from 102.66 to "
              "65.83 on the issuer's own free cash flow figure, and to 60.34 "
              "on the schema's basis 1. Nothing in the company changed.\n"
              "WHICH SIDE A FILER IS ON IS A FACT ABOUT ITS CASH FLOW "
              "STATEMENT and is recorded on the file, not guessed from the "
              "field. Where it is not recorded, basis 3 is unavailable: no "
              "ratio in this module forms it, and none may until the "
              "classification is on the page.\n"
              "Entered here only where the accounts print that net. Where "
              "they print the two sides separately, leave this blank and put "
              "them in `finance_costs_paid` and `finance_income_received`: "
              "THE STORE SUBTRACTS (FRAMEWORK-EDITS E18). It is NOT the same "
              "figure as `net_finance_costs`, which is the income "
              "statement's, and neither substitutes for the other."),
    FieldSpec("finance_costs_paid", "money", ("5.1C",),
              "Interest and other finance costs PAID, from the cash flow "
              "statement, as printed. One half of `net_interest_paid`."
              "\n"
              "SIGN: enter a POSITIVE MAGNITUDE. Statements print "
              "finance costs NEGATIVE -- Pandora's p.29 shows -325 -- "
              "and this file holds magnitudes, so a net is COSTS MINUS "
              "INCOME with both operands positive. A negative entered "
              "here inverts the net."),
    FieldSpec("finance_income_received", "money", ("5.1C",),
              "Finance income RECEIVED, from the cash flow statement, as "
              "printed. The other half. Where only one of the pair is "
              "available, that field and the net are DATA MISSING (E18)."
              "\n"
              "SIGN: enter a POSITIVE MAGNITUDE. Statements print "
              "finance costs NEGATIVE -- Pandora's p.29 shows -325 -- "
              "and this file holds magnitudes, so a net is COSTS MINUS "
              "INCOME with both operands positive. A negative entered "
              "here inverts the net."),
    FieldSpec("sbc", "money", ("5.1C",),
              "SHARE-BASED COMPENSATION FOR THE PERIOD, as the accounts "
              "state it. A POSITIVE MAGNITUDE: FCF0 SUBTRACTS it (E36).\n"
              "E36: it is a COST. Under both ASC 230 and IAS 7 an "
              "equity-settled award is a NON-CASH charge added back inside "
              "operating cash flow, so `operating_cash_flow` - capex "
              "contains it and every fair value struck before 2026-08-26 "
              "treated it as free. It is not free: it is a transfer of "
              "ownership from the holder to the employee, paid in the same "
              "currency as the thing being valued. Measured: NKE 715m = "
              "32.7% of FCF0, SAP's equity-settled 1,331m = 15.2%, DECK "
              "44.8m = 4.1%.\n"
              "EQUITY-SETTLED ONLY, where the accounts separate the two. A "
              "CASH-SETTLED award flows through operating cash flow as CASH "
              "when it is paid, so FCF0 already bears it and deducting it "
              "here would charge it twice -- SAP's FY2025 charge is 1,695 of "
              "which 364 is cash-settled, and deducting the headline gives "
              "134.82 against the 141.74 the equity-settled figure gives.\n"
              "NO OFFSET AGAINST THE DILUTED COUNT. A diluted count captures "
              "EXISTING grants and the basic-to-diluted gap is 0.2-0.4% for "
              "these names, against a charge worth 4-33% of FCF0. The "
              "deduction and the count are decided separately (E38)."),
    FieldSpec("free_cash_flow_reported", "money", ("reference",),
              "The company's OWN free cash flow line, as filed. Never "
              "derived here -- it is entered so the derived bases can be "
              "compared against the figure the company publishes.\n"
              "E101 (2026-09-01) is what finally compares them: it is "
              "construction-error DETECTOR 1, printed with every strike. "
              "The issuer's definition is usually NOT E34's, so a "
              "disagreement is NEVER a verdict that this project's figure "
              "is wrong -- it is a prompt to look."),
    FieldSpec("net_debt_reported", "money", ("reference",),
              "The company's OWN net debt line, as filed, POSITIVE for a "
              "net-debt company. Never derived here.\n"
              "E101 DETECTOR 2, and it exists because the hand version of "
              "it already worked: LIAB.ST's file compares the two in prose "
              "and that is what found the missing pension leg (E35.1, "
              "+6.3%). The issuer usually EXCLUDES the pension leg E35.1 "
              "includes, so a disagreement of a few per cent in that "
              "direction is expected and is not a fault -- which is "
              "precisely why nothing is adjusted on it."),
    # --- section 5.1 C: net debt, the bridge from EV to equity ----------
    FieldSpec("cash_and_equivalents", "money", ("5.1C",), "Balance sheet."),
    FieldSpec("other_current_financial_assets", "money", ("5.1C",),
              "Assumption A1 decides whether these count as cash."),
    FieldSpec("financial_liabilities_current", "money", ("5.1C",),
              "Balance sheet, and EXCLUDING LEASE LIABILITIES "
              "(FRAMEWORK-EDITS E14). Borrowings alone. Where the balance "
              "sheet presents one consolidated `Loans and borrowings` line "
              "-- which under IFRS 16 CONTAINS the leases -- that figure is "
              "NOT this field: take the split from the notes. The three "
              "fields are ADDITIVE: this + the non-current one + "
              "lease_liabilities is the consolidated line."),
    FieldSpec("financial_liabilities_noncurrent", "money", ("5.1C",),
              "Balance sheet, and EXCLUDING LEASE LIABILITIES "
              "(FRAMEWORK-EDITS E14). Borrowings alone, on the same terms as "
              "the current field above, and additive with it and with "
              "lease_liabilities."),
    FieldSpec("lease_liabilities", "money", ("5.1C",),
              "The LEASE PORTION, held apart from the two borrowing fields "
              "and ADDITIVE with them (FRAMEWORK-EDITS E14): the three sum to "
              "the consolidated `Loans and borrowings` line an IFRS 16 "
              "balance sheet presents. Assumption A2 -- do lease liabilities "
              "count as debt -- can only be thrown because they are kept "
              "apart here.\n"
              "WHERE THE ISSUER SPLITS IT NOWHERE IN THE FILING, ALL THREE "
              "FIELDS ARE DATA MISSING: never the consolidated figure in the "
              "borrowing fields, and never zero here. A2 is then untestable "
              "for that name, which is a fact about the disclosure and not a "
              "value to estimate.\n"
              "E73 (2026-08-30): where a filer DISCLOSES finance leases but "
              "sizes them nowhere in the filing, the finance component of "
              "this field is a NAMED ZERO -- `zero_basis: caption` for the "
              "component, the disclosure quoted on the field -- beside the "
              "operating total (GoDaddy, Note 2), in E68.2's form. The "
              "weaker component governs the figure's verification kind."
              + TOTAL_NOT_STATED),
    FieldSpec("pension_deficit", "money", ("5.1C",),
              "E35.1: THE PROVISION FOR PENSIONS AND SIMILAR OBLIGATIONS as "
              "the balance sheet presents it -- the recognised net "
              "defined-benefit LIABILITY (Lindab 'Provisions for pensions "
              "and similar obligations' 280 at 2026-06-30; SAP "
              "`RecognisedLiabilitiesDefinedBenefitPlan` 249). A LEG OF NET "
              "DEBT, added to the borrowings and the leases. A separately "
              "presented pension ASSET is NOT netted here: no field holds "
              "it, and omitting an asset is the conservative direction. "
              "ABSENT IS DATA MISSING for net debt, on the lease leg's terms; "
              "a filer with no defined-benefit plan states so, and the "
              "sentence is the evidence (E25 `note`).\n"
              "E74 (2026-08-30): a CURRENT PORTION the note discloses inside "
              "another caption -- accrued payroll, other current "
              "liabilities -- is NAMED on this field, with the caption that "
              "holds it, and NOT added: it already sits inside a line the "
              "bridge reads or deliberately excludes, and adding it would "
              "double-count against the balance sheet's own arithmetic "
              "(Accenture: 75,030 thousand inside 'Accrued payroll and "
              "related benefits')."),
    FieldSpec("asset_retirement_obligation", "money", ("5.1C",),
              "E68 (2026-08-29): THE ASSET RETIREMENT / DECOMMISSIONING "
              "OBLIGATION as the balance sheet presents it -- a legally "
              "required, discounted, cash-settled future outflow, DEBT IN "
              "SUBSTANCE and A LEG OF NET DEBT beside the borrowings, the "
              "leases and the pension deficit (Expand Energy "
              "`AssetRetirementObligation` 724m at 2025-12-31, 14.5% of its "
              "borrowings). The stated total, or two stated parts added with "
              "both named; a lone non-current part is not the obligation. "
              "ABSENT IS DATA MISSING for net debt, on the pension leg's "
              "terms. E68.1: where the balance sheet presents NO such "
              "provision and the business owns nothing requiring "
              "decommissioning, the leg is ZERO with `zero_basis: caption`, "
              "the page naming the balance sheet and the provisions or "
              "other-liabilities note read; extractive, utility, mining, "
              "shipping, chemical and heavy-industrial filers get no such "
              "zero -- DATA MISSING until the figure is read from the "
              "filing (E69). A provision present inside a note (Autotrader's "
              "dilapidations, 3.7) is a stated figure, entered under E69. "
              "E68.2: where the read has happened and the filer discloses a "
              "remediation or similar obligation WITHOUT a balance-sheet "
              "amount -- the liability inside a caption with room -- the "
              "leg is ZERO with `zero_basis: caption` and the disclosure is "
              "NAMED on the field (Lennox: Note 5, unquantified; 10.9m "
              "charged in 2025), so the omission is visible, not silent."),
    FieldSpec("prepaid_delivery_obligation", "money", ("5.1C",),
              "E81 (2026-08-30): A PREPAID DELIVERY OBLIGATION as the balance "
              "sheet presents it -- cash the issuer has RECEIVED IN ADVANCE "
              "against a future obligation to deliver product: a streaming "
              "agreement, a prepaid offtake, a metals stream (Lundin Gold's "
              "silver stream obligation, 690,345 US$k at 2026-06-30: current "
              "26,355 + non-current 663,990). The company has the money and "
              "must perform; that it is settled in metal rather than currency "
              "does not make it less of a claim. A LEG OF NET DEBT beside the "
              "borrowings, the leases, the pension deficit and the asset "
              "retirement obligation, on E68's reasoning: an obligation that "
              "is not optional, is measured, and is material. The stated "
              "total, or two stated parts added with both named. DATA MISSING "
              "where the issuer carries such an arrangement and states no "
              "balance; a CAPTION ZERO (`zero_basis: caption`, the balance "
              "sheet read named) where no such arrangement exists. NOT this "
              "leg: the ordinary contract liabilities of a subscription or "
              "services business, customer deposits, billings in advance -- "
              "working capital the flow already carries -- which are NAMED on "
              "the zero where they exist, so the reading is visible."),
    FieldSpec("noncurrent_derivative_assets_on_debt", "money", ("5.1C",),
              "Only where the company's own net-debt reconciliation "
              "includes it."),
    # --- share counts: the divisor on every per-share figure ------------
    FieldSpec("diluted_weighted_average_shares", "count", ("5.1A", "5.1C"),
              "The divisor where it is stated FOR THE WINDOW (E38). E88 "
              "(2026-08-30, reversing E75): on a TTM basis stitched from "
              "interims that state no twelve-month average, the divisor is "
              "the MOST RECENT ANNUAL weighted-average diluted count under "
              "E41's annual-only rule, declared on its own date with the "
              "basis mismatch flagged; a count at the window end stays MEMO "
              "and is never promoted. A6's choice is settled by that order."),
    FieldSpec("shares_outstanding_period_end", "count", ("5.1A", "5.1C"),
              "THE NET COUNT, AS PRINTED. Net of treasury shares, and entered "
              "here only where the accounts print that number.\n"
              "WHERE THEY PRINT ONLY ISSUED AND TREASURY SEPARATELY -- which "
              "is common, and is Pandora's note 4.1 -- leave this blank: put "
              "the two in `shares_issued_period_end` and "
              "`treasury_shares_period_end`, and THE STORE COMPUTES THE NET "
              "(FRAMEWORK-EDITS E16; E80, 2026-08-30, confirms this against "
              "E22: both figures are stated and only the subtraction is ours, "
              "and an employee trust the issuer excludes from its own EPS "
              "count comes out too, E54). An issued count entered here would "
              "be wrong against this field's own definition, by the whole of "
              "the treasury holding.\n"
              "E75 (2026-08-30) briefly made this count the divisor on a "
              "TTM basis; E88 (2026-08-30) REVERSED that the same day: it "
              "stays MEMO, never promoted -- the divisor falls back to "
              "E41's annual average, and the why names this count beside it."
              + STATED_COUNT_ONLY),
    FieldSpec("shares_diluted_period_end", "count", ("5.1A", "5.1C"),
              "THE DILUTED COUNT THE ISSUER STATES AT A PERIOD END, as "
              "printed -- a stock (E75.1, 2026-08-30). E88 (2026-08-30) "
              "reversed E75 / E75.1 the same day: no period-end count is a "
              "divisor any more; this one stays MEMO beside E41's annual "
              "average. Entered only where the accounts PRINT a diluted "
              "count at the date -- a basic count plus the warrants "
              "outstanding is a sum the accounts do not print as a count "
              "(E22)." + STATED_COUNT_ONLY),
    FieldSpec("shares_issued_period_end", "count", ("5.1A", "5.1C"),
              "Shares ISSUED at the period end, INCLUDING treasury shares. "
              "Entered only as one half of a pair: it is not a net count and "
              "must never stand in for one. Where the accounts print the net "
              "directly, this stays DATA MISSING and the net goes in "
              "`shares_outstanding_period_end` (E22); where they print only "
              "the pair, both halves are entered and the store subtracts "
              "(E16, E80)." + STATED_COUNT_ONLY),
    FieldSpec("treasury_shares_period_end", "count", ("5.1A", "5.1C"),
              "Shares held in TREASURY at the period end, as printed. The "
              "other half of the pair.\n"
              "WHERE ONLY ONE OF THE TWO IS AVAILABLE, ALL THREE SHARE-COUNT "
              "FIELDS ARE DATA MISSING (E16): an issued count alone is not a "
              "net count, and nothing here estimates the other half."
              + STATED_COUNT_ONLY),
    FieldSpec("employee_trust_shares_period_end", "count", ("5.1A", "5.1C"),
              "Shares held by an EMPLOYEE BENEFIT TRUST at the period end -- "
              "an ESOT, ESOP or equivalent -- where the issuer excludes them "
              "from its OWN earnings-per-share count alongside treasury "
              "(FRAMEWORK-EDITS E54, first application AUTO.L note 11: basic "
              "EPS uses shares 'excluding those held in treasury and by the "
              "Employee Share Option Trust'). Autotrader prints both counts "
              "separately -- AR p.125 notes 25 and 26 -- and folding this "
              "figure into `treasury_shares_period_end` would enter it under "
              "a field whose own definition it does not meet.\n"
              "OPTIONAL, AND UNLIKE THE ISSUED/TREASURY PAIR: most issuers "
              "carry no employee trust at all, and its absence never blocks "
              "`shares_outstanding_period_end` -- the store still subtracts "
              "issued minus treasury without it. Present, it subtracts a "
              "THIRD leg from the same net; absent, the net is issued minus "
              "treasury alone, exactly as E16 already had it." + STATED_COUNT_ONLY),
    # --- section 5.1 A and 5.3: earnings, and the leverage that sets tier
    FieldSpec("shares_point_in_time", "count", ("memo",),
              "A MEMO, NEVER THE DIVISOR (E38). The count STATED on one "
              "day: a filer's cover page, or its balance sheet at a period "
              "end. It IS 'the count itself' under E22 -- it is stated, it "
              "has an accession behind it, and it is what tells a reader "
              "that 3,253,000 shares were bought back in a quarter -- and "
              "section 5 does not divide by it.\n"
              "WHY NOT. It is a STOCK and the flow it would divide is a "
              "WINDOW. DECK's 140.95 divided a flow window ending "
              "2026-06-30 and a balance sheet at 2026-06-30 by a count "
              "stated as of 2026-07-09: nine days of buybacks in the "
              "divisor and not in the cash. The reverse choice is worse "
              "the other way -- for any filer that repurchases, the "
              "weighted average sits ABOVE the period-end count by "
              "construction, so dividing by the period-end count would "
              "systematically FLATTER every name that buys back stock.\n"
              "ITS DATE IS ON ITS PAGE REFERENCE, as `[as of YYYY-MM-DD]`, "
              "because a stock without a date is not a fact." + STATED_COUNT_ONLY),
    FieldSpec("diluted_eps", "per_share", ("5.1A",),
              "As filed. The A7 trailing-P/E proxy (FRAMEWORK-EDITS B5) is "
              "built from five years of this line."),
    FieldSpec("diluted_eps_adjusted", "per_share", ("5.1A",),
              "MEMO, non-GAAP. Consensus is usually struck on this basis; "
              "recording it is what makes the A7/A8 basis mismatch visible."),
    FieldSpec("operating_income_adjusted", "money", ("5.1B",),
              "MEMO, non-GAAP. Most peer EV/EBIT screens are on this basis "
              "-- Method B has to say which it used."),
    FieldSpec("nci_dividends_paid", "money", ("5.1C",),
              "E105 (2026-09-04): DIVIDENDS PAID TO NON-CONTROLLING "
              "INTERESTS over the window, as the cash flow statement states "
              "them. An OUTFLOW, NEGATIVE, the sign capex is entered in, "
              "and section 5 SUMS it into the flow.\n"
              "It is a leg of FCF0 and not a bridge item: that cash leaves "
              "the group and can never reach the owner, and E105 declines "
              "the liability treatment because valuing the minority would "
              "be a second unaudited lever beside the growth view (E29's "
              "ground).\n"
              "A group with NO minorities states a NAMED ZERO -- "
              "`zero_basis: note` where a sentence says there are none, "
              "`caption` where the cash flow statement lists the line and "
              "shows nil. AN ABSENT FIELD IS DATA MISSING AND SECTION 5 "
              "DOES NOT RUN: a coerced zero would report the record "
              "complete while overstating the flow by the whole of a "
              "group's distributions to its minorities. Found by E101 on "
              "IMB.L at GBP 156m, 4.9% of FCF0."),
    FieldSpec("net_income", "money", ("5.1C",),
              "The denominator of the FCF conversion figure section 4.3 "
              "reads as a green flag."),
    FieldSpec("ebitda", "money", ("5.3",),
              "The leverage denominator. Enter the one the company's own "
              "covenant and guidance use, and say so on the page reference."),
    FieldSpec("depreciation_amortisation", "money", ("5.3",),
              "Only to reconcile a stated EBITDA against operating income. "
              "Nothing here derives one from the other.\n"
              "E82 (2026-08-30): where the only printed line COMBINES "
              "depreciation and amortisation with impairment, this field is "
              "DATA MISSING -- entered as `value: null` with the combined "
              "line and its amount on the `page:` (a NAMED ABSENCE the "
              "report prints) -- because a one-off write-down inside a "
              "recurring charge makes a bad year look like a high-cost year. "
              "Where the notes state the charges apart from the impairments, "
              "their sum is an E69 hand read, every part named (Reckitt "
              "2025: 143 + 356 = 499 against a cash-flow line of 756)."),
    FieldSpec("rou_depreciation", "money", ("5.3",),
              "E117 clause 5 (2026-09-19): DEPRECIATION OF RIGHT-OF-USE ASSETS "
              "for the period (IFRS 16.53(a)), a POSITIVE MAGNITUDE. An IFRS 16 "
              "filer's operating income is after it and before rent; Gate 3's "
              "rent-bearing coverage adds it back and deducts the lease cash. "
              "Never read for a US GAAP filer, whose operating income bears the "
              "rent already."),
    FieldSpec("net_finance_costs", "money", ("5.3",),
              "THE INCOME STATEMENT'S FINANCE COSTS LESS FINANCE INCOME -- "
              "what was CHARGED for the period, not what was paid. Gate 3's "
              "interest-coverage limb reads it.\n"
              "Entered here only where the accounts print that net. Where "
              "they print the two sides separately -- which is usual, and is "
              "Pandora's p.100 -- leave this blank and put them in "
              "`finance_costs_period` and `finance_income_period`: THE STORE "
              "SUBTRACTS (FRAMEWORK-EDITS E18). It is NOT the same figure as "
              "`net_interest_paid`, which comes off the cash flow, and "
              "neither substitutes for the other."),
    FieldSpec("finance_costs_period", "money", ("5.3",),
              "Finance costs CHARGED for the period, from the income "
              "statement, as printed. One half of `net_finance_costs`."
              "\n"
              "SIGN: enter a POSITIVE MAGNITUDE. Statements print "
              "finance costs NEGATIVE -- Pandora's p.29 shows -325 -- "
              "and this file holds magnitudes, so a net is COSTS MINUS "
              "INCOME with both operands positive. A negative entered "
              "here inverts the net."),
    FieldSpec("finance_income_period", "money", ("5.3",),
              "Finance income EARNED in the period, from the income "
              "statement, as printed. The other half. Where only one of the "
              "pair is available, that field and the net are DATA MISSING."
              "\n"
              "SIGN: enter a POSITIVE MAGNITUDE. Statements print "
              "finance costs NEGATIVE -- Pandora's p.29 shows -325 -- "
              "and this file holds magnitudes, so a net is COSTS MINUS "
              "INCOME with both operands positive. A negative entered "
              "here inverts the net."),
    FieldSpec("net_debt_ebitda", "multiple", ("5.3",),
              "As the company states it. Section 5.3's tier test turns on "
              "it -- 2.3x sent UNA.AS to tier 2."),
    # --- ratios: entered so the arithmetic can be checked ---------------
    FieldSpec("op_margin", "ratio", ("check",),
              "A FRACTION. Entered for ONE reason: it is what reconciles "
              "operating_income against revenue and so says which line the "
              "operating income was read from. Leave it blank only by "
              "leaving operating_income blank too."),
    FieldSpec("revenue_yoy", "ratio", ("check",),
              "A FRACTION, as the report states it."),
)

FIELDS_BY_NAME: dict[str, FieldSpec] = {f.name: f for f in FIELDS}
FIGURE_KEYS: frozenset[str] = frozenset(FIELDS_BY_NAME)

#: Manual field -> the line name the store already knows it by. Only these
#: five reach `ranking.py`, and they MUST carry the store's own spelling:
#: `choose_ebit` reads `Total Operating Income As Reported` and the
#: denominator `Total Assets`, and a parallel vocabulary would return None
#: for every manual name with no error raised anywhere. `Gross Profit` is
#: still written to the record (E43 retired it from the key, not from the
#: store), so an old run stays readable.
STORE_LINES: dict[str, tuple[str, str]] = {
    "revenue": ("Total Revenue", "income"),
    "gross_profit": ("Gross Profit", "income"),
    "operating_income": ("Total Operating Income As Reported", "income"),
    "total_assets": ("Total Assets", "balance"),
    "net_ppe": ("Net PPE", "balance"),
}

#: Market facts. Not from the accounts and not per period: they are priced
#: on a date. The ranking key reads both -- `enterpriseValue` as the
#: earnings yield's denominator, `marketCap` as the bound that decides
#: whether the enterprise value is arithmetically possible at all (L2).
MARKET_FIELDS: dict[str, str] = {
    "enterprise_value": "enterpriseValue",
    "market_cap": "marketCap",
}

#: Header fields the store reads as text.
TEXT_FIELDS: dict[str, str] = {
    "reporting_currency": "financialCurrency",
    "quote_currency": "currency",
    "sector": "sector",
}

ALLOWED_TOP_KEYS = frozenset({
    "ticker", "name", "reporting_currency", "quote_currency", "sector",
    "reporting_frequency", "origin", "market", "periods", "annual",
    "interest_in_ocf", "money_unit", "share_unit", "cik",
    # E70 (2026-08-30): what the operating cash flow bears of the LEASE.
    "operating_leases_in_ocf",
    # E123 (2026-09-20): whether the OPERATING ASSET IS INVENTORY and its
    # purchase runs through operating cash flow. Where it is, Gate 3's FCF
    # and leverage limbs are DATA MISSING and section 4.4 rebases.
    "operating_asset_is_inventory",
})

#: THE UNIT A FILE'S FIGURES ARE STATED IN, declared once per file.
#: `money_unit` is the scale of every money figure -- ONE UNIT PER FILE, as
#: the template has always said -- and `share_unit` is the scale of every
#: share COUNT. They are DECLARED, never inferred: a file in SEK millions
#: beside a count printed as "77,036 thousand" is the same file whether the
#: count was typed as 77.036 or 77,036,000, and only the declaration tells
#: a divisor which. `runrecord.from_store` read both raw and divided, and a
#: millions-scale file with a whole-number count (PNDORA.CO, SYNSAM.ST)
#: came out a millionfold too small per share. The run record now reads
#: both declarations, NORMALISES TO WHOLE UNITS before dividing, and is
#: DATA MISSING where either is unstated. Nothing in the file is rescaled
#: by the declaration -- every figure stays as the source states it.
UNIT_SCALE: dict[str, float] = {
    "whole": 1.0, "thousands": 1e3, "millions": 1e6, "billions": 1e9,
}
VALID_UNITS: tuple[str, ...] = tuple(UNIT_SCALE)

#: E34's block. `value` is yes|no; `source` and `page` say where on the CASH
#: FLOW STATEMENT it was read, because the classification is a fact about
#: the filer and a fact needs a page like every other figure in this schema.
#: `interest_source` is E34.1's: which STATEMENT supplies the net a `yes`
#: filer adds back. Absent means the cash flow statement, E34 as written.
ALLOWED_INTEREST_KEYS = frozenset({"value", "source", "page", "interest_source"})

#: E34.1. A US filer states interest PAID as a cash figure and never interest
#: RECEIVED, so E18's cash pair cannot form; the add-back is then the INCOME
#: STATEMENT'S net -- `net_finance_costs`, "Interest expense (income), net"
#: -- and it is printed as an ACCRUAL PROXY beside FCF0. Interest paid alone
#: is never the net: on Nike FY2026 that would add back 323m against a true
#: net of -50m, which is an INCOME and is removed rather than added.
INTEREST_SOURCE_CASH_FLOW = "cash_flow_statement"
INTEREST_SOURCE_INCOME_STATEMENT = "income_statement_net"
#: E61, amending E34.1. Some US filers tag GROSS interest expense
#: (`InterestExpenseNonoperating`, the schema's `finance_costs_period`) but
#: never the NET (`InterestIncomeExpenseNonoperatingNet`) at all -- CTSH
#: tags the gross every year and the net in none. Interest income is never
#: negative, so the gross figure is always >= the true net, and adding it
#: back can only OVERSTATE FCF0, by no more than the unrecorded interest
#: income -- a bounded, one-sided error, not a guess. Unlike E34.1's net
#: this leg is UNSIGNED and always ADDED.
INTEREST_SOURCE_INTEREST_EXPENSE_ONLY = "interest_expense_only"
#: E115, the fourth shape. A filer states INTEREST PAID as a cash figure,
#: states NO interest received, and does not state the income statement's
#: net either -- so E34's pair, E34.1's accrual net and E61's tagged gross
#: expense all fail to form. HRB FY2026: interest paid 76,728,000 on the
#: cash-flow statement, no interest-income line anywhere in the 10-K and no
#: interest-income element tagged, its gross expense filed under
#: `InterestExpenseDebt` which this schema's `finance_costs_period` does not
#: read. The add-back is then INTEREST PAID ALONE, and the collision is
#: named rather than hidden: E34.1 says interest paid alone is never the
#: net, and it is not the net here either. It is a ONE-SIDED PROXY of the
#: same class as E61's -- interest income is never negative, so the figure
#: is >= the true net and FCF0 is overstated by the unstated income, never
#: understated. UNSIGNED and always ADDED, as E61's leg is.
INTEREST_SOURCE_CASH_PAID_ONLY = "cash_paid_only"
VALID_INTEREST_SOURCES = (INTEREST_SOURCE_CASH_FLOW,
                          INTEREST_SOURCE_INCOME_STATEMENT,
                          INTEREST_SOURCE_INTEREST_EXPENSE_ONLY,
                          INTEREST_SOURCE_CASH_PAID_ONLY)
ACCRUAL_PROXY_LABEL = "accrual proxy (E34.1): net interest from the income statement"
#: E61. The bound percentage is appended by whatever prints FCF0 -- it
#: needs FCF0 itself, which this module does not compute.
INTEREST_EXPENSE_ONLY_LABEL = ("proxy (E61 / E61.1): interest income not tagged, "
                               "or not stated anywhere in the filing; add-back "
                               "overstated by the unrecorded income")
#: E115. Same one-sided class as E61's, off the CASH figure rather than the
#: accrual one; whatever prints FCF0 appends the bound as a percentage.
CASH_PAID_ONLY_LABEL = ("proxy (E115): interest PAID alone -- no interest "
                        "received stated, no income-statement net, no tagged "
                        "gross expense; NOT the net (E34.1), and FCF0 is "
                        "overstated by the unstated interest income")
#: An `annual:` entry (FRAMEWORK-EDITS E15). Same shape as a period entry,
#: keyed on the FISCAL YEAR rather than on a period label -- deliberately,
#: because a label is what the overlap guard reasons about and an annual
#: entry must never enter that reasoning.
ALLOWED_ANNUAL_KEYS = frozenset({"fiscal_year", "period_end", "document",
                                 "url", "figures"})
#: Only the identity. The EMPTY TEMPLATE is a valid file -- it loads,
#: supplies nothing and refuses section 5 for having no periods -- and
#: demanding a currency and a sector of a file with no figures in it
#: would mean writing three placeholder strings into the committed
#: template. The currency becomes required the moment a figure carries a
#: value, which is the point at which not knowing it would matter.
REQUIRED_TOP_KEYS = frozenset({"ticker", "name"})
ALLOWED_PERIOD_KEYS = frozenset({"period", "period_end", "period_basis",
                                 "document", "url", "figures"})
ALLOWED_FIGURE_KEYS = frozenset({"value", "source", "page", "status",
                                 "zero_basis", "verified_kind",
                                 # E78: the issuer's sentence, verbatim.
                                 "statement",
                                 # E79.1 / E83: on `op_margin` only -- the
                                 # printed precision in percentage points,
                                 # and the accounts' explanation of a margin
                                 # outside the plausible band.
                                 "precision", "cause",
                                 # E85: the recorded search behind a leg
                                 # that is NOT PRESENTED.
                                 "not_presented",
                                 # E86: a cumulative year-to-date column
                                 # and its prior, each with a page.
                                 "cumulative", "cumulative_prior",
                                 "cumulative_prior_page",
                                 # E106 clause 3: a leg that is ABSENT but
                                 # BOUNDED. `bound` is a MAGNITUDE, and
                                 # `bound_direction` says which way the
                                 # unknown can move the answer.
                                 "bound", "bound_direction",
                                 # E120 (2026-09-19): an annual lease
                                 # interest standing in for a TTM window.
                                 "stand_in"})

#: E106: which way an undetermined leg can move `fv_base` from where it is
#: struck. A leg struck at ZERO whose true value is a DEDUCTION can only
#: lower it (`reduces` -- E105's shape); one whose true value is an
#: ADD-BACK can only raise it (`raises` -- E70's shape). `either` is for a
#: leg whose sign is itself unknown.
#:
#: **WHY THE DIRECTION IS RECORDED AND NOT ASSUMED.** E106 clause 1 says a
#: leg must not move `fv_base` "on ANY PLAUSIBLE VALUE", and the plausible
#: values of an add-back leg struck at zero are all ABOVE it. Perturbing it
#: downward -- which is what a single hard-coded direction did -- measures a
#: move that cannot happen and misses the one that can.
BOUND_REDUCES = "reduces"
BOUND_RAISES = "raises"
BOUND_EITHER = "either"
VALID_BOUND_DIRECTIONS = (BOUND_REDUCES, BOUND_RAISES, BOUND_EITHER)

#: E25: the three forms of evidence a ZERO may rest on. A zero is a CLAIM
#: ABOUT THE COMPANY and needs one of them; absence in a search is a fact
#: about the search, not about the issuer.
ZERO_CAPTION = "caption"      # the issuer lists the line and shows nil or a dash
ZERO_NOTE = "note"            # a sentence states there is none, cited to its page
ZERO_SUBTOTAL = "subtotal"    # the components shown sum to the subtotal shown
#: E107 (2026-09-04): a RECORDED SEARCH of a NAMED DOCUMENT for a NAMED
#: CONCEPT, finding it absent. E85's NOT PRESENTED evidence form, applied
#: to a field where it was missing -- caption, note and subtotal all need
#: the issuer to have SAID something, so a filing simply SILENT about a
#: concept could not be recorded at all, and E106 clause 5 turns on that
#: silence. Carries E85's three requirements, enforced at the load.
ZERO_SEARCHED = "searched"
VALID_ZERO_BASES = (ZERO_CAPTION, ZERO_NOTE, ZERO_SUBTOTAL, ZERO_SEARCHED)

#: E25: the fields where a WRONG zero carries a name through a gate it
#: should fail. Each improves a ratio: understated net debt, an interest
#: coverage struck on nothing, free cash flow with no capital spending in
#: it. A zero here must name its evidence.
#:
#: THE RULING SAYS "nine fields" AND LISTS TEN. The list governs; the count
#: is recorded as given and corrected here rather than silently.
ZERO_NEEDS_BASIS: frozenset[str] = frozenset({
    "financial_liabilities_current", "financial_liabilities_noncurrent",
    "lease_liabilities", "finance_costs_period", "net_finance_costs",
    "capex_ppe", "capex_intangibles", "capex_combined",
    "lease_payments_capital", "net_interest_paid",
    # E117 (2026-09-19): a wrong zero overstates the flow or net debt.
    "lease_interest_paid", "operating_lease_liabilities", "rou_depreciation",
    # E35.1 (2026-08-26): a wrong zero here understates net debt.
    "pension_deficit",
    # E68 (2026-08-29): the same shape, the same direction.
    "asset_retirement_obligation",
    # E81 (2026-08-30): a prepaid delivery obligation is net debt; a wrong
    # zero here understates it by the whole stream.
    "prepaid_delivery_obligation",
    # E105 (2026-09-04): THE RULING ASKS FOR THIS IN ITS OWN WORDS --
    # "a company with no non-controlling interests states so, and the leg
    # is ZERO on E25's note or caption basis, with the evidence cited --
    # never an inferred zero". A wrong zero here raises FCF0 by the whole
    # of a group's distributions to its minorities, which is the same
    # shape and the same direction as a wrong zero on capex.
    "nci_dividends_paid",
    # E36 (added 2026-08-26): a wrong ZERO here says stock is free and
    # raises FCF0 by the whole charge -- the same shape as a wrong zero on
    # capex. A filer that grants no stock states so, and the sentence is
    # the evidence (Lindab AR 2025 p.96 and p.112).
    "sbc",
})

#: E25: fields where a zero is refused OUTRIGHT, evidence or not, because
#: it would assert something about the company the accounts never say.
#: Three groups, one rule:
#:   * THE COUNTS (E22) -- a listed company has shares.
#:   * CONCEPT NOT PRESENTED -- gross_profit for a bank,
#:     other_current_financial_assets for Pandora, operating_cash_flow_pretax
#:     for Betsson. The issuer's FORMAT is not the issuer's AMOUNT.
#:   * NON-GAAP MEMOS -- a zero would claim the issuer reported zero, which
#:     is a different and false statement from publishing no such measure.
ZERO_REFUSED: dict[str, str] = {
    "diluted_weighted_average_shares": "a count (E22): a listed company has shares",
    "shares_outstanding_period_end": "a count (E22): a listed company has shares",
    "shares_issued_period_end": "a count (E22): a listed company has shares",
    "shares_diluted_period_end": "a count (E22): a listed company has shares",
    "treasury_shares_period_end": "a count (E22)",
    "employee_trust_shares_period_end": "a count (E22)",
    "gross_profit": "absence means the concept is NOT PRESENTED -- a bank and a "
                    "property company print none by design (E6)",
    "other_current_financial_assets": "absence means the concept is NOT "
                                      "PRESENTED -- Pandora's balance sheet has "
                                      "no such caption",
    "operating_cash_flow_pretax": "absence means the statement is NOT LAID OUT "
                                  "that way -- Betsson's subtotal sits after "
                                  "taxes paid",
    "diluted_eps_adjusted": "a non-GAAP MEMO: zero would claim the issuer "
                            "reported zero, not that it published none",
    "operating_income_adjusted": "a non-GAAP MEMO: zero would claim the issuer "
                                 "reported zero, not that it published none",
    "free_cash_flow_reported": "a non-GAAP MEMO: zero would claim the issuer "
                               "reported zero, not that it published none",
}

#: E25: the denominator interest coverage is struck on. EBIT / 0 is not a
#: large number -- it is undefined, and any code that reads it as "very
#: large" passes Gate 3 silently. That is the failure mode E19 was ruled to
#: remove, in a different place.
COVERAGE_DENOMINATOR = "net_finance_costs"
ALLOWED_MARKET_KEYS = frozenset({"as_of"}) | frozenset(MARKET_FIELDS)

#: Fields whose magnitude is stable from one period to the next, so a
#: jump of a round thousand between two of them is a unit mix rather than
#: a business event. The same argument -- and the same factor -- as
#: `config._check_one_scale`. Half-yearly against full-year figures differ
#: by two, nowhere near the bar.
SCALE_STABLE_FIELDS = ("revenue", "total_assets", "gross_profit",
                       "cash_and_equivalents", "net_ppe")

#: THE LEGS METHOD C DIVIDES AND DISCOUNTS -- guarded at the GATE, because
#: the load-time guard above cannot reach them.
#:
#: REVIEW-4 report B 7.1, RUN on a copy of `config/manual/DECK.yaml`: an
#: `operating_cash_flow` multiplied by 1,000 LOADS, and once its year is
#: flagged VERIFIED the gate says MAY RUN on a trillion-dollar operating
#: cash flow. The same for the share count, for the borrowing fields and
#: for a file mis-scaled throughout. `_check_one_scale` catches a slip in
#: one of the five fields above and NOTHING ELSE -- not OCF, not capex,
#: not debt, not leases, not the count.
#:
#: These are not "scale stable" the way revenue is, so the test is
#: narrower: a jump of a round thousand between two CONSECUTIVE entries.
#: Four quarters differ from a year by four, and a year from the year
#: before it by rather less; a factor of a thousand between neighbours is
#: a unit mix. Where it is not -- a capex line of 0.05m beside one of
#: 60m -- the refusal names the field and both periods and the reader
#: says so on the page.
#:
#: WHAT THIS STILL CANNOT SEE, stated rather than implied: a file mis-scaled
#: UNIFORMLY. Every period agrees with every other, so no comparison across
#: periods can find it; only an absolute band on what a figure may be could,
#: and no ruling sets one.
SECTION5_SCALE_FIELDS = (
    "operating_cash_flow", "operating_cash_flow_pretax", "income_tax_paid",
    "capex_ppe", "capex_intangibles", "capex_combined",
    "lease_payments_capital", "free_cash_flow_reported", "sbc",
    "cash_and_equivalents", "other_current_financial_assets",
    "financial_liabilities_current", "financial_liabilities_noncurrent",
    "lease_liabilities", "pension_deficit", "asset_retirement_obligation",
    "lease_interest_paid", "operating_lease_liabilities",
    "prepaid_delivery_obligation",
    "noncurrent_derivative_assets_on_debt",
    "diluted_weighted_average_shares", "shares_outstanding_period_end", "shares_diluted_period_end",
    "shares_issued_period_end", "treasury_shares_period_end",
    "employee_trust_shares_period_end",
)


# --- value objects --------------------------------------------------------


def cite_page(page: str | None) -> str:
    """A page reference as the owner wrote it, and never prefixed.

    The `page:` string SAYS WHERE IT IS in the words of whoever entered it:
    `note 4.2, p.131` from a report, `Financial statements_appendix ·
    Revenue` from a spreadsheet, `five-year summary, p.14`. Prefixing `p.`
    to any of those produced `p.five-year summary, p.14`, which is not a
    reference to anything.
    """
    return f" [{page}]" if page else ""


@dataclass(frozen=True)
class NotPresented:
    """E85: the search a NOT PRESENTED leg stands on -- repeatable, dated."""

    document: str
    scope: str
    date: date

    def describe(self) -> str:
        return (f"searched {self.document} ({self.scope}) on "
                f"{self.date.isoformat()}")


@dataclass(frozen=True)
class ManualFigure:
    """One hand-entered number and everything known about where it came from."""

    name: str
    #: "" for a market fact, which belongs to a date rather than a period.
    period: str
    period_end: date | None
    value: float | None
    source: str | None
    page: str | None
    status: str
    #: E25: which of the three forms of evidence a ZERO rests on, or None
    #: for any figure that is not zero.
    zero_basis: str | None = None
    #: E40: which kind of verification the VERIFIED flag stands on, or None
    #: for an UNVERIFIED figure. Never None on a VERIFIED one -- the parser
    #: reads an unstated kind as `same_page`.
    verified_kind: str | None = None
    #: E78: the issuer's own sentence, verbatim, on a zero verified as
    #: `caption_statement`; None on every other figure.
    statement: str | None = None
    #: E79.1: the precision the issuer printed `op_margin` to, in
    #: percentage points (1, 0.1, 0.01); None reads it from the value.
    precision: float | None = None
    #: E83: the statements' explanation of an `op_margin` outside the
    #: plausible band -- a gain inside operating profit -- quoted.
    cause: str | None = None
    #: E85: the recorded search behind a NOT PRESENTED leg; None otherwise.
    not_presented: "NotPresented | None" = None
    #: E86: a cumulative year-to-date column and the prior column it is
    #: taken against, each with its own page; `value` is the code's
    #: difference of the two, never a hand-computed one.
    cumulative: float | None = None
    cumulative_prior: float | None = None
    cumulative_prior_page: str | None = None
    #: E106 clause 3: the leg is ABSENT and BOUNDED. A MAGNITUDE, always
    #: positive, and `value` stays None -- a bound is not a figure the
    #: basis reads, it is a statement about how wrong the absence can be.
    #:
    #: **E21 THEREFORE DOES NOT GATE ON IT, and that is E21's own answer
    #: rather than an exception carved for E106.** E21 refuses on "an
    #: UNVERIFIED figure THE CURRENT BASIS READS"; no ratio takes a bound's
    #: value and the leg enters the arithmetic at zero, so the basis reads
    #: nothing here. What DOES bind is E106 clause 3's own condition -- *a
    #: bound is itself a figure and needs its evidence like any other* --
    #: and the parser enforces it: a bound with no page is refused at the
    #: load, and the tolerance test is asked on every basis that carries one.
    bound: float | None = None
    bound_direction: str | None = None
    #: E120: an ANNUAL figure standing in for a trailing-twelve-month window
    #: where the quarters do not state it (lease interest only).
    stand_in: bool = False

    @property
    def bounded(self) -> bool:
        return self.bound is not None

    @property
    def verified(self) -> bool:
        return self.status == STATUS_VERIFIED

    @property
    def status_with_kind(self) -> str:
        """`VERIFIED (tagged)`, `NOT PRESENTED (E85: ...)`, or plain `UNVERIFIED`."""
        if self.status == STATUS_NOT_PRESENTED and self.not_presented is not None:
            return f"{self.status} (E85: {self.not_presented.describe()})"
        if self.verified and self.verified_kind:
            return f"{self.status} ({self.verified_kind})"
        return self.status

    @property
    def page_provenance(self) -> str | None:
        """The page line as the record and the report print it: the page,
        E86's two columns with theirs, or E85's search beside the page."""
        if self.not_presented is not None:
            return f"{self.status_with_kind} -- {self.page}"
        if self.cumulative is not None:
            prior = (f" - {self.cumulative_prior:,.10g} [{self.cumulative_prior_page}]"
                     if self.cumulative_prior is not None
                     else " - prior column NOT STATED, so no quarter (E86)")
            result = f" = {self.value:,.10g}" if self.value is not None else ""
            return (f"E86: {self.cumulative:,.10g} [{self.page}]{prior}{result}"
                    f" -- the difference is the code's, both columns printed")
        return self.page

    @property
    def present(self) -> bool:
        return self.value is not None

    def provenance(self, origin: str = ORIGIN) -> str:
        where = self.source or "source not stated"
        when = f" [{self.period}]" if self.period else ""
        return (f"{origin}: {where}{cite_page(self.page)}{when} -- "
                f"{self.status_with_kind}")


#: E16's three share-count fields, named in one place so the rule that
#: binds them is findable rather than implied by three separate notes.
# --- ONE TWELVE-MONTH BASIS (FRAMEWORK-EDITS E19) -------------------------
#
# Every flow section 5 reads is a TWELVE-MONTH figure and every stock is
# taken at that window's END. For an annual reporter, the year as filed;
# for a quarterly one, the four most recent consecutive quarters summed,
# with the stocks at the newest of those four period ends. Fewer than four
# consecutive quarters is INPUT MISSING and section 5 does not run.
#
# E19 EXTENDS E13's exception from the ranking key to section 5 and
# supersedes E13's clause confining it there. The reasoning is E13's,
# unchanged: a figure's period length is part of what it is. What B18's
# five measurements added is that section 5 needs it too -- net debt over
# a THREE-MONTH EBITDA reads 7.33x against a cap of 2.5x, and a stock has
# no length, so requiring the two legs to "match" would have licensed it.
#
# WHAT A FIELD IS decides how it resolves, so the two sets are named here
# rather than inferred. A FLOW is measured OVER the window; a STOCK is a
# position AT its end.

#: Stated ratios: struck by the ISSUER on its own basis and not re-basable
#: by anyone. Neither a flow to sum nor a stock to take at a date -- if the
#: basis it was struck on is not the window, it is not usable.
#:
#: `op_margin` JOINED THIS SET 2026-08-25. It was omitted, so it resolved
#: as a flow and was SUMMED: BETS-B.ST read 0.6560 for four quarterly
#: margins of about 0.14 each, and PNDORA.CO read 0.8870 the same way.
#: A margin is not a quantity that accumulates over a window.
#:
#: WHAT THIS DOES NOT FIX, and it is left visible rather than papered
#: over: the value now taken is the newest quarter's margin, which the
#: issuer struck on THREE MONTHS, standing at a TWELVE-MONTH basis. That
#: is E13's own objection -- a figure's period length is part of what it
#: is -- and the field's other use is unaffected, because the margin
#: reconciliation runs PER PERIOD at load and never on the basis.
STATED_RATIO_FIELDS: frozenset[str] = frozenset({"net_debt_ebitda", "op_margin"})

STOCK_FIELDS: frozenset[str] = frozenset({
    "total_assets", "net_ppe", "cash_and_equivalents",
    # E123's measured figures read them at the window's end, like every
    # other balance-sheet caption here.
    "total_equity", "captive_finance_debt",
    "other_current_financial_assets", "financial_liabilities_current",
    "financial_liabilities_noncurrent", "lease_liabilities", "pension_deficit",
    "asset_retirement_obligation",
    # E81: a balance-sheet caption on every statement date -- a STOCK, and
    # deliberately NOT annual-only (E41): the stream sits on each interim
    # balance sheet, so the newest quarter must carry it.
    "prepaid_delivery_obligation",
    "noncurrent_derivative_assets_on_debt", "shares_outstanding_period_end", "shares_diluted_period_end",
    "shares_issued_period_end", "treasury_shares_period_end",
    "employee_trust_shares_period_end",
    # E38's memo. A STOCK: the count on one day, never summed across
    # quarters -- which is what a count outside this set would be.
    "shares_point_in_time",
    # E103's REFERENCE comparator for the bridge. A balance-sheet caption on
    # one date, so it is taken AT the window's end; outside this set it
    # would be SUMMED across four quarters, which would compare a valuation
    # against four times the issuer's own figure and blink on every name.
    "net_debt_reported",
})

#: E41: FIELDS A FILER STATES ONCE A YEAR. On a TTM basis they resolve from
#: the newest `annual:` entry whose year-end falls INSIDE the window, where
#: the quarters do not carry them -- E17's periods-first rule unchanged, E20
#: narrowed for exactly these. The record declares the departure (the
#: share count's as-of date is the annual entry's, and the as-of line says
#: THEY DO NOT AGREE). E35.1 adds `pension_deficit` to this set.
ANNUAL_ONLY_FIELDS: frozenset[str] = frozenset({
    "diluted_weighted_average_shares", "sbc", "pension_deficit",
    # E68: stated once a year with the pension note, on E41's terms.
    "asset_retirement_obligation",
})

#: B27, settled by E41: a WEIGHTED AVERAGE IS NEVER SUMMED. Four quarterly
#: averages added together are SYNSAM's 572,025,536, a count of nothing. On
#: a TTM basis the field comes from an annual entry (E41) or is DATA MISSING
#: with the reason; on a twelve-month period entry it is that entry's own.
NEVER_SUMMED: frozenset[str] = frozenset({"diluted_weighted_average_shares"})

#: The contiguity test for four consecutive quarters. THIRTEEN WEEKS IS 91
#: AND FILERS VARY BY A FEW, so it is a window rather than an equality --
#: the same bounds `vss/ranking.py` uses for E13's own TTM and `vss/xbrl.py`
#: uses to decide a tagged duration is a quarter at all. Imported rather
#: than restated: two implementations of one rule drift apart silently.
from .ranking import QUARTER_MAX_DAYS, QUARTER_MIN_DAYS, TTM_QUARTERS

#: Months in a quarter, for the TTM window.
QUARTER_MONTHS = 3

#: Months in an annual entry. It is a FISCAL YEAR by definition, and E17
#: compares a period entry's length against exactly this.
ANNUAL_MONTHS = 12

NET_SHARES = "shares_outstanding_period_end"
ISSUED_SHARES = "shares_issued_period_end"
TREASURY_SHARES = "treasury_shares_period_end"
#: FRAMEWORK-EDITS E54: a second leg the issuer may exclude from its OWN
#: EPS count alongside treasury. OPTIONAL on the rule below -- its absence
#: never blocks the issued-minus-treasury subtraction E16 already had.
TRUST_SHARES = "employee_trust_shares_period_end"


@dataclass(frozen=True)
class Subtraction:
    """One net the accounts may not print, and the figures that make it.

    E16 settled the share count and E18 the two finance nets on the same
    terms, so the rule lives in a table rather than three times in prose.

    ``optional_subtrahend`` is E54's addition: a THIRD leg, subtracted when
    the issuer states it and simply absent from the arithmetic when it does
    not -- unlike ``subtrahend``, whose absence blocks the whole net.
    """

    net: str
    minuend: str
    subtrahend: str
    #: How the report says what was done, in the field's own words.
    phrase: str
    optional_subtrahend: str | None = None


SUBTRACTIONS: tuple[Subtraction, ...] = (
    Subtraction(NET_SHARES, ISSUED_SHARES, TREASURY_SHARES,
                "issued − treasury", optional_subtrahend=TRUST_SHARES),
    Subtraction("net_finance_costs", "finance_costs_period",
                "finance_income_period", "finance costs − finance income"),
    Subtraction("net_interest_paid", "finance_costs_paid",
                "finance_income_received", "paid − received"),
)
SUBTRACTED_FIELDS: frozenset[str] = frozenset(r.net for r in SUBTRACTIONS)


@dataclass(frozen=True)
class NetShares:
    """The net share count, subtracted from two figures the accounts print.

    NOT a derivation of the kind `vss/appendix.py` is forbidden, and E16
    says why: both operands are printed in the accounts, each carries its
    own page, and the arithmetic is the subtraction of two stated counts
    rather than a judgement about what a line means. E14's lease portion
    of a consolidated line is the opposite case -- stated nowhere, and so
    not recoverable at all.

    IT IS NEVER WRITTEN BACK INTO THE FILE and carries no page of its own.
    The page it has is its two operands', and the report prints both.
    """

    value: float
    issued: ManualFigure
    treasury: ManualFigure
    rule: Subtraction
    #: E54: the optional third leg, present only where the issuer states it.
    optional: ManualFigure | None = None

    @property
    def provenance(self) -> str:
        def cite(figure: ManualFigure) -> str:
            return f"{figure.value:,.0f}{cite_page(figure.page)}"
        left, right = self.rule.phrase.split(" − ")
        text = (f"computed, not filed: {left} {cite(self.issued)} "
                f"− {right} {cite(self.treasury)}")
        if self.optional is not None:
            text += f" − {self.rule.optional_subtrahend} {cite(self.optional)}"
        return text


def subtract(holder, rule: Subtraction) -> NetShares | None:
    """One net for one period or annual entry, or None.

    None when the net is entered DIRECTLY -- there is nothing to compute --
    and None when either REQUIRED operand is absent, which under E16 and
    E18 leaves that operand AND the net DATA MISSING. Nothing estimates the
    half that is not there.

    E54's optional leg is different in kind: its absence subtracts nothing
    and blocks nothing -- most issuers carry no employee trust at all, and
    the pair rule above is unchanged for them.
    """
    if holder is None or holder.value(rule.net) is not None:
        return None
    minuend = holder.figures.get(rule.minuend)
    subtrahend = holder.figures.get(rule.subtrahend)
    if not (minuend and minuend.present and subtrahend and subtrahend.present):
        return None
    value = minuend.value - subtrahend.value
    optional = None
    if rule.optional_subtrahend:
        candidate = holder.figures.get(rule.optional_subtrahend)
        if candidate is not None and candidate.present:
            optional = candidate
            value -= candidate.value
    return NetShares(value, minuend, subtrahend, rule, optional)


def net_shares(holder) -> NetShares | None:
    """The share count specifically, kept because it reads better at the
    one call site that only ever wants that one."""
    return subtract(holder, SUBTRACTIONS[0])


@dataclass(frozen=True)
class ManualPeriod:
    period: str
    period_end: date
    period_basis: str | None
    document: str | None
    url: str | None
    figures: dict[str, ManualFigure] = field(default_factory=dict)

    def value(self, name: str) -> float | None:
        figure = self.figures.get(name)
        return figure.value if figure and figure.present else None


@dataclass(frozen=True)
class AnnualEntry:
    """One fiscal year of figures a company publishes only once a year.

    E15: diluted EPS, share counts, leverage ratios -- anything whose only
    stated basis is the full year. It carries everything a period entry
    carries and is keyed on the FISCAL YEAR instead of a period label,
    because a label is what the overlap guard reasons about and this block
    must never enter that reasoning.
    """

    fiscal_year: int
    period_end: date
    document: str | None
    url: str | None
    figures: dict[str, ManualFigure] = field(default_factory=dict)

    def value(self, name: str) -> float | None:
        figure = self.figures.get(name)
        return figure.value if figure and figure.present else None


@dataclass(frozen=True)
class InventoryOperatingAsset:
    """E123: the operating asset is inventory and its purchase runs through
    operating cash flow.

    A FACT ABOUT THE ACCOUNTS, never a judgment about the name: is the
    operating asset inventory, and does buying it run through operating cash
    flow? Where it is true, Gate 3's FCF-positivity limb and its leverage
    limb are DATA MISSING -- because growth drives free cash flow negative
    and contraction drives it positive, and EBITDA excludes the inventory
    spend that is the real capital cycle -- and section 4.4 rebases, as E99
    does for Gate 4. Absent is NOT `no`: it is the ordinary state of every
    other filer, and the limbs form as usual.
    """

    value: bool
    source: str
    page: str


@dataclass(frozen=True)
class LeaseClassification:
    """E70: whether this filer's operating cash flow bears its operating
    lease payments, and where that was read.

    `yes` for a US GAAP filer (ASC 842-20-45-5(a): operating lease
    payments are operating cash outflows) -- FCF0 adds the stated payment
    back, because the lease liability in net debt already charges it.
    `no` for an IFRS 16 filer (16.50(b): the principal is in financing) --
    the flow never bore it and nothing is added back. Absent is NOT `no`:
    it is DATA MISSING, and FCF0 does not form (the same shape as E34).
    """

    value: bool
    source: str
    page: str


@dataclass(frozen=True)
class InterestClassification:
    """E34: where this filer books interest, and where that was read.

    IT DESCRIBES THE BASIS YEAR. One filer can be on both sides inside one
    file -- SAP tags `InterestPaidClassifiedAsFinancingActivities` for
    FY2025 and the FY2024 20-F tagged the identical amounts as
    `...ClassifiedAsOperatingActivities`, because it reclassified in January
    2025 and re-tagged the comparatives. Section 5 reads the basis year and
    nothing else, so one attribute is enough for it; a five-year per-share
    proxy reading the same file is not covered, and E34 records that as a
    limit rather than solving it.
    """

    #: True where the filer's operating cash flow ALREADY BEARS its
    #: interest -- ASC 230 always, IAS 7 sometimes.
    value: bool
    source: str
    page: str
    #: E34.1 / E61: which statement supplies the figure that is added back.
    #: The cash flow statement (E34 as written, `net_interest_paid`) unless
    #: the filer states interest paid and never interest received, in
    #: which case the income statement's net (`net_finance_costs`) stands
    #: in as an ACCRUAL PROXY (E34.1) -- or, where even that net is never
    #: tagged, the gross interest expense alone (`finance_costs_period`)
    #: stands in as a bounded, one-sided proxy (E61). The record says
    #: which.
    interest_source: str = INTEREST_SOURCE_CASH_FLOW

    @property
    def accrual_proxy(self) -> bool:
        return self.interest_source == INTEREST_SOURCE_INCOME_STATEMENT

    @property
    def interest_expense_only_proxy(self) -> bool:
        return self.interest_source == INTEREST_SOURCE_INTEREST_EXPENSE_ONLY

    @property
    def cash_paid_only_proxy(self) -> bool:
        return self.interest_source == INTEREST_SOURCE_CASH_PAID_ONLY


@dataclass(frozen=True)
class ManualFile:
    """A parsed, validated manual file. Nothing here is computed."""

    ticker: str
    name: str
    reporting_currency: str
    quote_currency: str
    sector: str
    reporting_frequency: str
    path: Path
    #: Which path put the figures in this file. See VALID_ORIGINS.
    origin: str = ORIGIN
    periods: tuple[ManualPeriod, ...] = ()
    #: FRAMEWORK-EDITS E15. Read by section 5 where the figure it needs is
    #: annual by nature; EXCLUDED FROM EVERY TRAILING WINDOW by construction
    #: -- never summed, never combined with a period entry, and never
    #: reaching the ranking key, which under E13 reads TTM from `periods:`
    #: alone. `as_record` does not emit a single series point from here.
    annual: tuple[AnnualEntry, ...] = ()
    market: dict[str, ManualFigure] = field(default_factory=dict)
    market_as_of: date | None = None
    #: E34. None means the file does not say, which makes FCF0 DATA MISSING.
    interest_in_ocf: "InterestClassification | None" = None
    #: E70. None means the file does not say -- DATA MISSING, not `no`.
    operating_leases_in_ocf: "LeaseClassification | None" = None
    #: E123: the declaration that takes two Gate 3 limbs out of the count.
    operating_asset_is_inventory: "InventoryOperatingAsset | None" = None
    #: The scale the file's money figures and its share counts are stated
    #: in -- one of UNIT_SCALE, or None where the file does not say. See
    #: UNIT_SCALE: the run record divides on these and refuses without them.
    money_unit: str | None = None
    share_unit: str | None = None
    #: THE FILER'S SEC CENTRAL INDEX KEY, where it has one.
    #:
    #: **IT BELONGS IN THE STORE, ruled by the owner 2026-09-04**, and the
    #: reason is worth keeping: *a CIK identifies the COMPANY, not my
    #: watching of it, so the store is where it belongs — and a ticker
    #: lookup at runtime can match the wrong company on a re-used or
    #: dual-listed symbol and fetch the wrong document with nothing to catch
    #: it. A CIK written in the file is a fact I can see; a lookup is an
    #: assumption made fresh each run.*
    #:
    #: Five of these names carry no watchlist entry at all, so the entry
    #: could not hold it even where one existed -- which is what made the
    #: question live. Every value is sourced on the field.
    cik: int | None = None

    @property
    def newest_period(self) -> ManualPeriod | None:
        return self.periods[-1] if self.periods else None

    @property
    def newest_period_end(self) -> date | None:
        newest = self.newest_period
        return newest.period_end if newest else None

    @property
    def newest_annual(self) -> AnnualEntry | None:
        return self.annual[-1] if self.annual else None

    def _basis(self) -> tuple[dict[str, str], dict[str, tuple[str, int, float]]]:
        """Which block answers each field the two of them both carry.

        E15 gave the rule -- `periods:` wins -- and E17 gave it the test it
        was missing: **only at EQUAL LENGTH**. A quarter never displaces a
        year. PNDORA.CO is the case: a 2026-Q2 EBITDA of 2,133 covering
        three months was displacing an FY2025 EBITDA of 10,316 covering
        twelve, 4.84x apart, while the `net_debt_ebitda` entered beside it
        was struck on the annual figure. The file answered with two
        quantities on different bases and said nothing.

        Returns (shadowed, displaced):
          shadowed  field -> the period label that ANSWERS it, the period
                    being the same twelve months the annual entry is. The
                    annual figure is ignored, exactly as E15 says.
          displaced field -> (period label, its months, its value) for a
                    period figure NOT used because it is SHORTER than the
                    annual entry. The annual figure wins, and both are
                    named: silently preferring either would leave a reader
                    unable to see which basis the answer stands on.
        """
        shadowed: dict[str, str] = {}
        displaced: dict[str, tuple[str, int, float]] = {}
        for entry in self.annual:
            for name, figure in entry.figures.items():
                if not figure.present:
                    continue
                for period in reversed(self.periods):
                    value = period.value(name)
                    if value is None:
                        continue
                    months = period_months(period.period)
                    if months == ANNUAL_MONTHS:
                        shadowed[name] = period.period
                    else:
                        displaced[name] = (period.period, months, value)
                    break
        return shadowed, displaced

    def shadowed(self) -> dict[str, str]:
        """Annual figures `periods:` answers instead, and which period does.

        Only where that period covers the same twelve months (E17).
        """
        return self._basis()[0]

    def displaced(self) -> dict[str, tuple[str, int, float]]:
        """Period figures NOT used, because a year answers the field instead.

        field -> (period label, its length in months, its value).
        """
        return self._basis()[1]

    def annual_figure(self, name: str) -> ManualFigure | None:
        """The newest annual figure `periods:` does not already answer."""
        if name in self.shadowed():
            return None
        for entry in reversed(self.annual):
            figure = entry.figures.get(name)
            if figure is not None and figure.present:
                return figure
        return None

    def net_shares_for(self, holder) -> NetShares | None:
        """The computed net for one holder, and nothing else's.

        Deliberately per-holder: E16 subtracts two counts AT ONE PERIOD END,
        and an issued count from one date minus a treasury count from
        another is not a share count of anything.
        """
        return net_shares(holder)

    def basis_subtraction(self, basis: "Basis", rule: Subtraction):
        """The net and its operands, ALL resolved ON THE BASIS (E16/E18
        under E19; the optional third leg, E54).

        "At one period" becomes "on one basis", which is what makes the
        operands and their net incapable of disagreeing -- B18's third
        measurement, closed by construction rather than reported.

        Returns ``(value, a, b, c)`` -- ``c`` is the optional leg's
        `Resolved`, or None where the rule has none or the issuer does not
        state it. Always four, so one shape serves every rule in
        `SUBTRACTIONS`: the two finance nets simply never carry a ``c``.
        """
        if resolve_on_basis(self, basis, rule.net).value is not None:
            return None
        a = resolve_on_basis(self, basis, rule.minuend)
        b = resolve_on_basis(self, basis, rule.subtrahend)
        if a.value is None or b.value is None:
            return None
        value = a.value - b.value
        c = None
        if rule.optional_subtrahend:
            candidate = resolve_on_basis(self, basis, rule.optional_subtrahend)
            if candidate.value is not None:
                c = candidate
                value -= candidate.value
        return value, a, b, c

    def section5_subtractions(self) -> dict[str, tuple[NetShares, str]]:
        """Every net the store can subtract, ON THE BASIS (E19).

        The pre-E19 per-period search is gone: two operands from two
        periods were never a net of anything, and one basis makes the
        question moot rather than merely checked.
        """
        basis = section5_basis(self)
        if basis is None:
            return {}
        out: dict[str, tuple[NetShares, str]] = {}
        for rule in SUBTRACTIONS:
            got = self.basis_subtraction(basis, rule)
            if got is None:
                continue
            value, a, b, c = got

            def collect(key: str) -> tuple[ManualFigure, ...]:
                return tuple(
                    f for holder in basis.holders
                    for f in (holder.figures.get(key),) if f is not None)

            minuend_figures = collect(rule.minuend)
            subtrahend_figures = collect(rule.subtrahend)
            optional_figures = (collect(rule.optional_subtrahend)
                               if rule.optional_subtrahend and c is not None
                               else ())
            out[rule.net] = (
                NetShares(
                    value,
                    minuend_figures[0] if minuend_figures else None,
                    subtrahend_figures[-1] if subtrahend_figures else None,
                    rule,
                    optional_figures[-1] if optional_figures else None,
                ),
                basis.label,
            )
        return out

    def all_figures(self) -> tuple[ManualFigure, ...]:
        out: list[ManualFigure] = []
        for period in self.periods:
            out.extend(period.figures[name] for name in sorted(period.figures))
        for entry in self.annual:
            out.extend(entry.figures[name] for name in sorted(entry.figures))
        out.extend(self.market[name] for name in sorted(self.market))
        return tuple(out)

    def unverified(self) -> tuple[ManualFigure, ...]:
        """Entered figures nobody has read back. Absent ones are not here.

        An absent figure has nothing to verify -- it is DATA MISSING, a
        different fact, counted separately and never merged into this one.
        """
        # E85: a NOT PRESENTED leg is a recorded search, not an entered
        # figure -- there is nothing to read back, so it is not here either.
        return tuple(f for f in self.all_figures()
                     if f.present and not f.verified
                     and f.status != STATUS_NOT_PRESENTED)

    def missing(self) -> tuple[str, ...]:
        """Schema fields nothing supplies a value for.

        A net share count the store can SUBTRACT is not missing: it is not
        in the file and it is available, which is the whole of E16.
        """
        supplied = {f.name for f in self.all_figures() if f.present}
        supplied.update(self.section5_subtractions())
        return tuple(n for n in list(FIELDS_BY_NAME) + list(MARKET_FIELDS)
                     if n not in supplied)


# --- parsing --------------------------------------------------------------


def _fail(path: Path, where: str, message: str) -> None:
    raise ManualError(f"{path}: {where}: {message}")


def _as_float(value: Any, path: Path, where: str, key: str) -> float | None:
    if value is None:
        return None
    if isinstance(value, bool):
        _fail(path, where, f"{key} must be a number, got {value!r}")
    try:
        return float(value)
    except (TypeError, ValueError):
        _fail(path, where, f"{key} must be a number, got {value!r}")


def _as_text(value: Any) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text or None


def _as_date(value: Any, path: Path, where: str, key: str) -> date | None:
    if value is None:
        return None
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, date):
        return value
    try:
        return datetime.strptime(str(value).strip(), "%Y-%m-%d").date()
    except ValueError:
        _fail(path, where, f"{key} must be a YYYY-MM-DD date, got {value!r}")


def _parse_figure(raw: Any, name: str, period: str, period_end: date | None,
                  path: Path, where: str,
                  default_source: str | None) -> ManualFigure:
    """One figure block: value, source, page, status.

    A bare scalar is REFUSED rather than read as the value. `revenue: 1234`
    would be a figure with no page and no status, which is exactly the
    entry this schema exists to make impossible.
    """
    if raw is None:
        raw = {}
    if not isinstance(raw, Mapping):
        _fail(path, where,
              f"{name} must be a mapping with value/source/page/status keys, "
              f"got {type(raw).__name__}. A bare number carries no page and no "
              f"status, and this schema does not accept a figure without them")
    unknown = set(raw) - ALLOWED_FIGURE_KEYS
    if unknown:
        _fail(path, where, f"{name}: unknown key(s) {', '.join(sorted(unknown))}. "
                           f"Allowed: {', '.join(sorted(ALLOWED_FIGURE_KEYS))}")

    source = _as_text(raw.get("source")) or default_source
    page = _as_text(raw.get("page"))

    # E85: NOT PRESENTED -- a recorded search, not a figure and not a zero.
    np_raw = raw.get("not_presented")
    if np_raw is not None:
        beside = sorted(k for k in ("value", "status", "zero_basis",
                                    "verified_kind", "statement", "cumulative",
                                    "cumulative_prior") if k in raw)
        if beside:
            _fail(path, where, f"{name}: not_presented: stands alone (E85) -- "
                               f"it records a search, not a figure; remove "
                               f"{', '.join(beside)}")
        if (not isinstance(np_raw, Mapping)
                or set(np_raw) != {"document", "scope", "date"}):
            _fail(path, where, f"{name}.not_presented must carry exactly "
                               f"document, scope and date (E85) -- the search "
                               f"is what the record keeps, so it is stated in "
                               f"full or not at all")
        document = _as_text(np_raw.get("document"))
        scope = _as_text(np_raw.get("scope"))
        when = np_raw.get("date")
        if isinstance(when, str):
            try:
                when = date.fromisoformat(when.strip())
            except ValueError:
                when = None
        if not document or not scope or not isinstance(when, date):
            _fail(path, where, f"{name}.not_presented needs a document, a scope "
                               f"and an ISO date (E85)")
        if name not in NET_DEBT_LEGS or name == "cash_and_equivalents":
            _fail(path, where, f"{name} cannot be NOT PRESENTED (E85): the state "
                               f"exists for a net-debt leg the reader searched "
                               f"a whole report for; a flow or an asset the "
                               f"accounts do not state is DATA MISSING")
        if not page:
            _fail(path, where, f"{name} is NOT PRESENTED and names no page: "
                               f"the page says what the balance sheet presents "
                               f"INSTEAD, so the next reader starts there (E85)")
        return ManualFigure(name=name, period=period, period_end=period_end,
                            value=0.0, source=source, page=page,
                            status=STATUS_NOT_PRESENTED,
                            not_presented=NotPresented(document, scope, when))

    # E86: a cumulative column and its prior, each with a page; the
    # quarter is the code's difference, and a column without its prior is
    # an operand on file and no quarter.
    cumulative = _as_float(raw.get("cumulative"), path, where, f"{name}.cumulative")
    cumulative_prior = _as_float(raw.get("cumulative_prior"), path, where,
                                 f"{name}.cumulative_prior")
    cumulative_prior_page = _as_text(raw.get("cumulative_prior_page"))
    if (cumulative is not None or cumulative_prior is not None
            or cumulative_prior_page is not None):
        if "value" in raw:
            _fail(path, where, f"{name} carries cumulative: beside value: (E86). "
                               f"A quarter is EITHER stated, and entered as "
                               f"value, OR the code's difference of two stated "
                               f"columns -- never both, and never a hand-"
                               f"computed difference entered as a value")
        if cumulative is None:
            _fail(path, where, f"{name} carries a prior column and no "
                               f"cumulative: column (E86)")
        if not re.fullmatch(r"\d{4}-Q[1-4]", period or ""):
            _fail(path, where, f"{name}: cumulative columns belong to a "
                               f"QUARTERLY periods: entry (E86); {period!r} "
                               f"is not one")
        if (name in STOCK_FIELDS or name in STATED_RATIO_FIELDS
                or name in NEVER_SUMMED):
            _fail(path, where, f"{name} is not a flow: a cumulative column "
                               f"(E86) is a year-to-date FLOW, and a stock or "
                               f"a ratio has no year-to-date")
        if not page:
            _fail(path, where, f"{name}.cumulative has no page reference (E86)")
        if (cumulative_prior is None) != (cumulative_prior_page is None):
            _fail(path, where, f"{name}: cumulative_prior and "
                               f"cumulative_prior_page come together (E86) -- "
                               f"the prior column is a stated figure with its "
                               f"own page")
        value = (cumulative - cumulative_prior
                 if cumulative_prior is not None else None)
    else:
        value = _as_float(raw.get("value"), path, where, f"{name}.value")
    # E106 clause 3: a leg that is ABSENT but BOUNDED. "We do not know what
    # this is" and "we know this is at most X" are different states, and
    # only the second is tolerable -- so the second gets a form of its own
    # rather than being written as a value nobody meant.
    bound = _as_float(raw.get("bound"), path, where, f"{name}.bound")
    direction = _as_text(raw.get("bound_direction"))
    if bound is not None or direction is not None:
        if bound is None:
            _fail(path, where, f"{name} carries bound_direction and no "
                               f"bound (E106).")
        if "value" in raw or "cumulative" in raw:
            _fail(path, where,
                  f"{name} carries a bound BESIDE a value (E106). A leg is "
                  f"EITHER known, and entered as the figure, OR absent and "
                  f"bounded -- never both. A bound on a figure that is "
                  f"present says the figure is not trusted, which is what "
                  f"UNVERIFIED is for.")
        if bound <= 0:
            _fail(path, where,
                  f"{name}.bound is {bound}, and a bound is a MAGNITUDE: the "
                  f"largest the leg could be, positive whichever way it moves "
                  f"the answer. Which way is `bound_direction`. A bound of "
                  f"zero is not a bound, it is a determined zero, and E25's "
                  f"`zero_basis` is where that is stated.")
        direction = (direction or BOUND_REDUCES).strip().lower()
        if direction not in VALID_BOUND_DIRECTIONS:
            _fail(path, where,
                  f"{name}.bound_direction must be one of "
                  f"{'|'.join(VALID_BOUND_DIRECTIONS)}, got "
                  f"{raw.get('bound_direction')!r}. `reduces` = the true "
                  f"value can only LOWER fv_base from where it is struck "
                  f"(a deduction, E105's shape); `raises` = it can only "
                  f"raise it (an add-back, E70's shape); `either` = the sign "
                  f"itself is unknown.")
        if not _as_text(raw.get("page")):
            _fail(path, where,
                  f"{name} is bounded and carries no page (E106 clause 3): "
                  f"*a bound is itself a figure and needs its evidence like "
                  f"any other*. Without it, `at most X` is an assertion.")
    status = (_as_text(raw.get("status")) or STATUS_UNVERIFIED).upper()
    if status not in VALID_FIGURE_STATUSES:
        _fail(path, where, f"{name}.status must be one of "
                           f"{'|'.join(VALID_FIGURE_STATUSES)}, got {raw.get('status')!r}")
    # E40: the KIND of verification. Stated, or -- on a VERIFIED figure that
    # names none -- `same_page`, the weakest claim and the one every flag
    # set before E40 was. On an UNVERIFIED figure a kind is refused: it is
    # a property of a verification that happened.
    kind = _as_text(raw.get("verified_kind"))
    if kind is not None:
        kind = kind.strip().lower()
        if kind not in VERIFIED_KINDS:
            _fail(path, where, f"{name}.verified_kind must be one of "
                               f"{'|'.join(VERIFIED_KINDS)}, got "
                               f"{raw.get('verified_kind')!r} (E40)")
        if status != STATUS_VERIFIED:
            _fail(path, where, f"{name} carries verified_kind {kind!r} and "
                               f"status {status}. A kind is a property of a "
                               f"VERIFIED figure (E40); an unverified figure "
                               f"has no kind of verification to name")
    elif status == STATUS_VERIFIED:
        kind = KIND_SAME_PAGE
    # E78: the sentence a caption_statement stands on. Parsed here, checked
    # below once the zero and its form are known.
    statement = _as_text(raw.get("statement"))
    if statement is not None and kind != KIND_CAPTION_STATEMENT:
        _fail(path, where, f"{name} carries a statement: but is not "
                           f"verified as {KIND_CAPTION_STATEMENT} (E78). The "
                           f"sentence is that kind's evidence and belongs to "
                           f"it; on any other kind it says nothing the page "
                           f"reference does not")

    if value is not None:
        # Provenance is not optional on a figure that exists. The whole
        # point of the file is that every number can be walked back to a
        # page, and a figure that cannot be is not evidence of anything.
        if not source:
            fallback = ("and the period states no `document:` to fall back on"
                        if period else "and a market figure has no `document:` "
                                       "to fall back on -- name the source on "
                                       "the figure itself")
            _fail(path, where, f"{name} has a value but no source, {fallback}")
        if not page:
            _fail(path, where, f"{name} has a value but no page reference")

    # E25: A ZERO IS A CLAIM ABOUT THE COMPANY, and needs evidence rather
    # than absence. Everything below is about the number 0.
    zero_basis = _as_text(raw.get("zero_basis"))
    if zero_basis is not None:
        zero_basis = zero_basis.strip().lower()
        if zero_basis not in VALID_ZERO_BASES:
            _fail(path, where,
                  f"{name}.zero_basis must be one of "
                  f"{'|'.join(VALID_ZERO_BASES)}, got {raw.get('zero_basis')!r}. "
                  f"caption = the issuer lists the line and shows nil or a "
                  f"dash; note = a sentence states there is none, cited to its "
                  f"page; subtotal = the components shown sum to the subtotal "
                  f"shown, leaving no room for the line; searched = a "
                  f"RECORDED SEARCH of a named document for a named concept, "
                  f"finding it absent (E107)")
        if zero_basis == ZERO_SEARCHED:
            # E107 carries E85's three requirements, and they are enforced
            # rather than requested. A search that found nothing is a fact
            # about the SEARCH until it is recorded; recorded, it is a fact
            # about the FILING -- and it is only recorded when a later
            # reader can repeat it, judge it, and know what would supersede
            # it. Without the document it is not repeatable; without the
            # scope it cannot be judged; without the date it cannot be
            # superseded by a later filing.
            evidence = (_as_text(raw.get("page")) or "")
            for needle, what in ((r"searched", "the SCOPE of the search -- "
                                  "the terms looked for, written as "
                                  "`searched ... for ...`"),
                                 (r"\d{4}-\d{2}-\d{2}", "the DATE the "
                                  "search was made, as YYYY-MM-DD")):
                if not re.search(needle, evidence, re.I):
                    _fail(path, where,
                          f"{name}.zero_basis is `searched` and the page "
                          f"does not carry {what}. E107 requires the "
                          f"DOCUMENT, the SCOPE and the DATE on the field: "
                          f"a searched zero missing any of the three is not "
                          f"evidence, it is an assertion.")
            if len(evidence) < 40:
                _fail(path, where,
                      f"{name}.zero_basis is `searched` and the page does "
                      f"not name a DOCUMENT to have searched. E107: the "
                      f"document is named as a document, not as a company, "
                      f"and it must be one where the concept would appear "
                      f"if it existed.")
        if value != 0:
            _fail(path, where,
                  f"{name} carries zero_basis {zero_basis!r} and a value of "
                  f"{value!r}. zero_basis is evidence for a ZERO and says "
                  f"nothing about any other figure")
    if value == 0:
        if name in ZERO_REFUSED:
            _fail(path, where,
                  f"{name} may not be zero (E25): {ZERO_REFUSED[name]}. A "
                  f"figure the reader could not find is DATA MISSING -- leave "
                  f"it blank, which says nothing, rather than entering a zero, "
                  f"which says something the accounts do not")
        if name in ZERO_NEEDS_BASIS and zero_basis is None:
            _fail(path, where,
                  f"{name} is zero and carries no zero_basis (E25). A wrong "
                  f"zero here carries this name through a gate it should fail, "
                  f"so the entry must name what the reader SAW: zero_basis: "
                  f"{'|'.join(VALID_ZERO_BASES)}. If the line was simply not "
                  f"found, leave the figure blank -- absence in a search is a "
                  f"fact about the search, not about the company")
    # E79.1 / E83: two keys that belong to `op_margin` alone.
    precision = _as_float(raw.get("precision"), path, where, f"{name}.precision")
    cause = _as_text(raw.get("cause"))
    if (precision is not None or cause is not None) and name != "op_margin":
        _fail(path, where, f"{name} carries precision: or cause:, which belong "
                           f"to `op_margin` alone (E79.1, E83)")
    if precision is not None and precision not in (1, 0.1, 0.01):
        _fail(path, where, f"{name}.precision must be 1, 0.1 or 0.01 -- the "
                           f"percentage points the issuer printed the margin "
                           f"to (E79.1); got {precision!r}")
    if kind == KIND_CAPTION_STATEMENT:
        # E78: a stated nothing is not a number. The kind stands on a
        # ZERO, on E25's caption or note form, and on the sentence.
        if value != 0:
            _fail(path, where,
                  f"{name} is verified as {KIND_CAPTION_STATEMENT} but is "
                  f"{value!r}, not zero (E78). The kind exists for a stated "
                  f"ABSENCE; a number still needs E40's second read")
        if zero_basis not in (ZERO_CAPTION, ZERO_NOTE):
            _fail(path, where,
                  f"{name} is verified as {KIND_CAPTION_STATEMENT} on the "
                  f"zero form {zero_basis!r} (E78). The kind stands on a "
                  f"`caption` or `note` zero -- the issuer stating in words "
                  f"that the thing does not exist. A `subtotal` is "
                  f"arithmetic, not a sentence, and is verified on its own "
                  f"terms (E59)")
        if not statement:
            _fail(path, where,
                  f"{name} is verified as {KIND_CAPTION_STATEMENT} and "
                  f"carries no statement: (E78). The sentence, quoted "
                  f"verbatim from the page named, IS the evidence; a kind "
                  f"that names none has nothing to stand on")
    return ManualFigure(name=name, period=period, period_end=period_end,
                        value=value, source=source, page=page, status=status,
                        zero_basis=zero_basis, verified_kind=kind,
                        statement=statement, precision=precision, cause=cause,
                        cumulative=cumulative, cumulative_prior=cumulative_prior,
                        cumulative_prior_page=cumulative_prior_page,
                        bound=bound,
                        bound_direction=direction if bound is not None else None,
                        stand_in=_parse_stand_in(raw, name, path, where))


def _parse_stand_in(raw, name: str, path: Path, where: str) -> bool:
    """E120: `stand_in: true` is permitted on `lease_interest_paid` alone."""
    flag = raw.get("stand_in") if isinstance(raw, dict) else None
    if flag in (None, False):
        return False
    if flag is not True:
        _fail(path, where, f"{name}.stand_in must be true or absent (E120)")
    if name != "lease_interest_paid":
        _fail(path, where, f"{name}: stand_in is E120's, and E120 reaches "
                           f"lease_interest_paid only")
    return True


def lease_interest_stand_in(parsed: "ManualFile", basis: "Basis | None") -> "ManualFigure | None":
    """E120: the newest ANNUAL `lease_interest_paid` marked `stand_in`, at or
    before the basis end -- used only where the basis's own periods state no
    lease interest. None where there is none, or the basis states it."""
    if basis is None:
        return None
    if resolve_on_basis(parsed, basis, "lease_interest_paid").value is not None:
        return None
    best = None
    for entry in getattr(parsed, "annual", ()) or ():
        figure = entry.figures.get("lease_interest_paid")
        if (figure is not None and figure.stand_in and figure.value is not None
                and entry.period_end is not None and entry.period_end <= basis.end
                and (best is None or entry.period_end > best[0])):
            best = (entry.period_end, figure)
    return best[1] if best else None


def _check_subtotal_form(figures: Mapping[str, ManualFigure], path: Path,
                         where: str) -> None:
    """E25: `subtotal` is the only form that also excludes the THIRD reading
    -- that the line is subsumed in a caption the issuer does present.

    Where a combined line IS present, the subtotal has room for the split
    lines inside it, so the form proves nothing and is refused. Betsson's
    capex is the case: `Investments in intangibles/tangibles` is exactly a
    caption with room in it.
    """
    if not figures.get("capex_combined") or not figures["capex_combined"].present:
        return
    for name in ("capex_ppe", "capex_intangibles"):
        figure = figures.get(name)
        if figure is not None and figure.value == 0 and \
                figure.zero_basis == ZERO_SUBTOTAL:
            _fail(path, where,
                  f"{name} is zero on the `subtotal` form while "
                  f"`capex_combined` carries a value (E25). A combined line "
                  f"is a caption WITH ROOM IN IT: the subtotal does not "
                  f"exclude the split figures being inside it, which is the "
                  f"one thing this form exists to exclude. Use `caption` or "
                  f"`note` if the issuer says so, and otherwise leave the "
                  f"figure blank")


def _parse_period(raw: Any, index: int, path: Path, frequency: str,
                  seen: list[str]) -> ManualPeriod:
    where = f"period #{index + 1}"
    if not isinstance(raw, Mapping):
        _fail(path, where, f"expected a mapping, got {type(raw).__name__}")
    unknown = set(raw) - ALLOWED_PERIOD_KEYS
    if unknown:
        _fail(path, where, f"unknown key(s) {', '.join(sorted(unknown))}. "
                           f"Allowed: {', '.join(sorted(ALLOWED_PERIOD_KEYS))}")

    label = _as_text(raw.get("period"))
    if label is None or period_parts(label) is None:
        _fail(path, where, f"period must be a label the schema knows "
                           f"(YYYY-Qn, YYYY-H1, YYYY-H2 or YYYY-FY), got "
                           f"{raw.get('period')!r}")
    where = f"period {label}"
    if not period_kind_allowed(label, frequency):
        kinds = "/".join(PERIOD_KINDS_BY_FREQUENCY[frequency])
        _fail(path, where, f"{label} is a {period_months(label)}-month period but "
                           f"the ticker reports {frequency}, which stores {kinds} "
                           f"periods only")
    if label in seen:
        _fail(path, where, "duplicate period")
    if seen and period_sort_key(label) < period_sort_key(seen[-1]):
        _fail(path, where, f"periods must be listed oldest first -- {label} "
                           f"follows {seen[-1]}")

    period_end = _as_date(raw.get("period_end"), path, where, "period_end")
    if period_end is None:
        _fail(path, where,
              "period_end is required. It is the date the accounts closed, and "
              "STALE is measured on it -- a label alone cannot say how old a "
              "figure is")
    basis = _as_text(raw.get("period_basis"))
    if basis is not None:
        basis = basis.lower()
        if basis not in VALID_PERIOD_BASIS:
            _fail(path, where, f"period_basis must be one of "
                               f"{'|'.join(VALID_PERIOD_BASIS)}, got "
                               f"{raw.get('period_basis')!r}")
    if basis == "calendar":
        # Only checkable on a CALENDAR basis. A fiscal Q1 ends wherever the
        # filer's year does -- LULU's fiscal 2026 Q1 ended 2026-05-03 -- so
        # holding a fiscal label to the calendar span would reject correct
        # entries, which is the mirror of backlog B-3.
        year, first_month, last_month = period_span(label)
        if not (period_end.year == year and first_month <= period_end.month <= last_month):
            _fail(path, where,
                  f"period_end {period_end.isoformat()} falls outside {label} "
                  f"({year}-{first_month:02d}..{year}-{last_month:02d}) on a "
                  f"calendar basis. Set period_basis: fiscal if the company's "
                  f"year does not end in December")

    document = _as_text(raw.get("document"))
    url = _as_text(raw.get("url"))

    raw_figures = raw.get("figures") or {}
    if not isinstance(raw_figures, Mapping):
        _fail(path, where, f"figures must be a mapping, got "
                           f"{type(raw_figures).__name__}")
    unknown = set(raw_figures) - FIGURE_KEYS
    if unknown:
        _fail(path, where,
              f"unknown figure(s) {', '.join(sorted(unknown))}. This schema "
              f"carries only what the ranking key and the section 5 chain read; "
              f"allowed: {', '.join(sorted(FIGURE_KEYS))}")

    figures = {
        name: _parse_figure(raw_figures.get(name), name, label, period_end,
                            path, where, document)
        for name in sorted(raw_figures)
    }
    _check_subtotal_form(figures, path, where)
    return ManualPeriod(period=label, period_end=period_end, period_basis=basis,
                        document=document, url=url, figures=figures)


def _parse_annual(raw: Any, path: Path, seen_fields: set[str]) -> tuple[AnnualEntry, ...]:
    """The `annual:` block (E15). Oldest first, one entry per fiscal year.

    NOT held to the period rules, and that is the point: it carries no
    period LABEL, so `period_kind_allowed` and the overlap guard never see
    it. A fiscal year that ends in another calendar year -- a retailer's
    2025 closing 2026-01-31 -- is an ordinary entry here, where inside
    `periods:` it would be a label problem.
    """
    if raw is None:
        return ()
    if not isinstance(raw, list):
        raise ManualError(f"{path}: annual must be a list")

    out: list[AnnualEntry] = []
    years: list[int] = []
    for index, item in enumerate(raw):
        where = f"annual entry #{index + 1}"
        if not isinstance(item, Mapping):
            _fail(path, where, f"expected a mapping, got {type(item).__name__}")
        unknown = set(item) - ALLOWED_ANNUAL_KEYS
        if unknown:
            _fail(path, where, f"unknown key(s) {', '.join(sorted(unknown))}. "
                               f"Allowed: {', '.join(sorted(ALLOWED_ANNUAL_KEYS))}")
        raw_year = item.get("fiscal_year")
        try:
            year = int(raw_year)
            integral = not isinstance(raw_year, bool) and float(raw_year) == year
        except (TypeError, ValueError):
            integral = False
        if not integral or not 1900 <= year <= 2200:
            _fail(path, where, f"fiscal_year is required and must be a year, "
                               f"got {raw_year!r}")
        where = f"annual {year}"
        if year in years:
            _fail(path, where, "duplicate fiscal_year")
        if years and year < years[-1]:
            _fail(path, where, f"annual entries must be listed oldest first -- "
                               f"{year} follows {years[-1]}")
        years.append(year)

        end = _as_date(item.get("period_end"), "period_end", index, year)
        if end is None:
            _fail(path, where,
                  "period_end is required. It is the date the year closed, and "
                  "a fiscal year does not have to end in the calendar year it "
                  "is named for -- so the year alone cannot say it")
        document = _as_text(item.get("document"))
        url = _as_text(item.get("url"))

        raw_figures = item.get("figures") or {}
        if not isinstance(raw_figures, Mapping):
            _fail(path, where, f"figures must be a mapping, got "
                               f"{type(raw_figures).__name__}")
        unknown = set(raw_figures) - FIGURE_KEYS
        if unknown:
            _fail(path, where,
                  f"unknown figure(s) {', '.join(sorted(unknown))}. Allowed: "
                  f"{', '.join(sorted(FIGURE_KEYS))}")
        figures = {
            name: _parse_figure(raw_figures.get(name), name, f"FY{year}", end,
                                path, where, document)
            for name in sorted(raw_figures)
        }
        _check_subtotal_form(figures, path, where)
        seen_fields.update(n for n, f in figures.items() if f.present)
        out.append(AnnualEntry(fiscal_year=year, period_end=end,
                               document=document, url=url, figures=figures))
    return tuple(out)


def _parse_interest_in_ocf(raw: Any, path: Path) -> "InterestClassification | None":
    """E34's `interest_in_ocf:` block, or None where the file omits it."""
    if raw is None:
        return None
    if not isinstance(raw, Mapping):
        _fail(path, "interest_in_ocf",
              f"expected a mapping with value/source/page, got "
              f"{type(raw).__name__}. E34: where a filer books its interest "
              f"is a fact READ FROM ITS CASH FLOW STATEMENT, so it carries a "
              f"source and a page like every other figure here")
    unknown = set(raw) - ALLOWED_INTEREST_KEYS
    if unknown:
        _fail(path, "interest_in_ocf",
              f"unknown key(s) {', '.join(sorted(unknown))}. Allowed: "
              f"{', '.join(sorted(ALLOWED_INTEREST_KEYS))}")
    value = raw.get("value")
    if not isinstance(value, bool):
        _fail(path, "interest_in_ocf",
              f"value must be yes or no, got {value!r}. There is no third "
              f"state: a filer that does not say is DATA MISSING, which is "
              f"what leaving the whole block out means")
    source = _as_text(raw.get("source"))
    page = _as_text(raw.get("page"))
    if not source or not page:
        _fail(path, "interest_in_ocf",
              "source and page are both required. IAS 7.31-34 lets a filer "
              "put interest paid in operating or in financing, and which it "
              "chose decides whether FCF0 is a flow to the firm or to equity "
              "(E34). A claim that large is not made without a page")
    interest_source = (_as_text(raw.get("interest_source"))
                       or INTEREST_SOURCE_CASH_FLOW).strip().lower()
    if interest_source not in VALID_INTEREST_SOURCES:
        _fail(path, "interest_in_ocf",
              f"interest_source must be one of "
              f"{'|'.join(VALID_INTEREST_SOURCES)}, got "
              f"{raw.get('interest_source')!r} (E34.1)")
    if interest_source != INTEREST_SOURCE_CASH_FLOW and not value:
        _fail(path, "interest_in_ocf",
              f"interest_source: {interest_source} with value: no. A proxy "
              f"add-back (E34.1, E61) is the ADD-BACK for a filer whose "
              f"operating cash flow bears its interest; a filer whose "
              f"operating cash flow bears none has nothing to add back, so "
              f"the key claims a treatment that cannot apply")
    return InterestClassification(value=value, source=source, page=page,
                                  interest_source=interest_source)


ALLOWED_LEASE_KEYS = frozenset({"value", "source", "page"})


def _parse_operating_leases_in_ocf(raw: Any, path: Path) -> "LeaseClassification | None":
    """E70's `operating_leases_in_ocf:` block, or None where the file omits it."""
    if raw is None:
        return None
    if not isinstance(raw, Mapping):
        _fail(path, "operating_leases_in_ocf",
              f"expected a mapping with value/source/page, got "
              f"{type(raw).__name__}. E70: whether a filer's operating cash "
              f"flow bears its operating lease payments is a fact about the "
              f"standard it reports under and its cash flow statement, so it "
              f"carries a source and a page like every other figure here")
    unknown = set(raw) - ALLOWED_LEASE_KEYS
    if unknown:
        _fail(path, "operating_leases_in_ocf",
              f"unknown key(s) {', '.join(sorted(unknown))}. Allowed: "
              f"{', '.join(sorted(ALLOWED_LEASE_KEYS))}")
    value = raw.get("value")
    if not isinstance(value, bool):
        _fail(path, "operating_leases_in_ocf",
              f"value must be yes or no, got {value!r}. There is no third "
              f"state: a file that does not say is DATA MISSING, which is "
              f"what leaving the whole block out means (E70)")
    source = _as_text(raw.get("source"))
    page = _as_text(raw.get("page"))
    if not source or not page:
        _fail(path, "operating_leases_in_ocf",
              "source and page are both required (E70): ASC 842-20-45-5(a) "
              "puts operating lease payments INSIDE operating cash flow and "
              "IFRS 16.50(b) puts the principal in financing -- which one a "
              "filer is under decides whether FCF0 adds a payment back, and "
              "a claim that large is not made without a page")
    return LeaseClassification(value=value, source=source, page=page)


def _parse_operating_asset_is_inventory(raw: Any, path: Path
                                        ) -> "InventoryOperatingAsset | None":
    """E123's `operating_asset_is_inventory:` block, or None where absent."""
    if raw is None:
        return None
    if not isinstance(raw, Mapping):
        _fail(path, "operating_asset_is_inventory",
              f"expected a mapping with value/source/page, got "
              f"{type(raw).__name__}. E123: whether the operating asset is "
              f"inventory whose purchase runs through operating cash flow is "
              f"a FACT about the accounts, so it carries a source and a page "
              f"like every other figure here")
    unknown = set(raw) - ALLOWED_LEASE_KEYS
    if unknown:
        _fail(path, "operating_asset_is_inventory",
              f"unknown key(s) {', '.join(sorted(unknown))}. Allowed: "
              f"{', '.join(sorted(ALLOWED_LEASE_KEYS))}")
    value = raw.get("value")
    if not isinstance(value, bool):
        _fail(path, "operating_asset_is_inventory",
              f"value must be yes or no, got {value!r}. There is no third "
              f"state: a file that does not say is an ordinary filer, which "
              f"is what leaving the whole block out means (E123)")
    source = _as_text(raw.get("source"))
    page = _as_text(raw.get("page"))
    if not source or not page:
        _fail(path, "operating_asset_is_inventory",
              "source and page are both required (E123): this declaration "
              "takes TWO Gate 3 limbs out of the count and rebases section "
              "4.4 for the name, and a claim that large is not made without "
              "the balance sheet and cash flow lines that carry it")
    return InventoryOperatingAsset(value=value, source=source, page=page)


def _parse_market(raw: Any, path: Path) -> tuple[dict[str, ManualFigure], date | None]:
    if raw is None:
        return {}, None
    if not isinstance(raw, Mapping):
        _fail(path, "market", f"expected a mapping, got {type(raw).__name__}")
    unknown = set(raw) - ALLOWED_MARKET_KEYS
    if unknown:
        _fail(path, "market", f"unknown key(s) {', '.join(sorted(unknown))}. "
                              f"Allowed: {', '.join(sorted(ALLOWED_MARKET_KEYS))}")
    as_of = _as_date(raw.get("as_of"), path, "market", "as_of")
    figures = {
        name: _parse_figure(raw.get(name), name, "", as_of, path, "market", None)
        for name in sorted(set(raw) & set(MARKET_FIELDS))
    }
    if any(f.present for f in figures.values()) and as_of is None:
        _fail(path, "market",
              "as_of is required once a market figure carries a value. An "
              "enterprise value is priced on a date; without it nothing can "
              "say how old the denominator of the earnings yield is")
    return figures, as_of


def _parse_unit(raw: Any, key: str, path: Path) -> str | None:
    """`money_unit` / `share_unit`: one of UNIT_SCALE, or None (unstated).

    Unstated is a legitimate state and loads -- the file may hold figures
    nobody has yet divided -- but a run record built from it is DATA
    MISSING on the per-share division until the owner declares the unit.
    A word that is not a unit fails the load: "million" is not "millions"
    and a guess at what was meant is a guess at a factor of a thousand.
    """
    text = _as_text(raw)
    if text is None:
        return None
    unit = text.strip().lower()
    if unit not in UNIT_SCALE:
        _fail(path, "file",
              f"{key} must be one of {'|'.join(VALID_UNITS)}, got {raw!r}. "
              f"The declaration is what a divisor reads, and a misspelt one "
              f"is not corrected -- it is refused, so that no figure is "
              f"scaled by a factor nobody wrote down")
    return unit


def parse_manual(document: Any, *, path: Path) -> ManualFile:
    """Validate a parsed YAML document into a ManualFile, or raise."""
    if document is None:
        _fail(path, "file", "is empty")
    if not isinstance(document, Mapping):
        _fail(path, "file", f"must be a mapping, got {type(document).__name__}")

    unknown = set(document) - ALLOWED_TOP_KEYS
    if unknown:
        _fail(path, "file", f"unknown key(s) {', '.join(sorted(unknown))}. "
                            f"Allowed: {', '.join(sorted(ALLOWED_TOP_KEYS))}")
    missing = REQUIRED_TOP_KEYS - set(document)
    if missing:
        _fail(path, "file", f"missing required key(s) {', '.join(sorted(missing))}")
    for key in sorted(REQUIRED_TOP_KEYS):
        if _as_text(document.get(key)) is None:
            _fail(path, "file", f"{key} must not be empty")

    origin = (_as_text(document.get("origin")) or ORIGIN).strip().lower()
    if origin not in VALID_ORIGINS:
        _fail(path, "file", f"origin must be one of {'|'.join(VALID_ORIGINS)}, "
                            f"got {document.get('origin')!r}")

    raw_cik = document.get("cik")
    cik = None
    if raw_cik is not None:
        try:
            cik = int(str(raw_cik).strip())
        except (TypeError, ValueError):
            _fail(path, "file",
                  f"cik must be a whole number, got {raw_cik!r}. It is the "
                  f"SEC Central Index Key and a guess at one fetches another "
                  f"company's filings with nothing to catch it")
        if cik <= 0:
            _fail(path, "file", f"cik must be positive, got {raw_cik!r}")
    money_unit = _parse_unit(document.get("money_unit"), "money_unit", path)
    share_unit = _parse_unit(document.get("share_unit"), "share_unit", path)

    frequency = _as_text(document.get("reporting_frequency")) or DEFAULT_REPORTING_FREQUENCY
    frequency = frequency.lower()
    if frequency not in VALID_REPORTING_FREQUENCIES:
        _fail(path, "file", f"reporting_frequency must be one of "
                            f"{'|'.join(VALID_REPORTING_FREQUENCIES)}, got "
                            f"{document.get('reporting_frequency')!r}")

    raw_periods = document.get("periods") or []
    if not isinstance(raw_periods, list):
        _fail(path, "file", "periods must be a list")

    periods: list[ManualPeriod] = []
    seen: list[str] = []
    for index, raw in enumerate(raw_periods):
        parsed = _parse_period(raw, index, path, frequency, seen)
        seen.append(parsed.period)
        periods.append(parsed)

    problem = overlap_problem(seen)
    if problem:
        _fail(path, "file", problem)

    bases = {p.period_basis for p in periods if p.period_basis is not None}
    if len(bases) > 1:
        _fail(path, "file",
              f"periods mix period_basis {sorted(bases)}. A fiscal Q4 and a "
              f"calendar Q4 are different three-month windows -- pick one basis "
              f"per ticker or ordering breaks")

    annual_fields: set[str] = set()
    annual = _parse_annual(document.get("annual"), path, annual_fields)

    market, market_as_of = _parse_market(document.get("market"), path)
    interest_in_ocf = _parse_interest_in_ocf(document.get("interest_in_ocf"), path)
    operating_leases_in_ocf = _parse_operating_leases_in_ocf(
        document.get("operating_leases_in_ocf"), path)
    operating_asset_is_inventory = _parse_operating_asset_is_inventory(
        document.get("operating_asset_is_inventory"), path)

    parsed_file = ManualFile(
        ticker=str(document["ticker"]).strip(),
        name=str(document["name"]).strip(),
        reporting_currency=(_as_text(document.get("reporting_currency")) or "").upper(),
        quote_currency=(_as_text(document.get("quote_currency")) or "").upper(),
        sector=_as_text(document.get("sector")) or "",
        reporting_frequency=frequency,
        path=path,
        origin=origin,
        periods=tuple(periods),
        annual=annual,
        market=market,
        market_as_of=market_as_of,
        interest_in_ocf=interest_in_ocf,
        operating_leases_in_ocf=operating_leases_in_ocf,
        operating_asset_is_inventory=operating_asset_is_inventory,
        money_unit=money_unit,
        cik=cik,
        share_unit=share_unit,
    )
    _check_currency(parsed_file)
    _check_units(parsed_file)
    _check_one_scale(parsed_file)
    return parsed_file


def load_manual(ticker: str, *, directory: Path = MANUAL_DIR) -> ManualFile:
    """Read and validate one ticker's file. Fails loudly, never silently."""
    path = Path(directory) / f"{ticker.strip().upper()}.yaml"
    if not path.exists():
        raise ManualError(
            f"no manual file at {path}. Copy {TEMPLATE_PATH} to {path} and fill "
            f"it in from the company's own reports. vss will not invent one."
        )
    try:
        document = yaml.safe_load(path.read_text(encoding="utf-8"))
    except yaml.YAMLError as exc:
        raise ManualError(f"{path} is not valid YAML: {exc}")
    parsed = parse_manual(document, path=path)
    if parsed.ticker.upper() != ticker.strip().upper():
        raise ManualError(
            f"{path} names ticker {parsed.ticker!r} but was loaded for "
            f"{ticker.strip().upper()!r}. The file name is the key; a mismatch "
            f"means one of the two is about another company"
        )
    return parsed


# --- the checks the SEC path is held to -----------------------------------


def _check_currency(parsed: ManualFile) -> None:
    """A figure whose currency nobody stated is not a figure.

    Reporting currency and quote currency are separate facts and are
    checked separately: Equinor's accounts are in USD and its shares trade
    in NOK, and the ranking key converts one into the other before it
    forms the earnings yield. Neither is demanded of a file that carries
    no figures -- that file is the empty template.
    """
    if any(holder.value(name) is not None
           for holder in (*parsed.periods, *parsed.annual)
           for name in FIGURE_KEYS):
        if not parsed.reporting_currency:
            _fail(parsed.path, "file",
                  "a period figure carries a value but reporting_currency is "
                  "not stated. Every figure in the periods below is an amount "
                  "in the currency THE ACCOUNTS are kept in, and an amount "
                  "without a currency cannot be compared with anything")
    if any(f.present for f in parsed.market.values()) and not parsed.quote_currency:
        _fail(parsed.path, "file",
              "a market figure carries a value but quote_currency is not "
              "stated. Enterprise value is priced in the currency the SHARE "
              "trades in, which is frequently not the one the accounts are "
              "kept in -- the ranking key converts between them")


def _check_units(parsed: ManualFile) -> None:
    """The unit contract, asked of every period by the watchlist's own code.

    `config.unit_problem` is imported rather than reimplemented so there is
    ONE definition of a valid unit in the project. It exempts `source:
    xbrl` from the operating-margin reconciliation, because a us-gaap tag
    already says which line the operating income is. A HAND-READ figure has
    exactly the ambiguity that exemption was carved out of -- NIKE's
    "Income before income taxes" of 1,416 recorded where EBIT was 1,392 --
    so the manual path is NOT given it, and the mapping below never sets a
    source key.
    """
    # The annual block obeys the same contract. A ratio is a fraction there
    # too, and an operating income entered beside a revenue is reconciled
    # there too -- E15 gave the block a home, not an exemption.
    for period in (*parsed.periods, *parsed.annual):
        # `unit_problem` speaks the WATCHLIST's field names, so the two
        # lines it reconciles are handed to it under those names. No
        # `source` key is set: that is what keeps the xbrl exemption off
        # this path, and it is deliberate rather than an omission.
        margin = period.figures.get("op_margin")
        fields = {
            "revenue": period.value("revenue"),
            "op_income": period.value("operating_income"),
            "op_margin": period.value("op_margin"),
            "revenue_yoy": period.value("revenue_yoy"),
            # E79.1 / E83: the printed precision and the explained cause.
            "op_margin_precision": margin.precision if margin else None,
            "op_margin_cause": margin.cause if margin else None,
        }
        problem = unit_problem(fields)
        if problem:
            where = (f"period {period.period}" if hasattr(period, "period")
                     else f"annual {period.fiscal_year}")
            _fail(parsed.path, where, problem)


def _check_one_scale(parsed: ManualFile) -> None:
    """One file's figures must be in ONE unit.

    Every period is internally consistent whichever scale it was read in,
    so the band check and the reconciliation both pass while the file is
    out by a factor of a thousand. Only a comparison ACROSS periods can
    see it. Same argument and same factor as `config._check_one_scale`.
    """
    # ACROSS BOTH BLOCKS. An annual revenue is roughly four times a
    # quarterly one, nowhere near the thousandfold bar, so including the
    # annual entries costs nothing and catches a year entered in whole
    # units beside quarters entered in millions.
    for key in SCALE_STABLE_FIELDS:
        seen = [(getattr(p, "period", None) or f"FY{getattr(p, 'fiscal_year', '')}",
                 abs(p.value(key)))
                for p in (*parsed.periods, *parsed.annual) if p.value(key)]
        if len(seen) < 2:
            continue
        low_period, low = min(seen, key=lambda pair: pair[1])
        high_period, high = max(seen, key=lambda pair: pair[1])
        if high / low < SCALE_JUMP_FACTOR:
            continue
        _fail(parsed.path, "file",
              f"{key} jumps by {high / low:,.0f}x between {low_period} "
              f"({low:,.0f}) and {high_period} ({high:,.0f}). That is a UNIT MIX, "
              f"not a business event: one report states millions where another "
              f"states whole units. Re-read the odd periods from one document in "
              f"one unit -- do not rescale a figure by hand.")


def staleness(parsed: ManualFile, *, as_of: date,
              max_report_age_days: int = MAX_REPORT_AGE_DAYS) -> tuple[str, str | None]:
    """(status, detail) on the same limit and in the same words as the fetch.

    STALE is not a load failure. The figures are there and they are right;
    they are judged too old to divide into a price from today -- the same
    shape as a stale close, and the same shape `fundamentals.fetch_one`
    gives a vendor record.
    """
    newest = parsed.newest_period_end
    if newest is None:
        return STATUS_OK, None
    age = (as_of - newest).days
    if age > max_report_age_days:
        return STATUS_STALE, (f"newest reported period {newest.isoformat()} is "
                              f"{age} days before {as_of.isoformat()}")
    return STATUS_OK, None


# --- the store record -----------------------------------------------------


def as_record(parsed: ManualFile, *, as_of: date) -> TickerFundamentals:
    """A manual file in the shape the store and the ranking key already read.

    The prize, and the reason the line names above are the store's own:
    `ranking.extract_inputs` touches a record through `latest()`, `value()`,
    `text()`, `status` and `error` and nothing else. Hand it one of these
    and the whole E6 key runs on a company that has no endpoint, with no
    change to `ranking.py` beyond carrying the origin through.

    Every figure is offered, VERIFIED or not. The ranking key is a
    different consumer from section 5 and was not asked to refuse; what it
    is given is the ORIGIN, so its output can say which path each row came
    from.
    """
    status, detail = staleness(parsed, as_of=as_of)

    fields: list[FieldValue] = []
    for name, store_name in TEXT_FIELDS.items():
        text = getattr(parsed, name) or None
        fields.append(FieldValue(parsed.ticker, store_name,
                                 FIELD_OK if text else FIELD_NO_DATA, text=text))
    for name, store_name in MARKET_FIELDS.items():
        figure = parsed.market.get(name)
        number = figure.value if figure and figure.present else None
        fields.append(FieldValue(parsed.ticker, store_name,
                                 FIELD_OK if number is not None else FIELD_NO_DATA,
                                 number=number))

    series: list[SeriesPoint] = []
    for period in parsed.periods:
        for name, (store_name, statement) in STORE_LINES.items():
            figure = period.figures.get(name)
            if figure is None or not figure.present:
                continue
            series.append(SeriesPoint(
                parsed.ticker, store_name, period.period_end, figure.value,
                statement,
                # The LABEL says how long the period is -- 2026-Q2 is three
                # months, 2025-FY is twelve -- so nothing has to be assumed
                # about a hand-entered or appendix-read figure. Only a FLOW
                # line has a length; a balance figure is an instant.
                period_months(period.period) if statement == "income" else None))

    return TickerFundamentals(
        ticker=parsed.ticker,
        status=status,
        attempts=0,
        requests=0,
        fields=tuple(fields),
        series=tuple(series),
        error=detail,
        newest_period=parsed.newest_period_end,
        origin=parsed.origin,
    )


# --- section 5's gate -----------------------------------------------------
#
# NOT a valuation. Section 5's three methods stay in the owner's hands and
# in the per-name workbook. This decides one thing: whether the figures
# they would be built on may be handed over at all.


#: The `reads` marker for a ratio that belongs to the ranking key rather
#: than to section 5. Matched by string in ONE place, so the exemption is
#: findable rather than implied by a comment.
RANKING_LEG = "ranking key"

#: The figures section 5 itself reads, taken from the schema's own `reads`
#: column rather than listed twice. What section 5 hands over is what its
#: staleness is measured on -- ranking.py's rule 5, for the same reason:
#: `newest_period` is the MAX over every stored row, so a period entry
#: carrying only a line no method touches would make an old file read fresh.
SECTION5_FIELDS: tuple[str, ...] = tuple(
    spec.name for spec in FIELDS if any(r.startswith("5.") for r in spec.reads)
)

#: E103 (2026-09-01): fields that are ONLY EVER COMPARED against a
#: valuation, never used to build one.
#:
#: **A BASIS FIGURE ENTERS A VALUATION; A REFERENCE FIGURE IS ONLY COMPARED
#: AGAINST ONE**, and the whole ruling turns on the asymmetry. A wrong basis
#: figure produces a WRONG VALUE nothing downstream can detect, which is why
#: E40 reads every one of them back by hand. A wrong reference figure
#: produces a FALSE BLINK: E101's detector says the two disagree, the owner
#: looks, and it turns out to be the comparator. **The cost is one look**,
#: and the cost of the alternative -- a comparator nobody enters -- is the
#: detector not existing, which is where E101 stood on the day it was built.
#:
#: So these may be FETCHED AUTOMATICALLY and entered UNVERIFIED, and they
#: carry `reads=("reference",)` rather than a `5.*` section, which is what
#: keeps them out of `SECTION5_FIELDS` and therefore out of `basis_reads`
#: and out of the E21 gate. **`reference_fields_in_basis` is the mechanical
#: fence** -- see it, and `section5_gate`'s refusal.
REFERENCE_FIELDS: frozenset[str] = frozenset({
    "free_cash_flow_reported", "net_debt_reported",
})


def reference_fields_in_basis() -> tuple[str, ...]:
    """Any E103 reference field that has been wired into a §5 basis.

    **THE FENCE, AND IT IS MECHANICAL RATHER THAN A MATTER OF CARE.** E103
    opens a door: two fields may be entered UNVERIFIED without a read-back,
    because nothing depends on them being right. The one thing that must not
    come through that door is an UNVERIFIED number inside a FAIR VALUE --
    which is precisely what E40 exists to prevent.
    So the moment a reference field acquires a `5.*` reader, this returns
    its name and `section5_gate` REFUSES, loudly, naming the field. It costs
    one set intersection per gate call and it cannot be forgotten.
    """
    return tuple(sorted(REFERENCE_FIELDS.intersection(SECTION5_FIELDS)))

#: Every ratio section 5 forms out of the accounts, and the legs it takes.
#: The table is the check: both legs of a ratio come from ONE period entry,
#: and a leg absent from that entry makes the ratio DATA MISSING. It is
#: never back-filled from the period next door, which is the same rule the
#: E6 quality leg is held to (ranking.py, rule 3).
#: E23: the capex legs are chosen AT THE BASIS, not fixed in this table --
#: `capex_legs` decides between the split pair and the single line. The
#: marker stands where those legs go, and is expanded before any leg is
#: resolved. It is a marker rather than a third entry in the table because
#: a ratio must not be listed twice under two spellings of one input.
CAPEX_LEGS = "capex:*"
SPLIT_CAPEX = ("capex_ppe", "capex_intangibles")
COMBINED_CAPEX = ("capex_combined",)

#: E34's marker, on the same terms as E23's. Which leg it expands to is a
#: fact about the FILER and not about the basis: `net_interest_paid` where
#: the filer's operating cash flow already bears its interest, nothing where
#: it does not, and the pseudo-leg below where the file has not said.
INTEREST_LEGS = "interest:*"
#: E117's flow marker (E70's before it): replaced by `lease_legs` -- by
#: nothing for a US GAAP filer, whose flow already bears the rent; by the
#: IFRS 16 filer's principal and lease interest, which FCF0 deducts; and by
#: `LEASE_UNCLASSIFIED` where the file does not say.
LEASE_LEGS = "leases:*"
#: E117's net-debt marker: the part of `lease_liabilities` that LEAVES net
#: debt. A US GAAP filer names it (`operating_lease_liabilities`); an IFRS 16
#: filer's whole lease liability leaves and needs no second field.
LEASE_EXCLUDED_LEGS = "leases-excluded:*"

#: NOT A FIELD. It stands in the leg list so a ratio whose classification is
#: unrecorded resolves to `input missing` with a name a reader can act on,
#: instead of quietly forming the wrong sum.
INTEREST_UNCLASSIFIED = "interest_in_ocf"
LEASE_UNCLASSIFIED = "operating_leases_in_ocf"

#: The RATIOS label of the flow section 5 discounts (E34).
FCF0_RATIO = "free cash flow, FCF0 (E34)"

#: E35's four legs plus E35.1's pension leg, less the optional asset. See
#: the RATIOS entry below for why `other_current_financial_assets` is not
#: among them.
NET_DEBT_LEGS = ("financial_liabilities_current",
                 "financial_liabilities_noncurrent",
                 "lease_liabilities",
                 "pension_deficit",
                 # E68 (2026-08-29): a LIABILITY leg, so required on the
                 # same terms as the pension deficit -- absent is DATA
                 # MISSING, and omitting it would understate net debt.
                 "asset_retirement_obligation",
                 # E81 (2026-08-30): the same terms again -- cash received
                 # against product still to be delivered is a claim on the
                 # company, and leaving it out prices the stream as free.
                 "prepaid_delivery_obligation",
                 "cash_and_equivalents")

RATIOS: tuple[tuple[str, tuple[str, ...], str], ...] = (
    ("operating margin", ("operating_income", "revenue"), "check / 5.1B"),
    ("free cash flow, basis 1", ("operating_cash_flow", CAPEX_LEGS), "5.1C"),
    # E34: THE FLOW SECTION 5 ACTUALLY DISCOUNTS. Basis 1 above keeps its
    # own meaning -- OCF minus capex, the figure the framework has always
    # called that -- and this is what the DCF is handed. They differ by the
    # interest add-back for a filer whose operating cash flow bears it.
    # E70: and the lease add-back, for a filer whose operating cash flow
    # bears its operating lease payments -- the lease is counted once, in
    # net debt, never also in the flow.
    (FCF0_RATIO,
     ("operating_cash_flow", CAPEX_LEGS, INTEREST_LEGS, LEASE_LEGS, "sbc"), "5.1C"),
    # E35: LEASES ARE IN NET DEBT, ALWAYS. `lease_liabilities` was NOT a
    # leg of this ratio, so the gate called net debt computable for a file
    # whose lease liability is DATA MISSING and threw A2 to N silently,
    # every time it printed the table. Under IFRS 16 the operating cash
    # flow of every filer EXCLUDES lease principal, so leaving the
    # liability out prices the premises as free after the contracted term
    # and OVERSTATES the equity -- Pandora by about 84 DKK a share.
    #
    # `other_current_financial_assets` is deliberately NOT a required leg,
    # and the asymmetry is the argument. Omitting a LIABILITY (leases)
    # raises the value: generous, so it must be required. Omitting an
    # ASSET lowers it: conservative, so it may be absent. It is subtracted
    # wherever the file carries it -- see `net_debt_on_basis`.
    ("net debt", NET_DEBT_LEGS + (LEASE_EXCLUDED_LEGS,), "5.1C"),
    ("net debt / EBITDA", NET_DEBT_LEGS + (LEASE_EXCLUDED_LEGS, "ebitda"), "5.3"),
    ("FCF conversion", ("free_cash_flow_reported", "net_income"), "4.3 / 5.2"),
    # REPORTED, NEVER REFUSED ON. The quality leg belongs to the ranking key,
    # which section 5 does not read and which was not asked to refuse. Gating
    # section 5 on it would refuse every bank and every property company
    # outright -- E6 exempts them because the ratio does not describe them --
    # for a leg no method touches. E43 (2026-08-26): the leg is EBIT / total
    # assets; `gross_profit` stays a store field the key no longer reads.
    ("operating profitability", ("operating_income", "total_assets"), RANKING_LEG),
)

#: The three states a ratio can be in. The last two are counted APART, the
#: same distinction ranking.py draws between QUALITY_MISSING and
#: QUALITY_MIXED_PERIODS: "the line is not there" and "we have both and they
#: do not belong together" are different facts about a company.
RATIO_OK = "computable"
RATIO_MISSING = "input missing"
RATIO_MIXED_PERIODS = "periods do not match"

#: E19/E20: the file HOLDS the figure and the basis cannot take it -- one
#: state, counted apart from an absent line and from an unknown length.
#: It has TWO WORDINGS and they are not interchangeable: a FLOW is twelve
#: months of another twelve months, and a STOCK has no length at all, so
#: its refusal names the two period ENDS and claims nothing more (E20).
#: The state is single on purpose: a second constant would make every
#: comparison a set test and let the next site miss one flavour silently.
QUALITY_BASIS_MISMATCH = "another twelve months"

#: E19: the file supplies no twelve-month window, so section 5 does not run.
REFUSE_NO_BASIS = "NO TWELVE-MONTH BASIS"

REFUSE_UNVERIFIED = "UNVERIFIED"
#: There are period entries and not one of them supplies a figure section 5
#: reads. A period whose every figure is null is not a period section 5 can
#: read, and `NO PERIODS` does not catch it: the list is not empty, the
#: entries are.
REFUSE_EMPTY_PERIODS = "NO FIGURES IN ANY PERIOD"
#: E25: the coverage denominator resolved to zero. EBIT / 0 is undefined,
#: and code that reads it as "very large" passes Gate 3 in silence.
REFUSE_ZERO_DENOMINATOR = "ZERO DENOMINATOR"
REFUSE_STALE = "STALE"
REFUSE_PRICED_STALE = "PRICED FIGURE STALE"
REFUSE_MIXED_PERIODS = "PERIODS DO NOT MATCH"
REFUSE_NO_PERIODS = "NO PERIODS"
REFUSE_UNIT_MIX = "UNIT MIX"
REFUSE_INTEREST_UNCLASSIFIED = "INTEREST UNCLASSIFIED"
#: E103: a REFERENCE figure has been wired into a §5 basis. Section 5 does
#: not run at all until it is unwired -- an UNVERIFIED number inside a fair
#: value is the one thing E40 exists to prevent, and E103's door is the only
#: way one could ever get there.
REFUSE_REFERENCE_IN_BASIS = "REFERENCE FIGURE IN A BASIS"
REFUSE_LEASES_UNCLASSIFIED = "LEASES UNCLASSIFIED"
REFUSE_NO_FCF0 = "FCF0 DATA MISSING"
#: E106 clause 4: the store carries BOUNDED legs and the gate cannot show
#: they are inside the tolerance -- either because they are not, or because
#: no pre-registered growth view exists to take 3.5% OF. **THE SECOND CASE
#: REFUSES TOO**, and that is the point: a bound that has not been measured
#: is not a small absence, it is an unmeasured one, and E106 clause 3's
#: whole distinction is between "at most X" and "we do not know".
REFUSE_TOLERANCE = "UNDETERMINED LEGS PAST E106"

#: A FLAG, NOT A REFUSAL. It never blocks section 5: a share
#: split is a real event and a file may legitimately hold one
#: year on each basis. What it must not do is pass unremarked.
FLAG_SHARE_BASIS_STEP = "SHARE BASIS STEP"

#: E106 clause 3: a leg struck with a stated CEILING rather than a figure.
#: A FLAG and never a refusal -- the value is struck COMPLETE -- and it is
#: printed wherever the figure appears, which is the ruling's own condition.
FLAG_BOUNDED = "UNDETERMINED, BOUNDED (E106)"

#: E108: a leg whose read-back the SENSITIVITY FLOOR waives. A FLAG and
#: never a refusal, and it is printed rather than dropped: the reader has
#: to be able to see which legs section 5 ran on without a second pair of
#: eyes, and how far each of them could move the answer.
FLAG_EXEMPT = "VERIFIED-EXEMPT (E108)"

#: The step that says a per-share figure or a count changed BASIS
#: rather than changed. Two, not a thousand: a 6-for-1 split is
#: six, and a company does not grow its share count sixfold in a
#: year without saying so. REVIEW-4 report B 7.1 / report C
#: golden case G9: `config/manual/DECK.yaml` holds FY2022
#: `diluted_eps` 16.26 and 27,789,000 shares -- filed before the
#: 6-for-1 split of 2024-09-13 -- beside FY2023 3.23 and
#: 160,111,000, a 5.8x step in a count inside one file, and
#: `SCALE_STABLE_FIELDS` does not reach either field.
SHARE_BASIS_STEP_FACTOR = 2.0


@dataclass(frozen=True)
class Refusal:
    kind: str
    subject: str
    detail: str


@dataclass(frozen=True)
class RatioState:
    name: str
    reads: str
    period: str | None
    state: str
    detail: str

    @property
    def computable(self) -> bool:
        return self.state == RATIO_OK

    @property
    def for_ranking_key(self) -> bool:
        return self.reads == RANKING_LEG


@dataclass(frozen=True)
class Section5Gate:
    ticker: str
    as_of: date
    #: The period section 5's figures are handed over from -- the newest that
    #: supplies any of them, NOT simply the newest entry in the file.
    period: str | None
    refusals: tuple[Refusal, ...]
    ratios: tuple[RatioState, ...]
    missing: tuple[str, ...]
    unverified: tuple[ManualFigure, ...]
    #: Fields section 5 takes from the `annual:` block because `periods:`
    #: does not supply them (E15).
    annual_used: tuple[str, ...] = ()
    #: field -> the period label that answers it instead. E15: `periods:`
    #: wins, and the annual entry is IGNORED rather than absent.
    shadowed: dict[str, str] = field(default_factory=dict)
    #: field -> (period label, months, value) for a period figure NOT used
    #: because it is SHORTER than the annual entry answering the same field
    #: (E17). Both are named; neither is preferred silently.
    displaced: dict[str, tuple[str, int, float]] = field(default_factory=dict)
    #: The one twelve-month window this run stands on (E19), or None when
    #: the file supplies none and section 5 does not run.
    basis: "Basis | None" = None
    #: field -> why the basis cannot take it, in that figure's own terms:
    #: another twelve months for a flow, another date for a stock (E20).
    mismatched: dict[str, str] = field(default_factory=dict)
    #: E21: the UNVERIFIED figures the basis READS. These refuse.
    blocking: tuple[ManualFigure, ...] = ()
    #: E21: the UNVERIFIED figures it does not read, each with why. Named
    #: in the report, and never a refusal.
    unread: tuple[tuple[ManualFigure, str], ...] = ()
    #: E31: filed PERIODS -- not figures, and not the same thing as
    #: `unread` above -- that sit inside a twelve-month window NEWER than
    #: the basis and that the basis did not read. Naming them is the
    #: condition E31 attaches to letting a half-yearly reporter stand on
    #: the year as filed. Never a refusal.
    newer_filed: tuple[ManualPeriod, ...] = ()
    #: NON-BLOCKING observations, printed and never counted as refusals.
    #: Today: a >= 2x step in a per-share figure or a share count, which is
    #: what a share split looks like inside one file.
    flags: tuple[Refusal, ...] = ()

    @property
    def refused(self) -> bool:
        return bool(self.refusals)


@dataclass(frozen=True)
class Basis:
    """The one twelve-month window a section 5 run stands on (E19)."""

    #: "as filed" -- a single twelve-month entry -- or "ttm", four summed.
    kind: str
    end: date
    #: The entries the window is built from, oldest first. One for a year
    #: as filed, four for a TTM.
    periods: tuple[ManualPeriod, ...] = ()
    #: Where the window came from when `periods:` could not supply one.
    annual: "AnnualEntry | None" = None

    @property
    def holders(self) -> tuple:
        return self.periods if self.periods else (
            (self.annual,) if self.annual is not None else ())

    @property
    def label(self) -> str:
        if self.annual is not None:
            return f"annual FY{self.annual.fiscal_year}"
        if self.kind == "ttm":
            return "TTM " + "+".join(p.period for p in self.periods)
        return self.periods[0].period


@dataclass(frozen=True)
class Resolved:
    """One field on the basis, or why it is not on it."""

    name: str
    value: float | None
    source: str
    #: The window END the value actually covers. Equal to the basis end
    #: except for an annual entry filling a gap from another year.
    end: date | None
    state: str = RATIO_OK
    detail: str = ""
    verified: bool = False
    #: For a summed flow, the entries that made it -- E19 limit 2.
    components: tuple[str, ...] = ()
    #: The stored figures this answer was built from. E21 gates on these:
    #: what the basis READS is what the run can be wrong about.
    figures: tuple["ManualFigure", ...] = ()


def section5_basis(parsed: ManualFile) -> Basis | None:
    """The newest twelve-month window this file can put section 5 on.

    `periods:` first and `annual:` only where `periods:` cannot supply one
    at all -- E17 as narrowed by E19. A twelve-month PERIOD entry is the
    year as filed; otherwise the four most recent CONSECUTIVE quarters.
    Contiguity is measured, not assumed: four rows with a hole in them are
    not a trailing twelve months.
    """
    twelve = [x for x in parsed.periods
              if period_months(x.period) == ANNUAL_MONTHS]
    if twelve:
        return Basis("as filed", twelve[-1].period_end, (twelve[-1],))

    quarters = [x for x in parsed.periods
                if period_months(x.period) == QUARTER_MONTHS]
    window = quarters[-TTM_QUARTERS:]
    if len(window) == TTM_QUARTERS and all(
            QUARTER_MIN_DAYS <= (b.period_end - a.period_end).days <= QUARTER_MAX_DAYS
            for a, b in zip(window, window[1:])):
        return Basis("ttm", window[-1].period_end, tuple(window))

    if parsed.annual:
        entry = parsed.annual[-1]
        return Basis("as filed", entry.period_end, (), entry)
    return None


def _one_year_before(day: date) -> date:
    """The same day one year earlier.

    29 FEBRUARY HAS NO COUNTERPART in a common year and `date.replace`
    raises rather than choosing one, so the leap day is stepped back to
    the 28th. That is a deliberate one-day widening of the window below
    and not a typo: the alternative is a crash on one date in four years.
    """
    try:
        return day.replace(year=day.year - 1)
    except ValueError:
        return day.replace(year=day.year - 1, day=28)


def newer_filed_periods(parsed: ManualFile,
                        basis: Basis | None) -> tuple[ManualPeriod, ...]:
    """Filed periods newer than the basis that the basis did not read (E31).

    E31 lets section 5 stand on the YEAR AS FILED for a half-yearly
    reporter and requires, in exchange, that the report name what the
    file holds and the basis passed over. This is the collection; the
    report prints it, and NOTHING HERE CHANGES WHICH BASIS IS CHOSEN.

    The window is the twelve months ending at the NEWEST filed period
    end, and it exists only where that end is newer than the basis end --
    otherwise the file holds nothing the basis has not reached. A period
    lies inside the window when its own end does; membership is decided
    on ENDS alone, because a fiscal filer's label says nothing reliable
    about the day its period opened.

    Read periods are excluded BY LABEL. The overlap guard makes a label
    unique within a file, and a `ttm` basis whose four quarters are read
    must not have them named back as though it had skipped them.
    """
    if basis is None or not parsed.periods:
        return ()
    newest = max(x.period_end for x in parsed.periods)
    if newest <= basis.end:
        return ()
    start = _one_year_before(newest)
    read = {x.period for x in basis.periods}
    return tuple(x for x in parsed.periods
                 if x.period not in read and start < x.period_end <= newest)


def resolve_on_basis(parsed: ManualFile, basis: Basis, name: str) -> Resolved:
    """One field, on the basis and nowhere else.

    FLOW -- summed over the window's entries, and only when EVERY entry
    supplies it: three quarters of four is not a year, and the missing one
    is not zero. STOCK -- taken at the window's END. A STATED RATIO is
    usable only where the issuer struck it on this very window.

    `annual:` fills what `periods:` cannot, per E17 as narrowed -- but ONLY
    where its own period end IS the basis end (E20). An annual figure from
    another year is twelve months of a DIFFERENT twelve months, which is
    B18's first measurement, and it is NOT MEANINGFUL rather than a fill.
    E20 settled that: a flow belongs to the window it was earned in, and
    borrowing one across six months relocates the error E19 removed.
    """
    def cite(figures, value, source, end, components):
        return Resolved(name, value, source, end, RATIO_OK, "",
                        all(f.verified for f in figures), tuple(components),
                        tuple(figures))

    on_quarters = False
    if basis.periods:
        if name in STOCK_FIELDS or name in STATED_RATIO_FIELDS:
            newest = basis.periods[-1]
            figure = newest.figures.get(name)
            if figure is not None and figure.present:
                return cite([figure], figure.value, newest.period,
                            newest.period_end, (newest.period,))
        elif name in NEVER_SUMMED:
            # B27 / E41: a weighted average is a WINDOW figure and four
            # quarterly averages are not the window's. A twelve-month
            # period entry answers with its own; a TTM falls through to
            # the annual block, and says why if nothing is there.
            if basis.kind != "ttm":
                figure = basis.periods[0].figures.get(name)
                if figure is not None and figure.present:
                    return cite([figure], figure.value, basis.periods[0].period,
                                basis.end, (basis.periods[0].period,))
            on_quarters = any(x.figures.get(name) is not None
                              and x.figures[name].present
                              for x in basis.periods)
        else:
            got = [x.figures.get(name) for x in basis.periods]
            if all(f is not None and f.present for f in got):
                labels = [x.period for x in basis.periods]
                source = basis.label if basis.kind == "ttm" else labels[0]
                return cite(got, sum(f.value for f in got), source,
                            basis.end, labels)

    # NEWEST FIRST, and a mismatched end does not END the search: under E20
    # the question is which entry CLOSES ON the basis end, not which entry
    # happens to be newest. An FY that ends elsewhere is refused only when
    # no entry in the block ends where the basis does.
    off_basis = None
    for entry in reversed(parsed.annual):
        figure = entry.figures.get(name)
        if figure is None or not figure.present:
            continue
        if entry.period_end == basis.end:
            return cite([figure], figure.value, f"annual FY{entry.fiscal_year}",
                        entry.period_end, (f"FY{entry.fiscal_year}",))
        # E41: an ANNUAL-ONLY field, on a TTM basis, from the newest annual
        # entry whose year-end falls INSIDE the window. The departure from
        # E20 is carried in `end`, which the record prints as its own date.
        if (name in ANNUAL_ONLY_FIELDS and basis.kind == "ttm"
                and _one_year_before(basis.end) < entry.period_end < basis.end):
            return cite([figure], figure.value,
                        f"annual FY{entry.fiscal_year} (E41: annual-only, "
                        f"year-end {entry.period_end.isoformat()} inside the "
                        f"window)", entry.period_end, (f"FY{entry.fiscal_year}",))
        off_basis = off_basis if off_basis is not None else entry
    if off_basis is not None:
        return Resolved(name, None, "", off_basis.period_end,
                        QUALITY_BASIS_MISMATCH,
                        off_basis_detail(name, off_basis, basis))
    if on_quarters:
        return Resolved(name, None, "", None, RATIO_MISSING,
                        f"{name} is on the quarters as quarterly averages, "
                        f"and a window's average is NOT their sum (B27, E41); "
                        f"no annual entry with a year-end inside the window "
                        f"supplies it")

    return Resolved(name, None, "", None, RATIO_MISSING,
                    f"{name} is not on the basis")


def off_basis_detail(name: str, entry: "AnnualEntry", basis: Basis) -> str:
    """Why this figure is not on the basis, in the terms the figure has.

    A FLOW is twelve months of ANOTHER twelve months -- two windows, and
    the sentence may say so. A STOCK IS NOT: it is a balance on a date and
    has no length whatever, so saying it covers another twelve months
    claims a property it cannot have -- B18's fourth measurement, in the
    prose rather than in the arithmetic (E20). The stock case names the
    two ENDS and stops there. A STATED RATIO keeps the flow wording: the
    issuer struck it over a twelve-month denominator and a ratio from
    another year IS another year's ratio.
    """
    where = f"annual FY{entry.fiscal_year}"
    if name in STOCK_FIELDS:
        return (f"{where} states it at {entry.period_end.isoformat()} and the "
                f"basis ends {basis.end.isoformat()}. A stock is taken at the "
                f"window's END (E19) and this is another date -- not a shorter "
                f"or longer period, a different one, and nothing here moves a "
                f"balance from one date to another.")
    return (f"{where} covers the twelve months to "
            f"{entry.period_end.isoformat()}; the basis ends "
            f"{basis.end.isoformat()}. Twelve months of a DIFFERENT twelve "
            f"months is not the same figure, and nothing here re-bases it.")


def capex_legs(parsed: ManualFile, basis: Basis) -> tuple[tuple[str, ...], str]:
    """Which capex the basis supplies: the split pair, or the one line (E23).

    THE SPLIT WINS WHERE IT EXISTS. An issuer that prints both lines is
    telling you which spend was which, and a combined figure entered beside
    them would be the same money said twice. So: both split legs resolve at
    the basis -> the pair; otherwise the combined line, if the basis has it.

    NEVER A MIX. One split leg plus the combined line is not a sum -- it is
    one line added to a total that already contains it -- so a lone split
    leg is not used at all, and the report says it was not.

    Returns the legs and one sentence naming which, for the report to
    carry every time it uses either.
    """
    have = {name: resolve_on_basis(parsed, basis, name).value is not None
            for name in SPLIT_CAPEX + COMBINED_CAPEX}
    if have["capex_ppe"] and have["capex_intangibles"]:
        why = "split: capex_ppe + capex_intangibles, as the accounts print them"
        if have["capex_combined"]:
            why += (" -- capex_combined is ALSO entered and is NOT used (E23): "
                    "where the issuer prints the split, the split wins")
        return SPLIT_CAPEX, why
    if have["capex_combined"]:
        lone = [n for n in SPLIT_CAPEX if have[n]]
        why = "combined: capex_combined, the one line the issuer prints"
        if lone:
            why += (f" -- {', '.join(lone)} is entered without its pair and is "
                    f"NOT added to it (E23): that would be one line added to a "
                    f"total that already contains it")
        return COMBINED_CAPEX, why
    absent = "neither the split pair nor capex_combined is on the basis"
    return SPLIT_CAPEX, absent


def interest_legs(parsed: ManualFile) -> tuple[str, ...]:
    """E34's leg: what FCF0 adds back, given where this filer books interest.

    E34.1: for a `yes` filer whose file says `interest_source:
    income_statement_net`, the leg is `net_finance_costs` -- the income
    statement's net, an accrual proxy -- and NOT `net_interest_paid`, which
    such a filer can never form because it states no interest received.

    E61: for a `yes` filer whose file says `interest_source:
    interest_expense_only` -- a US filer that tags gross interest expense
    but never the net -- the leg is `finance_costs_period` alone, a
    bounded, one-sided proxy (interest income is never negative, so the
    gross figure can only overstate FCF0, never understate it).
    """
    if parsed.interest_in_ocf is None:
        return (INTEREST_UNCLASSIFIED,)
    if not parsed.interest_in_ocf.value:
        return ()
    if parsed.interest_in_ocf.accrual_proxy:
        return ("net_finance_costs",)
    if parsed.interest_in_ocf.interest_expense_only_proxy:
        return ("finance_costs_period",)
    if parsed.interest_in_ocf.cash_paid_only_proxy:
        # E115: the stated cash figure alone, one-sided like E61's.
        return ("finance_costs_paid",)
    return ("net_interest_paid",)


def lease_legs(parsed: ManualFile) -> tuple[str, ...]:
    """E117's legs: what FCF0 deducts so that it bears the whole rent.

    `yes` (a US GAAP filer, ASC 842): NOTHING -- its operating cash flow
    already bears the operating lease payments, and E70's add-back is
    reversed. `no` (an IFRS 16 filer): the principal in financing AND the
    lease interest, both DEDUCTED -- the total lease cash outflow, charged
    once whatever the interest classification. Not recorded:
    `LEASE_UNCLASSIFIED`, which is DATA MISSING for FCF0 and never `no`.

    Until 2026-09-19 (E70) the US filer's payment was ADDED BACK and the
    IFRS filer's flow was left rent-free; a record struck then replays that
    way (`runrecord.LeaseTreatment.rule`).
    """
    if parsed.operating_leases_in_ocf is None:
        return (LEASE_UNCLASSIFIED,)
    if not parsed.operating_leases_in_ocf.value:
        return ("lease_payments_capital", "lease_interest_paid")
    return ()


def lease_excluded_legs(parsed: ManualFile) -> tuple[str, ...]:
    """E117's net-debt leg: the field naming what leaves net debt, if any.

    A US GAAP filer (`yes`): `operating_lease_liabilities` -- the finance
    lease part of `lease_liabilities` stays in (E117 clause 3). An IFRS 16
    filer (`no`) or an undeclared file: nothing to read -- the IFRS
    liability leaves whole, and an undeclared file is refused elsewhere.
    """
    lease = parsed.operating_leases_in_ocf
    if lease is not None and lease.value:
        return ("operating_lease_liabilities",)
    return ()


def lease_in_net_debt(parsed: ManualFile, lease_liabilities: float,
                      operating: float | None) -> tuple[float | None, str]:
    """E117: the lease liability that STAYS in net debt, and the sentence.

    US GAAP: `lease_liabilities` less the operating part, which leaves --
    None where the operating part is not on the basis. IFRS 16: zero, the
    whole liability leaves. Undeclared: the whole liability, E70's way; the
    §5 gate refuses the file on `LEASE_UNCLASSIFIED` regardless.
    """
    lease = parsed.operating_leases_in_ocf
    if lease is None:
        return lease_liabilities, (f"leases {lease_liabilities:,.0f} (lease "
                                   f"treatment NOT DECLARED: in, E70's way)")
    if not lease.value:
        return 0.0, (f"leases 0 -- the IFRS 16 liability "
                     f"{lease_liabilities:,.0f} LEAVES net debt whole (E117: "
                     f"its cash is in the flow; one lessee model, no split)")
    if operating is None:
        return None, ""
    kept = lease_liabilities - operating
    return kept, (f"finance leases {kept:,.0f} (E117: the operating lease "
                  f"liability {operating:,.0f} LEAVES net debt, its rent being "
                  f"in the flow; finance leases stay)")


def expand_legs(parsed: ManualFile, basis: "Basis | None",
                legs: tuple[str, ...]) -> tuple[str, ...]:
    """The ratio's legs with E23's, E34's and E70's markers replaced by answers."""
    if (CAPEX_LEGS not in legs and INTEREST_LEGS not in legs
            and LEASE_LEGS not in legs and LEASE_EXCLUDED_LEGS not in legs):
        return legs
    chosen = capex_legs(parsed, basis)[0] if basis is not None else SPLIT_CAPEX
    interest = interest_legs(parsed)
    leases = lease_legs(parsed)
    out: list[str] = []
    for leg in legs:
        if leg == CAPEX_LEGS:
            out.extend(chosen)
        elif leg == INTEREST_LEGS:
            out.extend(interest)
        elif leg == LEASE_LEGS:
            out.extend(leases)
        elif leg == LEASE_EXCLUDED_LEGS:
            out.extend(lease_excluded_legs(parsed))
        else:
            out.append(leg)
    return tuple(out)


#: FRAMEWORK-EDITS E60. Declared `5.1C` (FieldSpec, above) but read by NO
#: live code path, for ANY file -- confirmed by search, not by inspection:
#: neither name is a leg of any RATIOS entry, a `capex_legs` or
#: `interest_legs` choice, a parameter of `free_cash_flow_zero`, or a
#: direct read inside `net_debt_on_basis` / `share_count_on_basis`.
#: `income_tax_paid` is STILL read by the scale gate
#: (`SECTION5_SCALE_FIELDS`, a different refusal -- REFUSE_UNIT_MIX): its
#: role INSIDE FCF0 was simply never wired. A field no method reads does
#: not block section 5 (E60) -- both stay UNVERIFIED on the figure and
#: NAMED in the run record, but neither refuses.
NEVER_A_SECTION5_LEG: frozenset[str] = frozenset(
    {"income_tax_paid", "proceeds_from_disposals_ppe"})

#: FRAMEWORK-EDITS E60. The interest marker's six declared fields
#: (FieldSpec, above) -- but only some are read for a given file, and
#: which is chosen dynamically (E34), not fixed. See `interest_read_names`.
INTEREST_MARKER_FIELDS: frozenset[str] = frozenset(
    {"net_finance_costs", "finance_costs_period", "finance_income_period",
     "net_interest_paid", "finance_costs_paid", "finance_income_received"})


def interest_read_names(parsed: ManualFile) -> frozenset[str]:
    """FRAMEWORK-EDITS E60: which of `INTEREST_MARKER_FIELDS` this file
    actually reads.

    `interest_legs` (E34) picks ONE shape for FCF0's interest add-back,
    filer by filer -- `net_interest_paid` off the cash flow statement,
    `net_finance_costs` as an accrual proxy (E34.1), or
    `finance_costs_period` alone as a bounded, one-sided proxy (E61) --
    and the OTHER shapes' own E18 operands are not something a run can be
    wrong about: a filer whose operating cash flow does not bear interest
    at all (`interest_in_ocf: no`) never forms `net_interest_paid`, and
    `finance_costs_paid` / `finance_income_received` are its operands and
    nothing else's.

    `net_finance_costs` and ITS OWN operands (`finance_costs_period`,
    `finance_income_period`) are read REGARDLESS of which shape FCF0
    chose, or whether interest is classified at all: E25's zero-coverage-
    denominator gate reads `net_finance_costs` directly, outside FCF0
    entirely (`COVERAGE_DENOMINATOR`, this module), and E61's own leg IS
    `finance_costs_period`, already in this base set for that reason.
    """
    names = {"net_finance_costs", "finance_costs_period", "finance_income_period"}
    if "net_interest_paid" in interest_legs(parsed):
        names |= {"net_interest_paid", "finance_costs_paid",
                  "finance_income_received"}
    return frozenset(names)


def unread_by_e60(parsed: ManualFile) -> frozenset[str]:
    """The `SECTION5_FIELDS` names E60 excludes from the read set for THIS
    file -- the two dead fields, always, plus whichever half of the
    interest marker `interest_read_names` did not choose."""
    return NEVER_A_SECTION5_LEG | (
        INTEREST_MARKER_FIELDS - interest_read_names(parsed))


def named_absences(parsed: ManualFile, name: str) -> tuple[ManualFigure, ...]:
    """E82: the figures entered for ``name`` with NO value and a page -- the
    reader's statement of which printed line was refused and why."""
    return tuple(f for f in parsed.all_figures()
                 if f.name == name and not f.present and f.page)


def basis_reads(parsed: ManualFile, basis: Basis) -> tuple[ManualFigure, ...]:
    """Every stored figure this basis actually hands to section 5 (E21, E60).

    Derived from `resolve_on_basis` rather than restated: whatever the
    resolver takes -- four quarters of a flow, the newest quarter of a
    stock, an annual entry filling a gap at the basis end -- is exactly
    what a run can be wrong about. A figure the resolver never touches
    cannot change a number section 5 produces.

    E60 NARROWS `SECTION5_FIELDS`' static declaration by `unread_by_e60`:
    the refusal table is built from FieldSpec.reads alone, which is
    unconditional, while the legs a ratio actually builds are chosen
    dynamically. Where the two disagree, the arithmetic governs -- the
    read set follows what THIS file's chain actually builds, not the
    schema's blanket claim.

    MARKET FIGURES ARE INCLUDED. They belong to a date rather than to the
    window, so no basis "reads" them in the resolver's sense, and section 5
    divides them into its own results all the same.
    """
    excluded = unread_by_e60(parsed)
    seen: dict[tuple[str, str], ManualFigure] = {}
    for name in SECTION5_FIELDS:
        if name in excluded:
            continue
        for figure in resolve_on_basis(parsed, basis, name).figures:
            seen[(figure.period, figure.name)] = figure
    # E91 (2026-08-30): the divisor may stand on figures resolve_on_basis
    # does not surface -- the four per-quarter diluted counts the coded
    # day-weighted average reads. The read set follows what the chain
    # actually builds (this function's own rule), so the divisor's operands
    # are added here; under E38 / E88 they coincide with the resolver's.
    for figure in share_divisor_on_basis(parsed, basis).figures:
        seen[(figure.period, figure.name)] = figure
    for figure in parsed.market.values():
        if figure.present:
            seen[(figure.period, figure.name)] = figure
    return tuple(seen.values())


def basis_bounds(parsed: ManualFile,
                 basis: "Basis | None") -> tuple[ManualFigure, ...]:
    """Every E106 BOUND the basis window carries, on a section 5 field.

    A bound is not a value, so `basis_reads` -- which follows what
    `resolve_on_basis` hands over -- never surfaces one. This walks the
    window's own holders instead, which is the only place a bound can sit:
    a bound on a period OUTSIDE the window bounds nothing this run reads.

    ONE BOUND PER FIELD, and where a TTM's quarters each carry one they are
    SUMMED -- the window's uncertainty is the sum of its quarters', the same
    way the window's flow is.
    """
    if basis is None:
        return ()
    # E117 (2026-09-19): a bound on a leg this file's valuation NO LONGER
    # READS bounds nothing. AOS's ceiling on `operating_lease_payments` was
    # E70's add-back; under E117 no US filer reads that leg, and charging
    # the tolerance for it would refuse a record on an uncertainty it does
    # not have.
    unread = set(non_valuation_fields(parsed))
    # E120: a lease interest STANDING IN drops the E106 bound it replaces
    if lease_interest_stand_in(parsed, basis) is not None:
        unread.add("lease_interest_paid")
    totals: dict[str, list[ManualFigure]] = {}
    for holder in basis.holders:
        for figure in holder.figures.values():
            if (figure.bounded and figure.name in SECTION5_FIELDS
                    and figure.name not in unread):
                totals.setdefault(figure.name, []).append(figure)
    out: list[ManualFigure] = []
    for name, figures in totals.items():
        if len(figures) == 1:
            out.append(figures[0])
            continue
        first = figures[0]
        directions = {f.bound_direction or BOUND_REDUCES for f in figures}
        out.append(replace(
            first,
            bound=sum(abs(f.bound) for f in figures),
            bound_direction=(directions.pop() if len(directions) == 1
                             else BOUND_EITHER),
            page="; ".join(f"{f.period}: {f.page}" for f in figures)))
    return tuple(sorted(out, key=lambda f: f.name))


def unread_reason(parsed: ManualFile, basis: Basis, figure: ManualFigure) -> str:
    """Why this basis does not read that figure -- measured, not guessed."""
    if figure.name in unread_by_e60(parsed):
        spec = FIELDS_BY_NAME.get(figure.name)
        reads = ", ".join(spec.reads) if spec else "nothing in section 5"
        if figure.name in NEVER_A_SECTION5_LEG:
            return (f"section 5 does not read `{figure.name}` on this file: "
                    f"it is DECLARED {reads}, but no live code path ever "
                    f"resolves it -- not a leg of any ratio and not a "
                    f"parameter of FCF0 (FRAMEWORK-EDITS E60)")
        classification = parsed.interest_in_ocf
        if classification is None:
            shape = "`interest_in_ocf` is not recorded on this file"
        elif not classification.value:
            shape = ("`interest_in_ocf: no` -- operating cash flow is "
                    "already pre-interest, and FCF0 adds nothing back")
        elif classification.accrual_proxy:
            shape = ("`interest_in_ocf: yes`, accrual proxy (E34.1) -- FCF0 "
                    "adds back `net_finance_costs` instead")
        elif classification.interest_expense_only_proxy:
            shape = ("`interest_in_ocf: yes`, interest-expense-only proxy "
                    "(E61) -- FCF0 adds back `finance_costs_period` instead")
        elif classification.cash_paid_only_proxy:
            shape = ("`interest_in_ocf: yes`, cash-paid-only proxy (E115) -- "
                    "FCF0 adds back `finance_costs_paid` instead")
        else:
            shape = ("`interest_in_ocf: yes` off the cash flow statement -- "
                    "FCF0 adds back `net_interest_paid` instead")
        return (f"section 5 does not read `{figure.name}` on this file: it "
                f"is DECLARED {reads}, but {shape} (FRAMEWORK-EDITS E34, "
                f"E60)")
    if figure.name not in SECTION5_FIELDS:
        spec = FIELDS_BY_NAME.get(figure.name)
        reads = ", ".join(spec.reads) if spec else "nothing in section 5"
        return (f"section 5 does not read `{figure.name}` at all: it is read "
                f"by {reads}, and no method of section 5 touches it")
    if figure.period not in {p.period for p in basis.periods}:
        return (f"`{figure.period}` is not in the basis window "
                f"{basis.label}, so nothing section 5 produces stands on it")
    return (f"the basis takes `{figure.name}` at the window's END "
            f"({basis.periods[-1].period}) and not from `{figure.period}`")


def subtracted_on_basis(parsed: ManualFile, basis: "Basis | None",
                        name: str) -> float | None:
    """A net E18 forms out of two stated operands, on this basis, or None."""
    if basis is None or name not in SUBTRACTED_FIELDS:
        return None
    rule = next(r for r in SUBTRACTIONS if r.net == name)
    got = parsed.basis_subtraction(basis, rule)
    return None if got is None else got[0]


def resolve_or_subtract(parsed: ManualFile, basis: "Basis | None",
                        name: str) -> float | None:
    """The figure the basis supplies for ``name``, entered or subtracted."""
    if basis is None:
        return None
    direct = resolve_on_basis(parsed, basis, name).value
    if direct is not None:
        return direct
    return subtracted_on_basis(parsed, basis, name)


DIVISOR_WEIGHTED = "weighted_average"
#: E75.1: the two period-end kinds, never confused -- a stated diluted count
#: at the window end, or the basic count where only that is stated.
DIVISOR_PERIOD_END_DILUTED = "period_end_diluted"
DIVISOR_PERIOD_END_BASIC = "period_end_basic"
#: E91 (2026-08-30): the coded day-weighted average of four stated
#: per-quarter diluted counts -- the window's own average.
DIVISOR_WINDOW_DAY_WEIGHTED = "window_day_weighted"
DIVISOR_KINDS = (DIVISOR_WEIGHTED, DIVISOR_PERIOD_END_DILUTED,
                 DIVISOR_PERIOD_END_BASIC, DIVISOR_WINDOW_DAY_WEIGHTED)
DILUTED_SHARES = "shares_diluted_period_end"


@dataclass(frozen=True)
class ShareDivisor:
    """E38 / E41 / E75: the count section 5 divides by, and which kind it is.

    `divisor_basis` is `weighted_average` (E38's window average, or E41's
    annual average declared on its own date), `period_end_diluted` (E75.1:
    the DILUTED count the issuer states at the window end, where no window
    average is stated) or `period_end_basic` (E75: the basic count at the
    window end, where only that is stated). None where no count at all
    serves.
    """

    count: float | None
    divisor_basis: str | None
    as_of: date | None
    why: str
    #: E75: the E41 annual average the period-end count replaced, and the
    #: drift (count - prior) / prior, so the record can print it.
    prior_average: float | None = None
    drift: float | None = None
    figures: tuple[ManualFigure, ...] = ()
    provenance: str = ""


def share_divisor_on_basis(parsed: ManualFile,
                           basis: "Basis | None") -> ShareDivisor:
    """The divisor in E88's order (2026-08-30; E75 / E75.1 reversed).

    1. A weighted-average DILUTED count stated for the window itself --
       a twelve-month period entry, or an annual entry closing on the
       basis end -- is the divisor (E38, unchanged).
    2. E91 (2026-08-30): where the issuer states a per-quarter
       weighted-average DILUTED count for all four basis quarters
       (calendar quarters), the divisor is the coded day-weighted average
       of the four stated figures -- the window's own average, dates
       agreeing, E86's operand pattern.
    3. Otherwise the MOST RECENT ANNUAL weighted-average diluted count is
       the divisor under E41's annual-only rule, declared on its own date,
       and the basis mismatch -- an annual average dividing R12M flows --
       is flagged in the why the run record prints. A count at the window
       end -- stated diluted or basic, or E16 / E80's issued-less-treasury
       pair -- stays MEMO per E38 and is NEVER promoted: the point-in-time
       pair gives fewer shares and a higher fair value, and promoting it
       would relax a rule in the direction that flatters the number (E88).
    4. Otherwise DATA MISSING. `shares_point_in_time` is a MEMO and is
       never the divisor (E38).

    Records struck under E75 / E75.1 remain complete as struck; their
    `divisor_basis` labels stay readable on replay (`from_dict`).
    """
    if basis is None:
        return ShareDivisor(None, None, None,
                            "the file supplies no twelve-month basis")
    resolved = resolve_on_basis(parsed, basis, "diluted_weighted_average_shares")
    memo = resolve_on_basis(parsed, basis, "shares_point_in_time").value
    aside = ("" if memo is None else
             f"; `shares_point_in_time` {memo:,.0f} is on the file as a MEMO "
             f"and is NOT the divisor (E38)")
    # 1. E38: the window's own weighted average.
    if resolved.value is not None and (resolved.end is None
                                       or resolved.end == basis.end):
        return ShareDivisor(
            resolved.value, DIVISOR_WEIGHTED, basis.end,
            f"weighted-average DILUTED count for {basis.label}, the same "
            f"window as the flows (E38){aside}",
            figures=tuple(resolved.figures),
            provenance="; ".join(f.page for f in resolved.figures if f.page))
    # 1.5 E91 (2026-08-30): where the issuer states a per-quarter
    # weighted-average DILUTED count for ALL FOUR basis quarters, the
    # divisor is the coded DAY-WEIGHTED average of the four stated
    # figures -- E86's pattern: stated operands, computed result, each
    # with its own page reference. Supersedes E88's annual fall-back for
    # such issuers. Calendar quarters only: a 4-4-5 filer's bounds are
    # not month arithmetic, and E91 does not guess them.
    if (basis.kind == "ttm" and len(basis.periods) == 4
            and all(p.period_basis == "calendar"
                    and p.period_end.month in (3, 6, 9, 12)
                    for p in basis.periods)):
        quarterly = [p.figures.get("diluted_weighted_average_shares")
                     for p in basis.periods]
        if all(f is not None and f.present for f in quarterly):
            weights = [
                (p.period_end
                 - date(p.period_end.year, p.period_end.month - 2, 1)).days + 1
                for p in basis.periods]
            total = sum(weights)
            count = sum(f.value * d
                        for f, d in zip(quarterly, weights)) / total
            operands = "; ".join(
                f"{p.period} {f.value:,.0f} x {d}d"
                for p, f, d in zip(basis.periods, quarterly, weights))
            return ShareDivisor(
                count, DIVISOR_WINDOW_DAY_WEIGHTED, basis.end,
                f"E91: the coded DAY-WEIGHTED average of the four stated "
                f"per-quarter diluted counts for {basis.label} -- "
                f"({operands}) / {total}d = {count:,.0f}. The window's own "
                f"average, so the dates agree; stated operands, the "
                f"arithmetic the code's (E86's pattern), superseding E88's "
                f"annual fall-back for this issuer{aside}",
                figures=tuple(quarterly),
                provenance="; ".join(f.page for f in quarterly if f.page))
    # 2. E88 (2026-08-30): where no window average exists, E41's ANNUAL
    # average is the divisor and the record flags the basis mismatch -- an
    # annual average dividing R12M flows. A count at the window end,
    # diluted or basic or E80's pair, is NEVER promoted (E75 / E75.1
    # reversed); where one is on the file it is named here as memo.
    end_memo = ""
    diluted = resolve_on_basis(parsed, basis, DILUTED_SHARES)
    net = resolve_on_basis(parsed, basis, NET_SHARES)
    if diluted.value is not None:
        end_memo = (f"; the DILUTED count stated at the window end, "
                    f"{diluted.value:,.0f}, stays MEMO -- never promoted (E88)")
    elif net.value is not None:
        end_memo = (f"; the count outstanding at the window end, "
                    f"{net.value:,.0f}, stays MEMO -- never promoted (E88)")
    else:
        got = parsed.basis_subtraction(basis, SUBTRACTIONS[0])
        if got is not None:
            end_memo = (f"; E16 / E80's issued-less-treasury pair at the "
                        f"window end, {got[0]:,.0f}, stays MEMO -- never "
                        f"promoted (E88)")
    if resolved.value is not None:
        return ShareDivisor(
            resolved.value, DIVISOR_WEIGHTED, resolved.end,
            f"weighted-average DILUTED count for {resolved.source}, NOT the "
            f"flows' own window {basis.label} -- E88: an ANNUAL average "
            f"divides twelve months of flows ending {basis.end.isoformat()}, "
            f"the basis mismatch flagged, taken under E41's annual-only rule "
            f"because no window average exists and a window-end count is "
            f"never promoted{end_memo}{aside}",
            figures=tuple(resolved.figures),
            provenance="; ".join(f.page for f in resolved.figures if f.page))
    # 3. DATA MISSING -- E88 admits no window-end substitute.
    return ShareDivisor(
        None, None, None,
        f"`diluted_weighted_average_shares` is not on the basis "
        f"{basis.label} and no annual average is on the file; a window-end "
        f"count is never promoted (E88) and E38 admits no substitute: a "
        f"point-in-time count is a stock and the flow it would divide is a "
        f"window{end_memo}{aside}")


def share_count_on_basis(parsed: ManualFile,
                         basis: "Basis | None") -> tuple[float | None, str]:
    """E38's divisor in E88's order -- see `share_divisor_on_basis`.

    Returns (count, one sentence naming the basis). Kept in this shape for
    every caller; the kind and the drift are on the `ShareDivisor`.
    """
    divisor = share_divisor_on_basis(parsed, basis)
    return divisor.count, divisor.why


#: E112 (2026-09-08): §3 Gate 3's limit. Named here so the reading and the
#: threshold sit together and neither can drift from the other.
COVERAGE_MINIMUM = 5.0

#: The elements a filer tags for an impairment charge. Read ONLY to print
#: the adjusted figure BESIDE the stated one -- E112's numerator is the
#: stated operating income and the adjustment never enters a verdict.
IMPAIRMENT_TAGS: tuple[str, ...] = (
    "GoodwillImpairmentLoss", "AssetImpairmentCharges",
    "ImpairmentOfIntangibleAssetsExcludingGoodwill",
    "ImpairmentOfIntangibleAssetsIndefinitelivedExcludingGoodwill",
    "TangibleAssetImpairmentCharges",
)


@dataclass(frozen=True)
class Coverage:
    """§3 Gate 3's interest coverage, under E112.

    `ratio` is THE ONE THAT COUNTS: operating income AS STATED over
    `net_finance_costs`. `adjusted` is printed beside it where impairments
    are known and material, and is never a verdict -- E112 is explicit that
    the adjustment is information, so a reader can see the size of what the
    rule refuses to net out.
    """

    ebit: float | None = None
    denominator: float | None = None
    ratio: float | None = None
    impairments: float | None = None
    adjusted: float | None = None
    why: str = ""
    #: E118 (2026-09-19): net finance costs zero or negative -- no interest
    #: burden. PASS, and where gross interest expense is on file the gross
    #: cover must ALSO clear 5x; both figures are recorded.
    net_income_case: bool = False
    gross_expense: float | None = None
    gross_cover: float | None = None
    #: P2 (owner, 2026-09-19): with an E106-BOUNDED lease interest the
    #: coverage is formed at BOTH ends of the bound; where they disagree the
    #: limb records REVIEW and shows both -- never FAIL on one end alone.
    bound_end: "Coverage | None" = None

    @property
    def state(self) -> str:
        own = {True: "PASS", False: "FAIL", None: "DATA MISSING"}[self._passes()]
        if self.bound_end is not None:
            other = {True: "PASS", False: "FAIL", None: "DATA MISSING"}[self.bound_end._passes()]
            if other != own:
                return "REVIEW"
        return own

    @property
    def passes(self) -> bool | None:
        """True / False where both ends of any bound agree; None otherwise
        (DATA MISSING, or REVIEW -- read `state`)."""
        st = self.state
        return True if st == "PASS" else False if st == "FAIL" else None

    def _passes(self) -> bool | None:
        """None where it cannot be formed -- DATA MISSING, never a FAIL."""
        if self.net_income_case:
            return (True if self.gross_cover is None
                    else self.gross_cover >= COVERAGE_MINIMUM)
        return None if self.ratio is None else self.ratio >= COVERAGE_MINIMUM

    @property
    def material(self) -> bool:
        """Do the two readings fall on OPPOSITE SIDES of the limit?"""
        if self.ratio is None or self.adjusted is None:
            return False
        return (self.ratio >= COVERAGE_MINIMUM) != (self.adjusted >= COVERAGE_MINIMUM)

    def line(self) -> str:
        if self.ratio is None:
            return f"interest coverage: DATA MISSING — {self.why}"
        verdict = "PASSES" if self.passes else "FAILS"
        out = (f"interest coverage **{self.ratio:,.2f}x** against "
               f"{COVERAGE_MINIMUM:,.0f}x — **{verdict}**. Numerator is "
               f"operating income AS STATED ({self.ebit:,.0f}), impairments "
               f"included (E112); denominator {self.denominator:,.0f}")
        if self.adjusted is not None:
            out += (f". **As information and not the verdict:** adding back "
                    f"{self.impairments:,.0f} of stated impairments gives "
                    f"{self.adjusted:,.2f}x"
                    + (" — **which is the OTHER SIDE of the limit**"
                       if self.material else " — the same side of the limit"))
        return out


def _coverage_from(ebit, denominator, parsed: ManualFile, basis: "Basis", rent_note: str = "", *, impairments: float | None = None) -> Coverage:
    """The ratio, E25 / E112 / E118, on the operands handed to it."""
    if ebit is None or denominator is None:
        absent = ", ".join(
            n for n, v in (("operating_income", ebit),
                           (COVERAGE_DENOMINATOR, denominator)) if v is None)
        why = f"{absent} is not on the basis {basis.label}"
        if ebit is None:
            # E126 STEP 3: the staircase ran out. Say which step failed,
            # because "operating_income is missing" and "this filer states
            # no such line and none can be reconstructed" are different
            # facts about the same absence.
            why += (". E126: no subtotal before financing cost is stated, "
                    "and step 2 could not form either -- "
                    + ("income_before_taxes"
                       if resolve_on_basis(parsed, basis,
                                           "income_before_taxes").value is None
                       else "finance_costs_period")
                    + " is not on the basis. DATA MISSING and OUT OF THE "
                      "GATE COUNT; section 4.4 rebases, and E126's tier "
                      "hold applies below four evaluable gates")
        return Coverage(ebit=ebit, denominator=denominator, why=why)
    if denominator <= 0:
        # E118 (2026-09-19), amending E112 and, here, E25's "EBIT / 0 is
        # undefined": NET FINANCE COSTS ZERO OR NEGATIVE IS NO INTEREST
        # BURDEN, and the limb PASSES -- but where gross interest expense is
        # on file, operating income over it must ALSO clear 5x, and both
        # figures are recorded. Still never a ratio divided by a negative.
        gross = resolve_on_basis(parsed, basis, "finance_costs_period").value
        gross = abs(gross) if gross else None
        cover = ebit / gross if gross else None
        verdict = ("PASS" if cover is None or cover >= COVERAGE_MINIMUM
                   else "FAIL")
        return Coverage(ebit=ebit, denominator=denominator,
                        net_income_case=True, gross_expense=gross,
                        gross_cover=cover,
                        why=(f"{COVERAGE_DENOMINATOR} is "
                             f"{'ZERO' if denominator == 0 else 'NEGATIVE'} "
                             f"({denominator:,.0f}) on the basis "
                             f"{basis.label}: no interest burden (E118) -- "
                             + (f"gross interest expense {gross:,.0f}, "
                                f"operating income / gross {cover:.1f}x "
                                f"against {COVERAGE_MINIMUM:.0f}x"
                                if gross else "no gross interest expense on file")
                             + f": {verdict}" + rent_note))
    ratio = ebit / denominator
    adjusted = ((ebit + abs(impairments)) / denominator
                if impairments else None)
    return Coverage(ebit=ebit, denominator=denominator, ratio=ratio,
                    impairments=abs(impairments) if impairments else None,
                    adjusted=adjusted, why=rent_note.strip())


#: FRAMEWORK §3 Gate 3 and §4.2.5: the two leverage thresholds E119 reads.
GATE3_LEVERAGE_MAX = 2.5
KILL_LEVERAGE_MAX = 3.5


@dataclass(frozen=True)
class Leverage:
    """E119 (2026-09-19): net debt / EBITDA on ONE window, and the line
    that shows the latest quarter's net debt over the same EBITDA.

    `ratio` is the RULED figure: the section 5 basis's EBITDA -- STATED where
    the filer states one, else DERIVED (operating income + D&A, and for an
    IFRS 16 filer less its total lease cash outflow, E117) -- over E117's
    net debt on that same basis (finance leases and pension deficit in).
    `latest_ratio` is INFORMATION: the newest quarter's net debt over the
    same EBITDA, legs the quarter does not restate carried from the newest
    period that does, each named. Above the threshold it records REVIEW.
    """

    ebitda: float | None = None
    ebitda_source: str = ""
    net_debt: float | None = None
    ratio: float | None = None
    basis_label: str = ""
    latest_period: str = ""
    latest_net_debt: float | None = None
    latest_ratio: float | None = None
    carried: tuple[str, ...] = ()
    why: str = ""
    #: E117 clause 5 with an E106-bounded lease interest: the ratio at the
    #: BOUND END (all of it paid). Above the threshold it records REVIEW,
    #: on E119 (b)'s terms -- the struck ratio is the generous end.
    bound_ratio: float | None = None

    def state(self, threshold: float) -> str:
        if self.ratio is None:
            return "DATA MISSING"
        if self.ratio > threshold:
            return "FAIL"
        if self.latest_ratio is not None and self.latest_ratio > threshold:
            return "REVIEW"
        if self.bound_ratio is not None and self.bound_ratio > threshold:
            return "REVIEW"
        return "PASS"

    def line(self, threshold: float) -> str:
        if self.ratio is None:
            return f"DATA MISSING: {self.why}"
        out = (f"{self.state(threshold)}: net debt {self.net_debt:,.0f} / "
               f"EBITDA {self.ebitda:,.0f} ({self.ebitda_source}) = "
               f"{self.ratio:.2f}x on {self.basis_label}, against {threshold}x")
        if self.bound_ratio is not None:
            out += f"; at the lease-interest BOUND {self.bound_ratio:.2f}x"
        if self.latest_ratio is not None:
            out += (f"; information line (E119 b): {self.latest_period} net "
                    f"debt {self.latest_net_debt:,.0f} / the same EBITDA = "
                    f"{self.latest_ratio:.2f}x"
                    + (f", carried: {', '.join(self.carried)}" if self.carried else ""))
        return out


def interest_coverage(parsed: ManualFile, basis: "Basis | None", *,
                      impairments: float | None = None) -> Coverage:
    """§3 Gate 3's coverage limb, formed ONE way (E112).

    **THE NUMERATOR IS OPERATING INCOME AS THE ACCOUNTS STATE IT.** Nothing
    is added back, because *a coverage ratio asks whether the business AS
    REPORTED can service its debt*, and adjusting an impairment out would
    substitute a reader's judgement of what is recurring for the accounts'
    own figure -- E22's refusal, applied to a ratio's numerator.

    ``impairments`` is optional and enters NO verdict: supplied, it is used
    only to print the adjusted figure beside the stated one, which E112
    requires where the difference is material.
    """
    if basis is None:
        return Coverage(why="the file supplies no twelve-month basis")
    ebit = resolve_on_basis(parsed, basis, "operating_income").value
    numerator_note = ""
    if ebit is None:
        # E126 STEP 2 (2026-09-20): no stated subtotal before financing
        # cost. The numerator is INCOME BEFORE INCOME TAXES plus THAT
        # STATED INTEREST EXPENSE -- both printed lines in the same column,
        # and the addition restores one stated deduction, so no new
        # quantity is created. Every other reconstruction is forbidden.
        pre_tax = resolve_on_basis(parsed, basis, "income_before_taxes").value
        charged = resolve_on_basis(parsed, basis, "finance_costs_period").value
        if pre_tax is not None and charged is not None:
            ebit = pre_tax + abs(charged)
            numerator_note = (f" [E126 step 2: no stated subtotal before "
                              f"financing cost, so income before income "
                              f"taxes {pre_tax:,.0f} + stated interest "
                              f"expense {abs(charged):,.0f}]")
    denominator = resolve_or_subtract(parsed, basis, COVERAGE_DENOMINATOR)
    if denominator is None:
        denominator = resolve_on_basis(parsed, basis, COVERAGE_DENOMINATOR).value
    rent_note = ""
    if _is_ifrs16(parsed) and ebit is not None and denominator is not None:
        # E117 clause 5 (2026-09-19): RENT-BEARING. An IFRS 16 filer's
        # operating income is after right-of-use depreciation and before
        # rent, and its finance costs carry the lease interest: add the
        # depreciation back, deduct the lease cash, take the lease interest
        # out of the denominator. A bounded lease interest is struck at 0,
        # which is the LOWER coverage, the conservative end for this ratio.
        rou = resolve_on_basis(parsed, basis, "rou_depreciation").value
        lp, li, bound, note = _ifrs_lease_cash(parsed, basis)
        if rou is None or lp is None:
            return Coverage(ebit=ebit, denominator=denominator,
                            why=("rou_depreciation is not on the basis "
                                 if rou is None else note)
                                + f" {basis.label}: no rent-bearing coverage "
                                  f"(E117 clause 5)")
        bound_end = None
        if bound is not None:
            # the other end: all of the bound paid as lease interest
            hi_ebit = ebit + abs(rou) - lp - bound
            hi_den = denominator - bound
            bound_end = _coverage_from(hi_ebit, hi_den, parsed, basis,
                                       f" [the lease-interest BOUND end: {bound:,.0f}]")
        ebit = ebit + abs(rou) - lp - li
        denominator = denominator - li
        rent_note = (f" [RENT-BEARING, E117 clause 5: + ROU depreciation "
                     f"{abs(rou):,.0f} - lease principal {lp:,.0f} - {note}]")
        struck = _coverage_from(ebit, denominator, parsed, basis, rent_note,
                                impairments=impairments)
        return replace(struck, bound_end=bound_end) if bound_end else struck
    return _coverage_from(ebit, denominator, parsed, basis,
                          rent_note + numerator_note, impairments=impairments)

def _ifrs_lease_cash(parsed: ManualFile, basis: "Basis") -> tuple[float | None, float | None, float | None, str]:
    """E117 clause 5: an IFRS 16 filer's (principal, lease interest struck,
    lease interest bound, sentence) on the basis. Lease interest ABSENT but
    BOUNDED (E106) is struck at zero and its bound returned beside it."""
    lp = resolve_on_basis(parsed, basis, "lease_payments_capital").value
    li = resolve_on_basis(parsed, basis, "lease_interest_paid").value
    stand = lease_interest_stand_in(parsed, basis)
    if li is None and stand is not None:
        return abs(lp) if lp is not None else None, abs(stand.value), None, (
            f"lease interest {abs(stand.value):,.0f} STAND-IN (E120, "
            f"{stand.period})")
    bound = next((abs(float(f.bound)) for f in basis_bounds(parsed, basis)
                  if f.name == "lease_interest_paid"), None)
    if li is None and bound is not None:
        li = 0.0
    if lp is None or li is None:
        return None, None, None, "the IFRS 16 lease legs are not on the basis (E117 clause 5)"
    note = (f"lease interest BOUNDED at {bound:,.0f}, struck at 0 (E106)"
            if bound is not None else f"lease interest {abs(li):,.0f}")
    return abs(lp), abs(li), bound, note


def _is_ifrs16(parsed: ManualFile) -> bool:
    lease = parsed.operating_leases_in_ocf
    return lease is not None and not lease.value


def _holders_newest_first(parsed: ManualFile) -> list:
    holders = list(parsed.periods) + list(getattr(parsed, "annual", ()) or ())
    return sorted(holders, key=lambda h: h.period_end, reverse=True)


def _stated(holder, name: str) -> float | None:
    figure = holder.figures.get(name)
    if figure is None or not figure.present:
        return None
    return figure.value


def _latest_net_debt(parsed: ManualFile) -> tuple[str, float | None, tuple[str, ...]]:
    """E119 (b): net debt at the NEWEST quarter that states cash and both
    borrowing legs. A leg that quarter does not restate is CARRIED from the
    newest period that does, and named -- never silently zero."""
    holders = _holders_newest_first(parsed)
    quarter = next((h for h in parsed.periods if all(
        _stated(h, n) is not None for n in ("cash_and_equivalents",
                                            "financial_liabilities_current",
                                            "financial_liabilities_noncurrent"))),
        None)
    if quarter is None:
        return "", None, ()
    newest = max((h for h in parsed.periods if all(
        _stated(h, n) is not None for n in ("cash_and_equivalents",
                                            "financial_liabilities_current",
                                            "financial_liabilities_noncurrent"))),
        key=lambda h: h.period_end)
    carried: list[str] = []

    def leg(name: str) -> float | None:
        value = _stated(newest, name)
        if value is not None:
            return value
        for h in holders:
            if h.period_end <= newest.period_end and _stated(h, name) is not None:
                label = getattr(h, "period", None) or f"FY{h.fiscal_year}"
                carried.append(f"{name} {_stated(h, name):,.0f} from {label}")
                return _stated(h, name)
        return None

    lease = parsed.operating_leases_in_ocf
    if lease is not None and not lease.value:
        kept = 0.0
    else:
        kept = None
        for h in [newest] + holders:
            ll, ol = _stated(h, "lease_liabilities"), _stated(h, "operating_lease_liabilities")
            if ll is not None and (ol is not None or lease is None):
                kept = ll - (ol or 0.0)
                if h is not newest:
                    label = getattr(h, "period", None) or f"FY{h.fiscal_year}"
                    carried.append(f"finance leases {kept:,.0f} from {label}")
                break
    legs = [leg("pension_deficit"), leg("asset_retirement_obligation"),
            leg("prepaid_delivery_obligation")]
    if kept is None or any(v is None for v in legs):
        return getattr(newest, "period", ""), None, tuple(carried)
    assets = _stated(newest, "other_current_financial_assets") or 0.0
    total = (_stated(newest, "financial_liabilities_current")
             + _stated(newest, "financial_liabilities_noncurrent") + kept + sum(legs)
             - _stated(newest, "cash_and_equivalents") - assets)
    return newest.period, total, tuple(carried)



# --- E123: the measured figures, which decide nothing ---------------------


@dataclass(frozen=True)
class Capitalisation:
    """E123's print: debt to total capitalisation on TWO bases, and the net
    position on each. NO THRESHOLD IS ATTACHED TO ANY OF IT.

    The owner's revision of 2026-09-20: print both bases rather than choose
    between them, because **the SPREAD between them is itself the
    information** -- small means the captive-finance question does not
    matter for that filer, large means it does. Where the captive finance
    debt cannot be read from any document the second line is **DATA
    MISSING with the reason, never omitted**: an omitted line and a zero
    look identical in a packet.
    """

    basis_label: str = ""
    operating_debt: float | None = None
    equity: float | None = None
    cash: float | None = None
    finance_debt: float | None = None
    finance_why: str = ""
    why: str = ""

    @property
    def ratio(self) -> float | None:
        if self.operating_debt is None or self.equity is None:
            return None
        total = self.operating_debt + self.equity
        return self.operating_debt / total if total else None

    @property
    def ratio_with_finance(self) -> float | None:
        if self.finance_debt is None or self.ratio is None:
            return None
        debt = self.operating_debt + self.finance_debt
        total = debt + self.equity
        return debt / total if total else None

    @property
    def net_position(self) -> float | None:
        if self.operating_debt is None or self.cash is None:
            return None
        return self.operating_debt - self.cash

    @property
    def net_position_with_finance(self) -> float | None:
        if self.finance_debt is None or self.net_position is None:
            return None
        return self.net_position + self.finance_debt

    def lines(self) -> list[str]:
        """The block as the packet prints it. Never a state, never a mark."""
        if self.ratio is None:
            return [f"debt to total capitalisation: DATA MISSING -- {self.why}"]
        out = [f"debt to total capitalisation, operating only: "
               f"{self.ratio * 100:.2f}%  (debt {self.operating_debt:,.0f} / "
               f"debt + equity {self.operating_debt + self.equity:,.0f})"]
        if self.ratio_with_finance is not None:
            out.append(f"same, including captive finance debt "
                       f"{self.finance_debt:,.0f}: "
                       f"{self.ratio_with_finance * 100:.2f}%")
        else:
            out.append(f"same, including captive finance debt: DATA MISSING "
                       f"-- {self.finance_why}")
        net = self.net_position
        if net is not None:
            out.append(f"net position, operating only: "
                       f"{'net cash' if net < 0 else 'net debt'} "
                       f"{abs(net):,.0f}  (information, not a ratio)")
        both = self.net_position_with_finance
        if both is not None:
            out.append(f"net position, including captive finance debt: "
                       f"{'net cash' if both < 0 else 'net debt'} "
                       f"{abs(both):,.0f}  (information, not a ratio)")
        out.append("NEITHER FIGURE DECIDES ANYTHING (E123): no threshold is "
                   "attached to either, and the SPREAD between them is the "
                   "information -- small means the captive-finance question "
                   "does not matter for this filer, large means it does.")
        return out


def capitalisation(parsed: ManualFile, basis: "Basis | None") -> Capitalisation:
    """E123's measured figures off the store. Reports; never decides."""
    if basis is None:
        return Capitalisation(why="the file supplies no twelve-month basis")
    current = resolve_on_basis(parsed, basis, "financial_liabilities_current").value
    noncurrent = resolve_on_basis(parsed, basis, "financial_liabilities_noncurrent").value
    equity = resolve_on_basis(parsed, basis, "total_equity").value
    cash = resolve_on_basis(parsed, basis, "cash_and_equivalents").value
    finance = resolve_on_basis(parsed, basis, "captive_finance_debt").value
    if current is None and noncurrent is None:
        return Capitalisation(basis_label=basis.label,
                              why=f"no borrowings leg on {basis.label}")
    if equity is None:
        return Capitalisation(basis_label=basis.label,
                              why=f"total_equity is not on {basis.label}")
    return Capitalisation(
        basis_label=basis.label,
        operating_debt=(current or 0.0) + (noncurrent or 0.0),
        equity=equity, cash=cash, finance_debt=finance,
        finance_why=("captive_finance_debt is not on "
                     f"{basis.label}: a captive finance line cannot be "
                     "reached by tag (E124) -- it comes from the filing or "
                     "it is DATA MISSING, and it is never omitted"))


#: E123: what the two limbs say when the declaration is true.
INVENTORY_LIMB_WHY = (
    "DATA MISSING under E123: the operating asset is inventory and its "
    "purchase runs through operating cash flow, so growth drives free cash "
    "flow negative and contraction drives it positive, and EBITDA excludes "
    "the inventory spend that is the real capital cycle. Out of the gate "
    "count; section 4.4 rebases (E99's treatment). Debt to total "
    "capitalisation is printed instead, with no threshold attached")


def inventory_operating_asset(parsed: ManualFile) -> bool:
    """E123's trigger: the declaration, and nothing else."""
    declared = parsed.operating_asset_is_inventory
    return bool(declared and declared.value)


def gate3_leverage(parsed: ManualFile, basis: "Basis | None") -> Leverage:
    """E119: Gate 3 leverage and the 4.2.5 kill's ratio, off the store.

    E123 (2026-09-20) comes FIRST: where the operating asset is inventory
    and its purchase runs through operating cash flow, this limb is DATA
    MISSING and out of the gate count, whatever the legs would have formed.
    """
    if inventory_operating_asset(parsed):
        return Leverage(basis_label=basis.label if basis else "",
                        why=INVENTORY_LIMB_WHY)
    if basis is None:
        return Leverage(why="the file supplies no twelve-month basis")
    stated = resolve_on_basis(parsed, basis, "ebitda").value
    bound = None
    if stated is not None:
        ebitda, source = stated, "STATED"
        if _is_ifrs16(parsed):
            lp, li, bound, note = _ifrs_lease_cash(parsed, basis)
            if lp is None:
                return Leverage(basis_label=basis.label, why=note)
            ebitda -= lp + li
            source += f" - lease cash (E117 clause 5: principal {lp:,.0f}, {note})"
    else:
        oi = resolve_on_basis(parsed, basis, "operating_income").value
        da = resolve_on_basis(parsed, basis, "depreciation_amortisation").value
        absent = [n for n, v in (("operating_income", oi),
                                 ("depreciation_amortisation", da)) if v is None]
        if absent:
            return Leverage(basis_label=basis.label,
                            why=f"no stated EBITDA, and {', '.join(absent)} is "
                                f"not on the basis {basis.label} to derive one (E119)")
        ebitda, source = oi + abs(da), "DERIVED (E119): operating income + D&A"
        lease = parsed.operating_leases_in_ocf
        if lease is not None and not lease.value:
            lp, li, bound, note = _ifrs_lease_cash(parsed, basis)
            if lp is None:
                return Leverage(basis_label=basis.label,
                                why="an IFRS 16 filer's derived EBITDA subtracts "
                                    "its total lease cash outflow (E119 c), and "
                                    "the lease legs are not on the basis")
            ebitda -= lp + li
            source += f" - lease cash (E119 c: principal {lp:,.0f}, {note})"
    net_debt, why = net_debt_on_basis(parsed, basis)
    if net_debt is None:
        return Leverage(ebitda=ebitda, ebitda_source=source,
                        basis_label=basis.label, why=why)
    if ebitda <= 0:
        return Leverage(ebitda=ebitda, ebitda_source=source, net_debt=net_debt,
                        basis_label=basis.label,
                        why=f"EBITDA {ebitda:,.0f} is not positive on "
                            f"{basis.label}: no leverage multiple exists")
    period, latest, carried = _latest_net_debt(parsed)
    bound_ebitda = ebitda - bound if bound is not None else None
    return Leverage(ebitda=ebitda, ebitda_source=source, net_debt=net_debt,
                    ratio=net_debt / ebitda, basis_label=basis.label,
                    bound_ratio=(net_debt / bound_ebitda
                                 if bound_ebitda and bound_ebitda > 0 else None),
                    latest_period=period, latest_net_debt=latest,
                    latest_ratio=(latest / ebitda if latest is not None else None),
                    carried=carried)



# --- E126: how many gates a name can be scored against --------------------

#: E126 (owner, 2026-09-20): A TIER REQUIRES AT LEAST FOUR EVALUABLE GATES.
#: Below four a name may carry a section 4.4 score but NO TIER, and
#: therefore no MBP. A HOLD, NOT A THRESHOLD: section 4.4's bands were
#: calibrated on four gates (E99) and have not been restated per
#: denominator. It lifts when they are -- B50.
TIER_MINIMUM_GATES = 4


def evaluable_gates(parsed: ManualFile, basis: "Basis | None") -> tuple[int, list[str]]:
    """How many of the five gates can be evaluated for this name, and why.

    WHAT THIS CAN AND CANNOT SEE. It counts the gates whose evaluability
    THE STORE decides: Gate 4, which E99 put out of the count for every
    name, and Gate 3, whose limbs are formed from the store. Gates 1, 2
    and 5 are the owner's readings -- a dislocation, a class, a dated
    event -- and nothing here judges them; they are counted as evaluable
    because the store cannot say otherwise.
    """
    reasons: list[str] = ["Gate 4: DATA MISSING for every name (E99)"]
    count = 4                                   # five, less Gate 4
    if basis is None:
        reasons.append("Gate 3: no twelve-month basis, so no limb forms")
        return count - 1, reasons

    limbs = {}
    if inventory_operating_asset(parsed):
        limbs["leverage"] = "DATA MISSING (E123)"
        limbs["FCF positivity"] = "DATA MISSING (E123)"
    else:
        limbs["leverage"] = ("forms" if gate3_leverage(parsed, basis).ratio
                             is not None else "DATA MISSING")
        limbs["FCF positivity"] = "forms"       # E4: judged on the stored flows
    cover = interest_coverage(parsed, basis)
    limbs["coverage"] = ("forms" if (cover.ratio is not None or cover.net_income_case)
                         else ("DATA MISSING (E126)" if "E126" in cover.why
                               else "DATA MISSING"))
    if all(v.startswith("DATA MISSING") for v in limbs.values()):
        count -= 1
        reasons.append("Gate 3: NO LIMB FORMS -- "
                       + "; ".join(f"{k} {v}" for k, v in limbs.items())
                       + ". The cleanliness limb (going concern, auditor, "
                         "restatement) is a READING and is not in the store")
    else:
        reasons.append("Gate 3: " + "; ".join(f"{k} {v}" for k, v in limbs.items()))
    return count, reasons


def tier_hold(parsed: ManualFile, basis: "Basis | None") -> str:
    """E126's hold, in words, or "" where the name may carry a tier."""
    count, reasons = evaluable_gates(parsed, basis)
    if count >= TIER_MINIMUM_GATES:
        return ""
    return (f"TIER HELD (E126): {count} evaluable gate(s); a tier requires "
            f"{TIER_MINIMUM_GATES}. A section 4.4 score may be carried; NO "
            f"TIER, and therefore NO MBP. This is a HOLD, not a threshold -- "
            f"section 4.4's bands were calibrated on four gates and have not "
            f"been restated per denominator (B50). Why: " + " | ".join(reasons))


#: E126 step 3 prints these four, measured and deciding nothing (E7's
#: shape, and E63's). Only `net_interest_paid` is a store field; the other
#: three live in ITS PAGE CITATION, which is printed verbatim -- an
#: existing citation is measured and sourced and invents nothing (owner,
#: 2026-09-20, refusing a `maturity_wall` field in the same breath: "free
#: text nothing reads is vocabulary for its own sake, and it would go
#: stale silently the first time a repayment passes").
STEP3_FIGURES = ("net_interest_paid", "finance_costs_paid", "lease_interest_paid")

#: The convention a packet looks for in an entry's notes for the maturity
#: wall. Absent, the packet NAMES THE DOCUMENT instead (the owner's
#: fallback): nothing is invented and the reader is told where to look.
MATURITY_MARKER = "MATURITY WALL"


def step3_block(parsed: ManualFile, basis: "Basis | None",
                notes: str = "") -> list[str]:
    """What prints where E126 step 3 leaves the coverage limb DATA MISSING."""
    out: list[str] = []
    for name in STEP3_FIGURES:
        if basis is None:
            break
        resolved = resolve_on_basis(parsed, basis, name)
        if resolved.value is None:
            continue
        # THE PAGE CITATION, VERBATIM. `Resolved` carries the figures it was
        # built from; the citation is on those, and it is what makes this
        # block measured and sourced without a new store field (owner,
        # 2026-09-20). PHM's `net_interest_paid` page carries the other
        # three interest figures inside it, which is why they print here
        # without ever becoming fields of their own.
        pages = [f.page for f in (resolved.figures or ()) if getattr(f, "page", "")]
        out.append(f"{name} {resolved.value:,.0f} -- "
                   + (pages[0] if pages else "no page citation on the figure"))
    wall = [line.strip() for line in (notes or "").splitlines()
            if MATURITY_MARKER in line.upper()]
    if wall:
        out += [f"maturity wall (from the entry): {line}" for line in wall]
    else:
        newest = (parsed.newest_period.document if parsed.newest_period else "") or ""
        out.append("maturity wall: NOT in the store and not on the entry. Read "
                   "the debt note and the liquidity paragraph of "
                   + (newest or "the newest filing in sources/")
                   + " -- the next scheduled repayment against cash and "
                     "undrawn facilities is what says whether this filer can "
                     "service its debt, and a coverage ratio cannot")
    return out


def kill_leverage_reading(ticker: str, *,
                          directory: Path = MANUAL_DIR) -> tuple[str, str] | None:
    """E119's reading for the 4.2.5 kill, ``(state, line)`` at 3.5x, or None
    where the name has no store. Never raises: a kill input that cannot be
    read is the kill's CANNOT EVALUATE, not an exception in the watch."""
    try:
        parsed = load_manual(ticker, directory=directory)
    except Exception:  # noqa: BLE001 -- no store, or one that does not load
        return None
    reading = gate3_leverage(parsed, section5_basis(parsed))
    return reading.state(KILL_LEVERAGE_MAX), reading.line(KILL_LEVERAGE_MAX)


def net_debt_on_basis(parsed: ManualFile,
                      basis: "Basis | None") -> tuple[float | None, str]:
    """E35 / E35.1 net debt on one basis, and one sentence naming what went in.

        financial liabilities (current + non-current)
          + lease liabilities
          + pension deficit
          + asset retirement obligation (E68)
          + prepaid delivery obligation (E81)
          - cash and equivalents
          - other current financial assets, where the file carries them

    LEASES ARE IN, ALWAYS (E35). A2 is no longer thrown for this
    calculation: under IFRS 16 the operating cash flow excludes lease
    principal, so a bridge without the lease liability prices the premises
    as free once the contracted term ends. THE PENSION DEFICIT IS IN
    (E35.1): on Lindab's components at 2026-06-30 E35's four legs gave
    4,217 against its stated 4,497, and the 280 was the pension provision.
    Absent, it is DATA MISSING on the lease leg's terms.

    WHAT IT STILL DOES NOT REACH. `manual.FIELDS` has no field for
    non-controlling interests, associates, preferred stock, convertibles or
    a separately presented pension ASSET. The formula is NOT plugged to
    close those, and the gap is named here so a reader meets it before a
    number does.

    Returns (net debt as a POSITIVE number for a net-debt company, why).
    """
    if basis is None:
        return None, "the file supplies no twelve-month basis"
    legs = {name: resolve_on_basis(parsed, basis, name).value
            for name in NET_DEBT_LEGS}
    # E106 clause 3: A BOUNDED LEG IS NOT INPUT MISSING. It enters the
    # bridge at ZERO -- which for a LIABILITY leg is the GENEROUS end, and
    # is exactly why E106 clause 4 then has to measure the bound before
    # section 5 may run. The same treatment `ratio_states` gives a bounded
    # flow leg, and it is here for the same reason: without it the bridge
    # would refuse a leg the ruling has already accounted for, and the gate
    # and the record would disagree about the same store.
    bounded = {f.name: f for f in basis_bounds(parsed, basis)}
    for name in list(legs):
        if legs[name] is None and name in bounded:
            legs[name] = 0.0
    # E117: the operating part leaves. A US filer names it; bounded it is
    # not -- a missing operating liability would leave rent charged twice.
    for name in lease_excluded_legs(parsed):
        legs[name] = resolve_on_basis(parsed, basis, name).value
    absent = [name for name, value in legs.items() if value is None]
    if absent:
        return None, f"{', '.join(sorted(absent))} is not on the basis {basis.label}"
    assets = resolve_on_basis(
        parsed, basis, "other_current_financial_assets").value
    leases_in, lease_why = lease_in_net_debt(
        parsed, legs["lease_liabilities"], legs.get("operating_lease_liabilities"))
    total = (legs["financial_liabilities_current"]
             + legs["financial_liabilities_noncurrent"]
             + leases_in
             + legs["pension_deficit"]
             + legs["asset_retirement_obligation"]
             + legs["prepaid_delivery_obligation"]
             - legs["cash_and_equivalents"]
             - (assets or 0.0))
    why = (f"borrowings {legs['financial_liabilities_current']:,.0f} + "
           f"{legs['financial_liabilities_noncurrent']:,.0f} + {lease_why} "
           f"+ pension "
           f"deficit {legs['pension_deficit']:,.0f} (E35.1) + asset retirement "
           f"obligations {legs['asset_retirement_obligation']:,.0f} (E68) + "
           f"prepaid delivery obligations "
           f"{legs['prepaid_delivery_obligation']:,.0f} (E81) - cash "
           f"{legs['cash_and_equivalents']:,.0f}")
    if assets is None:
        why += (" - other current financial assets DATA MISSING, so nothing "
                "is subtracted for them: omitting an ASSET raises net debt "
                "and lowers the value, which is the safe direction")
    else:
        why += f" - other current financial assets {assets:,.0f}"
    why += (". No NCI, associate, preferred or convertible leg exists in "
            "this schema (E35); a separately presented pension ASSET is not "
            "netted (E35.1)")
    searched = [name for name in NET_DEBT_LEGS
                if any(f.status == STATUS_NOT_PRESENTED
                       for f in resolve_on_basis(parsed, basis, name).figures)]
    if searched:
        why += (f". NOT PRESENTED (E85), entered at nil on a recorded search: "
                f"{', '.join(searched)}")
    return total, why


def ratio_states(parsed: ManualFile,
                 basis: "Basis | None" = None) -> tuple[RatioState, ...]:
    """For each ratio: whether the ONE BASIS supplies every leg, or why not.

    E19 replaced "both legs from one period entry" with "every leg on one
    twelve-month basis", and matching follows from that rather than being
    checked pair by pair. Two failures remain, counted apart as they always
    were: a leg the basis cannot supply at all is `input missing`, and a leg
    that exists as twelve months of ANOTHER twelve months is
    `periods do not match` -- which under E19 means exactly one thing, an
    annual entry whose window ends elsewhere.
    """
    basis = basis if basis is not None else section5_basis(parsed)
    out: list[RatioState] = []
    for name, legs, reads in RATIOS:
        if basis is None:
            out.append(RatioState(name, reads, None, RATIO_MISSING,
                                  "the file supplies no twelve-month basis"))
            continue
        resolved = {leg: resolve_on_basis(parsed, basis, leg)
                    for leg in expand_legs(parsed, basis, legs)}
        mismatched = [leg for leg, r in resolved.items()
                      if r.state == QUALITY_BASIS_MISMATCH]
        # E120: a lease interest STANDING IN is an annual figure inside a
        # TTM window BY RULING -- its mismatch is the one E120 permits, and
        # it is printed with its date on the record, not refused here.
        if lease_interest_stand_in(parsed, basis) is not None:
            mismatched = [leg for leg in mismatched if leg != "lease_interest_paid"]
        absent = [leg for leg, r in resolved.items() if r.state == RATIO_MISSING]
        # E18: A NET THE ACCOUNTS PRINT IN TWO HALVES IS STILL ON THE BASIS.
        # `resolve_on_basis` answers for the FIELD; where the file holds the
        # two operands instead, the store subtracts them and the leg is
        # supplied. Without this an IFRS filer that prints interest paid and
        # interest received separately -- which is the usual presentation --
        # would read `input missing` for a figure its accounts state twice.
        absent = [leg for leg in absent
                  if not subtracted_on_basis(parsed, basis, leg)]
        # E106 clause 3: A LEG THAT IS BOUNDED IS NOT INPUT MISSING. It is
        # absent, and known to be absent by at most a stated amount -- which
        # is the state the ruling exists to distinguish from "we do not know
        # what this is". The RATIO forms with the leg at the conservative end
        # of its bound; whether the bound is small enough for section 5 to
        # run at all is `RunRecord.tolerance`'s question, asked on the
        # record, and it is NOT re-asked here.
        bounded = {f.name for f in basis_bounds(parsed, basis)}
        if lease_interest_stand_in(parsed, basis) is not None:
            bounded.add("lease_interest_paid")          # E120: stands in
        absent = [leg for leg in absent if leg not in bounded]
        if absent:
            detail = f"{', '.join(absent)} is not on the basis {basis.label}"
            if INTEREST_UNCLASSIFIED in absent:
                detail = (
                    f"`interest_in_ocf` is NOT RECORDED on this file (E34). "
                    f"Where a filer books its interest decides whether "
                    f"OCF - capex is a flow to the firm or to equity, and "
                    f"net debt is subtracted from it either way -- so FCF0 "
                    f"is DATA MISSING until the cash flow statement is read "
                    f"and the answer written down with its page")
            elif LEASE_UNCLASSIFIED in absent:
                detail = (
                    f"`operating_leases_in_ocf` is NOT RECORDED on this file "
                    f"(E70). Whether the operating cash flow bears the "
                    f"operating lease payments decides whether FCF0 adds "
                    f"them back -- the lease liability in net debt already "
                    f"charges the obligation -- so FCF0 is DATA MISSING "
                    f"until the standard is named with its page")
            out.append(RatioState(name, reads, None, RATIO_MISSING, detail))
        elif mismatched:
            # PER LEG, because the two kinds fail differently: a flow is
            # another twelve months and a stock is another date (E20).
            clauses = [
                (f"{leg} is stated at {resolved[leg].end.isoformat()}"
                 if leg in STOCK_FIELDS
                 else f"{leg} covers another twelve months")
                for leg in mismatched]
            out.append(RatioState(
                name, reads, None, RATIO_MIXED_PERIODS,
                f"{', '.join(clauses)}, and the basis ends "
                f"{basis.end.isoformat()}"))
        else:
            out.append(RatioState(name, reads, basis.label, RATIO_OK,
                                  f"every leg on {basis.label}"))
    return tuple(out)


def section5_period(parsed: ManualFile) -> ManualPeriod | None:
    """The newest period that supplies a figure SECTION 5 reads.

    Not simply the newest entry. `newest_period` is the max over every stored
    period, so a file whose 2026 entry carries only `net_ppe` -- a line the
    ranking key's fingerprint uses and no method of section 5 touches -- would
    read as current while every figure section 5 would actually hand over came
    out of 2023. That is exactly SHL.DE's shape in ranking.py rule 5, and it
    is caught here the same way: by measuring on the rows that are read.
    """
    for period in reversed(parsed.periods):
        if any(period.value(name) is not None for name in SECTION5_FIELDS):
            return period
    return None


@dataclass(frozen=True)
class ScaleJump:
    """A >= 1000x step in one section 5 leg, and where it was found."""

    field: str
    span: str            # "consecutive entries" | "this file"
    low_label: str
    low: float
    high_label: str
    high: float

    @property
    def factor(self) -> float:
        return self.high / self.low


def scale_jumps(parsed: ManualFile) -> tuple[ScaleJump, ...]:
    """Every >= 1000x step in a leg section 5 divides or discounts.

    TWO TESTS, because one of them misses by a hair. The sequence scanned
    is the file's `periods:` in order followed by its `annual:` in order,
    so the junction between the two blocks is compared as well -- that is
    the case where a year entered in whole units sits beside quarters
    entered in millions.

      CONSECUTIVE entries. The ruled test. It caught DECK's FY2026
      `operating_cash_flow` x 1000 at 1,132x (report B 7.1's own case).

      ACROSS THE FILE, min against max -- the shape `_check_one_scale`
      already applies to the five scale-stable fields. It is here because
      the consecutive test misses by a hair when the two neighbours are
      themselves unequal: DECK's `diluted_weighted_average_shares` x 1000
      reads 954x against FY2025 and slips through, and 5,246x against
      FY2022. A slip of a round thousand is not less real for landing next
      to a bigger neighbour.

    A file-wide ratio CAN be reached honestly -- PNDORA.CO's operating cash
    flow spans 136x between a weak first quarter and a Christmas one -- and
    1,000x is set well above that. Both tests refuse at the GATE and not at
    the load, so a name that genuinely swings that far still loads, still
    prints, and states its case on the page.

    Zeros are skipped: a zero is a stated figure under E25 and forms no
    ratio. Signs are ignored -- capex is negative by convention and a unit
    mix is about magnitude.
    """
    found: list[ScaleJump] = []
    entries = [
        (getattr(entry, "period", None)
         or f"FY{getattr(entry, 'fiscal_year', '')}", entry)
        for entry in (*parsed.periods, *parsed.annual)
    ]
    for key in SECTION5_SCALE_FIELDS:
        seen = [(label, abs(entry.value(key)))
                for label, entry in entries if entry.value(key)]
        if len(seen) < 2:
            continue
        reported: set[tuple[str, str]] = set()
        for early, late in zip(seen, seen[1:]):
            low, high = sorted((early, late), key=lambda pair: pair[1])
            if low[1] and high[1] / low[1] >= SCALE_JUMP_FACTOR:
                found.append(ScaleJump(key, "consecutive entries",
                                       low[0], low[1], high[0], high[1]))
                reported.add((low[0], high[0]))
        low = min(seen, key=lambda pair: pair[1])
        high = max(seen, key=lambda pair: pair[1])
        if (low[1] and high[1] / low[1] >= SCALE_JUMP_FACTOR
                and (low[0], high[0]) not in reported):
            found.append(ScaleJump(key, "this file",
                                   low[0], low[1], high[0], high[1]))
    return tuple(found)


def share_basis_steps(parsed: ManualFile) -> tuple[ScaleJump, ...]:
    """Every >= 2x step in a per-share figure or a share count.

    Same scan as `scale_jumps` and a different question: that one asks
    whether a file is in one UNIT, this asks whether it is on one SHARE
    BASIS. A split changes every count and every per-share figure at once
    and changes nothing about the company, and `_pick` -- which takes the
    newest filing -- reports it as a RESTATEMENT. Where no later filing
    restates the year at all, it is not even that: the old basis simply
    stays in the file beside the new one.

    NEVER A REFUSAL, and nothing is rescaled. Section 5 reads the newest
    year and is unaffected; B5's five-year trailing-P/E proxy reads five,
    and would read DECK's FY2022 at six times its post-split value.
    """
    fields = tuple(spec.name for spec in FIELDS
                   if spec.kind in ("count", "per_share"))
    found: list[ScaleJump] = []
    entries = [
        (getattr(entry, "period", None)
         or f"FY{getattr(entry, 'fiscal_year', '')}", entry)
        for entry in (*parsed.periods, *parsed.annual)
    ]
    for key in fields:
        seen = [(label, abs(entry.value(key)))
                for label, entry in entries if entry.value(key)]
        for early, late in zip(seen, seen[1:]):
            low, high = sorted((early, late), key=lambda pair: pair[1])
            if low[1] and high[1] / low[1] >= SHARE_BASIS_STEP_FACTOR:
                found.append(ScaleJump(key, "consecutive entries",
                                       low[0], low[1], high[0], high[1]))
    return tuple(found)


#: E108 (2026-09-04): THE SENSITIVITY FLOOR. A leg perturbed by
#: ``SENSITIVITY_PERTURBATION`` either way that moves ``fv_base`` by less
#: than ``SENSITIVITY_FLOOR`` is `VERIFIED-EXEMPT`: section 5 runs on it
#: without the owner's read-back.
#:
#: **THE FLOOR IS NOT E106's TOLERANCE AND THE TWO MUST NOT BE READ INTO
#: EACH OTHER.** E106's 3.5% is what a MISSING leg may be worth; this 1% is
#: what a PRESENT leg may MOVE. The second is the tighter of the two on
#: purpose -- an absent leg is known to be absent, and an unread one is not
#: known to be anything.
SENSITIVITY_FLOOR = 0.01

#: E113 (2026-09-08): FIELDS THE `fv_base` COMPUTATION NEVER READS.
#:
#: `equity_value_per_share` takes three quantities out of a record -- FCF0,
#: net cash and the share count -- and nothing else reaches it. A field that
#: feeds none of the three moves the value by NOTHING on any perturbation,
#: which is below E108's 1% for any `fv_base` there is, so the read-back
#: gate may not refuse on it. The owner's ground: *the gate refusing on a
#: field the valuation does not read is the inverse of the rule's own
#: purpose.*
#:
#: **AN EXPLICIT LIST AND DELIBERATELY NOT `everything - leg_values`.** The
#: vocabulary bug this area already had made the gate too STRICT, which is
#: safe. The same bug under E113 would make it too LOOSE: a leg that
#: stopped being emitted would be silently exempted instead of loudly
#: refused. A hand-maintained list cannot fail that way -- a field has to
#: be PUT on it -- and the exemption additionally requires that the
#: measured limb say nothing about the field, so the two guards are
#: independent.
#:
#: **THESE ARE NOT WORTHLESS FIELDS.** Revenue, operating income and net
#: income are read by section 4.2's hard kills, 4.3's flags and E101's
#: conversion check; `ebitda` by section 5.3. E113 exempts them from the
#: SECTION 5 READ-BACK GATE and from nothing else.
#:
#: **WHAT IS DELIBERATELY ABSENT**, each of which participates for a filer
#: shape no committed store happens to have on 2026-09-08 -- which is why
#: this list is reasoned from what the arithmetic READS and never from what
#: was observed: `net_finance_costs` (E34.1's interest leg),
#: `finance_costs_period` (E61's), `finance_costs_paid` and
#: `finance_income_received` (E18's halves of E34's leg), `income_tax_paid`
#: and `operating_cash_flow_pretax` (a pre-tax presentation's operating
#: cash flow), and `noncurrent_derivative_assets_on_debt` (a bridge leg).
NON_VALUATION_FIELDS: frozenset[str] = frozenset({
    # income-statement lines: section 4 and E101 read them; fv_base does not
    "revenue", "gross_profit", "operating_income", "operating_income_adjusted",
    "net_income", "ebitda", "depreciation_amortisation",
    # per-share and ratio outputs, never inputs to the value
    "diluted_eps", "diluted_eps_adjusted", "op_margin", "revenue_yoy",
    "net_debt_ebitda",
    # balance-sheet lines the bridge does not read
    "total_assets", "net_ppe",
    # E103's REFERENCE figures, which no basis may read by rule
    "free_cash_flow_reported", "net_debt_reported",
    # disposal proceeds: `capex_legs` reads the capex fields alone
    "proceeds_from_disposals_ppe",
    # NOT LISTED, and the omission is the ruling working: the POINT-IN-TIME
    # SHARE COUNTS. E88 keeps them MEMO and never promotes one to the
    # DIVISOR -- but `share_count_on_basis` reads E80's issued-less-treasury
    # pair for its own purposes, and `test_the_operands_still_refuse_
    # section_5_while_unverified` has held since E54 that a computed net's
    # OPERANDS are what a person has to check. A field the GATE reads is
    # not a field the gate may excuse itself from, whatever fv_base does
    # with it (found 2026-09-08 by that test going red).
})

#: E113's CONDITIONAL half: fields whose participation is settled by THIS
#: FILE'S OWN DECLARATIONS, not by the schema. Both declarations are
#: themselves gated -- `interest_in_ocf` and `operating_leases_in_ocf` each
#: require a source and a page -- so this reasons from evidence the file
#: already had to supply, and never from what a record happened to emit.
INTEREST_FIELDS: frozenset[str] = frozenset({
    "net_interest_paid", "finance_costs_paid", "finance_income_received",
    "net_finance_costs", "finance_costs_period", "finance_income_period",
})

#: E113's own wording on the flag, so a reader meets the ground and not
#: just the verdict.
EXEMPT_NON_VALUATION = (
    "E113: the fv_base computation NEVER READS this field -- it is not a leg "
    "of the flow, not a leg of the bridge and not the divisor -- so a "
    "perturbation of any size moves the value by NOTHING, which is below "
    "E108's 1% for any fv_base there is. The read-back is waived and the "
    "PROVENANCE is not: the page stands, and a zero still names its evidence "
    "under E25. Section 4.2, 4.3, 5.3 and E101 read these fields and are "
    "untouched by this"
)


def non_valuation_fields(parsed: "ManualFile") -> frozenset[str]:
    """E113's set FOR THIS FILE: the schema's, plus what this file declares.

    **THE CONDITIONAL HALF IS REASONED FROM THE FILE'S OWN DECLARATIONS**,
    which E34 and E70 already require it to make with a source and a page.
    It is NOT `everything the record did not emit` -- that subtraction is
    what E113 refuses, because a leg that stopped being emitted would then
    be exempted silently.

    * **E117.** A file declaring `operating_leases_in_ocf: yes` is a US
      GAAP filer whose operating cash flow already bears the rent, so FCF0
      reads no lease flow field at all. A file declaring `no` is an IFRS 16
      filer, and FCF0 DEDUCTS `lease_payments_capital` and
      `lease_interest_paid`. `operating_lease_payments` (E70's add-back) is
      read by neither since E117.
    * **E34.** `interest_legs` names the ONE interest field this filer's
      FCF0 reads, and E18's halves where the net is formed from them. Every
      other interest field is out of the arithmetic for this file. A filer
      whose operating cash flow is struck BEFORE interest reads none of
      them at all, and `interest_legs` returns an empty tuple to say so.

    An UNDECLARED classification (`interest_in_ocf` absent) adds nothing:
    the file cannot then say which fields are out, and the gate stays
    strict, which is the direction a missing declaration must always take.
    """
    out = set(NON_VALUATION_FIELDS)

    # E117: a US filer's flow already bears the rent, so neither lease flow
    # field is read; an IFRS filer's principal and lease interest ARE read.
    # `operating_lease_payments` is read by nobody since E117.
    lease = parsed.operating_leases_in_ocf
    if lease is not None:
        out |= {"operating_lease_payments"}
        if lease.value:
            out |= {"lease_payments_capital", "lease_interest_paid"}

    if parsed.interest_in_ocf is not None:
        if INTEREST_UNCLASSIFIED in set(interest_legs(parsed)):
            return frozenset(out)          # undeclared: nothing is ruled out
        # E60's OWN ANSWER, and not `interest_legs`. FCF0 picks ONE interest
        # shape per filer, but E25's zero-coverage-denominator gate reads
        # `net_finance_costs` and its two operands DIRECTLY, outside FCF0
        # entirely -- so those three are read whatever shape FCF0 chose, and
        # `interest_read_names` is the function that already knew it.
        # Subtracting `interest_legs` instead exempted them and turned
        # `test_net_finance_costs_and_its_own_operands_always_read_for_the_
        # coverage_gate` red on 2026-09-08. A field ANOTHER gate limb reads
        # is not one E113 may excuse.
        out |= (INTEREST_FIELDS - interest_read_names(parsed))
    return frozenset(out)
SENSITIVITY_PERTURBATION = 0.10

#: E106's tolerance, spelled HERE so `manual` and `runrecord` cannot drift
#: apart on it -- `runrecord.INCOMPLETE_LEG_TOLERANCE` re-exports this one.
INCOMPLETE_LEG_TOLERANCE = 0.035
INCOMPLETE_LEG_TOLERANCE_PCT = "3.5%"

#: E108's own blind spot, named on the constant rather than left to be
#: found: perturbing an ENTERED figure cannot catch a figure entered WRONG,
#: and above all cannot catch a ZERO THAT SHOULD NOT BE THERE -- it perturbs
#: to zero and looks immovable. That is why the exemption is from READ-BACK
#: only. E25's `zero_basis` is what covers this, and E108 leaves it standing.
EXEMPT_READ_BACK = "VERIFIED-EXEMPT"


def floor_exempt_zeros(figures: "Sequence[ManualFigure]") -> tuple[ManualFigure, ...]:
    """E108's ZERO LIMB: the legs a store can exempt with NO valuation.

    A leg entered at zero on the basis moves `fv_base` by EXACTLY 0.0% when
    it is perturbed by +/-10%, whatever the growth view, the rate or the
    bridge -- so the store alone settles it and no record need be built.
    Every OTHER leg's exemption is MEASURED, on the record, against that
    record's own `fv_base` (`runrecord.RunRecord.sensitivity`); it is never
    assumed from the leg looking small.
    """
    return tuple(f for f in figures if f.value == 0)


def floor_bound_flow_legs(parsed: "ManualFile", basis: "Basis | None", *,
                          perturbation: float = SENSITIVITY_PERTURBATION,
                          ) -> dict[str, float]:
    """E108's THIRD LIMB: a growth-free UPPER BOUND on a flow leg's move.

    **THE ARGUMENT, because it is the whole licence for this function.**
    Equity value is the DCF of FCF0 **plus** net cash:

        fv x shares  =  D(g) x FCF0  +  net_cash

    and the DCF factor ``D(g)`` is the only part the growth view touches.
    Perturbing a FLOW leg changes ``FCF0`` and nothing else, so

        |dfv / fv|  =  |df / FCF0|  x  D / (D + net_cash / FCF0)

    and **where ``net_cash`` is not negative that second factor is at most
    1, for every D and therefore for every growth view there is.** So

        |dfv / fv|  <=  perturbation x |leg| / |FCF0|

    is a bound nobody has to pre-register a view to state. It is used only
    in that direction: a leg INSIDE the bound is exempt, and a leg outside
    it is not thereby refused -- it is simply not settled here, and goes to
    the measured limb (`runrecord.RunRecord.sensitivity`).

    **WHERE THE BRIDGE IS NET DEBT THIS RETURNS NOTHING.** With
    ``net_cash < 0`` the same factor is GREATER than 1 and grows without
    limit as the DCF shrinks, so no growth-free bound exists -- and a
    function that quietly used the same formula would exempt a leg on a
    leveraged name that a low growth view makes matter. The empty answer is
    the honest one.

    FCF0 and net cash are taken off the RECORD rather than rebuilt here:
    neither depends on the growth view, so the record is built with a
    placeholder base of zero and only its legs are read.
    """
    if basis is None:
        return {}
    from datetime import datetime as _dt, timezone as _tz

    from . import runrecord as _R
    try:
        record = _R.from_store(
            parsed, basis, growth=_R.Growth(base=0.0, view_file=""),
            run_ts=_dt.now(_tz.utc),
            tool_commit="E108 bound: legs only, no growth view is read")
        legs = record.legs()
    except Exception:      # noqa: BLE001 -- an unbuildable record bounds nothing
        return {}
    if legs.fcf0 <= 0 or legs.net_cash < 0:
        return {}
    out: dict[str, float] = {}
    for name, (value, where) in record.leg_values().items():
        if where != "flow":
            continue
        out[name] = perturbation * abs(value) * UNIT_SCALE[record.money_unit] \
            / abs(legs.fcf0)
    return out


def section5_gate(parsed: ManualFile, *, as_of: date,
                  measured_exempt: "Mapping[str, float] | None" = None,
                  tolerance: "tuple[float, str] | None" = None,
                  ) -> Section5Gate:
    """May section 5 be run on this file? The answer, with every reason.

    E19: the run stands on ONE twelve-month basis, chosen before anything
    is read. Refuses on:

      * no basis at all -- fewer than four consecutive quarters and no
        twelve-month entry. Section 5 does not run.
      * an UNVERIFIED figure THE CURRENT BASIS READS (E21). The older
        reading refused on any entered figure anywhere, on the ground that
        a half-checked file is one the reader audits by hand. That ground
        is KEPT and ANSWERED rather than dropped: it holds for the figures
        a run reads and does not reach the figures it cannot. PNDORA.CO
        carried 238 UNVERIFIED of which 186 sat in quarters outside the
        window, unable to move any number section 5 produces; requiring
        them bought nothing, and a gate that never opens is worked around.
        Every one of them is NAMED in the report instead -- visible and
        not blocking, the shape E7 gave the ranking key.
      * a basis too old to divide into a price from today (STALE).
      * a leg that is twelve months of ANOTHER twelve months.

    VERIFICATION IS A PROPERTY OF THE FIGURE, NOT OF THE RUN (E21). Nothing
    here writes a status back: a quarter that leaves the window keeps its
    flags and is never re-verified when it returns. What changes with the
    basis is WHICH figures are tested, which is why the gate names the
    basis it tested against every time -- the same file may go from MAY RUN
    to REFUSED when a newer quarter arrives, and the reason belongs on the
    page.
    """
    refusals: list[Refusal] = []
    flags: list[Refusal] = []
    # E103's FENCE, and it is asked FIRST -- before the basis, before the
    # figures, before anything. A reference figure may be entered UNVERIFIED
    # precisely because no valuation reads it; the moment one does, that
    # premise is false and every §5 answer built on it is an unverified
    # number wearing a verified one's clothes.
    wired = reference_fields_in_basis()
    if wired:
        refusals.append(Refusal(
            REFUSE_REFERENCE_IN_BASIS, ", ".join(wired),
            f"E103: {', '.join(wired)} is a REFERENCE figure -- it may be "
            f"fetched automatically and entered UNVERIFIED because nothing "
            f"depends on it being right -- and it has been given a `5.*` "
            f"reader, so a §5 basis now READS it. That puts an UNVERIFIED "
            f"number inside a fair value, which is the one thing E40 exists "
            f"to prevent. SECTION 5 DOES NOT RUN until the field's `reads` "
            f"is put back to `reference`, or the owner rules that it is a "
            f"basis figure and E40 applies to it in full."))
    unverified = parsed.unverified()
    basis = section5_basis(parsed)
    read = set(basis_reads(parsed, basis)) if basis is not None else set()
    read_unverified = tuple(f for f in unverified if f in read)
    # No basis, no reading: nothing is gated on figures until there is a
    # window, and the missing window is its own refusal below.
    unread = tuple(f for f in unverified if f not in read)
    # E108 (2026-09-04): THE SENSITIVITY FLOOR, applied HERE and nowhere
    # else -- this is the read-back gate, and the exemption is from the
    # read-back. Two limbs, and the first needs no valuation at all: a leg
    # entered at ZERO moves fv_base by exactly 0.0% on a +/-10%
    # perturbation. The second is `measured_exempt`, which a caller that
    # HAS built a record supplies as {field: the measured fraction}; the
    # gate never guesses it from the leg looking small.
    measured = dict(measured_exempt or {})
    # LIMB 3, and it is a BOUND rather than a measurement: where the bridge
    # is net cash, a flow leg cannot move fv_base by more than
    # perturbation x |leg| / |FCF0| for ANY growth view (see
    # `floor_bound_flow_legs`). A caller's measured figure is the better
    # answer and wins where both exist.
    bounds = floor_bound_flow_legs(parsed, basis) if basis is not None else {}
    zeros = set(floor_exempt_zeros(read_unverified))
    # E113 (2026-09-08): the schema's non-valuation fields plus the
    # ones THIS FILE's own E34 and E70 declarations put out of the
    # arithmetic. Computed once, per file, never per figure.
    exempt_fields = non_valuation_fields(parsed)
    exempt: list[tuple[ManualFigure, str]] = []
    blocking_list: list[ManualFigure] = []
    for figure in read_unverified:
        if figure in zeros:
            exempt.append((figure, "entered at ZERO, so a +/-10% "
                                   "perturbation moves fv_base by exactly "
                                   "0.0% -- below E108's 1% for any fv_base "
                                   "there is, whatever the growth view"))
            continue
        move = measured.get(figure.name)
        # A MEASURED MOVE IS AUTHORITATIVE EITHER WAY. Where the caller has
        # valued the record it knows the answer, and a looser bound must
        # not talk it out of a refusal -- so limb 3 is consulted only for a
        # leg limb 2 says nothing about.
        if move is not None and abs(move) >= SENSITIVITY_FLOOR:
            blocking_list.append(figure)
            continue
        if move is not None and abs(move) < SENSITIVITY_FLOOR:
            exempt.append((figure, f"a +/-{SENSITIVITY_PERTURBATION:.0%} "
                                   f"perturbation moves fv_base by "
                                   f"{abs(move):.4%}, MEASURED on the "
                                   f"record, below E108's "
                                   f"{SENSITIVITY_FLOOR:.0%}"))
            continue
        # E113 (2026-09-08): a field the valuation never reads. Placed
        # LAST among the exempting limbs and requiring that the measured
        # limb said NOTHING -- if a field ever starts reaching the
        # arithmetic, `measured` speaks first and this never fires.
        if figure.name in exempt_fields and figure.name not in measured:
            exempt.append((figure, EXEMPT_NON_VALUATION))
            continue
        bound = bounds.get(figure.name)
        if bound is not None and bound < SENSITIVITY_FLOOR:
            exempt.append((figure, f"a +/-{SENSITIVITY_PERTURBATION:.0%} "
                                   f"perturbation CANNOT move fv_base by "
                                   f"more than {bound:.4%} on ANY growth "
                                   f"view -- the bridge is net cash, so "
                                   f"the move is at most the leg's own "
                                   f"share of FCF0 -- below E108's "
                                   f"{SENSITIVITY_FLOOR:.0%}"))
            continue
        blocking_list.append(figure)
    blocking = tuple(blocking_list)
    for figure, why in exempt:
        where = figure.period or "market"
        flags.append(Refusal(
            FLAG_EXEMPT, f"{where} {figure.name}",
            f"{EXEMPT_READ_BACK} (E108): entered as {figure.value:,.4g} from "
            f"{figure.source or 'no source'}{cite_page(figure.page)}, never "
            f"read back, and the basis {basis.label} READS it -- but {why}. "
            f"THE READ-BACK IS WAIVED AND THE PROVENANCE IS NOT: the page "
            f"above is still required, and a zero still names its evidence "
            f"under E25. Recomputed when the basis moves."))
    for figure in blocking:
        where = figure.period or "market"
        refusals.append(Refusal(
            REFUSE_UNVERIFIED, f"{where} {figure.name}",
            f"entered as {figure.value:,.4g} from {figure.source or 'no source'}"
            f"{cite_page(figure.page)}, never read back, and the basis "
            f"{basis.label} READS it. "
            f"Verify it against that page and set status: {STATUS_VERIFIED}."))

    if basis is None:
        if not parsed.periods and not parsed.annual:
            refusals.append(Refusal(
                REFUSE_NO_PERIODS, "periods",
                "the file carries no fiscal period. Section 5 needs filed "
                "figures; an empty template loads, and has nothing to value."))
        else:
            quarters = [x.period for x in parsed.periods
                        if period_months(x.period) == QUARTER_MONTHS]
            # WHAT IT FOUND, NOT ONLY WHAT IT WANTED. A count of quarters
            # describes a file of four filed half-years as "0 quarter(s)",
            # which reads as an empty file rather than as twenty-four
            # months the basis rule cannot use. The labels are named so
            # the refusal says what is actually there.
            held = ", ".join(f"`{x.period}`" for x in parsed.periods)
            refusals.append(Refusal(
                REFUSE_NO_BASIS, "basis",
                f"section 5 runs on ONE twelve-month basis (E19) and this file "
                f"supplies none: no twelve-month period entry, and "
                f"{len(quarters)} quarter(s) where four CONSECUTIVE ones are "
                f"needed. The file DOES hold {len(parsed.periods)} filed "
                f"period(s): {held}. Fewer than four is INPUT MISSING and "
                f"section 5 does not run -- nothing is annualised to make up "
                f"the difference."))

    # E106 clause 4, asked HERE as well as on the record, because the two
    # must never disagree: `ratio_states` lets a BOUNDED leg form its ratio
    # (clause 3 -- an absence with a ceiling is not INPUT MISSING), and
    # without this the gate would print MAY RUN over a record that refuses.
    bounds = basis_bounds(parsed, basis)
    if bounds:
        named = "; ".join(
            f"`{f.name}` bounded at {f.bound:,.0f} "
            f"({f.bound_direction or BOUND_REDUCES} fv_base)" for f in bounds)
        if tolerance is None:
            refusals.append(Refusal(
                REFUSE_TOLERANCE, ", ".join(f.name for f in bounds),
                f"the basis carries {len(bounds)} BOUNDED leg(s) -- {named} -- "
                f"and E106 clause 4 asks whether their COMBINED worst case "
                f"moves fv_base by more than "
                f"{INCOMPLETE_LEG_TOLERANCE_PCT}. That question cannot be "
                f"answered here: it needs a fair value to take a percentage "
                f"OF, and this name has no pre-registered growth view on the "
                f"watchlist (E28). AN UNMEASURED BOUND IS NOT A SMALL ONE. "
                f"Register the view, or enter the leg itself."))
        elif tolerance[0] > INCOMPLETE_LEG_TOLERANCE:
            refusals.append(Refusal(
                REFUSE_TOLERANCE, ", ".join(f.name for f in bounds),
                f"the UNDETERMINED legs move fv_base by {tolerance[0]:.1%} "
                f"between them, past E106's {INCOMPLETE_LEG_TOLERANCE_PCT} -- "
                f"{tolerance[1] or named}. E106 clause 2: a leg above the "
                f"bound refuses, exactly as before the ruling."))
        else:
            flags.append(Refusal(
                FLAG_BOUNDED, ", ".join(f.name for f in bounds),
                f"E106 clause 3: {named}. The valuation is struck with the "
                f"leg at the CONSERVATIVE end of its bound and the leg is "
                f"NAMED AS UNDETERMINED wherever the figure appears; measured, "
                f"the bound moves fv_base by {tolerance[0]:.2%}, inside "
                f"E106's {INCOMPLETE_LEG_TOLERANCE_PCT}. The value is struck "
                f"COMPLETE -- not marked, not provisional -- and carries a "
                f"known unquantified gap of that size, which E106 accepts "
                f"knowingly."))

    ratios = ratio_states(parsed, basis)
    annual_used: tuple[str, ...] = ()
    mismatched: dict[str, str] = {}

    if basis is not None:
        resolved = {n: resolve_on_basis(parsed, basis, n) for n in SECTION5_FIELDS}
        annual_used = tuple(n for n, r in resolved.items()
                            if r.source.startswith("annual"))
        mismatched = {n: r.detail for n, r in resolved.items()
                      if r.state == QUALITY_BASIS_MISMATCH}
        if not any(r.value is not None for r in resolved.values()):
            refusals.append(Refusal(
                REFUSE_EMPTY_PERIODS, "basis",
                f"the basis {basis.label} supplies not one figure section 5 "
                f"reads."))

        # E25: EBIT / 0 IS NOT A LARGE NUMBER. Interest coverage is struck
        # on net_finance_costs, and a zero there -- entered with evidence or
        # arrived at by subtraction -- makes Gate 3's >= 5x limb pass on an
        # undefined quantity. Refused where it is formed, not where it is
        # divided, because nothing in this project does the dividing.
        coverage = resolve_on_basis(parsed, basis, COVERAGE_DENOMINATOR).value
        if coverage is None:
            subtraction = parsed.basis_subtraction(
                basis, next(r for r in SUBTRACTIONS
                            if r.net == COVERAGE_DENOMINATOR))
            coverage = subtraction[0] if subtraction else None
        if coverage == 0:
            refusals.append(Refusal(
                REFUSE_ZERO_DENOMINATOR, COVERAGE_DENOMINATOR,
                f"{COVERAGE_DENOMINATOR} is zero on the basis {basis.label}, "
                f"and section 3 Gate 3 strikes interest coverage as EBIT over "
                f"it. EBIT / 0 is undefined, not large: any reader -- person "
                f"or code -- that treats it as a big number passes a >= 5x "
                f"limb on nothing (E25). Enter the figure the accounts state, "
                f"or leave it blank so the limb reads DATA MISSING."))

        # AGE, MEASURED ON THE BASIS. A twelve-month window is as old as the
        # day it STOPS -- ranking.py rule 5, and now one date rather than a
        # scan over whichever rows happened to be read.
        age = (as_of - basis.end).days
        if age > MAX_REPORT_AGE_DAYS:
            refusals.append(Refusal(
                REFUSE_STALE, "accounts",
                f"the basis {basis.label} ends {basis.end.isoformat()}, "
                f"{age} days before {as_of.isoformat()}. Too old to divide "
                f"into a price from today."))

    # A PRICED figure ages differently from an account. Enterprise value and
    # market capitalisation are struck on a date, and BWY.L is the case: an
    # EBIT from 2024-07-31 divided into an enterprise value from 2026-08-21,
    # 751 days inside one quotient, with nothing saying so.
    if any(f.present for f in parsed.market.values()) and parsed.market_as_of:
        age = (as_of - parsed.market_as_of).days
        if age > MAX_CLOSE_AGE_DAYS:
            refusals.append(Refusal(
                REFUSE_PRICED_STALE, "market figures",
                f"priced {parsed.market_as_of.isoformat()}, {age} days before "
                f"{as_of.isoformat()}. A market figure is struck on a date; "
                f"re-read it rather than dividing an old one into today."))

    # E34: FCF0 IS DATA MISSING UNTIL THE FILE SAYS WHERE THE FILER BOOKS
    # ITS INTEREST. Refused only where the basis actually supplies an
    # operating cash flow -- a file with nothing to value refuses for that
    # reason instead, and two refusals saying the same thing help nobody.
    if basis is not None and parsed.interest_in_ocf is None:
        if resolve_on_basis(parsed, basis, "operating_cash_flow").value is not None:
            refusals.append(Refusal(
                REFUSE_INTEREST_UNCLASSIFIED, "interest_in_ocf",
                "the file does not say whether this filer's operating cash "
                "flow already bears its interest (E34). IAS 7.31-34 allows "
                "either and ASC 230 allows only the first, so the SAME "
                "`operating cash flow - capex` is a flow to the FIRM for one "
                "filer and a flow to EQUITY for the next -- and section 5 "
                "subtracts net debt from it either way, which charges the "
                "same interest twice for the second. Read the cash flow "
                "statement and add `interest_in_ocf:` with its value, source "
                "and page."))
    # E70: the same teeth for the lease. A file that does not say whether
    # its operating cash flow bears the operating lease payments cannot
    # form FCF0 -- for a US GAAP filer the payment is inside the flow and
    # the liability is in net debt, and only the declaration says so.
    if basis is not None and parsed.operating_leases_in_ocf is None:
        if resolve_on_basis(parsed, basis, "operating_cash_flow").value is not None:
            refusals.append(Refusal(
                REFUSE_LEASES_UNCLASSIFIED, "operating_leases_in_ocf",
                "the file does not say whether this filer's operating cash "
                "flow bears its operating lease payments (E70). ASC "
                "842-20-45-5(a) puts them INSIDE operating cash flow and "
                "IFRS 16.50(b) puts the principal in financing; the lease "
                "liability sits in net debt either way (E35, E65), so for a "
                "US GAAP filer the same obligation is charged twice unless "
                "the payment is added back. Add `operating_leases_in_ocf:` "
                "with its value, source and page."))

    # E34 GIVES FCF0 TEETH. "Absent -> DATA MISSING, section 5 does not
    # run" is not a rule until something refuses on it: a ratio that reads
    # `input missing` blocks nothing by itself, which is how a gate could
    # say MAY RUN while the flow the DCF discounts does not exist.
    if basis is not None and resolve_on_basis(
            parsed, basis, "operating_cash_flow").value is not None:
        fcf0 = next((r for r in ratios if r.name == FCF0_RATIO), None)
        if fcf0 is not None and fcf0.state != RATIO_OK and not any(
                r.kind == REFUSE_INTEREST_UNCLASSIFIED for r in refusals):
            refusals.append(Refusal(
                REFUSE_NO_FCF0, FCF0_RATIO,
                f"{fcf0.detail}. FCF0 is the ONE flow section 5 discounts "
                f"(E34); without it there is no fair value to strike and "
                f"nothing here estimates one."))

    # A UNIT MIX ON A LEG THE DCF DIVIDES BY (report B 7.1). Refused here
    # rather than at the load because the five scale-stable fields have a
    # load-time guard and these do not: a legitimate 1000x step between two
    # neighbouring quarters of a small line is possible, and refusing the
    # WHOLE FILE for it would leave the reader nowhere to state it. Section
    # 5 does not run; the file still loads and still prints.
    for jump in scale_jumps(parsed):
        refusals.append(Refusal(
            REFUSE_UNIT_MIX, jump.field,
            f"{jump.field} jumps by {jump.factor:,.0f}x between "
            f"{jump.low_label} ({jump.low:,.0f}) and {jump.high_label} "
            f"({jump.high:,.0f}), across {jump.span}. Section 5 DIVIDES AND "
            f"DISCOUNTS this leg: a figure out by a round thousand produces "
            f"a fair value out by a round thousand and nothing downstream "
            f"can see it. Re-read both periods from one document in one "
            f"unit -- do not rescale a figure by hand."))

    for ratio in ratios:
        if ratio.state != RATIO_MIXED_PERIODS or ratio.for_ranking_key:
            continue
        refusals.append(Refusal(REFUSE_MIXED_PERIODS, ratio.name, ratio.detail))

    flags.extend(
        Refusal(FLAG_SHARE_BASIS_STEP, jump.field,
                f"{jump.field} steps by {jump.factor:,.2f}x between "
                f"{jump.low_label} ({jump.low:,.4g}) and {jump.high_label} "
                f"({jump.high:,.4g}). A per-share figure and a share count "
                f"move together at a SPLIT and not otherwise: check the page "
                f"reference of the older figure for the basis it is on. "
                f"NOTHING IS RESCALED, and this does not refuse section 5 -- "
                f"the newest year is unaffected, and a five-year per-share "
                f"proxy is not.")
        for jump in share_basis_steps(parsed))

    return Section5Gate(
        ticker=parsed.ticker, as_of=as_of,
        period=basis.label if basis else None,
        refusals=tuple(refusals), ratios=ratios, flags=tuple(flags),
        missing=parsed.missing(), unverified=unverified,
        annual_used=annual_used, shadowed={}, displaced={},
        basis=basis, mismatched=mismatched, blocking=blocking,
        unread=tuple((f, unread_reason(parsed, basis, f)) for f in unread)
        if basis is not None else
        tuple((f, "the file supplies no basis, so nothing is read yet")
              for f in unread),
        newer_filed=newer_filed_periods(parsed, basis),
    )


# --- the report -----------------------------------------------------------


def _fmt(value: float | None, spec: FieldSpec | None = None) -> str:
    if value is None:
        return "DATA MISSING"
    if spec is not None and spec.kind == "ratio":
        return f"{value:.4f}"
    if spec is not None and spec.kind in ("per_share", "multiple"):
        return f"{value:,.2f}"
    return f"{value:,.2f}"


def _tested_against(gate: "Section5Gate") -> str:
    """E21 condition 3: the basis the verification was tested against.

    Printed whether the gate opened or closed, because the answer depends
    on it: the same file with the same flags may go from MAY RUN to
    REFUSED when a newer quarter arrives and the window moves onto figures
    nobody has read back.
    """
    if gate.basis is None:
        return ("**VERIFICATION TESTED AGAINST NO BASIS.** The file supplies "
                "no twelve-month window, so no figure is read and none was "
                "tested (E19, E21).")
    return (f"**VERIFICATION TESTED AGAINST THE BASIS `{gate.basis.label}`, "
            f"ending {gate.basis.end.isoformat()}.** "
            f"{len(gate.blocking)} of {len(gate.unverified)} "
            f"{STATUS_UNVERIFIED} figure(s) are read at it and refuse; the "
            f"rest are named below and do not (E21). **A DIFFERENT BASIS "
            f"TESTS A DIFFERENT SET** -- this answer holds for this window "
            f"and is re-decided, not inherited, when the window moves.")


def _group(reads: tuple[str, ...]) -> str:
    return ", ".join(reads)


def render_report(parsed: ManualFile, gate: Section5Gate) -> str:
    """The whole file, said back with its origin on every line."""
    out = [f"# vss manual -- {parsed.ticker} ({parsed.name}) -- "
           f"{gate.as_of.isoformat()}", ""]
    prose = ORIGIN_PROSE[parsed.origin].format(path=parsed.path)
    out.append(f"**ORIGIN: {parsed.origin}.** {prose} "
               f"{ORIGIN_CONTRAST[parsed.origin]}")
    out.append("")
    out.append(f"- reporting currency `{parsed.reporting_currency}` · quote "
               f"currency `{parsed.quote_currency}` · sector "
               f"`{parsed.sector}` · reports {parsed.reporting_frequency}")
    out.append(f"- units: money `{parsed.money_unit or 'NOT STATED'}` · share "
               f"counts `{parsed.share_unit or 'NOT STATED'}`"
               + ("" if parsed.money_unit and parsed.share_unit else
                  " -- a run record divides on these declarations and is "
                  "DATA MISSING per share until both are stated"))
    if parsed.market_as_of:
        out.append(f"- market figures priced {parsed.market_as_of.isoformat()}")
    documents = sorted({p.document for p in parsed.periods if p.document})
    if documents:
        out.append("- documents read:")
        for doc in documents:
            out.append(f"  - {doc}")
    out.append("")

    # --- the gate, first, because it decides whether the rest may be used
    if gate.refused:
        out.append("## SECTION 5 IS REFUSED")
        out.append("")
        out.append("Section 5 does not run on these figures. Each reason is "
                   "listed with what would clear it. Nothing below is a fair "
                   "value and nothing below may be entered as `fv_base`.")
        out.append("")
        out.append("| Refused on | Subject | Why |")
        out.append("|---|---|---|")
        for refusal in gate.refusals:
            out.append(f"| `{refusal.kind}` | {refusal.subject} | {refusal.detail} |")
        out.append("")
        out.append(_tested_against(gate))
        out.append("")
    else:
        out.append("## SECTION 5 MAY RUN")
        out.append("")
        out.append(f"Every figure the basis READS is {STATUS_VERIFIED} (E21), the "
                   f"accounts are inside the staleness limit, and every ratio "
                   f"section 5 forms has every leg on the one basis. The chain "
                   f"itself is still run BY HAND -- this says the inputs may be "
                   f"used, not what they are worth.")
        out.append("")
        out.append(_tested_against(gate))
        out.append("")

    if gate.flags:
        out.append("## FLAGGED, AND NOT A REFUSAL")
        out.append("")
        out.append("Section 5 runs regardless. These are facts about the "
                   "FILE that a reader has to know before using a figure "
                   "from a year other than the basis.")
        out.append("")
        out.append("| Flag | Subject | What it says |")
        out.append("|---|---|---|")
        for flag in gate.flags:
            out.append(f"| `{flag.kind}` | {flag.subject} | {flag.detail} |")
        out.append("")

    # --- E21 condition 1: what was NOT tested, named rather than hidden
    if gate.unread:
        out.append("## UNVERIFIED, AND NOT READ AT THIS BASIS")
        out.append("")
        out.append(f"{len(gate.unread)} entered figure(s) are still "
                   f"{STATUS_UNVERIFIED} and **do not refuse section 5**: this "
                   f"basis does not read them, so no number section 5 produces "
                   f"can be wrong because of them (E21). They are named here "
                   f"rather than hidden -- the flag is still theirs to clear, "
                   f"and a basis that moves may start reading them.")
        out.append("")
        out.append("| Figure | Value | Status | Why it does not block |")
        out.append("|---|---|---|---|")
        for figure, why in gate.unread:
            where = figure.period or "market"
            out.append(f"| `{where}` `{figure.name}` | {figure.value:,.4g} | "
                       f"{STATUS_UNVERIFIED} | {why} |")
        out.append("")

    # --- E31's condition: what the file holds that the basis passed over.
    # Printed whether or not section 5 is refused, because the naming is
    # the price of standing on the year as filed and does not depend on
    # whether some other reason refuses the run.
    if gate.newer_filed:
        out.append("## FILED, NEWER THAN THE BASIS, AND NOT READ")
        out.append("")
        out.append(f"The basis is **{gate.basis.label}**, ending "
                   f"{gate.basis.end.isoformat()}. The file holds "
                   f"{len(gate.newer_filed)} filed period(s) inside a "
                   f"twelve-month window NEWER than that, and the basis read "
                   f"none of them (E31). They are named here rather than "
                   f"passed over silently: section 5's figures are the "
                   f"basis's, and this is what the company has published "
                   f"since.")
        out.append("")
        out.append("| Period | Window end | Read at this basis |")
        out.append("|---|---|---|")
        for entry in gate.newer_filed:
            out.append(f"| `{entry.period}` | {entry.period_end.isoformat()} "
                       f"| **NOT READ** |")
        out.append("")

    # --- the input block
    out.append("## SECTION 5 INPUT BLOCK")
    out.append("")
    basis = gate.basis
    if basis is None:
        if not parsed.periods and not parsed.annual:
            out.append("No fiscal period is entered. The file is a valid empty "
                       "template: it loads, and it supplies nothing.")
        else:
            out.append("**No twelve-month basis.** Section 5 runs on one window "
                       "(E19) and this file supplies none, so there is no input "
                       "block to show. The refusal above says why.")
        out.append("")
    else:
        out.append(f"**BASIS: `{basis.label}`, the twelve months ending "
                   f"{basis.end.isoformat()}.** Every flow below is that whole "
                   f"window and every stock is taken at its end (E19). A "
                   f"summed flow names the entries it was built from, every "
                   f"time it appears, and is **written to no file**: it has no "
                   f"page and no status of its own, and is usable only where "
                   f"all four of its quarters are VERIFIED.")
        out.append("")
        out.append("| Figure | Value | From | Status | Read by | Origin |")
        out.append("|---|---|---|---|---|---|")
        for spec in FIELDS:
            r = resolve_on_basis(parsed, basis, spec.name)
            if r.value is not None:
                value, where = _fmt(r.value, spec), r.source
                # E40: the KIND is printed beside every VERIFIED figure.
                kinds = "/".join(sorted({f.verified_kind for f in r.figures
                                         if f.verified and f.verified_kind}))
                verified = f"VERIFIED ({kinds})" if kinds else "VERIFIED"
                status = (verified if r.verified else
                          "NOT PRESENTED (E85)" if any(
                              f.status == STATUS_NOT_PRESENTED for f in r.figures)
                          else "COMPUTED" if len(r.components) > 1 else "UNVERIFIED")
                if len(r.components) > 1:
                    status = "SUMMED, " + (f"all {verified}" if r.verified
                                           else "not all VERIFIED")
            elif r.state == QUALITY_BASIS_MISMATCH:
                value, where = "NOT MEANINGFUL", r.source or "--"
                status = (f"stated at {r.end.isoformat()}, not the window end"
                          if spec.name in STOCK_FIELDS
                          else f"another twelve months, to {r.end.isoformat()}")
            else:
                value, where, status = "DATA MISSING", "--", "--"
            out.append(f"| `{spec.name}` | {value} | {where} | {status} | "
                       f"{_group(spec.reads)} | `{parsed.origin}` |")
        out.append("")
        zeros = [f for f in parsed.all_figures() if f.value == 0]
        if zeros:
            out.append("**ZEROS, AND WHAT THE READER SAW (E25).** A zero is a "
                       "claim about the company, not an absence: each one below "
                       "names the form of evidence behind it.")
            out.append("")
            out.append("| Figure | Period | Form | Page |")
            out.append("|---|---|---|---|")
            for f in sorted(zeros, key=lambda f: (f.period, f.name)):
                if f.not_presented is not None:
                    # E85: not a zero the issuer states -- a recorded search.
                    form = (f"NOT PRESENTED (E85): {f.not_presented.describe()}"
                            f" -- the concept appears nowhere in that report; "
                            f"entered at nil, not a zero the issuer states")
                else:
                    form = f.zero_basis or "none required (a wrong zero here fails a gate rather than passing one)"
                if f.verified_kind == KIND_CAPTION_STATEMENT:
                    # E78: the sentence the zero stands on, beside its form.
                    form += (f" -- VERIFIED ({KIND_CAPTION_STATEMENT}, E78) on "
                             f"the issuer's words: \"{f.statement}\"")
                out.append(f"| `{f.name}` | {f.period or 'market'} | {form} | "
                           f"{f.page or '--'} |")
            out.append("")

        columns = [f for f in parsed.all_figures() if f.cumulative is not None]
        if columns:
            out.append("**CUMULATIVE COLUMNS (E86).** The issuer prints these "
                       "flows year-to-date only; each quarter below is the "
                       "code's difference of two stated columns, both printed "
                       "with their pages. A column without its prior is an "
                       "operand on file and no quarter.")
            out.append("")
            out.append("| Figure | Period | Columns |")
            out.append("|---|---|---|")
            for f in sorted(columns, key=lambda f: (f.period, f.name)):
                out.append(f"| `{f.name}` | {f.period} | {f.page_provenance} |")
            out.append("")

        legs, why = capex_legs(parsed, basis)
        values = {n: resolve_on_basis(parsed, basis, n) for n in legs}
        total = sum(r.value for r in values.values() if r.value is not None)
        out.append(
            f"**CAPEX ON THE BASIS (E23): {why}.** "
            + (" ".join(f"`{n}` {r.value:,.2f} [{r.source}]."
                        for n, r in values.items() if r.value is not None)
               or "Nothing to read: section 5.1 C's free cash flow basis 1 is "
                  "DATA MISSING on this basis.")
            + (f" Total capex on the basis: {total:,.2f}."
               if any(r.value is not None for r in values.values()) else ""))
        out.append("")
        subs = {r.net: parsed.basis_subtraction(basis, r) for r in SUBTRACTIONS}
        subs = {k: v for k, v in subs.items() if v}
        if subs:
            out.append("**SUBTRACTED ON THE BASIS** (E16, E18): every operand "
                       "resolved on the same window, so they cannot disagree "
                       "with the net they make.")
            out.append("")
            for name, (value, a, b, c) in sorted(subs.items()):
                line = (f"- `{name}` = {value:,.2f} — {a.name} "
                       f"{a.value:,.0f} [{a.source}] − {b.name} "
                       f"{b.value:,.0f} [{b.source}]")
                if c is not None:
                    # E54: the optional third leg, subtracted where the
                    # issuer states it.
                    line += f" − {c.name} {c.value:,.0f} [{c.source}]"
                out.append(line)
            out.append("")
        flows = [n for n in sorted(gate.mismatched) if n not in STOCK_FIELDS]
        stocks = [n for n in sorted(gate.mismatched) if n in STOCK_FIELDS]
        if flows:
            out.append("**NOT MEANINGFUL — another twelve months.** These are "
                       "twelve-month figures of a DIFFERENT twelve months than "
                       "the basis. Nothing re-bases them:")
            out.append("")
            for name in flows:
                out.append(f"- `{name}` — {gate.mismatched[name]}")
            out.append("")
        if stocks:
            out.append("**NOT MEANINGFUL — another period end.** A stock has "
                       "no length: these are balances on a DATE that is not "
                       "the window's end (E19, E20). Nothing moves them:")
            out.append("")
            for name in stocks:
                out.append(f"- `{name}` — {gate.mismatched[name]}")
            out.append("")

    # --- the annual block, and what it is and is not used for
    if parsed.annual:
        out.append("## THE ANNUAL BLOCK")
        out.append("")
        out.append(f"{len(parsed.annual)} fiscal year(s): "
                   + ", ".join(f"`FY{e.fiscal_year}` closing "
                               f"{e.period_end.isoformat()}"
                               for e in parsed.annual) + ".")
        out.append("")
        out.append("It holds figures the company publishes only once a year. "
                   "**It is excluded from every trailing window by "
                   "construction** — never summed, never combined with a "
                   "period entry, and it reaches the ranking key not at all: "
                   "under E13 that key reads a trailing twelve months from "
                   "`periods:` alone, and `as_record` emits no series point "
                   "from here.")
        out.append("")
        if gate.annual_used:
            out.append("Section 5 takes these from it, because `periods:` "
                       "does not answer them:")
            out.append("")
            for name in gate.annual_used:
                figure = parsed.annual_figure(name)
                out.append(f"- `{name}` = {_fmt(figure.value, FIELDS_BY_NAME.get(name))}"
                           f" [{figure.period}] — {figure.status_with_kind}")
            out.append("")
        if gate.displaced:
            out.append("**USED IN PLACE OF A SHORTER PERIOD FIGURE.** E17: "
                       "`periods:` wins only at EQUAL LENGTH, and a quarter "
                       "never displaces a year. Both are named, because "
                       "silently preferring either would leave you unable to "
                       "see which basis the answer stands on:")
            out.append("")
            for name, (label, months, value) in sorted(gate.displaced.items()):
                annual = parsed.annual_figure(name)
                spec = FIELDS_BY_NAME.get(name)
                out.append(
                    f"- `{name}` — **used: {_fmt(annual.value, spec)}** "
                    f"[{annual.period}, 12 months]. NOT used: "
                    f"{_fmt(value, spec)} [{label}, {months} months].")
            out.append("")
        if gate.shadowed:
            out.append("**IGNORED — `periods:` answers these instead.** E15: "
                       "where a figure is in both blocks, `periods:` wins. The "
                       "entries stay in the file and are not read; a file must "
                       "not be able to answer the same question twice.")
            out.append("")
            for name, period in sorted(gate.shadowed.items()):
                out.append(f"- `{name}` — the annual entry is ignored; "
                           f"`{period}` supplies it")
            out.append("")
        if not gate.annual_used and not gate.shadowed and not gate.displaced:
            out.append("It supplies nothing section 5 reads.")
            out.append("")

    # --- ratios: one period per ratio, said out loud
    out.append("## ONE FISCAL PERIOD PER RATIO")
    out.append("")
    out.append("Every ratio is formed from ONE entry of `periods:`, and never "
               "straddles the two blocks: E15 forbids combining an annual "
               "figure with a period one. A ratio whose legs sit wholly "
               "inside ONE annual entry is not formed either — E15 does not "
               "say it may be, and this does not decide it.")
    out.append("")
    out.append("Each ratio is formed from ONE period entry. A leg that is in "
               "NO period is `input missing` -- reported, and not a refusal, "
               "because absence is the ordinary third state. A leg that EXISTS "
               "in an earlier period is `periods do not match`: it is not "
               "borrowed, because two periods are not one ratio, and that is "
               "what section 5 is refused on. The quality leg belongs to the "
               "ranking key and never refuses section 5.")
    out.append("")
    # E123 (2026-09-20): the measured figures, printed where the operating
    # asset is inventory. They decide nothing and carry no threshold.
    if inventory_operating_asset(parsed):
        declared = parsed.operating_asset_is_inventory
        out.append("## E123 -- GATE 3's CASH LIMBS ARE DATA MISSING FOR THIS FILER")
        out.append("")
        out.append(f"**The operating asset is inventory and its purchase runs "
                   f"through operating cash flow**, declared in the file: "
                   f"{declared.page} (`{declared.source}`).")
        out.append("")
        out.append("So Gate 3's **FCF-positivity limb** and its **leverage "
                   "limb** are **DATA MISSING and out of the gate count**, and "
                   "§4.4 rebases as E99 does for Gate 4. Interest coverage is "
                   "untouched. What is printed instead:")
        out.append("")
        for line in capitalisation(parsed, gate.basis).lines():
            out.append(f"- {line}")
        out.append("")

    out.append("| Ratio | Read by | Period | State |")
    out.append("|---|---|---|---|")
    for ratio in gate.ratios:
        out.append(f"| {ratio.name} | {ratio.reads} | "
                   f"`{ratio.period or '--'}` | {ratio.state} -- {ratio.detail} |")
    out.append("")

    # --- what is not here
    if gate.missing:
        out.append("## DATA MISSING")
        out.append("")
        out.append("No period supplies a value for these. They are blank, not "
                   "zero, and nothing substitutes a near neighbour for them:")
        out.append("")
        for name in gate.missing:
            spec = FIELDS_BY_NAME.get(name)
            reads = _group(spec.reads) if spec else "ranking key"
            out.append(f"- `{name}` -- read by {reads}")
            # E82: a NAMED ABSENCE -- the file carries the field with no
            # value and a page saying which printed line it refused.
            for figure in named_absences(parsed, name):
                out.append(f"  - named (E82) -- {figure.period or 'market'}: "
                           f"{figure.page}")
        out.append("")
    # E82: every named absence, whether or not the field resolves on the
    # basis from another entry -- Reckitt's half-year line is refused while
    # its year is hand-read, and both facts belong on the page.
    absences = [f for f in parsed.all_figures() if not f.present and f.page]
    if absences:
        out.append("## NAMED ABSENCES (E82)")
        out.append("")
        out.append("Entered with no value and a page: the reader met a printed "
                   "line and refused it, and says which and why. Not a figure, "
                   "not UNVERIFIED, and never read by the basis.")
        out.append("")
        out.append("| Period | Figure | Why |")
        out.append("|---|---|---|")
        for f in absences:
            out.append(f"| `{f.period or 'market'}` | `{f.name}` | {f.page} |")
        out.append("")

    # --- provenance, every figure, every period
    entered = [f for f in parsed.all_figures() if f.present]
    out.append("## PROVENANCE")
    out.append("")
    if not entered:
        out.append("No figure carries a value. There is nothing to attribute.")
        out.append("")
    else:
        out.append("| Period | Figure | Value | Status | Origin | Source | Page |")
        out.append("|---|---|---|---|---|---|---|")
        for figure in entered:
            spec = FIELDS_BY_NAME.get(figure.name)
            out.append(
                f"| `{figure.period or 'market'}` | `{figure.name}` | "
                f"{_fmt(figure.value, spec)} | {figure.status_with_kind} | `{parsed.origin}` | "
                f"{figure.source or ''} | {figure.page or ''} |")
        out.append("")

    out.append("## THE RANKING KEY")
    out.append("")
    out.append("The E6 ranking key is a DIFFERENT consumer from section 5 and "
               "is not gated on the status flag: it produces review work, not "
               "a price, and it says DATA MISSING for itself. What it is given "
               f"is the origin -- a row built from this file carries "
               f"`origin={parsed.origin}` in `ranking.csv`, beside the vendor "
               f"rows.")
    out.append("")
    record = as_record(parsed, as_of=gate.as_of)
    out.append(f"- record status: `{record.status}`"
               + (f" -- {record.error}" if record.error else ""))
    for line in ("Gross Profit", "Total Assets",
                 "Total Operating Income As Reported"):
        found = record.latest(line)
        if found is None:
            out.append(f"- `{line}`: DATA MISSING")
        else:
            out.append(f"- `{line}`: {found[1]:,.2f} at {found[0].isoformat()}")
    out.append("")
    return "\n".join(out)


def registered_view_record(parsed: "ManualFile", *, entries=None):
    """The record for E108's measured limb and E106's tolerance, or None.

    **THE VIEW IS READ, NEVER FORMED.** E28 pre-registers it and the owner
    writes it; this asks the watchlist entry for the name and uses the three
    rates it finds. A name with no registered view gets None -- which is
    E28's rule showing through, and it makes the gate STRICTER rather than
    looser: no measured exemption, and no answer to E106 clause 4.

    `entries` is the LOADED watchlist, for a caller that already has it.
    The watchlist is a 2,400-line YAML file and this reads it once per
    name; a caller striking the gate for every store on disk was reading
    it thirty-three times, which is twenty-nine of the thirty-nine seconds
    that took. Absent, the file is read as before.
    """
    try:
        from pathlib import Path as _Path

        from .config import load_watchlist
        from .runrecord import Growth, Rate, from_store
        if entries is None:
            entries = load_watchlist(_Path("config/watchlist.yaml"))
        entry = next((e for e in entries if e.ticker == parsed.ticker), None)
        if entry is not None and entry.growth is not None:
            base, bear = entry.growth.base, entry.growth.bear
            bull, view_file = entry.growth.bull, entry.growth.view
            view_date = entry.growth.registered
        else:
            # E109's OWN ARRANGEMENT, not a new rule. E109 put the
            # machine-readable block on the WATCHLIST ENTRY and ruled in the
            # same breath that a name with a registered view and NO entry
            # stays off the watchlist, because entering one stamps
            # `dd_at_entry` and freezes Gate 1 under E12. Five such names
            # existed the day it was written; BOUV.OL and MEKKO.HE joined
            # them on 2026-09-08. Their views are real, pre-registered and
            # dated -- they simply live in the FILE, which
            # `readiness.read_growth_view` already parses. Reading it here
            # is what lets E108's measured limb run for exactly the names
            # E109 chose not to enter, and it forms nothing: a file with no
            # three readable rates still gives None.
            from .readiness import read_growth_view
            view = read_growth_view(parsed.ticker)
            if view is None or not view.registered:
                return None
            base, bear, bull = view.base, view.bear, view.bull
            view_file, view_date = str(view.path), None
        basis = section5_basis(parsed)
        if basis is None:
            return None
        return from_store(
            parsed, basis,
            growth=Growth(base=base, bear=bear, bull=bull,
                          view_file=view_file, view_date=view_date),
            run_ts=datetime.now(timezone.utc),
            rate=Rate(core_expected_return=0.070, premium=0.025),
            tool_commit="E106/E108, on the registered view")
    except Exception:      # noqa: BLE001 -- an answer that cannot be computed is not given
        return None


def registered_view_sensitivity(parsed: "ManualFile") -> dict[str, float]:
    """E108's MEASURED limb, on the growth view the WATCHLIST registered.

    **THE VIEW IS READ, NEVER FORMED.** E28 pre-registers it and the owner
    writes it; this asks the watchlist entry for the name and uses the three
    rates it finds, or returns nothing at all. A name with no registered
    view has no `fv_base` to take 1% of, so it has no measured limb -- which
    is E28's rule showing through rather than a gap here.

    A failure of any kind is an EMPTY answer and never an exception: the
    floor is an exemption, so failing to compute it can only make the gate
    stricter, and a gate that got stricter because a file was unreadable is
    a gate that behaved correctly.
    """
    record = registered_view_record(parsed)
    try:
        if record is None:
            return {}
        return _with_subtracted_halves(parsed, record.sensitivity())
    except Exception:      # noqa: BLE001 -- an exemption that cannot be computed is not granted
        return {}


def _with_subtracted_halves(parsed: "ManualFile",
                            measured: dict[str, float]) -> dict[str, float]:
    """E18's two operands, keyed by their own field names.

    **THE RECORD CARRIES THE NET AND THE GATE REFUSES ON THE HALVES.** Where
    E18 forms `net_interest_paid` from `finance_costs_paid` less
    `finance_income_received`, the run record holds one leg named for the
    net and `sensitivity` can only speak of that. The store holds two
    figures, each with its own status, and each is what the gate looks up.

    The scaling is EXACT, not an approximation: `equity_value_per_share` is
    linear in its `fcf0` argument, so a perturbation of d moves `fv_base` in
    proportion to d. A half perturbed by 10% moves the net by 10% of the
    HALF, so its share of the net's measured move is |half| / |net|.

    A net of zero, an absent half or a missing basis leaves the map
    untouched -- an exemption that cannot be computed is never granted.
    """
    basis = section5_basis(parsed)
    if basis is None:
        return measured
    out = dict(measured)
    for rule in SUBTRACTIONS:
        net_move = out.get(rule.net)
        if net_move is None:
            continue
        net_value = subtracted_on_basis(parsed, basis, rule.net)
        if not net_value:
            continue
        for half in (rule.minuend, rule.subtrahend, rule.optional_subtrahend):
            if not half or half in out:
                continue
            value = resolve_on_basis(parsed, basis, half).value
            if value is None:
                continue
            out[half] = net_move * abs(value) / abs(net_value)
    return out


def registered_view_tolerance(parsed: "ManualFile") -> "tuple[float, str] | None":
    """E106 clause 4's answer for the gate, or None where it cannot be asked."""
    record = registered_view_record(parsed)
    if record is None:
        return None
    try:
        fraction, _move, named = record.tolerance()
    except Exception:      # noqa: BLE001 -- unmeasurable is not "inside"
        return None
    return fraction, named


def gate_on_registered_view(parsed: "ManualFile", *, as_of: date,
                            entries=None) -> "Section5Gate":
    """The gate as `vss manual` strikes it: E108's MEASURED limb included.

    ONE CALL, TWO READERS. `run_manual` prints this gate and
    `vss.overview` counts its `blocking` figures into the queue, and the
    two must not be able to disagree about how many read-backs a name is
    waiting on. A name with no registered growth view has no record, so
    the measured limb is empty and the gate is STRICTER -- which is E28
    showing through, not a gap.

    **A LIMB THAT CANNOT BE COMPUTED IS NOT GRANTED, AND NEVER RAISES.**
    `registered_view_sensitivity` states the rule and this now keeps it:
    both limbs are EXEMPTIONS, so failing to compute one can only make the
    gate stricter, and a gate that got stricter because a store is short of
    a declaration is a gate behaving correctly. Before this, a store whose
    record would not value crashed `vss manual` with a traceback --
    SYNSAM.ST does, on E34's `interest_in_ocf`, and the crash reported
    nothing about the store at all.
    """
    record = registered_view_record(parsed, entries=entries)
    measured: dict[str, float] = {}
    tolerance = None
    if record is not None:
        try:
            measured = record.sensitivity()
        except Exception:  # noqa: BLE001 -- see the docstring
            log.warning("%s: E108's measured limb could not be computed, so "
                        "no leg is exempted by it", parsed.ticker)
        try:
            bound, _, why = record.tolerance()
            tolerance = (bound, why)
        except Exception:  # noqa: BLE001 -- see the docstring
            log.warning("%s: E106's tolerance could not be computed",
                        parsed.ticker)
    return section5_gate(parsed, as_of=as_of, measured_exempt=measured,
                         tolerance=tolerance)


def run_manual(*, ticker: str, as_of: date | None = None,
               directory: Path = MANUAL_DIR) -> tuple[int, str]:
    """Load, validate, gate and report. Returns (exit_code, report_markdown).

    Exit 1 when section 5 is refused. A load failure raises ManualError and
    is handled where every other ConfigError is -- loudly, exit 2, never a
    skipped file.
    """
    as_of = as_of or date.today()
    parsed = load_manual(ticker, directory=directory)
    gate = gate_on_registered_view(parsed, as_of=as_of)
    report = render_report(parsed, gate)
    log.info("%s: %d figure(s) entered, %d unverified of which %d read at "
             "the basis, section 5 %s",
             parsed.ticker, len([f for f in parsed.all_figures() if f.present]),
             len(gate.unverified), len(gate.blocking),
             "REFUSED" if gate.refused else "may run")
    return (1 if gate.refused else 0), report
