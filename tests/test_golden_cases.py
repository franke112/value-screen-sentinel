"""The seventeen golden cases REVIEW-4 report C Part 10 proposed.

**WHAT A GOLDEN CASE IS HERE.** Report C's own labelling rule, and it is the
first thing on this page for the same reason it was the first thing on that
one: THESE PIN ARITHMETIC GIVEN STATED ASSUMPTIONS. Not one of them is a
known-correct fair value. Every case carries its EIGHT DECLARATIONS AS DATA
-- `Case.declarations` below -- so that when a ruling moves a value the
failure names the choice that moved rather than the company.

    "A case whose declaration changes fails loudly by design: the
     declarations are the test."                     -- report C, Part 10

**THE THREE THAT CANNOT BE BUILT YET** are `skip`ped with the ruling named,
exactly as the build asked. Report C listed three; ONE OF THEM IS NOW RULED
-- C3, the staleness gate, decided by the owner on 2026-08-26 -- so G16 is a
live test rather than a skipped one, and that is stated on it.

**VALUES THAT MOVED.** E34 to E38 changed several of these. Where a case has
a figure report C or report A recorded, BOTH are here: the old value, the
new value, and the ruling that moved it. A golden case that silently adopted
the new number would be the "known-correct" label all over again.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, datetime
from pathlib import Path
from zoneinfo import ZoneInfo

import pytest

from vss import manual as M
from vss import metrics as MT
from vss import rules as RU
from vss import runrecord as R
from vss import valuation as V
from tests._vendor_data import need

AS_OF = date(2026, 8, 26)
RUN_TS = datetime(2026, 8, 26, 22, 30, tzinfo=ZoneInfo("Europe/Stockholm"))


@dataclass(frozen=True)
class Case:
    """One golden case, and the eight declarations it stands on AS DATA."""

    name: str
    source: str                       # the filing or the report it comes from
    catches: str                      # what a failure here would mean
    declarations: dict = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.name or not self.source or not self.catches:
            raise AssertionError(f"{self.name}: a case states what it is")


#: THE EIGHT, by number, so a case that omits one is visible at a glance.
DECLARATIONS = ("share_count", "sbc", "interest", "bridge", "conventions",
                "rate_and_growth", "as_of_dates", "provenance")


def declared(case: Case) -> None:
    """Every case in group A and B states all eight. Guards drift."""
    missing = [d for d in DECLARATIONS if d not in case.declarations]
    assert not missing, f"{case.name} declares nothing about {missing}"


AS_CODED = dict(horizon_years=10, terminal="2.5%", discounting="end-of-year",
                first_year_flow="FCF0 * (1 + g)",
                gordon="on year 10, discounted 10 full years")


# =========================================================================
# GROUP A — ENGINE CASES (arithmetic; each is one filer, one window)
# =========================================================================


G1 = Case(
    name="NKE-FY2026-as-struck",
    source="NKE 10-K 0000320187-26-000088, FY to 2026-05-31",
    catches="the DCF conventions (flips F1 and F5), a tag change (F2), a sum "
            "at the reader (F4b) — and, now, each of E34/E35/E36 by the "
            "amount it moves",
    declarations=dict(
        share_count=dict(basis="weighted-average diluted", value=1_481_000_000,
                         as_of="2026-05-31", ruling="E38"),
        sbc=dict(treatment="added back (as filed)", amount=715_000_000,
                 note="E36 deducts it; the value under E36 is below"),
        interest=dict(in_operating_cash_flow=True, amount=323_000_000,
                      basis="ASC 230-10-45-17(d)",
                      note="as struck, the net-debt step was applied WITHOUT "
                           "the add-back — the same interest charged twice, "
                           "and E34 is what removes it"),
        bridge=dict(net_debt=379_000_000, A1="N — short-term investments "
                    "1,464m tagged as DebtSecuritiesAvailableForSale…, out",
                    A2="N — operating leases 3,091m out; E35 puts them in",
                    nci=None, pensions=None),
        conventions=AS_CODED,
        rate_and_growth=dict(rate=0.095, anchor="7.0% core + 2.5% premium",
                             g=0.03, view="reference/growth-views/NKE.md",
                             view_date="2026-08-25"),
        as_of_dates=dict(flows="2026-05-31", balance_sheet="2026-05-31",
                         share_count="2026-05-31", price=None),
        provenance="10-K 0000320187-26-000088; every leg a tagged fact",
    ))


def test_G1_nke_as_struck_and_what_each_ruling_moves():
    declared(G1)
    nke = dict(shares=1481.0)
    as_struck = dict(fcf0=2184.0, net_cash=-379.0, **nke)

    # AS STRUCK, 2026-08-25 — the figure in NKE's watchlist note
    assert V.equity_value_per_share(growth=0.03, **as_struck) == pytest.approx(22.15, abs=0.005)
    band = V.fair_value(growth=0.03, **as_struck)
    assert (round(band.high, 2), round(band.low, 2)) == (20.64, 23.89)
    assert V.equity_value_per_share(growth=0.0, **as_struck) == pytest.approx(17.72, abs=0.005)
    assert V.equity_value_per_share(growth=0.05, **as_struck) == pytest.approx(25.73, abs=0.005)

    # E35 — leases 3,091m into the bridge. net debt 379 -> 3,470
    e35 = dict(fcf0=2184.0, net_cash=-3470.0, **nke)
    assert V.equity_value_per_share(growth=0.03, **e35) == pytest.approx(20.06, abs=0.005)

    # E36 — share-based compensation 715m deducted
    e36 = dict(fcf0=2184.0 - 715.0, net_cash=-3470.0, **nke)
    assert V.equity_value_per_share(growth=0.03, **e36) == pytest.approx(12.73, abs=0.005)

    # E34 — interest 323m added back, pre-tax, the net-debt step kept
    e34 = dict(fcf0=2868.0 - 684.0 - 715.0 + 323.0, net_cash=-3470.0, **nke)
    assert V.equity_value_per_share(growth=0.03, **e34) == pytest.approx(16.04, abs=0.005)
    assert V.equity_value_per_share(growth=0.0, **e34) == pytest.approx(12.40, abs=0.005)

    # OLD 22.15 -> NEW 16.04. Verdict unchanged: NKE is DROPPED and the
    # price is 39.48, four times either figure.


G2 = Case(
    name="DECK-FY2026-store",
    source="config/manual/DECK.yaml, FY2026 — written by `vss xbrl --annual`",
    catches="the store-to-engine path, the hand zero under E25 as an explicit "
            "RECORD input, and A2",
    declarations=dict(
        share_count=dict(basis="weighted-average diluted", value=145_805_000,
                         as_of="2026-03-31", ruling="E38",
                         memo=dict(value=139_978_000, as_of="2026-03-31",
                                   note="us-gaap:CommonStockSharesOutstanding "
                                        "— a tagged fact B36 said was not one")),
        sbc=dict(treatment="deducted", amount=44_835_000, ruling="E36"),
        interest=dict(in_operating_cash_flow=True, amount=-61_083_000,
                      basis="ASC 230-10-45-17(d); E34.1 accrual proxy: "
                            "InterestExpenseNonoperating 2,530,000 minus "
                            "InvestmentIncomeInterest 63,613,000 (E18)",
                      ruling="E34.1",
                      note="a net interest INCOME, REMOVED from FCF0. The "
                           "first build entered interest PAID 2,492,000 as "
                           "the net by hand; E34.1 says paid alone is never "
                           "the net, and the store supplies the pair"),
        bridge=dict(net_debt=-1_532_055_000,
                    borrowings="0 by a SENTENCE in the 10-Q (E25 `note`)",
                    A2="Y — operating leases 375,194,000 IN (E35)",
                    nci=None,
                    pensions="0 by the 10-K's benefit-plan note: defined "
                             "contribution plans only (E35.1, E25 `note`, "
                             "the weakest form)"),
        conventions=AS_CODED,
        rate_and_growth=dict(rate=0.095, anchor="7.0% core + 2.5% premium",
                             g=0.035, view="reference/growth-views/DECK.md",
                             view_date="2026-08-25"),
        as_of_dates=dict(flows="2026-03-31", balance_sheet="2026-03-31",
                         share_count="2026-03-31", price=None,
                         note="THEY AGREE — which G3 is about"),
        provenance="an accession on every figure in the file",
    ))


def test_G2_deck_store_basis_through_the_run_record():
    """The store -> engine path, which did not exist when report C wrote it."""
    from tests.test_runrecord import deck_record
    declared(G2)
    record = deck_record()
    assert record.complete, record.missing()
    # 124.58 under the first build's hand +2,492,000; 117.71 under E34.1;
    # 127.75 under E70 (92,823,000 of operating lease payments added back,
    # the lease being in the bridge already); 127.49 under E68 (36,790,000
    # of asset retirement obligations into the bridge, 2026-08-30); 120.03
    # under E117 (2026-09-19: rent an operating cost -- the 92,823,000
    # add-back reversed and the 375,194,000 operating lease liability out)
    assert record.strike() == pytest.approx(120.03, abs=0.005)
    # B36's 131.74, and the three rulings between them, are pinned in
    # tests/test_runrecord.py — one place, not two.
    # E117: the bridge keeps no lease (DECK has no finance leases); the
    # 375,194,000 operating liability is on the lease declaration as LEFT
    assert record.bridge.items["leases"] == 0.0
    assert record.lease.liability_excluded == 375_194_000
    assert record.shares.point_in_time == 139_978_000


G3 = Case(
    name="DECK-2026Q2-three-dates",
    source="10-Q 0000910521-26-000022 and 10-K 0001628280-26-037664",
    catches="the three-dates defect: a divisor and a balance sheet from "
            "different days inside one per-share number",
    declarations=dict(
        share_count=dict(basis="VARIES PER ROW — that is the case",
                         ruling="E38 settles it on the weighted average"),
        sbc=dict(treatment="added back (as filed)", amount=46_837_000,
                 note="as struck; E36 deducts it"),
        interest=dict(in_operating_cash_flow=True, amount=2_492_000,
                      basis="ASC 230"),
        bridge=dict(net_debt="VARIES PER ROW", A2="N as struck"),
        conventions=AS_CODED,
        rate_and_growth=dict(rate=0.095, g=0.035,
                             view="reference/growth-views/DECK.md"),
        as_of_dates=dict(note="THE POINT OF THE CASE — every row names its own"),
        provenance="all five counts are tagged facts (report A 2.3)",
    ))

#: (row, FCF0, cash, count, value). Report A 2.4's table, to the cent.
G3_ROWS = (
    ("cash 2026-06-30 + balance-sheet count 2026-06-30 — CONSISTENT",
     1117.9, 1602.589, 136.725, 140.63),
    ("cash 2026-06-30 + cover count 2026-07-09 — AS STRUCK, +0.32",
     1117.9, 1602.589, 136.414227, 140.95),
    ("cash 2026-03-31 + balance-sheet count 2026-03-31 — CONSISTENT",
     1097.332, 1907.249, 139.978, 137.22),
    ("cash 2026-03-31 + weighted average — the store, E38's answer",
     1097.332, 1907.249, 145.805, 131.74),
    ("cash 2026-03-31 + cover count 2026-07-09 — B36's pair, +3.59",
     1097.332, 1907.249, 136.414227, 140.81),
)


@pytest.mark.parametrize("row, fcf0, cash, shares, value", G3_ROWS)
def test_G3_every_pairing_of_dates_and_what_it_costs(row, fcf0, cash, shares, value):
    declared(G3)
    got = V.equity_value_per_share(fcf0=fcf0, growth=0.035, net_cash=cash,
                                   shares=shares)
    assert got == pytest.approx(value, abs=0.005), row


def test_G3_the_spread_between_two_CONSISTENT_pairings_is_the_window_alone():
    """140.63 against 137.22: same rule, different window. 3.41 of honest
    difference, against the 3.59 a July divisor on March cash invents."""
    consistent_june = 140.63
    consistent_march = 137.22
    b36_mismatch = 140.81
    assert round(b36_mismatch - consistent_march, 2) == 3.59
    assert round(consistent_june - consistent_march, 2) == 3.41


G4 = Case(
    name="SAP.DE-implied-growth-above-r",
    source="sap-valuation.xlsx C Sensitivity B13; NKE watchlist note",
    catches="the solver's cap at r — the test that pinned a FALSE claim",
    declarations=dict(
        share_count=dict(basis="diluted weighted average, Q2 2026",
                         value=1_158_000_000),
        sbc=dict(treatment="added back (as filed)", amount=None,
                 note="not part of what this case pins"),
        interest=dict(in_operating_cash_flow=False,
                      basis="sources/sap-q42025.pdf p.14 fn.1"),
        bridge=dict(net_debt=-1118.0, A1="Y current line only", A2="Y"),
        conventions=AS_CODED,
        rate_and_growth=dict(rate=0.095, g="SOLVED, not assumed"),
        as_of_dates=dict(price="2026-08-21", note="the close g* is solved at"),
        provenance="report C 9.3 #1 and flip F6",
    ))


def test_G4_a_price_above_the_value_at_g_equals_r_solves():
    declared(G4)
    assert V.implied_growth(price=188.12, fcf0=8730.0, net_cash=1118.0,
                            shares=1158.0) == pytest.approx(0.095988, abs=5e-6)
    assert V.implied_growth(price=39.41, fcf0=2184.0, net_cash=-379.0,
                            shares=1481.0) == pytest.approx(0.106731, abs=5e-6)
    # and the workbook's own hand answer, to two decimals
    assert round(V.implied_growth(price=188.12, fcf0=8730.0, net_cash=1118.0,
                                  shares=1158.0), 4) == 0.0960


# =========================================================================
# GROUP B — CONCEPT-PAIR CASES (one filer type each, twins side by side)
# =========================================================================


G5 = Case(
    name="SAP.DE-R12M-2026Q2",
    source="sap-valuation.xlsx; 20-F 0001104659-26-020058; "
           "sources/sap-q22026.pdf",
    catches="every finding that moves 185 — SBC, the share count, the "
            "bridge, and the fact that 185 is not a Method C number",
    declarations=dict(
        share_count=dict(basis="diluted weighted average, Q2 2026",
                         value=1_158_000_000, as_of="2026-06-30", ruling="E38",
                         twin=dict(value=1_175_000_000,
                                   basis="FY2025 AdjustedWeightedAverageShares")),
        sbc=dict(treatment="added back (as filed)", amount=1_331_000_000,
                 note="EQUITY-SETTLED; the 1,695 headline includes 364 of "
                      "cash-settled awards OCF has already borne (E36)"),
        interest=dict(in_operating_cash_flow=False,
                      basis="sources/sap-q42025.pdf p.14 fn.1: 'As of January "
                            "2025, SAP no longer classifies interest paid and "
                            "interest received as a part of cash flows from "
                            "operating activities'",
                      note="E34: FCF0 IS ALREADY a flow to the firm, so the "
                           "net-cash step is correct and NOTHING MOVES. The "
                           "held name the interest error does not touch"),
        bridge=dict(net_cash=1118.0,
                    A1="Y, the CURRENT line only — non-current other "
                       "financial assets 7,269 are OUT and undecided",
                    A2="Y — leases 1,684 inside the all-in 10,507 (E35)",
                    nci=488, pensions=230, associates=142),
        conventions=AS_CODED,
        rate_and_growth=dict(rate=0.095, anchor="7.0% core + 2.5% premium",
                             g=0.08, bear=0.06, bull=0.11,
                             view="config/watchlist.yaml:607 prose"),
        as_of_dates=dict(flows="2026-06-30", balance_sheet="2026-06-30",
                         share_count="2026-06-30", price="2026-08-21"),
        provenance="20-F 0001104659-26-020058 for the FY legs",
    ))


def test_G5_sap_de_and_the_weighting_E28_deleted():
    declared(G5)
    sap = dict(net_cash=1118.0, shares=1158.0)
    method_c = V.equity_value_per_share(fcf0=8730.0, growth=0.08, **sap)
    assert method_c == pytest.approx(167.07, abs=0.005)

    # 185 IS NOT A METHOD C NUMBER, and this is the arithmetic that says so
    weighted = 0.85 * method_c + 0.15 * 285.92
    assert weighted == pytest.approx(184.90, abs=0.005)
    assert round(weighted) == 185

    # the twins, each one ruling or one open question
    assert V.equity_value_per_share(fcf0=8730.0 - 1331.0, growth=0.08, **sap) \
        == pytest.approx(141.74, abs=0.005)                      # E36
    assert V.equity_value_per_share(fcf0=8730.0, growth=0.08, net_cash=1118.0,
                                    shares=1175.0) == pytest.approx(164.65, abs=0.005)
    # E34 moves NOTHING here: SAP's OCF has been pre-interest since Jan 2025
    # E105's leg at ZERO: this pins the arithmetic AS IT WAS STRUCK, before
    # the leg existed. SAP's own window figure is -30 (E86 operands on four
    # quarters), and the LIVE store is where that moves the answer.
    assert V.free_cash_flow_zero(operating_cash_flow=9465.0, capex=-735.0,
                                 interest_in_ocf=False, sbc=0.0,
                                 nci_dividends_paid=0.0) == 8730.0


def test_G5_sap_reaches_section_5_through_the_tool_now():
    """Report B #10's "the ONE finding I would fix first", closed.

    SAP.DE was reachable by NO code path: no manual file, no `cik:`, and a
    reader that opened `us-gaap` alone. All three are gone.
    """
    from vss.config import load_watchlist
    entries = {e.ticker: e for e in load_watchlist(Path("config/watchlist.yaml"))}
    assert entries["SAP.DE"].cik == 1000184
    assert entries["UNA.AS"].cik == 217410
    from vss import xbrl as X
    assert X.IFRS_TAXONOMY.name == "ifrs-full"
    assert any(f.field == "operating_cash_flow" for f in X.IFRS_ANNUAL_FIELDS)


G6 = Case(
    name="LIAB.ST-R12M-2026Q2",
    source="Lindab Q2 2026 interim, Nasdaq release 1454549 "
           "(downloaded to sources/ on 2026-08-26 through the issuer map)",
    catches="THE INTEREST DOUBLE COUNT — REVIEW-4's largest error, on the "
            "held name it lands on",
    declarations=dict(
        share_count=dict(basis="77,036 thousand at every one of the last "
                               "eight quarter ends — the period-end count "
                               "and the average COINCIDE, so E38's choice is "
                               "moot for this name",
                         value=77_036_000, as_of="2026-06-30"),
        sbc=dict(treatment="added back (as filed)", amount=None,
                 note="HYPOTHESIS < 3% of FCF0; no figure was found in the "
                      "extracted text of the 2025 annual report, so under "
                      "E36 this name has NO FCF0 until one is read"),
        interest=dict(in_operating_cash_flow=True, amount=201.0,
                      basis="interim p.17, OPERATING ACTIVITIES: 'Interest "
                            "received … 10 / Interest paid … −211'",
                      ruling="E34"),
        bridge=dict(net_debt=4497.0,
                    note="Lindab's own, interim p.25: interest-bearing "
                         "provisions and liabilities 5,073 less "
                         "interest-bearing assets 576",
                    A2="Y — leases 1,410 inside it (E35)",
                    pensions=280,
                    schema_reach="E35's four legs give 4,217; the 280 of "
                                 "pension provisions has NO FIELD"),
        conventions=AS_CODED,
        rate_and_growth=dict(rate=0.095, g=0.02, bear=0.01,
                             view="config/watchlist.yaml:592-597 prose"),
        as_of_dates=dict(flows="2026-06-30", balance_sheet="2026-06-30",
                         share_count="2026-06-30", price=None,
                         note="THE ENTRY RECORDS NONE OF THESE — report C 11.3"),
        provenance="interim pages 7, 17, 19-20, 25",
    ))


def test_G6_the_interest_double_count_on_the_held_name():
    declared(G6)
    liab = dict(shares=77.036, growth=0.02)

    as_struck = V.equity_value_per_share(fcf0=879.0, net_cash=-4497.0, **liab)
    assert as_struck == pytest.approx(102.66, abs=0.005)

    # E34, pre-tax add-back — the ruling's own answer
    under_e34 = V.equity_value_per_share(fcf0=879.0 + 201.0, net_cash=-4497.0, **liab)
    assert under_e34 == pytest.approx(139.48, abs=0.005)

    # report A's b1 applied a 20.6% tax shield; E34 explicitly does not, and
    # the difference is the bias E34 states rather than removes
    after_tax = V.equity_value_per_share(fcf0=879.0 + 201.0 * (1 - 0.206),
                                         net_cash=-4497.0, **liab)
    assert after_tax == pytest.approx(131.89, abs=0.005)
    assert under_e34 - after_tax == pytest.approx(7.59, abs=0.005)

    # the schema's own basis 1, not the issuer's KPI
    assert V.equity_value_per_share(fcf0=849.0 + 201.0, net_cash=-4497.0, **liab) \
        == pytest.approx(133.98, abs=0.005)
    # E35's four legs, without a pension field
    assert V.equity_value_per_share(fcf0=1080.0, net_cash=-4217.0, **liab) \
        == pytest.approx(143.11, abs=0.005)


def test_G6_the_direction_is_what_matters_for_the_position():
    """102.66 sat 19% BELOW the 126.30 close and read, under section 6.4's
    'at FV_base, trim 25-50%', as a name to TRIM. Every consistent treatment
    of its interest puts the price at or below fair value."""
    liab = dict(shares=77.036, growth=0.02)
    close = 126.30
    assert V.equity_value_per_share(fcf0=879.0, net_cash=-4497.0, **liab) < close
    for fcf0, net_debt in ((1080.0, 4497.0), (1050.0, 4497.0), (1080.0, 4217.0)):
        assert V.equity_value_per_share(fcf0=fcf0, net_cash=-net_debt, **liab) > close


G7 = Case(
    name="NKE-FY2026-bridge-variants",
    source="as G1",
    catches="each bridge choice on a post-interest US filer, one at a time",
    declarations={**G1.declarations,
                  "bridge": dict(note="VARIES PER ROW — that is the case")},
)

#: (variant, FCF0, net cash, value)
G7_ROWS = (
    ("as struck", 2184.0, -379.0, 22.15),
    ("A1 = Y — short-term investments 1,464m in", 2184.0, 1085.0, 23.14),
    ("E35 — leases 3,091m in", 2184.0, -3470.0, 20.06),
    ("E36 — SBC 715m deducted", 2184.0 - 715.0, -379.0, 14.81),
    ("E34 — interest 323m added back, PRE-TAX", 2184.0 + 323.0, -379.0, 25.46),
    ("FCFE for contrast — no net-debt step, interest left charged",
     2184.0, 0.0, 22.41),
)


@pytest.mark.parametrize("variant, fcf0, net_cash, value", G7_ROWS)
def test_G7_one_bridge_choice_at_a_time(variant, fcf0, net_cash, value):
    declared(G7)
    got = V.equity_value_per_share(fcf0=fcf0, growth=0.03, net_cash=net_cash,
                                   shares=1481.0)
    assert got == pytest.approx(value, abs=0.005), variant


def test_G7_the_FCFE_row_is_CONTRAST_and_not_an_alternative_E34_allows():
    """E34 subtracts net debt ONCE in both classifications. The FCFE reading
    -- drop the bridge, leave the interest charged -- answers a different
    question and gives a different number, and mixing the two is the defect."""
    assert "no FCFE path" in V.free_cash_flow_zero.__doc__


# =========================================================================
# GROUP C — STORE AND GATE GUARDS (the run must REFUSE or FLAG)
# =========================================================================


G8 = Case(name="scale-1000x", source="REVIEW-4 report B 7.1, RUN on DECK.yaml",
          catches="a figure out by a round thousand on a leg the DCF divides by")


def test_G8_a_thousandfold_leg_refuses_at_the_gate():
    from tests.test_manual import _four_quarters_with, parse
    gate = M.section5_gate(
        parse(_four_quarters_with("operating_cash_flow",
                                  [100.0, 110.0, 120.0, 130_000.0])),
        as_of=AS_OF)
    assert M.REFUSE_UNIT_MIX in {r.kind for r in gate.refusals}
    # AND THE RESIDUAL, stated: a UNIFORMLY mis-scaled file still passes.
    uniform = parse(_four_quarters_with(
        "operating_cash_flow", [100_000.0, 110_000.0, 120_000.0, 130_000.0]))
    assert M.scale_jumps(uniform) == ()


G9 = Case(name="split-vs-restatement", source="DECK FY2022 in config/manual/",
          catches="a 6-for-1 split read as a restatement, or as nothing")


def test_G9_the_split_is_marked_and_the_step_is_flagged():
    parsed = M.load_manual("DECK", directory=M.MANUAL_DIR)
    gate = M.section5_gate(parsed, as_of=AS_OF)
    # E108 (2026-09-04) puts a flag of a DIFFERENT KIND beside these -- the
    # E105 leg, VERIFIED-EXEMPT on the zero limb -- so G9's set is taken on
    # the share-basis kind it is a case about.
    assert {f.subject for f in gate.flags if f.kind != M.FLAG_EXEMPT} == {
        "diluted_eps", "diluted_weighted_average_shares", "shares_point_in_time"}
    text = Path("config/manual/DECK.yaml").read_text(encoding="utf-8")
    assert text.count("PRE-SPLIT BASIS") == 4
    # FY2022 eps and average, and the FY2022 and FY2023 memos --
    # every one of them filed before the 2024-09-13 split.
    assert "value: 16.26" in text                   # NOT rescaled
    assert M.FLAG_SHARE_BASIS_STEP not in {r.kind for r in gate.refusals}


G10 = Case(name="count-never-summed",
           source="SYNSAM.ST, four quarterly averages (B27)",
           catches="a share count summed across a TTM window")


def test_G10_a_point_in_time_count_is_a_stock_and_is_never_summed():
    from tests.test_manual import four_quarters, figure, parse
    parsed = parse(four_quarters(each={"shares_point_in_time": figure(100.0)}))
    got = M.resolve_on_basis(parsed, M.section5_basis(parsed),
                             "shares_point_in_time")
    assert got.value == 100.0
    assert "shares_point_in_time" in M.STOCK_FIELDS


G11 = Case(name="52-53-week-filer", source="LULU, live on the watchlist",
           catches="a drifting fiscal year end read as a stub")


def test_G11_a_year_that_drifts_across_a_month_boundary_is_still_the_year():
    from tests.test_xbrl_annual import _drifting_year_facts
    from vss import xbrl as X
    facts = _drifting_year_facts()
    ends, passed_over = X.fiscal_year_ends(facts, 1, currency="USD")
    assert ends[-2:] == ["2025-02-02", "2026-02-01"] and passed_over == []


@pytest.mark.skip(reason="STILL OPEN AFTER E41 — the HALF-YEAR shape of R1 / "
                         "B12. E41 (2026-08-26) settled the four-quarter case "
                         "(SAP.DE stands on its R12M now); UNA.AS's history "
                         "(2024-FY, 2025-H1, 2026-H1) needs FY - H1 + H1, a "
                         "subtraction E41 expressly does not license. G12 "
                         "waits on that ruling.")
def test_G12_half_yearly_basis():
    raise AssertionError("unreachable: skipped pending R1/B12")


G13 = Case(name="tagged-fact-VERIFIED",
           source="config/manual/SAP.DE.yaml, written by `vss xbrl --annual`",
           catches="E21 refusing the only fetched path on a flag no person "
                   "could set -- and, now, any drift in WHAT VERIFIED MEANS")


def test_G13_tagged_fact_VERIFIED():
    """RULED A (E40, 2026-08-26); skipped until then. A tagged SEC fact is
    VERIFIED by provenance -- tag + accession + filing date -- and carries
    `verified_kind: tagged`. The flag has three kinds and the gate accepts
    all three; the report prints the kind beside every figure."""
    parsed = M.load_manual("SAP.DE", directory=M.MANUAL_DIR)
    # the ANNUAL block is what the XBRL path wrote; the `periods:` beside it
    # are E41's hand-entered quarters and carry readings, not tags
    tagged = [f for e in parsed.annual for f in e.figures.values() if f.present]
    assert tagged and all(f.verified for f in tagged)
    # E84 (2026-08-30) corrected the two FY2025 borrowing legs from the
    # 20-F's NOMINAL tags to note (E.2)'s carrying amounts; E89 the same
    # day extended the ex-lease reading to every date (1,598 + 198 = 1,796 /
    # 4,194 + 397 = 4,591), and the owner's read-back confirmed both
    # operand pairs against p.39 -- verified cross_document on the tagged
    # FinancialLiabilities 8,070. Every other annual figure is still the
    # tag it was written from.
    assert {f.verified_kind for f in tagged} == {M.KIND_TAGGED, M.KIND_CROSS_DOCUMENT}
    assert {f.name for f in tagged if f.verified_kind == M.KIND_CROSS_DOCUMENT} == {
        "financial_liabilities_current", "financial_liabilities_noncurrent"}
    # the 2026-08-30 entries in `periods:` (E84-E86, the Half-Year Report)
    # were confirmed at the owner's read-back the same evening; the gate
    # refused nothing -- until E117 (2026-09-19). SAP never isolates its lease
    # interest, so its rent-bearing FCF0 is DATA MISSING (UNVERIFIED UNDER
    # E117), and E108's measured exemption of the minority-dividend quarters
    # lapses with it; the tagged kind is untouched by any of it
    gate = M.section5_gate(parsed, as_of=AS_OF)
    # A3 (owner, 2026-09-19): the lease interest is now E106-BOUNDED by each
    # quarter's total interest paid, so FCF0 forms and the gate refuses on
    # the TOLERANCE alone (the bound moves fv_base 6.9%)
    assert {r.kind for r in gate.refusals} == {"UNDETERMINED LEGS PAST E106"}
    assert M.VERIFIED_KINDS == ("tagged", "cross_document", "same_page",
                                "caption_statement")   # E78 added the fourth
    assert "VERIFIED (tagged)" in M.render_report(parsed, gate)


# =========================================================================
# GROUP D — PRICE-PATH GUARDS (the path that compares 165 and 112 tonight)
# =========================================================================


G14 = Case(name="phantom-halving", source="tests/fixtures/series-sanity/MNST.csv",
           catches="a feed fault printed as STOP BREACHED")


def test_G14_a_scale_switch_is_a_feed_fault_and_not_a_breach():
    from vss.series_sanity import KIND_SCALE_SWITCH, check
    import pandas as pd
    need("tests/fixtures/series-sanity/MNST.csv")
    frame = pd.read_csv("tests/fixtures/series-sanity/MNST.csv",
                        index_col=0, parse_dates=True)
    finding = check(frame, date(2026, 8, 21))
    assert finding is not None and finding.kind == KIND_SCALE_SWITCH


def test_G14_the_check_IS_wired_into_vss_run():
    """REPORT B #7, FIXED IN BUILD 2 (item 0, 2026-08-26). `series_sanity.check`
    now runs in `runner.build_row`, before any level is compared, and a
    finding makes the stop, MBP and dislocation checks DATA MISSING. The
    first build pinned this as NOT wired; the pin is flipped, not deleted,
    so the history of the gap stays on the page."""
    import inspect
    from vss import runner
    source = inspect.getsource(runner.build_row)
    assert "series_sanity.check(fetched.frame, as_of)" in source
    assert "series_finding=series_finding" in source


G15 = Case(name="short-history", source="REVIEW-4 report B 7.2, RUN",
           catches="a drawdown struck off a series that does not cover 52 weeks")


def test_G15_a_short_series_gives_no_drawdown_at_all():
    from tests.test_metrics import frame
    short = MT.compute(frame([100.0] * 120 + [80.0], end=date(2026, 8, 20)),
                       date(2026, 8, 20))
    assert short.high_52w is None and short.drawdown is None
    assert short.covers_52_weeks is False


G16 = Case(name="holiday-tuesday", source="REVIEW-4 report A 4.2, RUN",
           catches="every held name blocked on the first trading day after a "
                   "holiday — no stop check, no verdict")


@pytest.mark.parametrize("holiday, last_close, as_of", [
    ("US Memorial Day", date(2026, 5, 22), date(2026, 5, 26)),
    ("Easter Monday", date(2026, 4, 2), date(2026, 4, 7)),
    ("Midsommar", date(2026, 6, 18), date(2026, 6, 22)),
])
def test_G16_the_first_trading_day_after_a_holiday_is_not_stale(
        holiday, last_close, as_of):
    """NOT SKIPPED. Report C listed G16 as awaiting C3; C3 was RULED by the
    owner on 2026-08-26 and the gate now counts trading days."""
    assert RU.stale_close_blocker(last_close, as_of) is None, holiday
    assert (as_of - last_close).days > RU.MAX_CLOSE_AGE_TRADING_DAYS


G17 = Case(name="quote-vs-reporting-currency",
           source="BETS-B.ST (EUR accounts, SEK quote); JD.L (GBX)",
           catches="a pound fair value against a pence close")


def test_G17_a_pound_value_is_compared_with_a_pence_close_in_pence():
    """CLOSED 2026-09-19 on the owner's AUTO.L-S (it was PINNED AS A GAP
    since 2026-08-30). The record values the share in its accounts'
    currency; the close arrives in the quote unit. `runner.build_row` moves
    every level the assessment compares -- fv_base, the bear case, the MBP
    built on them -- into the quote unit FIRST (`fx.to_quote_units`), so a
    tier on a GBX name gives a buy price in pence against a close in pence."""
    from vss import fx
    from vss.fetch import FetchResult, SOURCE_LIVE
    from vss.config import WatchlistEntry
    from vss.runner import build_row
    from tests.test_runner import _series
    assert fx.to_quote_units(4.84, "GBP", "GBX") == pytest.approx(484.0)
    assert fx.to_quote_units(4.84, "GBP", "GBP") == 4.84
    assert fx.to_quote_units(100.0, "USD", "USD") == 100.0
    # E24's cross-currency case is NOT this seam and passes unchanged
    assert fx.to_quote_units(10.0, "EUR", "SEK") == 10.0
    record = "reference/run-records/AUTO.L-2026-09-19-e117.json"
    entry = WatchlistEntry(ticker="AUTO.L", name="Auto Trader", currency="GBX",
                           status="WATCH-PRICED", fv_base=4.84, tier=2,
                           run_record=record)
    fetched = FetchResult("AUTO.L", _series(last_close=488.2, last_volume=1000.0),
                          SOURCE_LIVE)
    row = build_row(entry, fetched, date(2026, 9, 19), date(2026, 9, 18))
    assert row.fv_refused is None
    # 4.8364 GBP x 100 x E90's tier-2 cushion 0.75 = 362.73 PENCE
    assert row.assessment.mbp == pytest.approx(362.73, abs=0.01)
    assert row.pct_to_mbp == pytest.approx(488.2 / 362.73 - 1, abs=1e-3)
    assert "AT/BELOW MBP" not in [v.label for v in row.assessment.verdicts]


# =========================================================================
# THE LIST ITSELF
# =========================================================================


ALL_CASES = (G1, G2, G3, G4, G5, G6, G7, G8, G9, G10, G11, G13, G14, G15,
             G16, G17)


def test_all_seventeen_are_accounted_for():
    """Sixteen built, one skipped with the ruling it waits on. G13 was the
    second skip until E40 (2026-08-26)."""
    assert len(ALL_CASES) == 16
    source = Path(__file__).read_text(encoding="utf-8")
    assert "def test_G12_half_yearly_basis" in source
    assert "def test_G13_tagged_fact_VERIFIED" in source
    assert len([l for l in source.splitlines()
                if l.startswith("@pytest.mark.skip")]) == 1
    # C3 was the third; it is RULED and G16 runs
    assert "NOT SKIPPED" in source


def test_every_engine_and_concept_case_states_all_eight_declarations():
    for case in (G1, G2, G3, G4, G5, G6, G7):
        declared(case)


# =========================================================================
# PHASE 5 — the two held names re-struck on the TOOL PATH ONLY
# =========================================================================
#
# The printout is `reference/RESTRIKE-2026-08-26.md`. The numbers are pinned
# here so the artefact cannot drift away from the code that made it.


def test_phase_5_sap_de_restruck_from_its_own_store_file():
    """`config/manual/SAP.DE.yaml`, written by `vss xbrl --annual` from CIK
    1000184 — a file that could not exist before the first build. THE FIRST
    BUILD'S 133.20 STOOD ON THE FY2025 BASIS; E41 (Build 2) moved the basis
    to the R12M to 2026-06-30, and the FY2025 arithmetic is kept here as the
    history it is."""
    parsed = M.load_manual("SAP.DE", directory=M.MANUAL_DIR)
    basis = M.section5_basis(parsed)
    assert basis.label == "TTM 2025-Q3+2025-Q4+2026-Q1+2026-Q2"   # E41
    assert parsed.interest_in_ocf.value is False        # E34: PRE-interest
    count, why = M.share_count_on_basis(parsed, basis)
    # 2026-08-30, three rulings in one evening: E75 briefly made the E80
    # pair the divisor (1,154.2m); E88 reversed it to the FY2025 annual
    # average 1,175m with the mismatch flagged; E91 then took the four
    # stated per-quarter diluted counts (1,172/1,172/1,168/1,158m, the
    # EPS footnotes) as operands of the coded DAY-WEIGHTED window average
    # -- the window's own figure, dates agreeing.
    assert count == pytest.approx(1_167_523_287.67, abs=0.5)
    assert "E91" in why and "x 92d" in why
    # the FY2025 arithmetic the first build printed, pinned as history
    fcf0 = V.free_cash_flow_zero(
        operating_cash_flow=9_156_000_000, capex=-739_000_000,
        interest_in_ocf=False, sbc=1_331_000_000,       # E36
        nci_dividends_paid=0.0)     # E105 at zero: history, struck before it
    assert V.equity_value_per_share(fcf0=fcf0 / 1e6, growth=0.08,
                                    net_cash=386.0, shares=1175.0) \
        == pytest.approx(133.20, abs=0.005)
    # E40: nothing the basis reads is UNVERIFIED. What the gate refuses on
    # now is what SAP's interims do not state standalone -- capex (printed
    # cumulatively) -- and E41 names it rather than inventing it.
    gate = M.section5_gate(parsed, as_of=AS_OF)
    # 2026-08-30 (E84-E86): the store now FORMS capex (the code's difference
    # of stated cumulative columns) and net debt (note E.2's ex-lease
    # operands, the lease total, and the two NOT PRESENTED legs), so the
    # FCF0 refusal E41 named is gone; and the owner's read-back the same
    # evening confirmed all fifteen 2026-08-30 entries (the nine basis
    # entries, the two E89 FY2025 operands, the four owners-only quarterly
    # profits), so the gate refused NOTHING -- until E117 (2026-09-19): the
    # lease interest SAP never isolates leaves FCF0 DATA MISSING, and E108's
    # measured exemption of the four minority-dividend quarters lapses with it.
    # A3 (owner, 2026-09-19): the lease interest is now E106-BOUNDED by each
    # quarter's total interest paid, so FCF0 forms and the gate refuses on
    # the TOLERANCE alone (the bound moves fv_base 6.9%)
    assert {r.kind for r in gate.refusals} == {"UNDETERMINED LEGS PAST E106"}
    net_debt = next(r for r in gate.ratios if r.name == "net debt")
    assert net_debt.state == M.RATIO_OK


def test_phase_5_sap_de_R12M_2026_08_30_the_store_rebuilds_139_48():
    """The strike of 2026-08-30 (tools/strike_sap_2026_08_30.py): after
    E84-E89 and the owner's read-back, `from_store` forms the WHOLE record
    with ZERO hand inputs and the number is the prior record's own 139.48
    -- E87's nulling lifted by its stated condition ('re-strike when it
    forms end to end'). The eight declarations are pinned AS DATA."""
    import json
    case = Case(
        name="SAP.DE-R12M-2026-06-30-as-struck",
        source="config/manual/SAP.DE.yaml; reference/run-records/SAP.DE-2026-08-30.json",
        catches="any drift in E84/E89's ex-lease legs, E85's NOT PRESENTED "
                "state, E86's coded difference, E88's divisor order or the "
                "bridge -- the store must keep rebuilding the shipped figure",
        declarations=dict(
            share_count=dict(basis="day-weighted window average of the four "
                                   "stated per-quarter diluted counts "
                                   "(1,172/1,172/1,168/1,158m x 92/92/90/91d)",
                             value=1_167_523_288, as_of="2026-06-30",
                             ruling="E91 -- the window's own average; E88's "
                                    "annual 1,175m is the fall-back and the "
                                    "E80 pair stays memo"),
            sbc=dict(treatment="deducted", amount=1_331_000_000,
                     note="equity-settled (E36); E41 annual fill"),
            interest=dict(in_operating_cash_flow=False, amount=None,
                          basis="the filer classifies interest paid/received "
                                "outside operating activities from January "
                                "2025; no add-back (E34)"),
            bridge=dict(net_debt=-869_000_000,
                        legs="1,685 + 7,087 (E84 ex-lease operands) + leases "
                             "1,735 + pension 249 + ARO 0 (E85) + prepaid 0 "
                             "(E85) - cash 10,511 - other current financial "
                             "assets 1,114 -- net CASH 869"),
            conventions=AS_CODED,
            rate_and_growth=dict(rate=0.095, anchor="7.0% core + 2.5% premium",
                                 g=0.08, view="reference/growth-views/SAP.DE.md",
                                 bear=0.06, bull=0.11),
            as_of_dates=dict(flows="2026-06-30", balance_sheet="2026-06-30",
                             share_count="2026-06-30",
                             note="THEY AGREE -- E91's divisor is the "
                                  "window's own average"),
            provenance="every input off the store; ZERO hand inputs (E87's "
                       "condition); read back by the owner 2026-08-30",
        ))
    declared(case)
    parsed = M.load_manual("SAP.DE", directory=M.MANUAL_DIR)
    basis = M.section5_basis(parsed)
    record = R.from_store(
        parsed, basis, run_ts=RUN_TS,
        growth=R.Growth(base=0.08, bear=0.06, bull=0.11,
                        view_file="reference/growth-views/SAP.DE.md"),
        rate=R.Rate(core_expected_return=0.070, premium=0.025))
    # E117 (2026-09-19): INCOMPLETE until the lease interest is on file --
    # SAP never isolates it. The case is pinned AS STRUCK by replaying the
    # same record under E70: its lease rule, and the 1,735,000,000 IFRS 16
    # liability put back into net debt.
    from dataclasses import replace as _replace
    assert not record.complete and "lease_interest_paid" in record.missing()[0]
    assert record.lease.liability_excluded == 1_735_000_000
    record = _replace(record, undetermined=(),
                      lease=R.LeaseTreatment(False, "IFRS 16.50(b)", rule="E70"),
                      bridge=_replace(record.bridge, net_debt=record.bridge.net_debt
                                      + record.lease.liability_excluded))
    assert record.complete and not record.missing()
    assert not [i.name for i in record.inputs if i.entered_by == "hand"]
    legs = record.legs()
    # E105 (2026-09-04) MOVED THIS CASE, and the move is pinned rather than
    # the old figure being edited away. FCF0 was 7,399,000,000 -- OCF 9,465
    # less capex 735 less SBC 1,331 -- and the leg takes 30,000,000 out of
    # it: the dividends SAP paid its minorities over the window, -3 (Q3
    # 2025) + 1 (Q4 2025) - 5 (Q1 2026) - 23 (Q2 2026), each an E86
    # difference of two stated cumulative columns. 140.37 -> 139.81, a move
    # of 0.40%, and E108 measures the same leg at 0.0405% on a +/-10%
    # perturbation -- two orders inside the floor, which is why the four
    # UNVERIFIED quarters do not refuse.
    assert legs.fcf0 == 7_369_000_000 and legs.net_cash == 869_000_000
    assert record.nci_dividends_paid == -30_000_000
    assert legs.shares == pytest.approx(1_167_523_287.67, abs=0.5)   # E91
    assert record.shares.divisor_basis == "window_day_weighted"
    assert record.shares.as_of == date(2026, 6, 30) and record.dates.agree
    assert record.band().mid == pytest.approx(139.81, abs=0.01)
    assert record.strike(0.06) == pytest.approx(120.55, abs=0.01)
    assert record.strike(0.11) == pytest.approx(174.71, abs=0.01)
    assert V.maximum_buy_price(
        fcf0=legs.fcf0, g_base=0.08, net_cash=legs.net_cash,
        shares=legs.shares, tier=1).mid == pytest.approx(118.84, abs=0.01)   # E90
    # WITHOUT the leg it is still 140.37: the case's own before-and-after,
    # so a later reader can see exactly what E105 cost this name.
    from dataclasses import replace as _replace
    assert _replace(record, nci_dividends_paid=0.0).band().mid \
        == pytest.approx(140.37, abs=0.01)
    assert record.sensitivity()["nci_dividends_paid"] < M.SENSITIVITY_FLOOR
    # the E88-era shipped record (divisor 1,175m) stays on disk as history
    # and still replays to ITS figure
    shipped = R.RunRecord.from_dict(json.loads(Path(
        "reference/run-records/SAP.DE-2026-08-30.json").read_text(encoding="utf-8")))
    assert shipped.band().mid == pytest.approx(139.48, abs=0.005)
    assert shipped.legs().shares == 1_175_000_000


def test_phase_5_lii_the_store_rebuilds_319_37_under_e70_and_285_07_under_e117():
    """LII's E70 re-strike of 2026-08-30, which was PRINTED and never
    written: `reference/run-records/LII-2026-08-30-e70.json`.

    The pre-E70 record (274.27) charged the lease twice -- once in net debt
    under E35 and again inside the operating cash flow it never added back.
    Both records stay on disk and both replay to their own figure; this pins
    the E70 one and the store that rebuilds it with ZERO hand inputs.

    LII IS NOT ON THE WATCHLIST, and this case asserts that too: the figure
    is a printout, and entering the name is the owner's act (E93/E94)."""
    import json
    case = Case(
        name="LII-annual-FY2025-e70",
        source="config/manual/LII.yaml; "
               "reference/run-records/LII-2026-08-30-e70.json",
        catches="any drift in E70's lease add-back, the E68.2/E81 caption "
                "zeros, or E34.1's accrual interest proxy -- the store must "
                "keep rebuilding 319.37 with no hand input",
        declarations=dict(
            share_count=dict(basis="weighted-average diluted for annual "
                                   "FY2025 (E38)",
                             value=35_400_000, as_of="2025-12-31",
                             ruling="E38 -- the window's own average"),
            sbc=dict(treatment="deducted", amount=29_100_000, note="E36"),
            interest=dict(in_operating_cash_flow=True,
                          amount=40_900_000,
                          basis="ASC 230-10-45-17(d): interest paid is an "
                                "OPERATING outflow for every US filer, so the "
                                "flow already bears it; the add-back is the "
                                "income statement's NET as an accrual proxy "
                                "(E34.1)"),
            lease=dict(in_operating_cash_flow=True,
                       principal_added_back=90_600_000,
                       ruling="E70 declaration 3.1 -- ASC 842-20-45-5(a): "
                              "the flow bears the operating lease payments "
                              "and the 382.3m liability is already in net "
                              "debt, so the lease is charged ONCE"),
            bridge=dict(net_debt=1_755_200_000,
                        legs="244.3 + 1,144.1 borrowings + leases 382.3 "
                             "(E35/E65) + pension 18.7 (E35.1) + ARO 0 "
                             "(E68.2, a caption zero) + prepaid 0 (E81) "
                             "- cash 34.2"),
            conventions=AS_CODED,
            rate_and_growth=dict(rate=0.095, anchor="7.0% core + 2.5% premium",
                                 g=0.05, view="reference/growth-views/LII.md",
                                 bear=0.0, bull=0.08),
            as_of_dates=dict(flows="2025-12-31", balance_sheet="2025-12-31",
                             share_count="2025-12-31", note="THEY AGREE"),
            provenance="every input off the store; ZERO hand inputs. 11 legs "
                       "VERIFIED (tagged), 2 VERIFIED (same_page) -- the "
                       "E68.2 and E81 caption zeros the owner read",
        ))
    declared(case)
    parsed = M.load_manual("LII", directory=M.MANUAL_DIR)
    basis = M.section5_basis(parsed)
    assert basis.label == "annual FY2025"
    record = R.from_store(
        parsed, basis, run_ts=RUN_TS,
        growth=R.Growth(base=0.05, bear=0.0, bull=0.08,
                        view_file="reference/growth-views/LII.md"),
        rate=R.Rate(core_expected_return=0.070, premium=0.025))
    assert record.complete and not record.missing()
    assert not [i.name for i in record.inputs if i.entered_by == "hand"]
    legs = record.legs()
    # E117 (2026-09-19) moved the store's answer: E70's 90,600,000 add-back
    # reversed (741.2m -> 650.6m) and the 382,300,000 operating lease
    # liability out of net debt; the 68,900,000 of finance leases inside
    # the borrowing lines stay. 319.37 is the E70 record's, pinned below.
    assert legs.fcf0 == 650_600_000
    assert legs.net_cash == -1_372_400_000   # C3 (2026-09-19): + short-term investments 0.5m
    assert legs.shares == 35_400_000
    assert record.dates.agree
    assert record.lease.rule == "E117" and record.lease.in_operating_cash_flow is True
    assert record.band().mid == pytest.approx(285.08, abs=0.01)   # 285.07 before C3
    assert record.strike(0.0) == pytest.approx(185.22, abs=0.01)
    assert record.strike(0.08) == pytest.approx(366.16, abs=0.01)

    # BOTH records stay on disk and each replays to ITS OWN figure: the
    # pre-E70 one is history, not a mistake to be deleted (E32's shape).
    e70 = R.RunRecord.from_dict(json.loads(Path(
        "reference/run-records/LII-2026-08-30-e70.json").read_text(encoding="utf-8")))
    before = R.RunRecord.from_dict(json.loads(Path(
        "reference/run-records/LII-2026-08-30.json").read_text(encoding="utf-8")))
    assert e70.band().mid == pytest.approx(319.37, abs=0.005)
    assert before.band().mid == pytest.approx(274.27, abs=0.005)
    assert before.lease.in_operating_cash_flow is None      # predates E70

    # AND LII IS NOT ENTERED. The 319.37 is a printout; entering the name
    # is the owner's write and nothing here makes it. From 2026-09-04 LII
    # IS on the watchlist -- as E111 INTAKE, READ AND NOT WATCHED -- which
    # is a stronger version of the same claim and is asserted as one: it
    # carries a growth view so E108 and E106 clause 4 can run, and NO
    # fv_base, NO tier and therefore NO MBP, and NO entry stamp of any
    # kind. E12's clock starts at promotion to PIPELINE.
    from vss.config import load_watchlist
    entry = next(e for e in load_watchlist(Path("config/watchlist.yaml"))
                 if e.ticker == "LII")
    assert entry.status == "INTAKE"
    assert entry.fv_base is None and entry.tier is None
    assert entry.dd_at_entry is None and entry.peak_date is None
    assert entry.stop_price is None and entry.mbp_basis is None
    assert entry.growth is not None and entry.growth.base == 0.05


def test_phase_5_liab_st_restruck_from_hand_inputs_with_their_pages():
    """No store file exists for LIAB.ST and none can yet: no SEC filer, and
    no reader for the PDF the issuer map now downloads."""
    liab = dict(shares=77.036, growth=0.02)
    fcf0 = V.free_cash_flow_zero(operating_cash_flow=1176.0, capex=-327.0,
                                 interest_in_ocf=True, net_interest_paid=201.0,
                                 sbc=0.0,
                                 # E105 at zero, and for Lindab it IS zero:
                                 # the store now carries a searched absence
                                 # on all four quarters of the window.
                                 nci_dividends_paid=0.0)
    assert fcf0 == 1050.0
    assert V.equity_value_per_share(fcf0=fcf0, net_cash=-4217.0, **liab) \
        == pytest.approx(137.62, abs=0.005)
    # the SBC of zero is what makes it inadmissible under E36
    with pytest.raises(V.ValuationError, match="share-based compensation"):
        V.free_cash_flow_zero(operating_cash_flow=1176.0, capex=-327.0,
                              interest_in_ocf=True, net_interest_paid=201.0)


def test_phase_5_wrote_its_printout_and_NOT_the_watchlist():
    """The first build printed and stopped. E39 was then APPROVED by the
    owner and APPLIED in Build 2 (item 4, 2026-08-26): fv_base, tier and
    mbp are null on both held names, the stops stand, and the prose that
    held every input of the superseded figures is kept.

    Later the same day the OWNER sold SAP.DE under C4 (FRAMEWORK-EDITS
    E42), moved it to WATCH-PRICED with the stop nulled, and -- once E28
    was wired -- linked its run record with fv_base 139.48; then linked
    LIAB.ST's with fv_base 133.48, stop 112 untouched: owner's writes, not
    the tool's."""
    printout = Path("reference/RESTRIKE-2026-08-26.md").read_text(encoding="utf-8")
    assert "IS NOT WRITTEN" in printout
    assert "133.20 EUR" in printout and "137.62 SEK" in printout
    watchlist = Path("config/watchlist.yaml").read_text(encoding="utf-8")
    assert "# was 185" in watchlist and "was 102.66" in watchlist   # history kept (LIAB.ST's now behind its E117 comment)
    from vss.config import load_watchlist
    entries = {e.ticker: e for e in load_watchlist(Path("config/watchlist.yaml"))}
    assert entries["SAP.DE"].fv_base == 140.37 and entries["SAP.DE"].stop_price is None   # E87-nulled 2026-08-30, re-struck end to end; E91's divisor moved it to 140.37 the same evening
    # E117 + E120, 2026-09-19; 133.48 before. The stop was CLEARED with the
    # fill of 2026-09-21 -- it guarded a position that no longer exists.
    assert entries["LIAB.ST"].fv_base == 68.97 and entries["LIAB.ST"].stop_price is None
    # SOLD 2026-08-26 (E42); WATCH-PRICED -> WATCH-GATED 2026-09-20 (owner):
    # a bound, pre-E117 value on a superseded basis was carrying a live
    # buy line, and the tier predates the record it rests on.
    assert entries["SAP.DE"].status == "WATCH-GATED"
    # SOLD 2026-09-21, 121 shares at 120.70 (C4 / E42): the last holding is
    # closed and the watchlist carries no HELD name.
    assert entries["LIAB.ST"].status == "DROPPED"
    # HELD again from 2026-09-25, recorded 2026-10-05: CTSH, 3 shares, stop
    # re-derived at fill to 53.45, with the bull the HELD rule requires.
    # CRUS is owned too but stays DROPPED -- no strike, so no level.
    assert [e.ticker for e in entries.values() if e.status == "HELD"] == ["CTSH"]
    assert entries["CTSH"].stop_price == 53.45 and entries["CTSH"].fv_bull == 104.66
    assert entries["CRUS"].status == "DROPPED"


def test_item_5_the_tiers_are_re_entered_as_inputs_and_produce_no_mbp():
    """RULED A 2026-08-26: SAP.DE tier 1, LIAB.ST tier 2, carried from the
    pre-REVIEW-4 scoring with section 4.4 untouched. A tier without an
    fv_base is an INPUT waiting for a re-strike -- `compute_mbp` still
    returns None, so no buy price appears from it."""
    from vss.config import load_watchlist
    entries = {e.ticker: e for e in load_watchlist(Path("config/watchlist.yaml"))}
    assert entries["SAP.DE"].tier == 1 and entries["LIAB.ST"].tier == 2   # SAP.DE tier re-entered 2026-08-30 with the re-strike (E87-nulled earlier that day)
    # both records are linked by the owner now (E28 wired); the tiers
    # were inputs BEFORE that, and a tier alone still produces no mbp
    assert entries["SAP.DE"].fv_base == 140.37 and entries["LIAB.ST"].fv_base == 68.97   # LIAB.ST: E117 + E120, 2026-09-19 (133.48 before)
    assert RU.compute_mbp(None, 1) is None and RU.compute_mbp(None, 2) is None
    text = Path("config/watchlist.yaml").read_text(encoding="utf-8")
    assert text.count("carried from pre-REVIEW-4 scoring; 4.4 untouched by the review") == 2


def _growth_view(ticker: str) -> dict:
    """The three rates as the view file states them: base, bear, bull."""
    import re
    text = Path(f"reference/growth-views/{ticker}.md").read_text(encoding="utf-8")
    base = re.search(r"Base case FCF growth, 10 years: (\d+(?:\.\d+)?)%", text)
    bear = re.search(r"^Bear: (\d+(?:\.\d+)?)%", text, flags=re.M)
    bull = re.search(r"^Bull: (\d+(?:\.\d+)?)%", text, flags=re.M)
    assert base and bear and bull, ticker
    return dict(base=float(base.group(1)) / 100, bear=float(bear.group(1)) / 100,
                bull=float(bull.group(1)) / 100, text=text)


def test_item_6_both_held_names_carry_a_dated_pre_registered_growth_view():
    """RULED A 2026-08-26: SAP.DE 8 / 6 / 11, LIAB.ST 2 / 0 / 4, set by the
    owner, Lindab's bear and bull translated from the margin scenarios."""
    sap, liab = _growth_view("SAP.DE"), _growth_view("LIAB.ST")
    assert (sap["base"], sap["bear"], sap["bull"]) == (0.08, 0.06, 0.11)
    assert (liab["base"], liab["bear"], liab["bull"]) == (0.02, 0.0, 0.04)
    for view in (sap, liab):
        assert "Set by the owner, 2026-08-26" in view["text"]
        assert view["bear"] < view["base"] < view["bull"]
    import re
    flat = {k: re.sub(r"\s+", " ", v["text"]) for k, v in (("sap", sap), ("liab", liab))}
    assert "TRANSLATED from the earlier MARGIN scenarios" in flat["liab"]
    assert "bear 1.0%" in flat["liab"]         # what the first re-strike used
    assert "Nothing moves on g" in flat["sap"]


# =========================================================================
# BUILD 2, ITEM 10 -- the two held names re-struck on the TOOL PATH, again
# =========================================================================
#
# The printout is `reference/RESTRIKE-2026-08-26-b.md`; the two run records
# are `reference/run-records/<TICKER>-2026-08-26.json`. The numbers are
# pinned here so neither artefact can drift from the code that made it.


def _record(ticker):
    import json
    return json.loads(Path(f"reference/run-records/{ticker}-2026-08-26.json")
                      .read_text(encoding="utf-8"))


def test_build_2_sap_de_record_replays_to_139_48_and_says_what_it_stands_on():
    raw = _record("SAP.DE")
    assert R.replay(raw) == pytest.approx(139.48, abs=0.005)
    record = R.RunRecord.from_dict(raw)
    assert record.complete and record.basis == "TTM 2025-Q3+2025-Q4+2026-Q1+2026-Q2"
    assert record.fcf0() == pytest.approx(7_399_000_000.0)
    assert record.bridge.net_debt == pytest.approx(-869_000_000.0)    # net CASH
    assert record.shares.count == 1_175_000_000 and record.shares.as_of == date(2025, 12, 31)
    assert not record.dates.agree                                       # E41, declared
    hand = {i.name: i for i in record.inputs if i.entered_by == "hand"}
    assert set(hand) == {"capex_combined", "financial_liabilities_consolidated"}
    assert hand["capex_combined"].value == -735_000_000.0
    assert hand["financial_liabilities_consolidated"].value == 10_507_000_000.0
    assert record.bridge.items["pensions"] == 249_000_000.0
    assert record.growth.view_file == "reference/growth-views/SAP.DE.md"
    assert (record.growth.base, record.growth.bear, record.growth.bull) == (0.08, 0.06, 0.11)
    assert record.strike(0.06) == pytest.approx(120.27, abs=0.005)
    assert record.strike(0.11) == pytest.approx(174.30, abs=0.005)


def test_build_2_liab_st_record_replays_to_133_48_from_the_store_alone():
    raw = _record("LIAB.ST")
    assert R.replay(raw) == pytest.approx(133.48, abs=0.005)
    record = R.RunRecord.from_dict(raw)
    assert record.complete
    assert not any(i.entered_by == "hand" for i in record.inputs)      # no hand input at all
    assert record.fcf0() == 1050.0 and record.bridge.net_debt == 4536.0
    assert record.shares.count == 77.036 and record.sbc.amount == 0.0
    assert record.interest.net_interest_paid == 201.0
    assert (record.growth.base, record.growth.bear, record.growth.bull) == (0.02, 0.0, 0.04)
    assert record.strike(0.0) == pytest.approx(107.23, abs=0.005)
    assert record.strike(0.04) == pytest.approx(164.12, abs=0.005)


def test_build_2_the_delta_against_the_first_restrike_is_arithmetic_item_by_item():
    ev = V.equity_value_per_share
    # SAP.DE: 133.20 -> 139.07 (E41 window) -> 139.69 (E41 bridge) -> 139.48 (E35.1)
    assert ev(fcf0=9_156e6 - 739e6 - 1_331e6, growth=0.08, net_cash=386e6,
              shares=1_175e6) == pytest.approx(133.20, abs=0.005)
    assert ev(fcf0=9_465e6 - 735e6 - 1_331e6, growth=0.08, net_cash=386e6,
              shares=1_175e6) == pytest.approx(139.07, abs=0.005)
    assert ev(fcf0=9_465e6 - 735e6 - 1_331e6, growth=0.08,
              net_cash=10_511e6 + 1_114e6 - 10_507e6, shares=1_175e6) \
        == pytest.approx(139.69, abs=0.005)
    assert ev(fcf0=9_465e6 - 735e6 - 1_331e6, growth=0.08,
              net_cash=10_511e6 + 1_114e6 - 10_507e6 - 249e6, shares=1_175e6) \
        == pytest.approx(139.48, abs=0.005)
    # LIAB.ST: 137.62 -> 133.98 (E35.1) -> 133.48 (item 7's page reads), all
    # on the 77.036m the first re-strike actually divided by
    assert ev(fcf0=1050.0, growth=0.02, net_cash=-4217.0, shares=77.036) \
        == pytest.approx(137.62, abs=0.005)
    assert ev(fcf0=1050.0, growth=0.02, net_cash=-4497.0, shares=77.036) \
        == pytest.approx(133.98, abs=0.005)
    assert ev(fcf0=1050.0, growth=0.02, net_cash=-4536.0, shares=77.036) \
        == pytest.approx(133.48, abs=0.005)


def test_build_2_the_printout_exists_and_the_watchlist_is_STILL_not_written():
    printout = Path("reference/RESTRIKE-2026-08-26-b.md").read_text(encoding="utf-8")
    assert "IS NOT WRITTEN" in printout
    assert "139.48 EUR" in printout and "133.48 SEK" in printout
    assert "section 6.4, 'At FV_base, trim 25-50%; reassess': FIRES" in printout
    assert "C4, 'exit when even the bull case does not beat the index': FIRES" in printout
    assert "NOT a recommendation" in printout
    from vss.config import load_watchlist
    entries = {e.ticker: e for e in load_watchlist(Path("config/watchlist.yaml"))}
    # THE TOOL WROTE NOTHING. What the watchlist carries since is the
    # OWNER's: both records linked with the figures they replay to once E28
    # was wired (the commits after E42), SAP.DE's stop nulled on the C4
    # sale, LIAB.ST's stop 112 untouched.
    assert entries["SAP.DE"].fv_base == 140.37   # E87-nulled 2026-08-30, re-struck from the store, then E91 moved the divisor the same evening
    assert entries["SAP.DE"].run_record == "reference/run-records/SAP.DE-2026-08-30-e91.json"   # the -08-30 (E88 divisor) and -08-26 records stay on disk as history
    assert entries["LIAB.ST"].fv_base == 68.97   # E117 + E120, 2026-09-19 (133.48 before)
    # relinked 2026-08-30 to the re-strike under E65-E68 and E70, which
    # replays to the same 133.48; relinked again 2026-09-19 to the E117
    # record (E120's stand-in), 68.97; both earlier records stay on disk
    assert entries["LIAB.ST"].run_record == "reference/run-records/LIAB.ST-2026-09-19-e117.json"
    # SAP.DE's stop was nulled when the position was sold (2026-08-26);
    # LIAB.ST's 112 stood until ITS fill on 2026-09-21 and was cleared with
    # it. Neither name guards a position now.
    assert entries["SAP.DE"].stop_price is None and entries["LIAB.ST"].stop_price is None


def test_build_2_the_records_satisfy_item_9_once_linked(tmp_path):
    """What the owner's write would do: an entry that names the record and
    the figure it replays to PRINTS; one that names a different figure does
    not. Exercised on copies; config/watchlist.yaml is not touched."""
    from vss.config import WatchlistEntry
    from vss.runner import recorded_fair_value
    for ticker, currency, fv in (("SAP.DE", "EUR", 139.48), ("LIAB.ST", "SEK", 133.48)):
        path = f"reference/run-records/{ticker}-2026-08-26.json"
        good = WatchlistEntry(ticker=ticker, name=ticker, currency=currency,
                              status="HELD", fv_base=fv, run_record=path)
        assert recorded_fair_value(good, Path(".")) == (fv, None)
        stale = WatchlistEntry(ticker=ticker, name=ticker, currency=currency,
                               status="HELD", fv_base=fv + 5, run_record=path)
        printed, why = recorded_fair_value(stale, Path("."))
        assert printed is None and "replays to" in why
