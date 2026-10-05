"""FRAMEWORK section 5 arithmetic: the reverse DCF engine (E28) and the
hurdle rate (E29).

WHAT THIS IS. E28 made Method C the engine: a reverse DCF on filed TTM free
cash flow, net debt and a STATED share count produces the fair value on its
own. Methods A and B are context shown beside it and are never averaged in.
This module is that arithmetic and nothing else -- it reads no files, fetches
nothing and decides nothing.

THE RATE IS A PREFERENCE, NOT A MEASUREMENT (E29). ``r`` is the OWNER'S
HURDLE RATE -- what he requires to move capital out of the index core -- and
NOT an estimate of what the market demands. Three consequences, all of them
deliberate and all of them recorded in FRAMEWORK-EDITS E29:

  FLAT.      It does not vary by market, sector, currency or capital
             structure, because it is a statement about the owner and not
             about a company. This knowingly accepts an asymmetry: a flat
             nominal rate demands roughly 180bp more of a Swedish issuer
             than a US one, because Sweden's government borrows more
             cheaply. The alternative was a second owner-set lever per name
             at the moment E28 made g the single one -- and g is
             pre-registered and auditable where r would not be.
  ANCHORED.  r = the long-run expected return of the index core plus 2-3
             percentage points. Today that is 9.5%. The anchor is what gives
             it a condition for changing: if the core's expected return
             moves materially, r moves with it.
  ASYMMETRIC IN TIME. The rate that strikes a PURCHASE is frozen with that
             verdict, as E24 froze FX. An EXIT under C4 is re-struck at
             today's rate, because C4's own reasoning is that a level set
             months earlier states where the thesis was rather than what the
             capital can earn next.

FRAGILITY IS DISPLAYED, NEVER ADJUDICATED (E29). The proposed +/-0.5% veto --
"a decision that reverses inside the band is not a decision" -- was REFUSED:
it can only ever remove a conclusion, never produce one, and this framework's
diagnosed defect is that it cannot say yes. Instead every MBP is reported
with its value at r-0.5% and r+0.5% beside it.

  ** THERE IS NO SCALAR MBP FUNCTION IN THIS MODULE, AND THAT IS ON PURPOSE. **

``maximum_buy_price`` returns a Sensitivity triple. A caller that wants a bare
number has to reach into it and say so, which is the difference between
displaying fragility and hiding it.
"""

from __future__ import annotations

from dataclasses import dataclass

#: The standing hurdle rate (E29). NOT a market estimate -- see the module
#: docstring. Changes only when the index core's expected return moves.
HURDLE_RATE = 0.095

#: The band E29 requires every MBP to be reported across. It is a DISPLAY
#: width, not a veto: nothing in this module refuses a verdict because it
#: moves inside the band.
HURDLE_SENSITIVITY = 0.005

#: E29's anchor: r = core expected return + a premium in this range, the
#: premium being what the owner requires for carrying single-company risk.
HURDLE_PREMIUM_MIN = 0.02
HURDLE_PREMIUM_MAX = 0.03

#: FRAMEWORK section 5.3. Unchanged by E28 -- what changed is what the cushion
#: is applied TO (the bear-case price, not a weighted point estimate).
TIER_MULTIPLIER = {1: 0.80, 2: 0.70, 3: 0.60}
#: E90 (2026-08-30): the live cushions, applied to the BASE-case value.
TIER_CUSHION_E90 = {1: 0.85, 2: 0.75, 3: 0.65}

#: E37. The currency the flat rate is least wrong in. NOT a claim that the
#: rate is a US rate -- the index core is Avanza Zero (OMXS30, SEK) plus
#: Avanza USA (USD) -- but the anchor E29's asymmetry is measured against.
RATE_REFERENCE_CURRENCY = "USD"

#: E37's declaration, printed BESIDE EVERY NON-USD FAIR VALUE.
#:
#: E29 accepted the currency asymmetry knowingly and did not record its
#: SIZE. A single nominal 9.5% is a HIGHER REAL hurdle for a low-inflation,
#: low-risk-free currency, so it UNDERSTATES every non-USD name relative to
#: a currency-matched rate -- by a known, one-directional amount. Measured
#: on 2026-08-25 against the sovereign gap (US 10y 4.66%, Bund ~3.2%,
#: Sweden ~2.90%): SAP.DE's Method C 167.07 -> 215.17 at 8.04%, +40.9 on
#: `fv_base`; LIAB.ST 102.66 -> 156.21 at 7.74%, +53.5. Those are the two
#: largest per-share effects REVIEW-4 found on either held name, and they
#: are the effect of a RULING rather than of a defect.
#:
#: A bias nobody has measured is indistinguishable from a bias nobody has.
#: This line is the whole of E37.
NON_USD_BIAS_DECLARATION = "r 9.5% flat; non-USD bias: conservative"


def rate_declaration(currency: str | None) -> str:
    """E37's sentence for one currency: the declaration, or the plain rate."""
    if currency and currency.strip().upper() != RATE_REFERENCE_CURRENCY:
        return NON_USD_BIAS_DECLARATION
    return f"r {HURDLE_RATE:.1%} flat"


#: FRAMEWORK section 5.1 Method C, unchanged by E28 and E29.
TERMINAL_GROWTH = 0.025
DCF_YEARS = 10

#: The widest growth `implied_growth` will bracket. NOT a model limit -- the
#: ten-year DCF converges at any g -- but a sanity bound: a price implying
#: more than this is an input fault (a share count out by a thousand, a
#: currency unconverted), and saying so is more use than a number.
SOLVER_MAX_GROWTH = 10.0


class ValuationError(Exception):
    """Raised when an input cannot support the arithmetic at all."""


def _require_nci(nci_dividends_paid: float | None) -> float:
    """E105's leg, or the refusal. A helper so the check can be ORDERED.

    NEGATIVE as the statement prints it and summed like capex, so a figure
    entered with the wrong sign RAISES FCF0 -- and is then caught by E101's
    check against the issuer's own free cash flow rather than by nothing.
    """
    if nci_dividends_paid is None:
        raise ValuationError(
            "dividends paid to non-controlling interests are DATA MISSING "
            "(E105): that cash LEAVES THE GROUP and can never reach the "
            "owner, so FCF0 deducts it. Both this construction and the "
            "issuer's agree it is gone -- E101 found the leg standing in "
            "Imperial Brands' own build and absent from ours at GBP 156m, "
            "4.9% of FCF0. A group with NO minorities states a NAMED ZERO "
            "on E25's note or caption basis; absent is not zero, because a "
            "coerced zero reports the record complete while overstating the "
            "flow by the whole of a group's distributions")
    return abs(float(nci_dividends_paid))


def free_cash_flow_zero(*, operating_cash_flow: float | None,
                        capex: float | None,
                        interest_in_ocf: bool | None,
                        net_interest_paid: float | None = None,
                        sbc: float | None = None,
                        operating_leases_in_ocf: bool | None = None,
                        operating_lease_payments: float | None = None,
                        nci_dividends_paid: float | None = None,
                        lease_rule: str = "E70",
                        lease_cash_paid: float | None = None) -> float:
    """FCF0 under E34, E36 and E70 / E117. THE ONE PLACE THIS SUM IS FORMED.

    E117 (2026-09-19), ``lease_rule="E117"``: RENT IS AN OPERATING COST. A
    US GAAP filer's flow already bears its operating lease payments, so
    NOTHING is added back (E70's add-back reversed). An IFRS 16 filer's
    ``lease_cash_paid`` -- principal AND lease interest, a positive
    magnitude -- is DEDUCTED, whatever its interest classification; None is
    DATA MISSING. The operating lease liability has left net debt, so the
    lease is still counted once. ``lease_rule="E70"`` is how every record
    struck before 2026-09-19 replays, and is documented below.

    E70, in one line: A LEASE IS COUNTED ONCE, IN NET DEBT, NEVER ALSO IN
    THE FLOW. Where the filer's operating cash flow already bears its
    operating lease payments (ASC 842-20-45-5(a): a US GAAP filer), the
    stated cash paid for operating leases is ADDED BACK -- principal under
    E70, and the interest component inside the single lease payment under
    the filer's own interest rule (ASC 230 puts it in operating cash flow,
    E34 adds it back). An IFRS 16 filer's flow never bore the principal
    (IFRS 16.50(b), financing), so nothing is added back. ``None`` on
    ``operating_leases_in_ocf`` means NOT DECLARED and adds nothing here;
    the run record is what refuses an undeclared lease treatment (E70's
    declaration, dated). ``True`` with no payment figure is DATA MISSING.
    This RAISES FCF0 for every lease-heavy US filer: the removal of a
    double charge, not a loosening.

    ``capex`` is an OUTFLOW, negative, because that is the sign this
    project's schema states it in and section 5 SUMS the capex legs into
    operating cash flow. ``net_interest_paid`` is a MAGNITUDE, positive,
    the way the schema holds finance costs.

    E105 (2026-09-04): ``nci_dividends_paid`` is the cash the group paid to
    its NON-CONTROLLING INTERESTS over the window, entered NEGATIVE as the
    statement prints it, and SUMMED in like capex. That cash left the group
    and can never reach the owner; both this construction and the issuer's
    agree it is gone, and until E105 only the issuer's counted it. It is a
    LEG and not a bridge item -- E105 declined valuing the minority as a
    liability, because that is a second unaudited lever beside the
    pre-registered growth view (E29's ground). ``None`` is DATA MISSING and
    the record refuses; a group with no minorities states a NAMED ZERO.

    E34, in three lines:

      interest_in_ocf is None -> DATA MISSING. A file that does not say
        where its filer books interest cannot produce a fair value, because
        the same arithmetic means two different things depending on the
        answer.
      interest_in_ocf is True  -> the operating cash flow ALREADY BEARS the
        interest, so it is ADDED BACK, as printed and PRE-TAX. FCF0 is then
        a flow to the FIRM and the net-debt step below it is correct.
      interest_in_ocf is False -> the operating cash flow is already
        pre-interest and nothing is added.

    IN BOTH CASES NET DEBT IS SUBTRACTED ONCE, AFTER DISCOUNTING, by
    `equity_value_per_share`. There is no FCFE path and this function does
    not open one: what was wrong was never the bridge, it was the flow
    handed across it.

    E36, in one line: ``sbc`` is SUBTRACTED, as a positive magnitude, for
    the same window as the flows. An equity-settled award is a non-cash
    charge added back inside operating cash flow under both ASC 230 and
    IAS 7, so ``operating_cash_flow - capex`` contains it -- and a charge
    paid in the same currency as the thing being valued is not free.
    ABSENT IS DATA MISSING, not zero: a filer that grants no stock states
    zero, and this schema has E25 for exactly that difference.

    E34.1, the US sub-case: where the filer states interest paid but no
    interest received as cash, ``net_interest_paid`` is the INCOME
    STATEMENT'S net -- an accrual proxy -- and it is SIGNED: a net interest
    INCOME arrives negative and is removed from the flow, because interest
    earned on a cash pile is not the firm's operating flow either. Nike
    FY2026: -50m, not +323m.

    THE PRE-TAX ADD-BACK IS GENEROUS AND E34 SAYS SO. Interest is
    deductible, so the after-tax cost to equity is lower than the printed
    figure. On LIAB.ST at Sweden's 20.6% that is 139.48 against 131.89 --
    this ruling's own answer is +7.59 a share above the after-tax one. An
    effective tax rate is a second estimated lever per name and is not
    printed on a cash flow statement; a figure the accounts state beats a
    figure the reader computes.
    """
    if operating_cash_flow is None:
        raise ValuationError("operating cash flow is DATA MISSING")
    if capex is None:
        raise ValuationError("capex is DATA MISSING")
    if interest_in_ocf is None:
        raise ValuationError(
            "interest_in_ocf is DATA MISSING (E34): the file does not say "
            "whether this filer's operating cash flow already bears its "
            "interest. IAS 7.31-34 allows either and ASC 230 allows only "
            "the first, so the same OCF - capex is a flow to the firm for "
            "one filer and a flow to equity for the next -- and net debt is "
            "subtracted from it either way. Read the cash flow statement "
            "and record `interest_in_ocf` with its page")
    if sbc is None:
        raise ValuationError(
            "share-based compensation is DATA MISSING (E36): it is a COST "
            "and FCF0 subtracts it. It arrives added back inside operating "
            "cash flow as a non-cash charge, so leaving it out is not "
            "neutral -- it treats stock paid to employees as free. A filer "
            "that grants none states zero; absent is not zero")
    # E105's refusal is asked LAST, after every older leg's. A new leg that
    # preempted them would rewrite the message on every existing DATA
    # MISSING path -- the same figure refused, for a reason that arrived
    # months later and is not the one the reader is chasing.
    base = float(operating_cash_flow) + float(capex) - abs(float(sbc))
    if lease_rule == "E117":
        if operating_leases_in_ocf is False:
            if lease_cash_paid is None:
                raise ValuationError(
                    "the lease cash outflow is DATA MISSING and "
                    "`operating_leases_in_ocf: no` (E117): rent is an "
                    "operating cost, and an IFRS 16 filer's principal and "
                    "lease interest are deducted from the flow -- without "
                    "both there is no rent-bearing FCF0, and none is "
                    "printed as an upper bound")
            base -= abs(float(lease_cash_paid))
    elif operating_leases_in_ocf:
        if operating_lease_payments is None:
            raise ValuationError(
                "operating_lease_payments is DATA MISSING and "
                "`operating_leases_in_ocf: yes` (E70): the operating cash "
                "flow bears the operating lease payments that the lease "
                "liability in net debt already charges, and the stated cash "
                "paid for operating leases is not on the file")
        base += abs(float(operating_lease_payments))
    if not interest_in_ocf:
        return base - _require_nci(nci_dividends_paid)
    if net_interest_paid is None:
        raise ValuationError(
            "net_interest_paid is DATA MISSING and `interest_in_ocf: yes` "
            "(E34): the operating cash flow bears interest that has to be "
            "added back, and the amount is not on the file")
    return base + float(net_interest_paid) - _require_nci(nci_dividends_paid)


@dataclass(frozen=True)
class Sensitivity:
    """One figure at three rates. E29 forbids reporting the middle alone.

    ``low`` is struck at r - 0.5%, ``mid`` at r, ``high`` at r + 0.5%. Note
    that for a fair value ``low`` is the LARGER number: a lower hurdle
    discounts the same cash flows less.
    """

    low: float
    mid: float
    high: float
    rate: float
    delta: float

    @property
    def spread(self) -> float:
        """How far the figure travels across the band, always positive."""
        return abs(self.low - self.high)

    def reverses_around(self, price: float) -> bool:
        """True if ``price`` sits on different sides of the band's ends.

        REPORTED, NEVER ACTED ON. E29 refused the veto this would have
        implemented; the framework shows the owner that a comparison is
        fragile and he judges it. Nothing in vss may branch on this to
        withhold a verdict.
        """
        below = [price <= v for v in (self.low, self.mid, self.high)]
        return any(below) and not all(below)

    def __str__(self) -> str:
        return (f"{self.mid:.2f} "
                f"(r{self.rate - self.delta:.3%} {self.low:.2f} / "
                f"r{self.rate + self.delta:.3%} {self.high:.2f})")


def _check(fcf0: float, net_cash: float, shares: float, rate: float) -> None:
    if shares is None or shares <= 0:
        raise ValuationError(
            "share count must be positive and STATED (E22): a count derived "
            "from share capital over par value is not a count")
    if fcf0 is None:
        raise ValuationError("free cash flow is DATA MISSING")
    if rate <= TERMINAL_GROWTH:
        raise ValuationError(
            f"hurdle rate {rate:.3%} must exceed the terminal growth rate "
            f"{TERMINAL_GROWTH:.3%}; the terminal value is undefined otherwise")
    if net_cash is None:
        raise ValuationError("net cash / net debt is DATA MISSING")


def equity_value_per_share(*, fcf0: float, growth: float, net_cash: float,
                           shares: float, rate: float = HURDLE_RATE,
                           terminal: float = TERMINAL_GROWTH,
                           years: int = DCF_YEARS) -> float:
    """Fair value per share at a given growth rate.

    ``fcf0`` is the TWELVE-MONTH free cash flow at the basis (E19); ``net_cash``
    is positive for a net-cash company and negative for a net-debt one, taken
    at that window's end. Nothing here is annualised or scaled -- a figure of
    the wrong length is DATA MISSING, never a figure adjusted to fit.
    """
    _check(fcf0, net_cash, shares, rate)
    if growth <= -1.0:
        raise ValuationError(f"growth rate {growth:.3%} is not a rate")
    pv = sum(fcf0 * (1 + growth) ** t / (1 + rate) ** t
             for t in range(1, years + 1))
    terminal_value = fcf0 * (1 + growth) ** years * (1 + terminal) / (rate - terminal)
    enterprise = pv + terminal_value / (1 + rate) ** years
    return (enterprise + net_cash) / shares


def implied_growth(*, price: float, fcf0: float, net_cash: float, shares: float,
                   rate: float = HURDLE_RATE, terminal: float = TERMINAL_GROWTH,
                   years: int = DCF_YEARS) -> float:
    """The growth rate the current price implies -- E28's g*.

    E28: a growth view written AFTER this has been seen is VOID. This function
    cannot enforce that; the pre-registration lives in
    ``reference/growth-views/<TICKER>.md`` and its dating is the record.
    """
    _check(fcf0, net_cash, shares, rate)
    if price <= 0:
        raise ValuationError(f"price must be positive, got {price}")

    def gap(g: float) -> float:
        return equity_value_per_share(
            fcf0=fcf0, growth=g, net_cash=net_cash, shares=shares,
            rate=rate, terminal=terminal, years=years) - price

    lo = -0.90
    if gap(lo) > 0:
        raise ValuationError(
            f"price {price:.2f} is below the value of a company shrinking 90% "
            f"a year; the inputs, not the market, are wrong")
    # THE BRACKET IS WIDENED, NOT CAPPED AT r. The old upper bound was
    # `rate - 1e-9` with the note "growth at or above the hurdle diverges".
    # That is a PERPETUITY's property and this is not a perpetuity: with a
    # ten-year explicit horizon and a terminal rate fixed BELOW r, the value
    # is finite and strictly increasing in g for every g, so every price
    # above the g=0 value has an answer. The cap refused solvable prices on
    # held names -- SAP.DE at its own workbook inputs and 2026-08-21 close
    # returned nothing while the workbook solved 9.60% by hand (REVIEW-4
    # report C 9.3 #1, F6). Only a price beyond SOLVER_MAX_GROWTH refuses,
    # and it refuses as an INPUT fault rather than as a model limit.
    hi = max(2 * rate, 0.20)
    while gap(hi) < 0:
        hi *= 2
        if hi > SOLVER_MAX_GROWTH:
            raise ValuationError(
                f"price {price:.2f} implies growth above "
                f"{SOLVER_MAX_GROWTH:.0%} a year; the inputs, not the market, "
                f"are wrong")
    for _ in range(200):
        mid = (lo + hi) / 2
        if gap(mid) < 0:
            lo = mid
        else:
            hi = mid
    return (lo + hi) / 2


def fair_value(*, fcf0: float, growth: float, net_cash: float, shares: float,
               rate: float = HURDLE_RATE, delta: float = HURDLE_SENSITIVITY,
               terminal: float = TERMINAL_GROWTH,
               years: int = DCF_YEARS) -> Sensitivity:
    """Fair value at one growth rate, across E29's band."""
    def at(r: float) -> float:
        return equity_value_per_share(
            fcf0=fcf0, growth=growth, net_cash=net_cash, shares=shares,
            rate=r, terminal=terminal, years=years)
    return Sensitivity(low=at(rate - delta), mid=at(rate), high=at(rate + delta),
                       rate=rate, delta=delta)


def maximum_buy_price(*, fcf0: float, g_base: float, net_cash: float,
                      shares: float, tier: int | None,
                      rate: float = HURDLE_RATE,
                      delta: float = HURDLE_SENSITIVITY,
                      terminal: float = TERMINAL_GROWTH,
                      years: int = DCF_YEARS) -> Sensitivity:
    """E90's MBP, across E29's band. THERE IS NO SCALAR FORM OF THIS.

    MBP is the BASE-case value x the tier cushion (E90, 2026-08-30: tier 1
    0.85 / tier 2 0.75 / tier 3 0.65). The cushion covers MODEL AND INPUT
    ERROR, not scenario risk -- the pre-registered growth views carry
    that, and the bear and bull values stay printed as information.
    ``g_base`` must come from ``reference/growth-views/<TICKER>.md``.
    Supersedes E28's bear-value form; the dated strike tools that called
    this with ``g_bear`` are records of their day and are not re-run.

    A name with no tier has a fair value and NO MBP -- a legitimate state, and
    whether a gate-failed name may carry a tier at all is B22, open. So
    ``tier=None`` raises rather than defaulting to a cushion nobody chose.
    """
    if tier not in TIER_CUSHION_E90:
        raise ValuationError(
            f"tier must be one of {sorted(TIER_CUSHION_E90)}, got {tier!r}. A "
            f"name with no tier has a fair value and NO MBP, which is a "
            f"legitimate state -- do not supply a tier to obtain one")
    cushion = TIER_CUSHION_E90[tier]
    fv = fair_value(fcf0=fcf0, growth=g_base, net_cash=net_cash, shares=shares,
                    rate=rate, delta=delta, terminal=terminal, years=years)
    return Sensitivity(low=fv.low * cushion, mid=fv.mid * cushion,
                       high=fv.high * cushion, rate=fv.rate, delta=fv.delta)


def anchored_rate(core_expected_return: float, premium: float) -> float:
    """E29's anchor: r = the index core's expected return + 2-3 points.

    Refuses a premium outside the stated band. The band is the owner's, not a
    finding, and it is the whole of what makes r anchored rather than invented.
    """
    if not HURDLE_PREMIUM_MIN - 1e-12 <= premium <= HURDLE_PREMIUM_MAX + 1e-12:
        raise ValuationError(
            f"E29 sets the single-company premium at "
            f"{HURDLE_PREMIUM_MIN:.1%}-{HURDLE_PREMIUM_MAX:.1%}, got "
            f"{premium:.3%}. Moving it is a change to the ruling, not an input")
    return core_expected_return + premium
