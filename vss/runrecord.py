"""The section 5 RUN RECORD: every input and every choice, or no fair value.

WHY THIS EXISTS. REVIEW-4 report C Part 11 asked one question of four
different records -- the store row, the watchlist entry, the `vss manual`
report and the emitted XBRL file -- and got the same answer from all four:
**no record produced by the code holds more than one of the nine input
classes a fair value stands on.** The only record that holds all the inputs
of one is a gitignored markdown written by hand for one name, and it omits
the share-based compensation treatment, the interest classification and the
discounting conventions -- the three classes report C Part 9 found unpinned.

For the two HELD names the record is a prose paragraph in
`config/watchlist.yaml`. SAP.DE's carries numbers and one date, the price's.
LIAB.ST's carries numbers and **no date at all**. Both fair values can be
RE-TYPED from prose; neither can be regenerated as a dated, declared
calculation, and the difference between those two states is the whole of
what this module is for.

THE RULE (Phase 3 of the REVIEW-4 build, 2026-08-26):

    A RUN WITHOUT A COMPLETE RECORD DOES NOT PRINT A FAIR VALUE.

Not "prints one with a warning" and not "prints one and logs". `strike`
raises. A fair value whose basis nobody wrote down is a number that will be
read months later as though somebody had.

THE EIGHT DECLARATIONS, from report C Part 10, are the fields of
`RunRecord`, one for one:

  1 share-count basis, WITH ITS DATE          `shares`
  2 share-based compensation, treatment and amount   `sbc`
  3 interest: where the filer books it, and therefore what FCF0 is
                                               `interest`
  4 the enterprise-to-equity bridge, item by item, in or out   `bridge`
  5 the DCF conventions                        `conventions`
  6 r with its anchor, and g with the view it came from   `rate`, `growth`
  7 the three as-of dates, plus the price date `dates`
  8 provenance per input                       `inputs`

WHAT A RECORD IS NOT. It is not a cache and it is not a result: it holds
INPUTS and CHOICES, and the arithmetic is re-run from them every time. That
is what makes "regenerate from the record alone" a test of the record rather
than of a stored answer -- and it is why a convention change (a mid-year
factor, a different first-year flow) moves a replayed value instead of
leaving every stored `fv_base` looking current, which is defect (vi) of
report C 11.2.

A HAND INPUT BELONGS IN THE RECORD. DECK's borrowings are nil, and that is a
SENTENCE in a 10-Q (E25's `note` basis), not a tagged fact -- the annual XBRL
path cannot emit it, because absence of a tag is DATA MISSING and inventing a
zero from it is the substitution that path exists not to make. So the zero is
entered ONCE, HERE, with its page, as an `Input` whose `entered_by` is
`hand`. The record is then complete and the replay needs no hand input,
because the hand input IS the record. That is the difference between a hand
input and an unrecorded one.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field, fields as dataclass_fields
from datetime import date, datetime, timezone
from typing import Any, Mapping, Sequence

from .manual import (ACCRUAL_PROXY_LABEL, BOUND_EITHER, BOUND_RAISES,
                     CASH_PAID_ONLY_LABEL,
                     BOUND_REDUCES, INTEREST_EXPENSE_ONLY_LABEL,
                     UNIT_SCALE,
                     INCOMPLETE_LEG_TOLERANCE as _INCOMPLETE_LEG_TOLERANCE,
                     SENSITIVITY_FLOOR as _SENSITIVITY_FLOOR,
                     SENSITIVITY_PERTURBATION as _SENSITIVITY_PERTURBATION)
from .valuation import (DCF_YEARS, HURDLE_RATE, HURDLE_SENSITIVITY,
                        TERMINAL_GROWTH, Sensitivity, ValuationError,
                        equity_value_per_share, fair_value,
                        free_cash_flow_zero, rate_declaration)

#: Where a figure in the record came from. `store` is a file `vss` wrote or
#: a person filled; `hand` is a fact stated in a filing that no field of the
#: schema can hold; `code` is a constant of this project (r, the horizon).
#: A record made only of `code` and `hand` is a hand run wearing a record's
#: clothes, and the origin column is what makes that visible.
ENTERED_BY = ("store", "hand", "code")

#: E36's two treatments. There is no third: "not stated" is not a treatment,
#: it is an incomplete record.
SBC_DEDUCTED = "deducted"
SBC_ADDED_BACK = "added back (as filed)"

#: The bridge items report C Part 10 requires a case to declare. `None` for
#: an item means DATA MISSING -- the schema has no field for three of them,
#: pensions having gained one under E35.1 -- and that is recorded rather
#: than left to a reader to notice.
BRIDGE_ITEMS = ("short_term_investments", "leases", "non_controlling_interests",
                "pensions", "current_financial_assets",
                "asset_retirement_obligations",
                # E81 (2026-08-30): cash received against product still to
                # be delivered -- a stream, a prepaid offtake.
                "prepaid_delivery_obligations")

#: E108 (2026-09-08): THE BRIDGE'S NAMES AND THE STORE'S ARE NOT THE SAME
#: NAMES, and `sensitivity` has to speak the STORE's, because that is what
#: `manual.section5_gate` refuses on.
#:
#: **THIS MAPPING IS THE DEFECT'S FIX AND ITS OWN GUARD.** `BRIDGE_ITEMS`
#: above is a REPORTING vocabulary -- report C Part 10 requires those exact
#: labels -- and `leg_values` reused it for the sensitivity map. The gate
#: then looked up `lease_liabilities` in a map keyed `leases`, missed, and
#: refused. **The intersection was EMPTY on every name and nothing said
#: so**: an exemption that cannot be granted looks exactly like an exemption
#: that was not earned. Found on MEKKO.HE 2026-09-08 when two read-backs
#: left fourteen refusals that E108's own words exempt.
#:
#: `tests/test_runrecord.py::test_every_bridge_leg_names_a_real_store_field`
#: fails if a key here stops naming a field the schema has.
BRIDGE_LEG_FIELDS: dict[str, tuple[str, ...]] = {
    "leases": ("lease_liabilities",),
    "pensions": ("pension_deficit",),
    "asset_retirement_obligations": ("asset_retirement_obligation",),
    "prepaid_delivery_obligations": ("prepaid_delivery_obligation",),
    # A1's line: one schema field, two bridge labels.
    "short_term_investments": ("other_current_financial_assets",),
    "current_financial_assets": ("other_current_financial_assets",),
    # E105: not a bridge item at all -- the minority is deducted in the
    # FLOW. Named here with NO store field so the test can tell "deliberately
    # unmapped" from "forgotten".
    "non_controlling_interests": (),
}

#: The STORE fields that are legs of the NET-DEBT bridge but are not bridge
#: ITEMS -- the record reads them, the gate refuses on them, and they are
#: perturbed as stocks. Taken off the record's own `inputs`, so a field the
#: record never read is never exempted.
NET_DEBT_STORE_LEGS: tuple[str, ...] = (
    "cash_and_equivalents",
    "financial_liabilities_current",
    "financial_liabilities_noncurrent",
    "noncurrent_derivative_assets_on_debt",
)

#: A RECORD IS A STATEMENT MADE ON A DATE UNDER THE RULES OF THAT DATE. An
#: item that became declarable AFTER a record was struck is not a gap in
#: that record: E68 (2026-08-29) added the asset-retirement leg, and the
#: four records struck before it (AUTO.L, CTSH, LIAB.ST, SAP.DE) stay
#: complete AS STRUCK -- their rendering says the item postdates them --
#: while every record struck from that date on must declare it.
BRIDGE_ITEMS_SINCE: dict[str, date | datetime] = {
    "asset_retirement_obligations": date(2026, 8, 29),
    # E81 (2026-08-30, 15:00 UTC): after the morning's strikes (LIAB.ST
    # 08:26 UTC, LII 08:18, NVR and ULTA 11:16), which stay complete AS
    # STRUCK; every record from that hour on must declare the leg.
    "prepaid_delivery_obligations": datetime(2026, 8, 30, 15, 0, tzinfo=timezone.utc),
}


def item_predates(run_ts: datetime, since: "date | datetime") -> bool:
    """True where a record was struck before a bridge item existed. A DATE
    exempts every record struck on an earlier day (E68's form); a DATETIME
    exempts every record struck before that instant (E81's form), so a
    ruling made in the afternoon does not reopen the morning's records."""
    if isinstance(since, datetime):
        return struck_before(run_ts, since)
    return run_ts.date() < since

#: What a bridge item says when the SCHEMA has no field for it at all --
#: which is true of three of the items report A 4.1 lists (pensions gained
#: a field under E35.1). Distinct from
#: DATA MISSING, which is a fact about one basis rather than about the
#: vocabulary.
NO_FIELD = "no field in this schema (E35)"

#: E106 (2026-09-04): how far the UNDETERMINED legs may move `fv_base`
#: between them before §5 refuses to strike at all.
#:
#: **THE OWNER'S NUMBER, CHOSEN AND NOT DERIVED**, and expressly NOT a
#: statement about the market -- unlike E77's regime adjustment or Gate 1's
#: band it does not move when conditions do. It is a property of how much
#: missing arithmetic this framework will carry.
#:
#: His ground: *this framework is strict everywhere else, and it should not
#: lose a candidate on a formality when the leg in question cannot move the
#: answer by more than a fraction of the cushion.* The loosest cushion is
#: 15% (E90 tier 1); 3.5% is under a quarter of it.
#:
#: WHAT IT GIVES UP, and E106 says it rather than leaving it to be found: a
#: struck value may carry a known unquantified gap of up to 3.5%, which IS
#: large enough to move a name across its buy line. Accepted knowingly.
#: ONE DEFINITION, in `manual`, beside the gate that also asks it. The two
#: must never drift: `section5_gate` refuses on this number and
#: `RunRecord.missing` refuses on it too, and a gate that said MAY RUN over
#: a record that refused would be the worst of both.
INCOMPLETE_LEG_TOLERANCE = _INCOMPLETE_LEG_TOLERANCE

#: E108 (2026-09-04): THE SENSITIVITY FLOOR. A leg perturbed by
#: ``SENSITIVITY_PERTURBATION`` either way that moves `fv_base` by less than
#: this is exempt from the owner's READ-BACK -- and from nothing else.
#:
#: **IT IS NOT E106's TOLERANCE ABOVE, AND THE TWO ARE NOT COMPARABLE.**
#: E106's 3.5% is what a MISSING leg may be worth and still let section 5
#: run; this 1% is what a PRESENT leg may MOVE and still skip a second pair
#: of eyes. Tighter on purpose: an absent leg is known to be absent, and an
#: unread one is not known to be anything.
#: ONE DEFINITION, in `manual`, because that is where the gate that acts on
#: it lives. Re-exported here so a reader of the record's own arithmetic
#: does not have to know which module owns the number.
SENSITIVITY_FLOOR = _SENSITIVITY_FLOOR
SENSITIVITY_PERTURBATION = _SENSITIVITY_PERTURBATION


@dataclass(frozen=True)
class Undetermined:
    """A leg that is absent but BOUNDED (E106).

    ``bound`` is the largest absolute amount the leg could be, in the
    store's money unit, and it is a FIGURE: it needs its evidence like any
    other, which is what ``page`` carries. An absence with no bound is not
    an `Undetermined` at all -- it is a gap, and it refuses.

    ``direction`` says WHICH WAY the unknown can move `fv_base` from where
    the record struck it, and it exists because **E106 clause 1 says "on
    ANY PLAUSIBLE VALUE"** and the plausible values are one-sided. A leg
    struck at zero whose true value is a DEDUCTION can only lower the
    answer (`reduces` -- E105's shape). One whose true value is an ADD-BACK
    can only raise it (`raises` -- E70's shape, and A. O. Smith's operating
    lease payments are the first). Perturbing an add-back leg downward
    measures a move that cannot happen and misses the one that can.
    """

    name: str
    bound: float
    page: str = ""
    direction: str = BOUND_REDUCES

    def line(self) -> str:
        which = ("can only LOWER fv_base" if self.direction == BOUND_REDUCES
                 else "can only RAISE fv_base" if self.direction == BOUND_RAISES
                 else "may move fv_base EITHER way")
        return (f"{self.name} UNDETERMINED, bounded at {self.bound:,.0f}, "
                f"{which}" + (f" ({self.page})" if self.page else ""))
#: E105: what the bridge says about the minority now that the flow deducts
#: it. NOT an absence -- an answer, and one that says where the answer is.
NCI_IN_THE_FLOW = ("not a bridge item — E105 deducts the dividends PAID to "
                   "minorities in the FLOW, and declines to value the stake "
                   "as a liability (a second unaudited lever, E29's ground)")


class RecordError(Exception):
    """The record cannot support a fair value, and says which part is absent."""


@dataclass(frozen=True)
class Input:
    """One figure, what it is, and where it came from."""

    name: str
    value: float | None
    provenance: str
    entered_by: str = "store"
    #: E40: what the figure's VERIFIED flag stands on -- `VERIFIED (tagged)`,
    #: `VERIFIED (same_page)`, `UNVERIFIED` -- or `hand` for a record-level
    #: input. Printed beside every figure in the inputs table.
    verified: str = ""

    def __post_init__(self) -> None:
        if self.entered_by not in ENTERED_BY:
            raise RecordError(
                f"entered_by must be one of {ENTERED_BY}, got "
                f"{self.entered_by!r}. Where a figure came from is part of "
                f"what the record is for")
        if not self.provenance:
            raise RecordError(
                f"`{self.name}` has no provenance. A figure without a page, "
                f"a tag or an accession is a figure a reader cannot check, "
                f"and this record exists so that never happens again")


@dataclass(frozen=True)
class ShareBasis:
    """Declaration 1: which count, and AS OF WHEN."""

    count: float
    basis: str                     # e.g. "weighted-average diluted, FY2026"
    as_of: date
    #: E38's memo, where the file carries one. Printed, never divided by.
    point_in_time: float | None = None
    point_in_time_as_of: date | None = None
    #: The scale the count is STATED in -- the store's `share_unit`, one of
    #: `manual.UNIT_SCALE` -- or None where the store did not say. The
    #: division normalises on it; a None makes the record INCOMPLETE.
    unit: str | None = None
    #: E75 / E75.1 (2026-08-30): WHICH KIND of count the division used --
    #: `weighted_average` (E38's window average, or E41's annual average on
    #: its own date), `period_end_diluted` (the diluted count the issuer
    #: states at the window end, E75.1) or `period_end_basic` (the basic
    #: count at the window end, where only that is stated). Records struck
    #: before E75 carry the default and are complete as struck. E88
    #: (2026-08-30) reversed E75: new records carry `weighted_average`;
    #: the period-end kinds stay readable for records struck under E75.
    divisor_basis: str = "weighted_average"
    #: E75: the annual average the period-end count replaced, and the
    #: drift (count - prior) / prior. None where E75 did not fire.
    prior_average: float | None = None
    drift: float | None = None

    def __post_init__(self) -> None:
        if self.divisor_basis not in ("weighted_average", "period_end_diluted",
                                      "period_end_basic",
                                      "window_day_weighted"):
            raise RecordError(
                f"divisor_basis {self.divisor_basis!r} is not one of "
                f"'weighted_average', 'period_end_diluted', 'period_end_basic', "
                f"'window_day_weighted' (E75 / E75.1 / E88 / E91)")
        if self.unit is not None and self.unit not in UNIT_SCALE:
            raise RecordError(
                f"share count unit {self.unit!r} is not one of "
                f"{'|'.join(UNIT_SCALE)}. A unit the record cannot scale is "
                f"a divisor nobody can check")


@dataclass(frozen=True)
class Legs:
    """The three figures the division reads, each in WHOLE units.

    Money in whole currency, the count in whole shares -- whatever scale
    the store stated them in. This is the ONLY place a stored figure is
    rescaled, it is done from the file's own declaration, and the record
    prints which declaration it applied.
    """

    fcf0: float
    net_cash: float
    shares: float


@dataclass(frozen=True)
class SbcTreatment:
    """Declaration 2: deducted or added back, and how much."""

    treatment: str
    amount: float | None
    #: E41: the window the amount was stated for, where it is not the
    #: flows' own -- "annual FY2025 (E41: annual-only, ...)".
    basis: str = ""

    def __post_init__(self) -> None:
        if self.treatment not in (SBC_DEDUCTED, SBC_ADDED_BACK):
            raise RecordError(
                f"share-based compensation is {self.treatment!r}; E36 knows "
                f"two treatments, {SBC_DEDUCTED!r} and {SBC_ADDED_BACK!r}. "
                f"'not stated' is not a treatment, it is an incomplete record")


@dataclass(frozen=True)
class InterestTreatment:
    """Declaration 3: where the filer books it, and what FCF0 became."""

    #: None means NOT RECORDED. It is not `no`: saying interest sits
    #: outside operating cash flow is a POSITIVE CLAIM about a filer, and
    #: `bool(None)` would make it silently for every file that omits the
    #: block. E34's own rule is that absent is DATA MISSING.
    in_operating_cash_flow: bool | None
    page: str
    net_interest_paid: float | None = None
    #: E34.1 / E61: `cash_flow_statement` (E34 as written),
    #: `income_statement_net` -- the accrual proxy a US filer is left with
    #: when it tags no interest received -- or `interest_expense_only` --
    #: the bounded, one-sided proxy for a US filer that tags neither the
    #: net nor an interest-received figure.
    source: str = "cash_flow_statement"

    @property
    def accrual_proxy(self) -> bool:
        return self.source == "income_statement_net"

    @property
    def interest_expense_only_proxy(self) -> bool:
        return self.source == "interest_expense_only"

    @property
    def cash_paid_only_proxy(self) -> bool:
        return self.source == "cash_paid_only"

    @property
    def sentence(self) -> str:
        if self.in_operating_cash_flow is None:
            return ("where this filer books its interest is NOT RECORDED "
                    "(E34) -- and that is not the same as `no`. FCF0 cannot "
                    "be formed")
        if not self.in_operating_cash_flow:
            return ("interest paid is OUTSIDE operating cash flow, so FCF0 is "
                    "already a flow to the FIRM and nothing is added back "
                    "(E34)")
        if self.net_interest_paid is None:
            return ("interest paid is INSIDE operating cash flow and the "
                    "amount is DATA MISSING -- FCF0 cannot be formed (E34)")
        if self.accrual_proxy:
            net = self.net_interest_paid
            moved = (f"net interest EXPENSE of {net:,.0f} is ADDED BACK"
                     if net >= 0 else
                     f"net interest INCOME of {-net:,.0f} is REMOVED")
            return (f"interest paid is INSIDE operating cash flow; the filer "
                    f"states interest paid as cash but no interest received, "
                    f"so the net is the INCOME STATEMENT'S -- an ACCRUAL "
                    f"PROXY (E34.1): {moved}, and net debt is then "
                    f"subtracted ONCE. Interest paid alone is never the net")
        if self.interest_expense_only_proxy:
            gross = self.net_interest_paid
            return (f"interest paid is INSIDE operating cash flow; the filer "
                    f"tags gross interest expense but no net and no "
                    f"interest-received figure, so the add-back is the "
                    f"TAGGED INTEREST EXPENSE ALONE, {gross:,.0f} -- a "
                    f"PROXY (E61), bounded and one-sided: interest income is "
                    f"never negative, so this can only OVERSTATE FCF0, by no "
                    f"more than the unrecorded interest income, and net debt "
                    f"is then subtracted ONCE")
        if self.cash_paid_only_proxy:
            paid = self.net_interest_paid
            return (f"interest paid is INSIDE operating cash flow; the filer "
                    f"states interest PAID as cash, states no interest "
                    f"received, states no income-statement net and tags no "
                    f"gross expense this schema reads, so the add-back is "
                    f"INTEREST PAID ALONE, {paid:,.0f} -- a PROXY (E115), "
                    f"bounded and one-sided in E61's class: interest income "
                    f"is never negative, so this can only OVERSTATE FCF0, by "
                    f"no more than the unstated interest income, and net debt "
                    f"is then subtracted ONCE. E34.1 holds that interest paid "
                    f"alone is never the net, and this is not the net: it is "
                    f"a named proxy with its bias printed")
        return (f"interest paid is INSIDE operating cash flow, so "
                f"{self.net_interest_paid:,.0f} is ADDED BACK, as printed and "
                f"PRE-TAX, and net debt is then subtracted ONCE (E34). The "
                f"pre-tax add-back is the generous end of E34's own band")


@dataclass(frozen=True)
class Bridge:
    """Declaration 4: the enterprise-to-equity bridge, item by item."""

    net_debt: float               # positive for a net-debt company
    items: dict[str, float | None] = field(default_factory=dict)
    note: str = ""

    @property
    def net_cash(self) -> float:
        """The sign `equity_value_per_share` wants: positive = net cash."""
        return -self.net_debt


#: E101 (2026-09-01): the band a free-cash-flow-to-net-income conversion
#: must sit inside before it stops being a question.
#:
#: **A DETECTOR'S BAND, NOT A QUALITY TEST.** Section 4.3 already reads a
#: conversion above 90% as a GREEN FLAG, so a high ratio is a good fact
#: about a business and this must not read it as a fault. What is being
#: detected is a figure on the WRONG BASIS: a quarter divided into a year,
#: a segment into a group, a per-share figure into a total. Those land far
#: outside any plausible business, and a factor of four is the smallest one
#: that matters (backlog B-8, first found on PNDORA.CO).
#:
#: So the band is DELIBERATELY WIDE -- 0.2x to 3.0x. A real business can
#: convert at 40% (heavy working capital) or at 250% (a year of releases),
#: and neither is worth a line.
#:
#: **ACCEPTED BY THE OWNER 2026-09-01 AND RULED AS HIS** (beneath E101), in
#: his own terms: *the band is deliberately wide because section 4.3 already
#: reads a high conversion as a GREEN FLAG, so what is detected is a figure
#: on the WRONG BASIS -- not a business that converts well.* A band tight
#: enough to argue with 4.3 would be a second, contradictory quality test
#: wearing a detector's clothes.
FCF_CONVERSION_BAND: tuple[float, float] = (0.2, 3.0)

#: How far apart a derived figure and the issuer's own may sit before the
#: detector says so.
#:
#: **ACCEPTED BY THE OWNER 2026-09-01 AND RULED AS HIS** (beneath E101), in
#: his own terms: *5% allows for rounding and definitional differences
#: without hiding a missing leg.* That is the whole trade, and it is sized
#: against the case the check was built from -- LIAB.ST's pension leg was
#: +6.3%, so a tolerance that swallowed it would have swallowed the one
#: finding this detector exists to have made.
#:
#: It follows that the check SPEAKS ON MOST NAMES, and that is the design:
#: it is a PROMPT, and a detector that only fires on catastrophes catches
#: only catastrophes.
DISAGREEMENT_TOLERANCE = 0.05


@dataclass(frozen=True)
class Comparator:
    """E101: an issuer-stated figure this record can be checked against.

    ``value`` is the figure as the issuer publishes it, on the issuer's own
    definition, in the store's money unit. None means the issuer publishes
    none that anybody has entered -- DATA MISSING, which is a fact about the
    filing and never a disagreement of zero.
    """

    value: float | None = None
    page: str = ""
    #: E103: whether the owner has read this comparator back. False is the
    #: ordinary state -- an automatically entered figure is UNVERIFIED by
    #: the ruling -- and it is what makes the "verify this one" line honest.
    verified: bool = False


def _comparator_from(raw: Mapping[str, Any] | None) -> "Comparator":
    """One E101 comparator read back. Absent is the empty comparator --
    DATA MISSING, which is a fact about the filing and not a zero."""
    return Comparator(**raw) if raw else Comparator()


@dataclass(frozen=True)
class Disagreement:
    """One construction check, and it NEVER adjudicates.

    `ours` and `theirs` are printed side by side with the measure between
    them. **Nothing is adjusted, refused or blocked on this** -- E101 is
    explicit that the issuer's definition is usually not this project's, so
    a disagreement is a prompt to look and not a verdict about who is right.
    """

    name: str
    ours: float | None
    theirs: float | None
    detail: str = ""
    #: E103 clause 4: the field the owner would read back if he treats this
    #: disagreement as real, and the page it was entered from. The
    #: comparator is UNVERIFIED and is the likelier of the two to be wrong,
    #: so it is what gets named -- ONE figure, after something has told him
    #: where to look, instead of every figure in advance.
    comparator_field: str = ""
    comparator_page: str = ""
    comparator_verified: bool = False
    #: "gap" -- two constructions of the SAME quantity, compared as a
    #: percentage. "ratio" -- two DIFFERENT quantities whose QUOTIENT is
    #: the check, compared against a band. Conflating them printed
    #: "+18.5% LOOK" beside "inside the band" on CTSH, which is a detector
    #: arguing with itself and is how a reader learns to ignore one.
    kind: str = "gap"
    band: tuple[float, float] | None = None

    @property
    def measurable(self) -> bool:
        return (self.ours is not None and self.theirs is not None
                and self.theirs != 0)

    @property
    def gap(self) -> float | None:
        """(ours - theirs) / |theirs|. Positive = ours is the larger."""
        if not self.measurable:
            return None
        return (self.ours - self.theirs) / abs(self.theirs)

    @property
    def ratio(self) -> float | None:
        """ours / theirs, for a check whose QUOTIENT is the question."""
        if not self.measurable:
            return None
        return self.ours / self.theirs

    @property
    def flagged(self) -> bool:
        if self.kind == "ratio":
            ratio, band = self.ratio, self.band
            if ratio is None or band is None:
                return False
            return not (band[0] <= ratio <= band[1])
        gap = self.gap
        return gap is not None and abs(gap) > DISAGREEMENT_TOLERANCE

    @property
    def measure(self) -> str:
        """The middle column: a percentage for a gap, a multiple for a
        ratio. Never both, and never a percentage where the band is a
        multiple."""
        if self.kind == "ratio":
            return "—" if self.ratio is None else f"{self.ratio:.2f}x"
        return "—" if self.gap is None else f"{self.gap:+.1%}"

    def line(self) -> str:
        if self.ours is None:
            return f"| {self.name} | DATA MISSING | — | — | {self.detail} |"
        if self.theirs is None:
            return (f"| {self.name} | {self.ours:,.0f} | DATA MISSING | — | "
                    f"the issuer publishes none on this basis, or none is "
                    f"entered — never a disagreement of zero |")
        mark = " **LOOK**" if self.flagged else ""
        return (f"| {self.name} | {self.ours:,.0f} | {self.theirs:,.0f} | "
                f"{self.measure}{mark} | {self.detail}{self.verify_line()} |")

    def verify_line(self) -> str:
        """What a disagreement asks of the reader — E104, replacing E103's
        clause 4.

        **IT NO LONGER ASKS FOR A READ-BACK.** E103 moved the read-back from
        every figure in advance to the figure that blinked; E104 asks
        whether the machine can answer that one itself, and it can. A
        comparator this project entered is RE-EXTRACTED before anything
        reaches the owner: two readings agreeing settle the transcription
        and make the disagreement CONSTRUCTION, which is his to judge; two
        disagreeing convict the extraction and the figure withdraws itself.
        """
        if not self.flagged or not self.comparator_field:
            return ""
        if self.comparator_verified:
            return (" — **both figures are VERIFIED, so the disagreement is "
                    "real: it is a difference of CONSTRUCTION, not of "
                    "transcription. Yours to judge.**")
        return (f" — `{self.comparator_field}` is an UNVERIFIED automatic "
                f"figure ({self.comparator_page or 'no page recorded'}). "
                f"**E104: it is re-extracted before this reaches you** — run "
                f"`vss reference-figures --confirm`. Two readings agreeing "
                f"make this CONSTRUCTION and yours; two disagreeing withdraw "
                f"the figure and nothing reaches you at all.")


@dataclass(frozen=True)
class Conventions:
    """Declaration 5: the discounting, stated so a change fails loudly."""

    horizon_years: int = DCF_YEARS
    terminal_growth: float = TERMINAL_GROWTH
    mid_year: bool = False
    first_year_flow: str = "FCF0 * (1 + g)"

    @property
    def sentence(self) -> str:
        return (f"{self.horizon_years} explicit years; terminal "
                f"{self.terminal_growth:.1%}; "
                f"{'MID-YEAR' if self.mid_year else 'END-OF-YEAR'} "
                f"discounting; first-year flow {self.first_year_flow}; "
                f"Gordon on year {self.horizon_years}, discounted "
                f"{self.horizon_years} full years")


@dataclass(frozen=True)
class Rate:
    """Declaration 6a: r, and the anchor E29 says makes it maintainable."""

    rate: float = HURDLE_RATE
    core_expected_return: float | None = None
    premium: float | None = None
    band: float = HURDLE_SENSITIVITY

    @property
    def anchor_sentence(self) -> str:
        if self.core_expected_return is None or self.premium is None:
            return ("anchor NOT RECORDED. E29 says r moves when the index "
                    "core's expected return moves; that return is written in "
                    "no file and no watchlist entry carries a `hurdle:` "
                    "block, so the condition for changing r cannot fire")
        return (f"{self.core_expected_return:.1%} core expected return + "
                f"{self.premium:.1%} single-company premium (E29)")


@dataclass(frozen=True)
class Growth:
    """Declaration 6b: g, and the pre-registered view it came from."""

    base: float
    view_file: str
    view_date: date | None = None
    bear: float | None = None
    bull: float | None = None


@dataclass(frozen=True)
class AsOfDates:
    """Declaration 7. THE THREE, plus the price's where a price is used.

    They are separate fields because they are separate facts, and REVIEW-4
    measured what happens when they are quietly assumed to agree: DECK's
    140.95 paired a July divisor with June cash, +0.32; B36's 140.81 paired
    a July divisor with MARCH cash, +3.59.
    """

    flows_window_end: date
    balance_sheet: date
    share_count: date
    price: date | None = None

    @property
    def agree(self) -> bool:
        return self.flows_window_end == self.balance_sheet == self.share_count

    @property
    def disagreement(self) -> str:
        """Which date differs from the flows' window end, by name (E41)."""
        parts = []
        if self.balance_sheet != self.flows_window_end:
            parts.append(f"balance sheet {self.balance_sheet.isoformat()}")
        if self.share_count != self.flows_window_end:
            parts.append(f"share count {self.share_count.isoformat()}")
        return " and ".join(parts)


@dataclass(frozen=True)
class LeaseTreatment:
    """Declaration 3.1 (E70): what the flow bore of the LEASE, and what was
    added back so the lease is charged once, in net debt.

    `in_operating_cash_flow` None means NOT RECORDED -- for a record struck
    before E70 existed that is the state of the world, not a gap
    (RECORD_DECLARATIONS_SINCE); for a record struck after it, it is DATA
    MISSING and the record is incomplete.
    """

    in_operating_cash_flow: bool | None
    page: str
    principal_added_back: float | None = None
    #: The leg the add-back was read from, and how its interest half was
    #: treated -- named, the way E34's add-back names its leg.
    leg: str = ""
    #: E117 (2026-09-19). A record without the key was struck under E70 and
    #: REPLAYS UNDER E70: the rule is part of what the record states.
    rule: str = "E70"
    #: E117, IFRS 16: the principal and lease interest DEDUCTED from the flow.
    lease_cash_deducted: float | None = None
    principal_paid: float | None = None
    interest_paid: float | None = None
    #: E117: the lease liability that LEFT net debt (US: the operating part;
    #: IFRS 16: all of it).
    liability_excluded: float | None = None

    @property
    def sentence(self) -> str:
        if self.rule == "E117":
            return self._e117_sentence()
        if self.in_operating_cash_flow is None:
            return ("whether the operating cash flow bears the operating "
                    "lease payments is NOT RECORDED (E70)")
        if not self.in_operating_cash_flow:
            return ("the operating cash flow does NOT bear the lease "
                    "principal (IFRS 16.50(b): in financing), so nothing is "
                    "added back -- the lease is charged once, in net debt "
                    "(E35, E65, E70)")
        if self.principal_added_back is None:
            return ("the operating cash flow BEARS the operating lease "
                    "payments (ASC 842) and the stated cash paid is DATA "
                    "MISSING -- FCF0 cannot be formed (E70)")
        return (f"the operating cash flow BEARS the operating lease payments "
                f"(ASC 842-20-45-5(a)); {self.principal_added_back:,.0f} is "
                f"ADDED BACK so the lease is charged once, in net debt (E70) "
                f"-- leg: {self.leg}")

    def _e117_sentence(self) -> str:
        excluded = (f"; the lease liability {self.liability_excluded:,.0f} "
                    f"LEFT net debt" if self.liability_excluded is not None
                    else "")
        if self.in_operating_cash_flow is None:
            return ("whether the operating cash flow bears the lease "
                    "payments is NOT RECORDED (E117)")
        if self.in_operating_cash_flow:
            return ("RENT IS AN OPERATING COST (E117): the operating cash "
                    "flow bears the operating lease payments (ASC "
                    "842-20-45-5(a)) and NOTHING is added back" + excluded
                    + "; finance leases stay in net debt")
        if self.lease_cash_deducted is None:
            return ("RENT IS AN OPERATING COST (E117) and the IFRS 16 lease "
                    "cash outflow is DATA MISSING -- FCF0 cannot be formed")
        return (f"RENT IS AN OPERATING COST (E117): the IFRS 16 lease cash "
                f"outflow {self.lease_cash_deducted:,.0f} is DEDUCTED -- "
                f"principal {self.principal_paid or 0:,.0f} + lease interest "
                f"{self.interest_paid or 0:,.0f}" + excluded)


#: A RECORD IS A STATEMENT MADE ON A DATE UNDER THE RULES OF THAT DATE (the
#: E68 mechanism, generalised). A declaration that became required AFTER a
#: record was struck is not a gap in that record; its rendering says the
#: declaration postdates it. E70 (2026-08-30 08:00 UTC, between the last
#: strike made before the ruling, 07:14 UTC, and the first under it): the
#: lease treatment.
RECORD_DECLARATIONS_SINCE: dict[str, datetime] = {
    "lease": datetime(2026, 8, 30, 8, 0, tzinfo=timezone.utc),
    # E105 (2026-09-04): the dividends paid to non-controlling interests.
    # Every record this project keeps was struck before it, and none of
    # them is INCOMPLETE for want of a leg that did not exist on the day.
    # THE RECORD STAYS COMPLETE AND THE STORE MOVES ON: E87 is what
    # supersedes the watchlist figure when the store can no longer rebuild
    # it, and E105's affected names are re-struck rather than patched.
    "nci": datetime(2026, 9, 4, 0, 0, tzinfo=timezone.utc),
}


def struck_before(run_ts: datetime, since: datetime) -> bool:
    """True where a record predates a declaration. A naive timestamp is
    read as UTC rather than refused: the comparison is a courtesy to old
    records, not a gate on new ones."""
    stamp = run_ts if run_ts.tzinfo is not None else run_ts.replace(tzinfo=timezone.utc)
    return stamp < since


@dataclass(frozen=True)
class RunRecord:
    """One section 5 run, complete enough to be re-run from."""

    ticker: str
    currency: str
    run_ts: datetime
    basis: str                       # the E19 window's own label
    shares: ShareBasis
    sbc: SbcTreatment
    interest: InterestTreatment
    bridge: Bridge
    dates: AsOfDates
    growth: Growth
    operating_cash_flow: float | None
    capex: float | None              # an OUTFLOW, negative
    conventions: Conventions = field(default_factory=Conventions)
    rate: Rate = field(default_factory=Rate)
    inputs: tuple[Input, ...] = ()
    tool_commit: str = ""
    notes: str = ""
    #: The scale every MONEY figure in this record is stated in -- the
    #: store's `money_unit`, one of `manual.UNIT_SCALE` -- or None where
    #: the store did not say. Hand inputs are entered in the same unit as
    #: the store they fill. None makes the record INCOMPLETE: a per-share
    #: value divided across an unstated scale was out by 1e6 on a
    #: millions-scale file with a whole-number count.
    money_unit: str | None = None
    #: E105: dividends paid to NON-CONTROLLING INTERESTS over the window, as
    #: the cash flow statement states them -- NEGATIVE, and a LEG of FCF0
    #: rather than a bridge item. None is DATA MISSING and the record
    #: refuses; a group with no minorities states a NAMED ZERO (E25).
    nci_dividends_paid: float | None = None
    #: E106: legs that are absent, BOUNDED, and inside the tolerance. They
    #: are struck at ZERO and their bound is carried so the report can name
    #: them and `tolerance` can sum them.
    undetermined: tuple["Undetermined", ...] = ()
    #: E101: the issuer's OWN figures, for the three construction checks.
    #: Carried, never used to compute anything -- see `construction_checks`.
    fcf_reported: "Comparator" = field(default_factory=lambda: Comparator())
    net_debt_reported: "Comparator" = field(default_factory=lambda: Comparator())
    net_income: "Comparator" = field(default_factory=lambda: Comparator())
    #: E70 (declaration 3.1). Defaults to NOT RECORDED so a record struck
    #: before the ruling reads back; `missing()` dates the requirement.
    lease: LeaseTreatment = field(default_factory=lambda: LeaseTreatment(None, ""))

    def __post_init__(self) -> None:
        if self.money_unit is not None and self.money_unit not in UNIT_SCALE:
            raise RecordError(
                f"money unit {self.money_unit!r} is not one of "
                f"{'|'.join(UNIT_SCALE)}. A unit the record cannot scale is "
                f"a figure nobody can check")

    # --- completeness -----------------------------------------------------

    def _bounded(self, name: str) -> bool:
        """Is this absent leg carried as an E106 bound?"""
        return any(u.name == name for u in self.undetermined)

    def _unit_gaps(self) -> list[str]:
        """THE UNITS THE DIVISION NORMALISES ON, and nothing else.

        Unstated is DATA MISSING, not "whole": a millions-scale file with a
        whole-number count divided raw is out by 1e6 per share, and nothing
        downstream can tell.

        **IT IS ITS OWN FUNCTION BECAUSE `legs` MAY NOT ASK `missing`.**
        `missing` asks `tolerance` (E106 clause 4), `tolerance` values the
        record, valuing it asks `legs`, and `legs` asked `missing` -- a
        cycle that only closed once a record actually carried an
        undetermined leg, which is to say the first time E106's clause 4
        had anything to measure. `legs` needs the two unit declarations and
        no other part of the answer.
        """
        gaps: list[str] = []
        if self.shares.unit is None:
            gaps.append("the unit the share count is stated in -- "
                        "`share_unit` on the store file (declaration 1)")
        if self.money_unit is None:
            gaps.append("the unit the money figures are stated in -- "
                        "`money_unit` on the store file (declaration 8)")
        return gaps

    def tolerance(self) -> tuple[float, float, str]:
        """E106: (worst-case move as a fraction, the absolute move, why).

        Struck EXACTLY rather than approximated: the record is valued twice,
        once with every undetermined leg at zero and once with each at its
        bound in the direction that REDUCES value, and the difference is
        taken. The DCF is linear in FCF0 only until net cash is added, so an
        approximation would be wrong by the bridge.

        THE LEGS ARE SUMMED (clause 4). A tolerance applied one leg at a
        time is not a tolerance; it is a way of admitting any number of them.
        """
        if not self.undetermined:
            return 0.0, 0.0, ""
        base = self._strike_unchecked()
        # THE TWO DIRECTIONS ARE SUMMED SEPARATELY and the LARGER absolute
        # move taken. Netting them would let a deduction leg and an add-back
        # leg cancel, and two unknowns that happen to point opposite ways
        # are not one smaller unknown -- they are two.
        down = sum(abs(u.bound) for u in self.undetermined
                   if u.direction in (BOUND_REDUCES, BOUND_EITHER))
        up = sum(abs(u.bound) for u in self.undetermined
                 if u.direction in (BOUND_RAISES, BOUND_EITHER))
        move = max(abs(base - self._strike_unchecked(fcf0_adjustment=-down)),
                   abs(base - self._strike_unchecked(fcf0_adjustment=up)))
        fraction = move / abs(base) if base else float("inf")
        named = "; ".join(u.line() for u in self.undetermined)
        return fraction, move, named

    def missing(self) -> tuple[str, ...]:
        """Every declaration this record cannot make. Empty means complete."""
        gaps: list[str] = []
        # THE TWO LEGS FCF0 IS BUILT FROM. `capex` is a SUM of one or two
        # stated lines and an absent one is DATA MISSING, never zero -- a
        # record that coerced it would overstate FCF0 by the whole of a
        # filer's capital spending and report itself complete.
        if self.operating_cash_flow is None:
            gaps.append("operating cash flow (declaration 8)")
        if self.capex is None:
            gaps.append("capex — DATA MISSING on the basis, and E23 refuses "
                        "a lone split leg (declaration 8)")
        if self.interest.in_operating_cash_flow is None:
            gaps.append("where this filer books its interest (declaration 3)")
        if self.shares.count is None or self.shares.count <= 0:
            gaps.append("share count (declaration 1)")
        gaps.extend(self._unit_gaps())
        if self.sbc.amount is None:
            gaps.append("share-based compensation amount (declaration 2)")
        if (self.nci_dividends_paid is None
                and not self._bounded("nci_dividends_paid")
                and not struck_before(self.run_ts,
                                      RECORD_DECLARATIONS_SINCE["nci"])):
            gaps.append("dividends paid to non-controlling interests (E105) "
                        "-- DATA MISSING on the basis and NOT BOUNDED. A "
                        "group with no minorities states a NAMED ZERO (E25); "
                        "a group that may have them states a BOUND (E106). "
                        "An unbounded absence is not a small one")
        if self.interest.in_operating_cash_flow and \
                self.interest.net_interest_paid is None:
            gaps.append("net interest paid (declaration 3)")
        # E106 clause 4, asked AFTER every hard gap: legs that are each
        # inside the tolerance may still exceed it between them.
        if self.undetermined and not gaps:
            fraction, move, named = self.tolerance()
            if fraction > INCOMPLETE_LEG_TOLERANCE:
                gaps.append(
                    f"the UNDETERMINED legs move fv_base by "
                    f"{fraction:.1%} between them, past E106's "
                    f"{INCOMPLETE_LEG_TOLERANCE:.1%} — {named}. No single "
                    f"leg refuses and together they do, which is what "
                    f"summing them is for")
        if not self.interest.page:
            gaps.append("the page the interest classification was read from "
                        "(declaration 3)")
        # E70: the lease treatment, required on every record struck after
        # the ruling; a record struck before it with NOTHING RECORDED is
        # complete AS STRUCK. A `yes` with no payment stated can never
        # compute, whatever the date.
        if self.lease.in_operating_cash_flow is None:
            if not struck_before(self.run_ts, RECORD_DECLARATIONS_SINCE["lease"]):
                gaps.append("whether the operating cash flow bears the lease "
                            "payments (declaration 3.1, E70)")
        elif self.lease.rule == "E117":
            if (self.lease.in_operating_cash_flow is False
                    and self.lease.lease_cash_deducted is None):
                gaps.append("the IFRS 16 lease cash outflow to deduct "
                            "(declaration 3.1, E117)")
        elif (self.lease.in_operating_cash_flow
                and self.lease.principal_added_back is None
                and not self._bounded("operating_lease_payments")):
            gaps.append("the operating lease payments to add back "
                        "(declaration 3.1, E70)")
        if self.bridge.net_debt is None:
            gaps.append("net debt (declaration 4)")
        for item in BRIDGE_ITEMS:
            since = BRIDGE_ITEMS_SINCE.get(item)
            if since is not None and item_predates(self.run_ts, since):
                continue        # struck before the item existed (E68, E81)
            if item not in self.bridge.items:
                gaps.append(f"bridge item `{item}` in or out (declaration 4)")
        if not self.growth.view_file:
            gaps.append("the growth view g came from (declaration 6)")
        if not self.inputs:
            gaps.append("provenance for any input (declaration 8)")
        for entry in self.inputs:
            if entry.value is None:
                gaps.append(f"a value for `{entry.name}` (declaration 8)")
        return tuple(gaps)

    @property
    def complete(self) -> bool:
        return not self.missing()

    # --- the arithmetic ---------------------------------------------------

    @property
    def nci_predates_the_ruling(self) -> bool:
        """Was this record struck before E105 existed, carrying no leg?

        A RECORD IS A STATEMENT MADE ON A DATE UNDER THE RULES OF THAT DATE.
        Every record kept before 2026-09-04 was struck without this leg, and
        it is not INCOMPLETE for want of one -- it replays to the figure it
        was struck at, and its rendering says the declaration postdates it.
        **This is not a licence to omit the leg going forward:** a record
        struck today carries it or refuses, and the affected names are
        RE-STRUCK off the store rather than patched in place (E87).
        """
        return (self.nci_dividends_paid is None
                and not self._bounded("nci_dividends_paid")
                and struck_before(self.run_ts,
                                  RECORD_DECLARATIONS_SINCE["nci"]))

    def fcf0(self) -> float:
        """FCF0 under E34, E36 and E105, from this record's own inputs."""
        return free_cash_flow_zero(
            operating_cash_flow=self.operating_cash_flow,
            capex=self.capex,
            interest_in_ocf=self.interest.in_operating_cash_flow,
            net_interest_paid=self.interest.net_interest_paid,
            sbc=self.sbc.amount if self.sbc.treatment == SBC_DEDUCTED else 0.0,
            operating_leases_in_ocf=self.lease.in_operating_cash_flow,
            # E106: a BOUNDED add-back is struck at ZERO -- the low end of
            # its own range, so the value it produces is the conservative
            # one -- and the bound is what `tolerance` then measures. This
            # is the same shape as E105's bounded deduction, inverted:
            # there the struck value is the HIGH end.
            operating_lease_payments=(
                0.0 if (self.lease.principal_added_back is None
                        and self._bounded("operating_lease_payments"))
                else self.lease.principal_added_back),
            # E105 postdates every record kept: one struck before it forms
            # FCF0 the way it was struck, and says so when it renders.
            nci_dividends_paid=(0.0 if self.nci_predates_the_ruling
                                else self.nci_dividends_paid),
            lease_rule=self.lease.rule,
            lease_cash_paid=self.lease.lease_cash_deducted)

    def legs(self) -> Legs:
        """FCF0, net cash and the count, each NORMALISED TO WHOLE UNITS.

        The store states money in one unit per file and counts in their
        own; the two need not agree (PNDORA.CO: DKK millions beside a
        count of 77,189,151 shares) and dividing them raw is out by the
        ratio of the two scales. Every division in this record goes
        through here, on the store's own declarations, and REFUSES where a
        declaration is absent -- "whole" is never assumed.
        """
        absent = self._unit_gaps()
        if absent:
            raise RecordError(
                f"{self.ticker}: cannot divide -- {'; '.join(absent)}. A "
                f"per-share value across an unstated scale is a number "
                f"nobody can check")
        money = UNIT_SCALE[self.money_unit]
        count = UNIT_SCALE[self.shares.unit]
        return Legs(fcf0=self.fcf0() * money,
                    net_cash=self.bridge.net_cash * money,
                    shares=self.shares.count * count)

    def _strike_unchecked(self, growth: float | None = None, *,
                          fcf0_adjustment: float = 0.0,
                          net_cash_adjustment: float = 0.0,
                          shares_adjustment: float = 0.0) -> float:
        """The arithmetic alone, with no completeness check.

        `strike` asks `missing`, `missing` asks `tolerance`, and `tolerance`
        has to value the record -- so the valuation and the gate cannot be
        the same call.

        The money adjustments are in the STORE's money unit and are scaled
        here, the same way the legs are: E108 perturbs a leg as the file
        states it, not as the arithmetic normalises it.

        `shares_adjustment` is in the store's SHARE unit and exists because
        THE DIVISOR IS A LEG. E108 says perturb each leg; the divisor moves
        `fv_base` by about 9% for a 10% perturbation on any record, so
        leaving it unperturbable meant the one leg most certain to be above
        the floor could never be measured at all (found 2026-09-08).
        """
        legs = self.legs()
        money = UNIT_SCALE[self.money_unit]
        shares = legs.shares + shares_adjustment * UNIT_SCALE[self.shares.unit]
        return equity_value_per_share(
            fcf0=legs.fcf0 + fcf0_adjustment * money,
            growth=self.growth.base if growth is None else growth,
            net_cash=legs.net_cash + net_cash_adjustment * money,
            shares=shares,
            rate=self.rate.rate, terminal=self.conventions.terminal_growth,
            years=self.conventions.horizon_years)

    def leg_values(self) -> dict[str, tuple[float, str]]:
        """Each named leg the record carries: field -> (value, where).

        ``where`` is ``"flow"`` for a leg of FCF0 and ``"stock"`` for one of
        the net-cash bridge, because a perturbation enters the valuation at
        a different point in each case. A leg the record does NOT carry is
        absent from the mapping rather than present as zero -- E108 measures
        legs that exist, and an absent one is E106's question, not this one.
        """
        out: dict[str, tuple[float, str]] = {}

        def put(name, value, where):
            if value is not None:
                out[name] = (float(value), where)

        put("operating_cash_flow", self.operating_cash_flow, "flow")
        put("capex", self.capex, "flow")
        put("capex_combined", self.capex, "flow")
        put("capex_ppe", self.capex, "flow")
        put("capex_intangibles", self.capex, "flow")
        put("sbc", self.sbc.amount, "flow")
        put("nci_dividends_paid", self.nci_dividends_paid, "flow")
        if self.interest.in_operating_cash_flow:
            put("net_interest_paid", self.interest.net_interest_paid, "flow")
        if self.lease.rule == "E117":
            put("lease_payments_capital", self.lease.principal_paid, "flow")
            put("lease_interest_paid", self.lease.interest_paid, "flow")
            put("operating_lease_liabilities", self.lease.liability_excluded,
                "stock")
        elif self.lease.in_operating_cash_flow:
            put("lease_payments_capital", self.lease.principal_added_back,
                "flow")
            put("operating_lease_payments", self.lease.principal_added_back,
                "flow")
        put("net_debt", self.bridge.net_debt, "stock")
        for name, value in self.bridge.items.items():
            if isinstance(value, (int, float)):
                put(name, value, "stock")
                # E108 (2026-09-08): and again under the STORE's own field
                # name, which is the vocabulary the gate refuses on.
                for field_name in BRIDGE_LEG_FIELDS.get(name, ()):
                    put(field_name, value, "stock")

        # The net-debt legs the bridge does not itemise. Read off the
        # record's own inputs, so nothing the record did not read appears.
        by_input = {entry.name: entry.value for entry in self.inputs}
        for field_name in NET_DEBT_STORE_LEGS:
            if field_name in by_input:
                put(field_name, by_input[field_name], "stock")

        # THE DIVISOR IS A LEG (E108: "perturb each leg"). It moves fv_base
        # by about 9% for a 10% perturbation on any record -- the single
        # most certain leg to sit ABOVE the floor -- and until 2026-09-08 it
        # was absent from this mapping, so the gate could not measure it.
        put("diluted_weighted_average_shares", self.shares.count, "divisor")
        return out

    def sensitivity(self, *, perturbation: float = SENSITIVITY_PERTURBATION,
                    ) -> dict[str, float]:
        """E108: field -> the fraction of `fv_base` a +/-``perturbation``
        of that leg moves.

        **MEASURED, NOT ESTIMATED.** The record is valued three times per
        leg -- unperturbed, up, down -- and the LARGER of the two moves is
        taken, because the DCF is linear in FCF0 only until net cash is
        added and a leg that is small against the flow need not be small
        against the answer.

        The result is what `manual.section5_gate` takes as
        ``measured_exempt``. The gate's OTHER limb -- a leg entered at
        zero -- needs none of this and is settled on the store alone: +/-10%
        of zero is zero, whatever this record would have said.

        **WHAT IT CANNOT SEE.** Perturbing an ENTERED figure cannot catch a
        figure entered WRONG. E108 is an exemption from the READ-BACK and
        never from the provenance, and E25's `zero_basis` is what covers the
        blind spot this leaves.
        """
        base = self._strike_unchecked()
        if not base:
            return {}
        out: dict[str, float] = {}
        for name, (value, where) in self.leg_values().items():
            delta = abs(value) * perturbation
            if not delta:
                out[name] = 0.0
                continue
            moves = []
            for sign in (+1.0, -1.0):
                if where == "flow":
                    kwargs = {"fcf0_adjustment": sign * delta}
                elif where == "divisor":
                    kwargs = {"shares_adjustment": sign * delta}
                else:
                    kwargs = {"net_cash_adjustment": sign * delta}
                moves.append(abs(self._strike_unchecked(**kwargs) - base))
            out[name] = max(moves) / abs(base)
        return out

    def strike(self, growth: float | None = None) -> float:
        """The fair value per share. REFUSES on an incomplete record.

        A run without a complete record does not print a fair value: the
        number would be read months later as though somebody had written
        down what it stood on.
        """
        gaps = self.missing()
        if gaps:
            raise RecordError(
                f"{self.ticker}: the run record is INCOMPLETE and section 5 "
                f"does not print a fair value from it. Absent: "
                f"{'; '.join(gaps)}. Each of these is a declaration REVIEW-4 "
                f"found missing from every record this project keeps, and a "
                f"figure struck without them is one nobody can check.")
        if self.conventions.mid_year:
            raise RecordError(
                "this record declares MID-YEAR discounting and "
                "`equity_value_per_share` is end-of-year. The convention is "
                "declared so that a change fails LOUDLY rather than moving "
                "every stored figure in silence; wire it before declaring it")
        legs = self.legs()
        return equity_value_per_share(
            fcf0=legs.fcf0, growth=self.growth.base if growth is None else growth,
            net_cash=legs.net_cash, shares=legs.shares,
            rate=self.rate.rate, terminal=self.conventions.terminal_growth,
            years=self.conventions.horizon_years)

    def band(self, growth: float | None = None) -> Sensitivity:
        """E29's triple, across the +/- 0.5% display band."""
        if self.missing():
            self.strike()                      # raises with the same message
        legs = self.legs()
        return fair_value(
            fcf0=legs.fcf0, growth=self.growth.base if growth is None else growth,
            net_cash=legs.net_cash, shares=legs.shares,
            rate=self.rate.rate, delta=self.rate.band,
            terminal=self.conventions.terminal_growth,
            years=self.conventions.horizon_years)

    # --- serialisation, so a record can be REPLAYED -----------------------

    def to_dict(self) -> dict:
        """Plain data, with dates and the timestamp as ISO strings."""
        return _isoformat(asdict(self))

    @classmethod
    def from_dict(cls, raw: Mapping[str, Any]) -> "RunRecord":
        """A record read back. The arithmetic is re-run, never restored.

        **EVERY FIELD `to_dict` WRITES IS READ BACK HERE, and the guard at
        the foot of this method is what keeps that true.** A field added to
        the record and forgotten here is invisible: `to_dict` writes it,
        the JSON on disk states it, and the replay silently strikes without
        it. That is what happened to `nci_dividends_paid` between E105 and
        2026-09-08 -- five records whose own JSON said `0.0` replayed as
        DATA MISSING and refused to print the figure they were struck at,
        which is the exact condition E39/E87 null a stored fair value for.
        A serialisation gap must never be able to null a value.
        """
        data = dict(raw)
        built = dict(
            ticker=data["ticker"], currency=data["currency"],
            run_ts=datetime.fromisoformat(data["run_ts"]),
            basis=data["basis"],
            shares=ShareBasis(
                count=data["shares"]["count"], basis=data["shares"]["basis"],
                as_of=date.fromisoformat(data["shares"]["as_of"]),
                point_in_time=data["shares"].get("point_in_time"),
                point_in_time_as_of=_as_date(
                    data["shares"].get("point_in_time_as_of")),
                unit=data["shares"].get("unit"),
                # E75.1: E75's short-lived `period_end` label reads back as
                # the basic kind it was.
                divisor_basis={"period_end": "period_end_basic"}.get(
                    data["shares"].get("divisor_basis", "weighted_average"),
                    data["shares"].get("divisor_basis", "weighted_average")),
                prior_average=data["shares"].get("prior_average"),
                drift=data["shares"].get("drift")),
            sbc=SbcTreatment(**data["sbc"]),
            interest=InterestTreatment(**data["interest"]),
            lease=(LeaseTreatment(**data["lease"]) if data.get("lease")
                   else LeaseTreatment(None, "")),
            bridge=Bridge(**data["bridge"]),
            dates=AsOfDates(
                flows_window_end=date.fromisoformat(
                    data["dates"]["flows_window_end"]),
                balance_sheet=date.fromisoformat(data["dates"]["balance_sheet"]),
                share_count=date.fromisoformat(data["dates"]["share_count"]),
                price=_as_date(data["dates"].get("price"))),
            growth=Growth(
                base=data["growth"]["base"],
                view_file=data["growth"]["view_file"],
                view_date=_as_date(data["growth"].get("view_date")),
                bear=data["growth"].get("bear"),
                bull=data["growth"].get("bull")),
            operating_cash_flow=data["operating_cash_flow"],
            capex=data["capex"],
            conventions=Conventions(**data.get("conventions", {})),
            rate=Rate(**data.get("rate", {})),
            inputs=tuple(Input(**i) for i in data.get("inputs", ())),
            tool_commit=data.get("tool_commit", ""),
            notes=data.get("notes", ""),
            money_unit=data.get("money_unit"),
            # E105's leg. ABSENT and `null` are the same answer here -- DATA
            # MISSING -- and `nci_predates_the_ruling` is what decides
            # whether a record struck before the ruling is entitled to it.
            nci_dividends_paid=data.get("nci_dividends_paid"),
            # E106's bounded legs. Dropping these does not only lose the
            # bound `tolerance` sums; it makes `_bounded` false, so a leg
            # that was properly bounded reads back as an unbounded absence
            # and refuses.
            undetermined=tuple(Undetermined(**u)
                               for u in (data.get("undetermined") or ())),
            # E101's comparators. Carried, never used to compute anything --
            # but a construction check that reads back as DATA MISSING is a
            # check nobody ran.
            fcf_reported=_comparator_from(data.get("fcf_reported")),
            net_debt_reported=_comparator_from(data.get("net_debt_reported")),
            net_income=_comparator_from(data.get("net_income")))

        # THE GUARD. Not a style check -- the defect above was exactly this
        # set being non-empty, and nothing in the codebase could see it.
        unread = [f.name for f in dataclass_fields(cls) if f.name not in built]
        if unread:
            raise RecordError(
                f"`from_dict` does not read back {', '.join(sorted(unread))}. "
                f"`to_dict` writes every field of this record; a field this "
                f"method drops replays as though the record never stated it, "
                f"and the record then refuses -- or worse, strikes -- on a "
                f"value that is on disk and was not read")
        return cls(**built)

    # --- the page a person reads -----------------------------------------

    def construction_checks(self) -> list["Disagreement"]:
        """E101's three disagreement checks. DETECTORS, never adjudicators.

        **WHAT THIS EXISTS FOR.** E40's read-back verifies that a figure was
        correctly TRANSCRIBED from the page it names. It cannot see that the
        right figure was read from the WRONG page, that a leg is missing
        entirely, or that a bridge does not balance -- every one of those is
        correctly transcribed. All four corrections of the week to
        2026-08-31 (+36% E34, -33% E36, +56% E70, +29% E37) were of that
        kind, and none was findable by any rule in this repo.

        **NONE OF THE THREE IS AUTHORITATIVE.** The issuer's free cash flow
        is on the issuer's definition, which is usually not E34's; the
        issuer's net debt usually excludes the pension leg E35.1 includes.
        LIAB.ST's +6.3% disagreement was the ISSUER being narrower and this
        project's figure stood. So the size and direction are printed, and
        **nothing is adjusted, refused or blocked.**
        """
        out: list[Disagreement] = []
        try:
            fcf0 = self.fcf0()
        except Exception:                      # noqa: BLE001 -- a detector never raises
            fcf0 = None

        out.append(Disagreement(
            "FCF0 vs the issuer's own free cash flow",
            fcf0, self.fcf_reported.value,
            "E34's construction against the issuer's; the two definitions "
            "differ by design (interest, leases), so a gap is a PROMPT",
            comparator_field="free_cash_flow_reported",
            comparator_page=self.fcf_reported.page,
            comparator_verified=self.fcf_reported.verified))

        # E117 / C5 (owner, 2026-09-19): an issuer's own net debt carries its
        # leases, and E117 takes the operating part out of ours. The
        # comparison adds that liability BACK on our side, so the check
        # compares like with like; the E117 figure is shown beside it.
        excluded = (self.lease.liability_excluded
                    if self.lease.rule == "E117" else None)
        ours = (self.bridge.net_debt + excluded
                if self.bridge.net_debt is not None and excluded else self.bridge.net_debt)
        out.append(Disagreement(
            "net debt vs the issuer's own net debt",
            ours, self.net_debt_reported.value,
            "E35/E35.1 against the issuer's; the issuer usually EXCLUDES "
            "the pension leg, so a positive gap of a few per cent is "
            "expected -- this is the check that found LIAB.ST's"
            + (f". OURS IS COMPARED LEASE-INCLUSIVE: E117's net debt "
               f"{self.bridge.net_debt:,.0f} + the lease liability it excludes "
               f"{excluded:,.0f} = {ours:,.0f} (C5)"
               if excluded and self.bridge.net_debt is not None else ""),
            comparator_field="net_debt_reported",
            comparator_page=self.net_debt_reported.page,
            comparator_verified=self.net_debt_reported.verified))

        # 3. A check on the BASIS and not on the business: section 4.3
        #    already reads a high conversion as a GREEN FLAG, so the band is
        #    wide enough not to argue with the framework's own reading.
        net_income = self.net_income.value
        conversion = (fcf0 / net_income
                      if fcf0 is not None and net_income else None)
        low, high = FCF_CONVERSION_BAND
        if conversion is None:
            detail = ("no net income on this basis -- the ratio cannot be "
                      "formed, which is not a ratio of zero")
        elif low <= conversion <= high:
            detail = (f"inside the {low:g}-{high:g}x band -- both figures "
                      f"are on the same kind of basis")
        else:
            detail = (f"**OUTSIDE the {low:g}-{high:g}x band -- LOOK.** A "
                      f"conversion this far out usually means one figure is "
                      f"on a different basis from the other: a quarter "
                      f"against a year, a segment against a group, a "
                      f"per-share figure against a total")
        out.append(Disagreement(
            "FCF0 / net income (conversion)", fcf0, net_income, detail,
            kind="ratio", band=FCF_CONVERSION_BAND))
        return out

    def render_construction_checks(self) -> list[str]:
        """The block E101 requires beside every strike."""
        out = ["## Construction checks (E101) — DETECTORS, NOT VERDICTS", "",
               "| check | this record | the issuer | measure | |",
               "|---|---:|---:|---:|---|"]
        out += [check.line() for check in self.construction_checks()]
        out += ["",
                "*E101: E40 verifies that a figure was correctly TRANSCRIBED "
                "from the page it names; nothing in this project has ever "
                "checked that it was CONSTRUCTED right. These three do — and "
                "**none of them is authoritative and none adjudicates.** The "
                "issuer's definitions are not this project's (interest under "
                "E34, the pension leg under E35.1), so a gap is a prompt to "
                "look and never a finding that either figure is wrong. "
                "**Nothing here adjusts, refuses or blocks anything.** A "
                "comparator the issuer does not publish is DATA MISSING, "
                "never a disagreement of zero.*", "",
                "*E103: the comparators are REFERENCE figures — compared "
                "against a valuation, never used to build one — so they are "
                "fetched automatically and entered UNVERIFIED, and no §5 "
                "basis may read them. Where a check disagrees, the line "
                "names the ONE figure to read back. **The read-back moves "
                "from every figure in advance to the figure that actually "
                "blinked.***"]
        return out

    def render(self) -> str:
        """The record as markdown, in the order report C Part 10 lists."""
        out = [f"# section 5 run record — {self.ticker} — "
               f"{self.run_ts.isoformat(timespec='seconds')}", ""]
        gaps = self.missing()
        if gaps:
            out += ["## INCOMPLETE — NO FAIR VALUE IS PRINTED", ""]
            out += [f"- {gap}" for gap in gaps]
            out += ["", "A run without a complete record does not print a "
                    "fair value.", ""]
        else:
            value = self.strike()
            out += [f"**Fair value {value:,.2f} {self.currency}** at g "
                    f"{self.growth.base:.2%}, r {self.rate.rate:.2%}.", "",
                    f"*{rate_declaration(self.currency)}*", ""]
            # E34.1: "accrual proxy" is printed BESIDE FCF0, every time.
            # E61: the interest-expense-only proxy gets its own label PLUS
            # its bound, as a percentage of FCF0 -- computed HERE, not in
            # `manual.py`, because that module never sees FCF0 itself.
            if self.interest.accrual_proxy:
                proxy = f" — {ACCRUAL_PROXY_LABEL}"
            elif self.interest.interest_expense_only_proxy:
                fcf0_value = self.fcf0()
                bound = (f" (bound: {abs(self.interest.net_interest_paid) / abs(fcf0_value):.1%} of FCF0)"
                         if fcf0_value else "")
                proxy = f" — {INTEREST_EXPENSE_ONLY_LABEL}{bound}"
            elif self.interest.cash_paid_only_proxy:
                # E115: the same bound, off the cash figure.
                fcf0_value = self.fcf0()
                bound = (f" (bound: {abs(self.interest.net_interest_paid) / abs(fcf0_value):.1%} of FCF0)"
                         if fcf0_value else "")
                proxy = f" — {CASH_PAID_ONLY_LABEL}{bound}"
            else:
                proxy = ""
            out += [f"- **FCF0:** {self.fcf0():,.0f} {self.currency} "
                    f"{self.money_unit}{proxy}", ""]
        out += [f"- **basis (E19):** {self.basis}", ""]
        if not gaps:
            # E101: printed with EVERY strike, agreeing or not. A detector
            # visible only when it fires cannot be checked for being wrong.
            out += self.render_construction_checks()
        out += [f"- **units:** money stated in "
                f"{self.money_unit or '**UNIT NOT STATED**'}, the count in "
                f"{self.shares.unit or '**UNIT NOT STATED**'}; the division "
                f"normalises both to whole units on the store's declaration", ""]

        out += ["## The eight declarations", "",
                "| # | declaration | this run |", "|---|---|---|"]
        pit = ("—" if self.shares.point_in_time is None else
               f"{self.shares.point_in_time:,.0f} as of "
               f"{self.shares.point_in_time_as_of}")
        count = (f"{self.shares.count:,.0f}" if self.shares.unit in (None, "whole")
                 else f"{self.shares.count:,.3f} {self.shares.unit}")
        out += [
            f"| 1 | share-count basis | {count} — "
            f"{self.shares.basis.split(';')[0]}, as of "
            f"{self.shares.as_of.isoformat()}; divisor basis "
            f"`{self.shares.divisor_basis}` (E75 / E75.1 / E88 / E91)"
            + (f", drift {self.shares.drift:+.2%} against the annual "
               f"average {self.shares.prior_average:,.0f}"
               if self.shares.drift is not None else "")
            + f"; memo (E38, never the divisor): {pit} |",
            f"| 2 | share-based compensation | {self.sbc.treatment}"
            + (f", {self.sbc.amount:,.0f}" if self.sbc.amount is not None
               else ", amount DATA MISSING")
            + (f" — for {self.sbc.basis}" if self.sbc.basis else "") + " |",
            f"| 3 | interest | {self.interest.sentence}. Read from: "
            f"{self.interest.page} |",
            f"| 3.1 | lease principal (E70) | "
            + (f"NOT DECLARED -- this record was struck "
               f"{self.run_ts.date().isoformat()}, before the declaration "
               f"existed (E70, 2026-08-30); complete AS STRUCK and, for a "
               f"filer whose operating cash flow bears its operating lease "
               f"payments, charged for the lease twice until re-struck"
               if self.lease.in_operating_cash_flow is None
               and struck_before(self.run_ts, RECORD_DECLARATIONS_SINCE["lease"])
               else f"{self.lease.sentence}"
               + (f". Read from: {self.lease.page}" if self.lease.page else ""))
            + " |",
            f"| 4 | bridge | net debt "
            + ("DATA MISSING" if self.bridge.net_debt is None
               else f"{self.bridge.net_debt:,.0f}")
            + (f" — {self.bridge.note}" if self.bridge.note else "") + " |",
            f"| 5 | DCF conventions | {self.conventions.sentence} |",
            f"| 6 | r and g | r {self.rate.rate:.2%}, "
            f"{self.rate.anchor_sentence}; g {self.growth.base:.2%} from "
            f"`{self.growth.view_file}`"
            + (f" ({self.growth.view_date.isoformat()})"
               if self.growth.view_date else "") + " |",
            f"| 7 | as-of dates | flows to "
            f"{self.dates.flows_window_end.isoformat()}; balance sheet "
            f"{self.dates.balance_sheet.isoformat()}; share count "
            f"{self.dates.share_count.isoformat()}"
            + (f"; price {self.dates.price.isoformat()}"
               if self.dates.price else "; no price used")
            + (" — **THEY AGREE**" if self.dates.agree
               else f" — **THEY DO NOT AGREE** ({self.dates.disagreement} "
                    f"against flows to "
                    f"{self.dates.flows_window_end.isoformat()}), and the "
                    f"difference is inside the number") + " |",
            f"| 8 | provenance | {len(self.inputs)} input(s), below |",
            "",
        ]

        out += ["## Bridge items (declaration 4, item by item)", "",
                "| item | in the bridge? |", "|---|---|"]
        for item in BRIDGE_ITEMS:
            value = self.bridge.items.get(item, "NOT DECLARED")
            since = BRIDGE_ITEMS_SINCE.get(item)
            if (item not in self.bridge.items and since is not None
                    and item_predates(self.run_ts, since)):
                ruling = "E68" if item == "asset_retirement_obligations" else "E81"
                value = (f"NOT DECLARED -- this record was struck "
                         f"{self.run_ts.isoformat()}, before the leg "
                         f"existed ({since.isoformat()}, {ruling}); the bridge "
                         f"is complete AS STRUCK and incomplete under {ruling} "
                         f"until the leg is entered and the value re-struck")
            if value is None:
                shown = "**DATA MISSING** on this basis"
            elif value == 0:
                shown = "0 (stated)"
            elif isinstance(value, str):
                shown = value
            else:
                shown = f"{value:,.0f}"
            out.append(f"| `{item}` | {shown} |")
        out.append("")

        out += ["## Inputs (declaration 8)", "",
                "| input | value | entered by | verified (E40) | provenance |",
                "|---|---:|---|---|---|"]
        for entry in self.inputs:
            shown = "DATA MISSING" if entry.value is None else f"{entry.value:,.4g}"
            out.append(f"| `{entry.name}` | {shown} | {entry.entered_by} | "
                       f"{entry.verified or '—'} | {entry.provenance} |")
        out.append("")
        if self.tool_commit:
            out += [f"*Tool commit: `{self.tool_commit}`.*", ""]
        if self.notes:
            out += [self.notes, ""]
        return "\n".join(out)


def _as_date(value: Any) -> date | None:
    if value is None or isinstance(value, date):
        return value
    return date.fromisoformat(value)


def _isoformat(value: Any) -> Any:
    """Dates and datetimes to ISO strings, recursively. Nothing else moves."""
    if isinstance(value, datetime):
        return value.isoformat(timespec="seconds")
    if isinstance(value, date):
        return value.isoformat()
    if isinstance(value, dict):
        return {k: _isoformat(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [_isoformat(v) for v in value]
    return value


def replay(raw: Mapping[str, Any], growth: float | None = None) -> float:
    """The whole point, in one function: a record in, a fair value out.

    No file is opened, no hand input is asked for and no constant is taken
    from anywhere but the record. If this does not reproduce the figure the
    run printed, the record was not a record.
    """
    return RunRecord.from_dict(raw).strike(growth)


# --- building one from a store file ---------------------------------------


def _comparator(parsed, basis, hand,
                name: str) -> tuple[float | None, str, bool]:
    """One issuer-stated figure on the run's own basis, with its page.

    E101. Same resolution the legs use, and the same hand-entry fallback,
    so a comparator can never be read off a different window from the
    figure it is compared with (E19).
    """
    from . import manual as M

    resolved = M.resolve_on_basis(parsed, basis, name)
    value = resolved.value
    # `Resolved` carries the FIGURES it was built from, not a page of its
    # own -- a summed flow has four. The first one's page is what E103's
    # "verify this one" line points at, and for a STOCK there is only one.
    figures = tuple(getattr(resolved, "figures", ()) or ())
    page = (getattr(figures[0], "page", "") or "") if figures else ""
    verified = bool(getattr(resolved, "verified", False))
    if value is None and name in hand:
        value = hand[name].value
        page = getattr(hand[name], "page", "") or ""
        verified = bool(getattr(hand[name], "verified", False))
    return value, page, verified


def from_store(parsed, basis, *, growth: "Growth", run_ts: datetime,
               hand_inputs: Sequence[Input] = (),
               price_date: date | None = None,
               rate: "Rate | None" = None,
               conventions: "Conventions | None" = None,
               tool_commit: str = "", notes: str = "") -> "RunRecord":
    """A record built from a `config/manual/<TICKER>.yaml` and the choices.

    EVERYTHING THE FILE CAN ANSWER COMES OFF THE FILE, with the page the
    figure carries. Everything it cannot is a `hand_inputs` entry with its
    own page -- and it is IN THE RECORD, which is what makes the replay
    need no hand input of its own.

    ``hand_inputs`` may supply a leg the store does not hold. DECK's
    borrowings are nil and that is a SENTENCE in a 10-Q (E25's `note`
    basis): the annual XBRL path cannot emit it, because absence of a tag is
    DATA MISSING and inventing a zero from one is exactly the substitution
    that path exists not to make. A hand input is entered IN THE STORE'S
    OWN UNIT -- the record carries one `money_unit` and one `shares.unit`,
    read off the file's declarations, and every division normalises on
    them (`legs`). A file that declares neither builds a record that is
    INCOMPLETE on the division, not one that divides raw.
    """
    from . import manual as M

    hand = {entry.name: entry for entry in hand_inputs}
    inputs: list[Input] = []

    def kinds_of(figures) -> str:
        """E40: the verification the figures stand on, in one label."""
        figures = [f for f in figures if f is not None]
        if not figures:
            return ""
        if all(f.verified for f in figures):
            kinds = "/".join(sorted({f.verified_kind for f in figures
                                     if f.verified_kind}))
            return f"VERIFIED ({kinds})" if kinds else "VERIFIED"
        if all(f.status == M.STATUS_NOT_PRESENTED for f in figures):
            return "NOT PRESENTED (E85)"
        return "UNVERIFIED"

    def leg(name: str) -> float | None:
        if name in hand:
            entry = hand[name]
            if not entry.verified:
                entry = Input(entry.name, entry.value, entry.provenance,
                              entry.entered_by, "hand")
            inputs.append(entry)
            return entry.value
        resolved = M.resolve_on_basis(parsed, basis, name)
        value = resolved.value
        if value is None:
            rule = next((r for r in M.SUBTRACTIONS if r.net == name), None)
            got = parsed.basis_subtraction(basis, rule) if rule else None
            if got is not None:
                value, a, b, c = got
                # E54's optional third leg has never reached this path -- it
                # is only ever wired for shares_outstanding_period_end, and
                # nothing in the run record divides by that count (A6 reads
                # diluted_weighted_average_shares instead). Handled anyway,
                # so a future caller cannot silently drop the leg's evidence.
                detail = f"E18: {rule.minuend} - {rule.subtrahend}"
                verify_figures = list(a.figures) + list(b.figures)
                spread = "both"
                if c is not None:
                    detail += f" - {rule.optional_subtrahend} (E54)"
                    verify_figures += list(c.figures)
                    spread = "all"
                inputs.append(Input(
                    name, value, f"{detail}, {spread} on {basis.label}",
                    "store", kinds_of(verify_figures)))
                return value
            return None
        # E85 / E86: the page line carries the search, or both columns.
        pages = "; ".join(f.page_provenance for f in resolved.figures
                          if f.page_provenance)
        inputs.append(Input(name, value,
                            pages or f"{resolved.source} on {basis.label}",
                            "store", kinds_of(resolved.figures)))
        return value

    capex_legs, capex_why = M.capex_legs(parsed, basis)
    # E41: a filer that prints capex CUMULATIVELY (SAP) has no stated
    # quarter for the store, and the window's figure enters the RECORD by
    # hand, as the one combined line, with every column it was netted from
    # on its provenance. Only where the store supplies NEITHER shape.
    if ("capex_combined" in hand and not all(
            M.resolve_on_basis(parsed, basis, n).value is not None
            for n in M.SPLIT_CAPEX)):
        capex_legs = M.COMBINED_CAPEX
        capex_why = ("combined BY HAND (E41): the issuer prints capex "
                     "cumulatively and states no standalone quarter, so the "
                     "window's figure is netted from stated cumulative columns "
                     "and entered on the record with all of them named")
    # KEEP None AS None. `capex_legs` returns the split pair even when
    # NEITHER shape is on the basis, so summing `or 0.0` over it produced a
    # capex of zero for a file whose capital spending is DATA MISSING -- and
    # `missing()` never saw it, because an absent leg records no input.
    capex_values = [leg(name) for name in capex_legs]
    capex = (None if not capex_values or any(v is None for v in capex_values)
             else sum(capex_values))
    ocf = leg("operating_cash_flow")
    sbc = leg("sbc")
    # E34 / E34.1: the leg is whatever `interest_legs` says it is for this
    # filer -- `net_interest_paid` off the cash flow statement, or the
    # income statement's `net_finance_costs` as an accrual proxy. Never
    # interest paid alone.
    interest_leg = [name for name in M.interest_legs(parsed)
                    if name != M.INTEREST_UNCLASSIFIED]
    net_interest = leg(interest_leg[0]) if interest_leg else None
    # THE BRIDGE ITEMS AND THE LEASE FIGURE, resolved once for the record.
    leases_on_basis = M.resolve_on_basis(parsed, basis, "lease_liabilities").value
    if leases_on_basis is None and "lease_liabilities" in hand:
        leases_on_basis = hand["lease_liabilities"].value
    pension_on_basis = M.resolve_on_basis(parsed, basis, "pension_deficit").value
    if pension_on_basis is None and "pension_deficit" in hand:
        pension_on_basis = hand["pension_deficit"].value
    # E68: the asset-retirement leg, on the pension leg's terms.
    aro_on_basis = M.resolve_on_basis(parsed, basis,
                                      "asset_retirement_obligation").value
    if aro_on_basis is None and "asset_retirement_obligation" in hand:
        aro_on_basis = hand["asset_retirement_obligation"].value
    # E81: the prepaid-delivery leg, on the same terms.
    # E105: the flow's newest leg, read on the basis like every other.
    nci_on_basis = M.resolve_on_basis(parsed, basis, "nci_dividends_paid").value
    if nci_on_basis is None and "nci_dividends_paid" in hand:
        nci_on_basis = hand["nci_dividends_paid"].value
    pdo_on_basis = M.resolve_on_basis(parsed, basis,
                                      "prepaid_delivery_obligation").value
    if pdo_on_basis is None and "prepaid_delivery_obligation" in hand:
        pdo_on_basis = hand["prepaid_delivery_obligation"].value
    # E38 / E41 / E75: the divisor in E75's order. A window average is
    # E38's; the count OUTSTANDING at the window end replaces E41's annual
    # average where no window average is stated (E75, 2026-08-30); the
    # annual average stands only where nothing at the window end is stated,
    # and then carries ITS OWN date, which the record prints as such.
    divisor = M.share_divisor_on_basis(parsed, basis)
    if divisor.divisor_basis == M.DIVISOR_WINDOW_DAY_WEIGHTED:
        # E91: the four stated quarterly counts, day-weighted by the code;
        # the window's own average, so the share date is the basis end.
        count = divisor.count
        count_as_of = divisor.as_of
        inputs.append(Input(
            "diluted_weighted_average_shares", count,
            divisor.provenance or f"on {basis.label}",
            "store", kinds_of(list(divisor.figures))))
    elif divisor.divisor_basis in (M.DIVISOR_PERIOD_END_DILUTED,
                                   M.DIVISOR_PERIOD_END_BASIC):
        count = divisor.count
        count_as_of = divisor.as_of
        inputs.append(Input(
            (M.DILUTED_SHARES if divisor.divisor_basis == M.DIVISOR_PERIOD_END_DILUTED
             else M.NET_SHARES), count,
            divisor.provenance or f"on {basis.label}",
            "store", kinds_of(list(divisor.figures))))
    else:
        count = leg("diluted_weighted_average_shares")
        count_as_of = (divisor.as_of if count is not None and divisor.as_of
                       else basis.end)
    sbc_resolved = M.resolve_on_basis(parsed, basis, "sbc")
    sbc_basis = (sbc_resolved.source
                 if sbc_resolved.value is not None
                 and sbc_resolved.end != basis.end else "")
    memo = leg("shares_point_in_time")
    for name in M.NET_DEBT_LEGS:
        leg(name)
    assets = leg("other_current_financial_assets")
    net_debt, bridge_why = M.net_debt_on_basis(parsed, basis)
    if net_debt is None:
        # A HAND INPUT FILLS A LEG THE STORE CANNOT HOLD, and only that leg.
        # DECK's borrowings are nil by a SENTENCE in a 10-Q; its cash and its
        # leases are tagged facts and still come off the file.
        legs = {}
        for name in M.NET_DEBT_LEGS:
            legs[name] = (hand[name].value if name in hand
                          else M.resolve_on_basis(parsed, basis, name).value)
        consolidated = hand.get("financial_liabilities_consolidated")
        excluded_hand = (
            (hand["operating_lease_liabilities"].value
             if "operating_lease_liabilities" in hand
             else M.resolve_on_basis(parsed, basis,
                                     "operating_lease_liabilities").value)
            if M.lease_excluded_legs(parsed) else None)
        kept_hand = (M.lease_in_net_debt(parsed, legs["lease_liabilities"],
                                         excluded_hand)[0]
                     if legs["lease_liabilities"] is not None else None)
        if all(v is not None for v in legs.values()) and kept_hand is not None:
            net_debt = (legs["financial_liabilities_current"]
                        + legs["financial_liabilities_noncurrent"]
                        + kept_hand
                        + legs["pension_deficit"]
                        + legs["asset_retirement_obligation"]
                        + legs["prepaid_delivery_obligation"]
                        - legs["cash_and_equivalents"] - (assets or 0.0))
            named = ", ".join(f"`{n}` by hand" for n in M.NET_DEBT_LEGS
                              if n in hand)
            bridge_why = (f"E35's legs (E35.1 pension, E68 asset retirement, "
                          f"E81 prepaid delivery), "
                          f"{named} and the rest off the store on {basis.label}")
        elif (consolidated is not None
              and legs["cash_and_equivalents"] is not None
              and legs["pension_deficit"] is not None
              and legs["asset_retirement_obligation"] is not None
              and legs["prepaid_delivery_obligation"] is not None
              and all(legs[n] is None for n in ("financial_liabilities_current",
                                                 "financial_liabilities_noncurrent",
                                                 "lease_liabilities"))
              # E117: the leases inside an unsplit consolidated line cannot
              # be taken out of it, so an IFRS file on this path has no
              # rent-bearing net debt -- refused rather than overstated.
              and not (parsed.operating_leases_in_ocf is not None
                       and not parsed.operating_leases_in_ocf.value)):
            # E41: ONE consolidated `Financial liabilities` line, leases and
            # derivatives inside, and no note that splits it (SAP's
            # interim). E14 keeps it OUT of the borrowing fields; E35 needs
            # only the SUM, which this line IS. So it enters the RECORD by
            # hand, with its page, and the bridge says so -- never the
            # store.
            entry = consolidated if consolidated.verified else Input(
                consolidated.name, consolidated.value, consolidated.provenance,
                consolidated.entered_by, "hand")
            inputs.append(entry)
            net_debt = (entry.value + legs["pension_deficit"]
                        + legs["asset_retirement_obligation"]
                        + legs["prepaid_delivery_obligation"]
                        - legs["cash_and_equivalents"] - (assets or 0.0))
            leases_on_basis = (f"inside the consolidated line "
                               f"{entry.value:,.0f} -- not split (E14), and "
                               f"IN net debt with it (E35)")
            bridge_why = (f"CONSOLIDATED financial liabilities "
                          f"{entry.value:,.0f} BY HAND (E41: one line per "
                          f"side, leases and derivatives inside, split not "
                          f"stated -- E14's three fields stay DATA MISSING "
                          f"in the store) + pension deficit "
                          f"{legs['pension_deficit']:,.0f} (E35.1) + asset "
                          f"retirement obligations "
                          f"{legs['asset_retirement_obligation']:,.0f} (E68) + prepaid "
                          f"delivery obligations "
                          f"{legs['prepaid_delivery_obligation']:,.0f} (E81) - cash "
                          f"{legs['cash_and_equivalents']:,.0f}"
                          + (f" - other current financial assets {assets:,.0f}"
                             if assets is not None else
                             " - other current financial assets DATA MISSING"))

    # E106 clause 3: every BOUNDED leg the basis would have read, collected
    # off the store. A bound is not a value -- `resolve_on_basis` never
    # returns one -- so the legs it covers stay absent and the record
    # carries the bound beside them, which is what `tolerance` measures and
    # what `missing` consults before it calls an absence a gap.
    undetermined: list[Undetermined] = []
    for figure in M.basis_bounds(parsed, basis):
        # A BOUND ON A LEG THAT IS ACTUALLY THERE IS NOT AN UNDETERMINED
        # LEG. The store may carry a ceiling for a window in which the
        # figure itself is absent and a hand input, or a newer filing, may
        # supply it anyway -- and once it is supplied there is nothing left
        # to bound. Keeping both would charge the tolerance for an
        # uncertainty the record does not have.
        if (M.resolve_on_basis(parsed, basis, figure.name).value is not None
                or figure.name in hand):
            continue
        undetermined.append(Undetermined(
            name=figure.name, bound=abs(float(figure.bound)),
            page=f"{figure.source or 'source not stated'} -- {figure.page}",
            direction=figure.bound_direction or BOUND_REDUCES))

    classification = parsed.interest_in_ocf
    # E117 (2026-09-19): RENT IS AN OPERATING COST. Every record struck from
    # here states `rule: E117`; one struck before replays under E70.
    lease_class = parsed.operating_leases_in_ocf
    leases_kept = leases_on_basis
    if lease_class is None:
        lease = LeaseTreatment(None, "", rule="E117")
    elif not lease_class.value:
        principal = leg("lease_payments_capital")
        interest = leg("lease_interest_paid")
        # E120 (2026-09-19): the newest annual lease interest marked
        # STAND-IN, where the basis's own periods state none -- entered on
        # the record with its date, so the window mismatch is never hidden.
        stand = M.lease_interest_stand_in(parsed, basis)
        if interest is None and stand is not None:
            interest = abs(stand.value)
            inputs.append(Input("lease_interest_paid", interest,
                                f"STAND-IN (E120): {stand.period} -- {stand.page}",
                                "store", kinds_of([stand])))
        # E106 clause 3 on E117's leg (owner, 2026-09-19, LIAB.ST): lease
        # interest ABSENT but BOUNDED is struck at ZERO -- the generous end
        # -- and the bound goes on the record's `undetermined`, where the
        # tolerance measures it. Never a value invented inside the bound.
        interest_bounded = interest is None and any(
            f.name == "lease_interest_paid" for f in M.basis_bounds(parsed, basis))
        struck_interest = 0.0 if interest_bounded else interest
        cash = (abs(principal) + abs(struck_interest)
                if principal is not None and struck_interest is not None else None)
        excluded = (leases_on_basis
                    if isinstance(leases_on_basis, (int, float)) else None)
        leases_kept = 0.0 if excluded is not None else leases_on_basis
        lease = LeaseTreatment(
            False, f"{lease_class.source} {lease_class.page}",
            leg=("`lease_payments_capital` + `lease_interest_paid`, DEDUCTED "
                 "(E117: the IFRS 16 principal and lease interest)"
                 + ("; lease interest BOUNDED, struck at zero (E106)"
                    if interest_bounded else "")
                 + (f"; lease interest STAND-IN (E120, {stand.period})"
                    if stand is not None else "")),
            rule="E117", lease_cash_deducted=cash,
            principal_paid=abs(principal) if principal is not None else None,
            interest_paid=abs(interest) if interest is not None else None,
            liability_excluded=excluded)
    else:
        operating = leg("operating_lease_liabilities")
        if isinstance(leases_on_basis, (int, float)) and operating is not None:
            leases_kept = M.lease_in_net_debt(parsed, leases_on_basis,
                                              operating)[0]
        lease = LeaseTreatment(
            True, f"{lease_class.source} {lease_class.page}",
            leg="none -- the operating cash flow bears the rent (E117)",
            rule="E117", liability_excluded=operating)
    return RunRecord(
        ticker=parsed.ticker, currency=parsed.reporting_currency,
        run_ts=run_ts, basis=basis.label,
        shares=ShareBasis(
            count=count, basis=divisor.why,
            as_of=count_as_of, point_in_time=memo,
            point_in_time_as_of=basis.end if memo is not None else None,
            unit=parsed.share_unit,
            divisor_basis=divisor.divisor_basis or "weighted_average",
            prior_average=divisor.prior_average, drift=divisor.drift),
        sbc=SbcTreatment(SBC_DEDUCTED, sbc, sbc_basis),
        interest=InterestTreatment(
            in_operating_cash_flow=(None if classification is None
                                    else classification.value),
            page=(f"{classification.source} {classification.page}"
                  if classification else ""),
            net_interest_paid=net_interest,
            source=(classification.interest_source if classification
                    else "cash_flow_statement")),
        lease=lease,
        nci_dividends_paid=nci_on_basis,
        undetermined=tuple(undetermined),
        bridge=Bridge(
            net_debt=net_debt,
            items={
                # A1's line, and it is the SAME field: this schema has one
                # `other_current_financial_assets` and section 5 subtracts it
                # wherever it is present (E35).
                "short_term_investments": assets,
                "current_financial_assets": assets,
                # E117: what of the lease liability STAYS in net debt --
                # finance leases (US), nothing (IFRS 16). What left is on
                # the lease declaration as `liability_excluded`.
                "leases": leases_kept,
                # E35.1: a FIELD now, and a leg. None here is DATA MISSING
                # on this basis, which is what makes net debt DATA MISSING.
                "pensions": pension_on_basis,
                # E68: a FIELD and a leg. None is DATA MISSING on this basis.
                "asset_retirement_obligations": aro_on_basis,
                # E81: a FIELD and a leg, the same terms.
                "prepaid_delivery_obligations": pdo_on_basis,
                # E105 (2026-09-04): THE MINORITY IS NOT A BRIDGE ITEM.
                # Report A 4.1 named its absence a structural finding and
                # E101 measured it on IMB.L; E105 answered it in the FLOW,
                # not here, and DECLINED the liability treatment because
                # valuing a minority stake is a second unaudited lever
                # beside the pre-registered growth view (E29's ground).
                # The bridge carries no equity claim of any kind.
                "non_controlling_interests": NCI_IN_THE_FLOW,
            },
            note=f"{bridge_why}. Capex legs: {capex_why}"),
        dates=AsOfDates(flows_window_end=basis.end, balance_sheet=basis.end,
                        share_count=count_as_of, price=price_date),
        growth=growth,
        operating_cash_flow=ocf, capex=capex,
        conventions=conventions or Conventions(),
        rate=rate or Rate(),
        inputs=tuple(inputs), tool_commit=tool_commit, notes=notes,
        money_unit=parsed.money_unit,
        # E101: the issuer's own figures, carried so the construction
        # checks can be struck. Read on the SAME BASIS as everything else
        # (E19) -- a comparator off a different window would manufacture a
        # disagreement rather than detect one.
        fcf_reported=Comparator(
            *_comparator(parsed, basis, hand, "free_cash_flow_reported")),
        net_debt_reported=Comparator(
            *_comparator(parsed, basis, hand, "net_debt_reported")),
        net_income=Comparator(
            *_comparator(parsed, basis, hand, "net_income")))
