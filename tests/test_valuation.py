"""FRAMEWORK-EDITS E28's engine and E29's hurdle rate."""

import pytest

from vss import valuation as V

# =========================================================================
# WHAT THESE TESTS ARE  (REVIEW-4 report C, Part 10's labelling rule)
# =========================================================================
#
# THEY PIN ARITHMETIC GIVEN STATED ASSUMPTIONS. Not one of them is a
# "known-correct" fair value, and none may be read as one: every figure
# below is the arithmetic of the choices listed here, made on 2026-08-25 by
# the same reading of those choices as the code. Where a choice is later
# ruled the other way THESE ARE THE TESTS THAT FAIL -- which is what they
# are for, provided the failure names the choice that moved.
#
# THE EIGHT DECLARATIONS, for DECK's figures below:
#
#   1 SHARE-COUNT BASIS.  136,414,227, the cover-page count of the Q1 FY27
#     10-Q, as of 2026-07-09. A tagged fact
#     (`dei:EntityCommonStockSharesOutstanding`, B36 corrected). NOT the
#     weighted average (145,805,000, FY2026) and not the balance-sheet
#     count at the flow window's end (136,725,000, 2026-06-30). A6 is
#     unthrown; E38 makes the weighted average the divisor, and when it
#     does, THIS TEST MOVES to 131.87 and says so.
#   2 SBC.  46.8m for the TTM window, ADDED BACK -- it is a non-cash charge
#     inside operating cash flow and nothing here removes it. E36 deducts
#     it; under E36 the same inputs give 135.54.
#   3 INTEREST.  Deckers files under ASC 230, so interest paid (2.5m, TTM)
#     is INSIDE operating cash flow. FCF0 is therefore an equity-level flow
#     and the net-CASH step is applied anyway. Immaterial here (+0.02) and
#     declared because it is not immaterial for a net-debt name.
#   4 BRIDGE.  net_cash = +1,602.589m: cash at 2026-06-30, borrowings NIL
#     (a sentence in the 10-Q, E25), A1 = N (no short-term investments
#     tagged), A2 = N (operating leases 472.3m OUT, with ASC 842 rent
#     already inside operating cash flow -- the consistent pairing). No
#     NCI, no pension, no associates.
#   5 DCF CONVENTIONS.  Ten explicit years; terminal 2.5%; END-OF-YEAR
#     discounting; the stream starts at FCF0*(1+g) so FCF0 itself is never
#     counted; Gordon on year ten, discounted ten full years. No mid-year
#     factor -- applying one moves 140.95 to 146.95.
#   6 r AND g.  r 9.5%, E29's flat hurdle = a 7.0% core expected return plus
#     a 2.5% premium. g per row: 0 / 3.5% / 8%, the 3.5% from
#     `reference/growth-views/DECK.md`.
#   7 THE THREE AS-OF DATES.  Flow window ends 2026-06-30; net cash at
#     2026-06-30; share count as of 2026-07-09. They do NOT agree, and the
#     nine days between the last two are 311k shares of buybacks counted in
#     the divisor and not in the cash: +0.32 against the consistent
#     2026-06-30 pair (140.63). Price where used: see each test.
#   8 PROVENANCE.  10-Q 0000910521-26-000022 (filed 2026-07-30) for the TTM
#     legs, the June cash and the cover count; 10-K 0001628280-26-037664 for
#     the FY2026 comparatives. Reproduced in
#     `reports/DECK-METHOD-C-2026-08-25.md`.

DECK = dict(fcf0=1117.9, net_cash=1602.589, shares=136.414227)

#: AN INTRADAY PRINT, and it is declared rather than corrected because it is
#: what the hand run of 2026-08-25 17:13 CEST actually used. The SETTLED
#: close that evening was 88.74 (REVIEW-4 report A 4.2). Item 3 of this build
#: stops `vss run` reading a live bar as a close; this constant is a record
#: of one number struck before that, not a price anything acts on.
DECK_PRICE = 88.55
DECK_SETTLED_CLOSE = 88.74


def test_e28_engine_reproduces_the_deck_run():
    """PINS ARITHMETIC GIVEN THE EIGHT DECLARATIONS ABOVE.

    The numbers in `reports/DECK-METHOD-C-2026-08-25.md`, to the cent. What
    "to the cent" means here: the engine reproduces the arithmetic of that
    day's choices exactly. It does not mean the choices are settled --
    declarations 1, 2 and 7 are each open or superseded, and each has a
    stated alternative value beside it above.
    """
    assert V.equity_value_per_share(growth=0.0, **DECK) == pytest.approx(111.62, abs=0.005)
    assert V.equity_value_per_share(growth=0.035, **DECK) == pytest.approx(140.95, abs=0.005)
    assert V.equity_value_per_share(growth=0.080, **DECK) == pytest.approx(192.31, abs=0.005)
    g = V.implied_growth(price=DECK_PRICE, **DECK)
    assert g == pytest.approx(-0.03636, abs=1e-5)


def test_e28_engine_reproduces_the_earlier_session_anchor():
    """The engine reproduces a figure struck by hand on 2026-08-23.

    `deck-scoring-evidence.md` recorded an implied growth of -2.02% on its
    own basis: shares 145.805 (the FY26 weighted average, a flow to
    2026-03-31), cash 1603.0 (2026-06-30), FCF 1117.9 (TTM to 2026-06-30),
    price 91.68 (the 2026-08-21 settled close).

    THE DOCSTRING USED TO SAY "if this ever fails, the model changed -- not
    the company", and that was false (REVIEW-4 report C 9.3 #4). It is true
    only if all four inputs are frozen, which they are: they are literals in
    this test. What the sentence hid is that the four do not agree with each
    other -- a June flow, a June stock, a MARCH-AVERAGE divisor and an
    August price, the three-dates defect of report A 2.4 in one line. This
    test calibrates the engine against its own earlier arithmetic on a
    mismatched basis, and that is all it does.
    """
    g = V.implied_growth(price=91.68, fcf0=1117.9, net_cash=1603.0, shares=145.805)
    assert g == pytest.approx(-0.0202, abs=5e-5)


# --- E29: the rate is a preference, flat, anchored -------------------------


def test_e29_the_rate_is_one_flat_number():
    """No per-name rate exists, and that is the ruling, not an omission.

    E29 declined a per-currency or per-capital-structure rate knowingly: it
    would be a second owner-set lever per name at the moment E28 made g the
    single one, and g is pre-registered and auditable where r would not be.
    """
    assert V.HURDLE_RATE == 0.095
    assert V.HURDLE_SENSITIVITY == 0.005


def test_the_anchor_s_core_is_recorded_by_no_entry_anywhere():
    """REVIEW-4 report C 9.3 #9 / report B 6.6, and it is a real gap.

    E29 says r is ANCHORED: the index core's expected return plus 2-3
    points, and "if the core's expected return moves materially, r moves
    with it". That condition cannot fire, because the core's expected
    return -- the 7.0% below -- is written in NO file. `config.HurdleRecord`
    parses a four-fact `hurdle:` block and refuses a partial one, and NOT ONE
    watchlist entry carries the block. The 9.5% behind both held fair values
    is prose in a comment.

    Pinned as a fact rather than fixed: what the core's expected return IS
    is the owner's to state, and inventing one here would be worse than
    recording that it is missing.
    """
    from pathlib import Path
    from vss.config import HurdleRecord, load_watchlist
    watchlist = Path("config/watchlist.yaml")
    assert "\n    hurdle:" not in watchlist.read_text(encoding="utf-8")
    assert all(e.hurdle is None for e in load_watchlist(watchlist))
    # the record EXISTS and refuses a partial block; it is simply empty
    assert HurdleRecord is not None
    # and the core is a literal in this test file and nowhere else
    assert V.anchored_rate(0.070, 0.025) == pytest.approx(V.HURDLE_RATE)


def test_e29_anchor_reconciles_and_refuses_a_premium_outside_the_band():
    assert V.anchored_rate(0.070, 0.025) == pytest.approx(0.095)
    for premium in (0.019, 0.031, 0.05):
        with pytest.raises(V.ValuationError, match="premium"):
            V.anchored_rate(0.070, premium)
    # the band's own ends are inside it
    assert V.anchored_rate(0.070, V.HURDLE_PREMIUM_MIN) == pytest.approx(0.09)
    assert V.anchored_rate(0.070, V.HURDLE_PREMIUM_MAX) == pytest.approx(0.10)


# --- E29: fragility is displayed, never adjudicated ------------------------


def test_e29_there_is_no_scalar_mbp_function():
    """The rule cannot be followed by accident.

    E29 requires every MBP to be reported with r-0.5% and r+0.5% beside it.
    The module enforces that structurally: the only way to obtain an MBP is
    as a Sensitivity, so a caller cannot print a bare threshold without
    reaching into the triple and saying so.
    """
    mbp = V.maximum_buy_price(g_base=0.0, tier=1, **DECK)
    assert isinstance(mbp, V.Sensitivity)
    assert not isinstance(mbp, float)
    scalar_returning = [n for n in dir(V)
                        if "mbp" in n.lower() or "buy_price" in n.lower()]
    assert scalar_returning == ["maximum_buy_price"]


def test_e29_mbp_triple_matches_the_deck_run():
    """E90 (2026-08-30): the cushion is 0.85 on the BASE-case value; the
    pre-E90 triple (89.30 / 95.14 / 84.23 at 0.80 on the bear) is history
    in the 2026-08-25 hand-run record."""
    mbp = V.maximum_buy_price(g_base=0.0, tier=1, **DECK)
    assert mbp.mid == pytest.approx(94.88, abs=0.005)
    assert mbp.low == pytest.approx(101.09, abs=0.005)    # r = 9.0%
    assert mbp.high == pytest.approx(89.49, abs=0.005)    # r = 10.0%
    assert mbp.spread == pytest.approx(11.60, abs=0.005)


def test_e29_fragility_is_reported_not_acted_on():
    """DECK on 2026-08-25 is the case the vetoed rule would have struck.

    Under E90's cushions (2026-08-30) it is TIER 2's MBP that reverses
    around the price inside the band; tiers 1 and 3 do not. E29 refused
    the veto -- so the engine still RETURNS the tier 2 MBP, and only says
    that the comparison is fragile.
    """
    t2 = V.maximum_buy_price(g_base=0.0, tier=2, **DECK)
    assert t2.reverses_around(DECK_PRICE) is True
    assert t2.mid == pytest.approx(83.72, abs=0.005)   # returned, not withheld

    for tier in (1, 3):
        assert V.maximum_buy_price(g_base=0.0, tier=tier,
                                   **DECK).reverses_around(DECK_PRICE) is False


def test_e29_no_code_path_withholds_a_verdict_on_fragility():
    """The refusal of the veto, pinned.

    If a future change makes any function raise or return None because a
    figure moves inside the band, this fails -- which is the point. E29's
    grounds: a rule whose only possible output is NO, added to a framework
    that has never said yes, is a serious thing to do.
    """
    fragile = V.maximum_buy_price(g_base=0.0, tier=2, **DECK)
    assert fragile.reverses_around(DECK_PRICE)
    assert all(v > 0 for v in (fragile.low, fragile.mid, fragile.high))


# --- refusals --------------------------------------------------------------


def test_no_tier_means_no_mbp_rather_than_a_default_cushion():
    """B22 is open; a name with no tier has a fair value and NO MBP."""
    with pytest.raises(V.ValuationError, match="legitimate state"):
        V.maximum_buy_price(g_base=0.0, tier=None, **DECK)
    assert V.fair_value(growth=0.0, **DECK).mid == pytest.approx(111.62, abs=0.005)


@pytest.mark.parametrize("kwargs,match", [
    (dict(shares=0.0), "STATED"),
    (dict(shares=None), "STATED"),
    (dict(fcf0=None), "DATA MISSING"),
    (dict(net_cash=None), "DATA MISSING"),
])
def test_missing_or_unstated_inputs_refuse(kwargs, match):
    args = {**DECK, "growth": 0.0, **kwargs}
    with pytest.raises(V.ValuationError, match=match):
        V.equity_value_per_share(**args)


def test_a_rate_at_or_below_terminal_growth_refuses():
    with pytest.raises(V.ValuationError, match="terminal"):
        V.equity_value_per_share(growth=0.0, rate=0.025, **DECK)


def test_a_price_above_the_value_at_g_equals_r_still_solves():
    """The cap at r was a perpetuity's property, and this is not a perpetuity.

    DELETED with this test: `test_growth_at_or_above_the_hurdle_does_not_
    converge_and_says_so`, which pinned the message "the model does not
    converge" for any price above the value at g = r. REVIEW-4 report C 9.3
    #1 (and its flip F6) shows the claim is false as mathematics -- with a
    ten-year explicit horizon and a terminal rate fixed below r the value is
    finite and strictly increasing in g -- and shows it refusing SOLVABLE
    prices on two names the owner holds or has struck:

      SAP.DE at 188.12 (its 2026-08-21 close, on its own workbook inputs)
      returned nothing while `sap-valuation.xlsx` C Sensitivity B13 solved
      9.60% by hand; NKE's watchlist note carries 10.67% struck outside the
      tool. Both come out of the engine now, to four decimal places.
    """
    g = V.implied_growth(price=188.12, fcf0=8730.0, net_cash=1118.0, shares=1158.0)
    assert g == pytest.approx(0.095988, abs=5e-6)
    g = V.implied_growth(price=39.41, fcf0=2184.0, net_cash=-379.0, shares=1481.0)
    assert g == pytest.approx(0.106731, abs=5e-6)


def test_a_price_beyond_the_sanity_bound_refuses_as_an_INPUT_fault():
    """The refusal that replaces it says the inputs are wrong, not the model."""
    with pytest.raises(V.ValuationError, match="implies growth above"):
        V.implied_growth(price=1e18, **DECK)


def test_sensitivity_low_is_the_larger_value():
    """A lower hurdle discounts the same cash flows less. Stated so nobody
    reads `low` as `the low fair value`."""
    fv = V.fair_value(growth=0.0, **DECK)
    assert fv.low > fv.mid > fv.high


# --- E34: the invariant the ruling creates --------------------------------


def test_the_two_classifications_give_THE_SAME_equity_value():
    """THE WHOLE OF E34, as one equality.

    One company, two cash-flow presentations of the same facts. IAS 7.31-34
    lets a filer put interest paid in operating or in financing; ASC 230
    puts it in operating always. Under E34 both reach the same equity value,
    because both reduce to `EV(pre-interest flow) - net debt`:

      interest in FINANCING  -> OCF is already pre-interest; FCF0 = OCF - capex
      interest in OPERATING  -> OCF bears the interest; FCF0 = OCF - capex
                                + the interest, added back

    NET DEBT IS SUBTRACTED ONCE IN BOTH CASES. The ruling deliberately does
    NOT go to an FCFE reading (drop the net-debt step, keep the interest
    charged): that answers a different question and gives a different number
    -- 161.03 against 131.89 on LIAB.ST -- and mixing the two is the defect.
    """
    net_debt, shares, growth = -2000.0, 100.0, 0.03
    capex, interest = -100.0, 50.0
    financing = V.free_cash_flow_zero(
        nci_dividends_paid=0.0,
        operating_cash_flow=1000.0, capex=capex, interest_in_ocf=False, sbc=0.0)
    operating = V.free_cash_flow_zero(
        nci_dividends_paid=0.0,
        operating_cash_flow=1000.0 - interest, capex=capex,
        interest_in_ocf=True, net_interest_paid=interest, sbc=0.0)
    assert financing == operating == 900.0
    both = [V.equity_value_per_share(fcf0=f, growth=growth, net_cash=net_debt,
                                     shares=shares)
            for f in (financing, operating)]
    assert both[0] == both[1] == pytest.approx(116.74257, abs=1e-5)

    # THE DEFECT, for the size: the same filer with no add-back.
    defect = V.equity_value_per_share(
        fcf0=(1000.0 - interest) + capex, growth=growth,
        net_cash=net_debt, shares=shares)
    assert defect == pytest.approx(109.1458, abs=1e-4)


def test_FCF0_refuses_rather_than_guessing_the_classification():
    with pytest.raises(V.ValuationError, match="interest_in_ocf is DATA MISSING"):
        V.free_cash_flow_zero(operating_cash_flow=1000.0, capex=-100.0,
                              interest_in_ocf=None, sbc=0.0)
    with pytest.raises(V.ValuationError, match="net_interest_paid is DATA MISSING"):
        V.free_cash_flow_zero(operating_cash_flow=1000.0, capex=-100.0,
                              interest_in_ocf=True, sbc=0.0)


def test_E34_on_the_held_name_and_the_bias_the_ruling_accepts():
    """LIAB.ST: interest paid 211, received 10, both INSIDE operating cash
    flow (Lindab Q2 2026 interim p.17), then 4,497 of net debt subtracted."""
    liab = dict(growth=0.02, net_cash=-4497.0, shares=77.036)
    as_struck = V.equity_value_per_share(fcf0=879.0, **liab)
    under_e34 = V.equity_value_per_share(fcf0=879.0 + 201.0, **liab)
    after_tax = V.equity_value_per_share(fcf0=879.0 + 201.0 * (1 - 0.206), **liab)
    assert as_struck == pytest.approx(102.66, abs=0.005)
    assert under_e34 == pytest.approx(139.48, abs=0.005)
    # the bias E34 states rather than removes: the add-back is PRE-TAX
    assert after_tax == pytest.approx(131.89, abs=0.005)
    assert under_e34 - after_tax == pytest.approx(7.59, abs=0.005)


# --- E36: share-based compensation is a cost ------------------------------


def test_sbc_is_subtracted_and_the_sign_it_is_entered_in_does_not_matter():
    """The schema holds a magnitude; FCF0 subtracts it either way."""
    # E105: the newest leg is stated at zero so this test stays about SBC.
    kw = dict(operating_cash_flow=1000.0, capex=-100.0, interest_in_ocf=False,
              nci_dividends_paid=0.0)
    assert V.free_cash_flow_zero(sbc=20.0, **kw) == 880.0
    assert V.free_cash_flow_zero(sbc=-20.0, **kw) == 880.0
    assert V.free_cash_flow_zero(sbc=0.0, **kw) == 900.0


def test_absent_sbc_is_DATA_MISSING_and_never_zero():
    """A filer that grants no stock STATES zero; absent is not that."""
    with pytest.raises(V.ValuationError, match="share-based compensation is DATA MISSING"):
        V.free_cash_flow_zero(operating_cash_flow=1000.0, capex=-100.0,
                              interest_in_ocf=False)


def test_E36_on_DECK_both_pairings_with_the_pairing_NAMED():
    """The spec's "3.8-4.2% below" is the HAND-RUN pairing, not the store's.

    44.835m is the FY2026 charge and belongs with the FY2026 store basis,
    where it is -3.68%. 46.837m is the TTM charge to 2026-06-30 and belongs
    with the hand run, where it is -3.84%. Pairing an FY charge with a TTM
    flow is the same mismatch E38 removes from the share count, so both are
    pinned with their own window.
    """
    store = dict(growth=0.035, net_cash=1907.249, shares=145.805)
    hand = dict(growth=0.035, net_cash=1602.589, shares=136.414227)

    before = V.equity_value_per_share(fcf0=1097.332, **store)
    after = V.equity_value_per_share(fcf0=1097.332 - 44.835, **store)
    assert (round(before, 2), round(after, 2)) == (131.74, 126.89)
    assert (after - before) / before == pytest.approx(-0.03680, abs=5e-5)

    before = V.equity_value_per_share(fcf0=1117.9, **hand)
    after = V.equity_value_per_share(fcf0=1117.9 - 46.837, **hand)
    assert (round(before, 2), round(after, 2)) == (140.95, 135.54)
    assert (after - before) / before == pytest.approx(-0.03841, abs=5e-5)


def test_E36_flips_the_only_below_MBP_reading_the_engine_has_produced():
    """REVIEW-4 report A 3.2. The bear case (g 0) with the tier-1 cushion.

    88.55 was 0.8% BELOW the MBP and is 3.0% above it once the stock DECK
    pays its staff is a cost. Not a verdict change -- DECK is WATCH-GATED --
    but it is the one threshold comparison the engine has ever produced.
    """
    hand = dict(growth=0.0, net_cash=1602.589, shares=136.414227)
    bear_before = V.equity_value_per_share(fcf0=1117.9, **hand)
    bear_after = V.equity_value_per_share(fcf0=1117.9 - 46.837, **hand)
    assert (round(bear_before, 2), round(bear_after, 2)) == (111.62, 107.44)
    mbp_before, mbp_after = bear_before * 0.80, bear_after * 0.80
    assert (round(mbp_before, 2), round(mbp_after, 2)) == (89.30, 85.95)
    assert 88.55 < mbp_before and 88.55 > mbp_after
    assert 88.74 < mbp_before and 88.74 > mbp_after      # the settled close too


def test_the_cash_settled_half_is_already_borne_and_must_not_be_deducted():
    """SAP FY2025: 1,695 total, 1,331 equity-settled, 364 cash-settled.

    A cash-settled award flows through operating cash flow as CASH when it
    is paid, so FCF0 already bears it.
    """
    sap = dict(growth=0.08, net_cash=1118.0, shares=1158.0)
    assert V.equity_value_per_share(fcf0=8730.0, **sap) == pytest.approx(167.07, abs=0.005)
    assert V.equity_value_per_share(fcf0=8730.0 - 1331.0, **sap) == pytest.approx(141.74, abs=0.005)
    assert V.equity_value_per_share(fcf0=8730.0 - 1695.0, **sap) == pytest.approx(134.82, abs=0.005)


# --- E70 (2026-08-30): a lease is counted once, in net debt, never also in the flow


def test_E70_a_us_filers_operating_lease_payment_is_added_back_and_an_ifrs_filers_is_not():
    kw = dict(operating_cash_flow=1000.0, capex=-100.0, interest_in_ocf=False,
              sbc=0.0, nci_dividends_paid=0.0)   # E105 at zero: this is E70's test
    ifrs = V.free_cash_flow_zero(operating_leases_in_ocf=False, **kw)
    us = V.free_cash_flow_zero(operating_leases_in_ocf=True, operating_lease_payments=90.6, **kw)
    assert ifrs == 900.0 and us == pytest.approx(990.6)
    # not declared adds nothing here; the record is what refuses (dated)
    assert V.free_cash_flow_zero(**kw) == 900.0
    # a positive magnitude either way
    assert V.free_cash_flow_zero(operating_leases_in_ocf=True, operating_lease_payments=-90.6, **kw) == pytest.approx(990.6)


def test_E70_yes_without_the_stated_payment_is_DATA_MISSING():
    with pytest.raises(V.ValuationError, match="operating_lease_payments is DATA MISSING"):
        V.free_cash_flow_zero(operating_cash_flow=1000.0, capex=-100.0, interest_in_ocf=False,
                              sbc=0.0, operating_leases_in_ocf=True)
