"""The ranking key: operating profitability and earnings yield (E6 as amended by E43).

THIS IS THE ONLY PLACE IN THE TOOL WHERE AN ORDERING ARISES. Every other step
is a filter with a pass, a fail and a third state, and every other report says
in as many words that its output is an order and not a ranking. Here it is a
ranking, and it performs the 100:1 selection.

It is still not a recommendation. The output is REVIEW WORK: names that become
PIPELINE without an mbp and without an fv_base, after which the whole
FRAMEWORK section 5 chain is run by hand. A high rank means the name is worth
the hours.

    operating profitability = EBIT / total assets            (E43, 2026-08-26)
    EY                      = EBIT / enterprise value

Rank separately on each, sum the two ranks, sort ascending. No weighting, no
thresholds, no score.

E43 REPLACED THE QUALITY LEG'S NUMERATOR, AND THE REASON IS THE VENDOR'S
LINE. E6's numerator was ``Gross Profit``, and SCREENER-REVIEW-3 measured
it against the annual reports of the five names section 5 would have
received: it reconciled to a line of the report for NONE of them. The
vendor manufactures a gross profit for a by-nature filer -- net sales less
whatever it calls cost of revenue -- so AFRY's carried 15,817m of personnel
below the line and read 75.7% of total assets for an engineering
consultancy. Operating profit is a line every filer states, by nature or by
function, and E8 already measured which vendor label carries it. It is the
SAME figure the price leg divides, on the same E13 basis; the two legs now
share a numerator, and E43 says so rather than pretending the sum is two
independent readings. ``Gross Profit`` is read by NOTHING in this module;
an AST test holds that line as one holds it for ``ebitda``.

E6 REPLACED THE QUALITY LEG BEFORE THAT, AND THE REASON WAS THE DENOMINATOR.
E5 used Greenblatt's ``EBIT / (net working capital + net PP&E)``. That denominator is
a difference between large numbers, so it goes to zero for float-funded,
asset-light businesses, and for a given EBIT the ratio is monotone in
``1 / denominator``. Ranking on it was in part ranking on how small the
denominator was: measured on the 2026-08-21 run, the thirteen names whose
capital employed was less than half a year's EBIT held quality placings 1
through 13, without exception. Total assets is present for every company and
cannot go to zero, so the pole is gone and the question of which cash is
"excess" stops mattering. E5 is kept in FRAMEWORK-EDITS, marked SUPERSEDED.

Eight rules the code must not soften:

1. EBIT comes from an alias set ordered on MEANING, not on coverage:
   Total Operating Income As Reported -> Operating Income -> EBIT. Measured
   against the companies' own filings, the last of those three matches the
   as-filed operating income for 6 of 32 US names and the first for 30. The
   YEAR is settled before the label -- the newest year end any label reports,
   then meaning within it -- because the labels stop in different years and
   the oldest of them would otherwise carry a name to the staleness gate on a
   figure up to five years old. And two labels for that one year end whose
   ratio is a round power of a thousand are one figure in two units: the EBIT
   is then DATA MISSING, named, never guessed at from the other label.
   ``ebitda`` is NEVER a substitute for any of them: it adds back
   depreciation and amortisation, which flatters exactly the heaviest balance
   sheets. This module does not read that field at all.
2. An absent line is DATA MISSING, never zero. ASM.AS has no Long Term Debt
   line because it has no long-term debt; a bank presents no operating
   profit under any of the three labels because its accounts do not present
   the concept. Those are different facts and neither is zero.
3. The quality leg's two lines must come from the SAME period end: the EBIT
   window's end and the balance sheet AT that end (`stock_at`). Nothing else
   makes them agree, and ``newest_period`` cannot catch a disagreement: it is
   the max over every stored row, so a record whose ranked lines are a year
   apart still reads as OK. Differing periods are DATA MISSING, never a
   number.
4. Financial Services and Real Estate get NOT APPLICABLE on the quality leg,
   and so does any candidate whose total assets are not positive. They are
   ranked on earnings yield alone, in their OWN section, never interleaved and
   never given a synthesised quality placing.
5. A candidate whose OWN RANKED LINES are too old is EXCLUDED from the
   ranking, counted and named. BWY.L was ranked on an EBIT from 2024-07-31
   against an enterprise value from 2026-08-21 -- 751 days in one quotient --
   and until 2026-08-22 neither the CSV nor the report said so.
   THE AGE IS MEASURED ON THE ROWS THIS KEY ACTUALLY READS, not on
   ``newest_period``. That field is the MAX over every stored row, including
   rows no component touches, so it answers a different question: SHL.DE's
   gross profit, total assets and EBIT were ALL from 2024-09-30, 690 days
   before the run, and it read ``OK`` at rank 246 because Net PPE and
   Ordinary Shares Number carried 2025-09-30. COLO-B.CO is the same 690 days
   old and was excluded. Same age, opposite treatment, decided by a row no
   leg touches. Rule 3 already said ``newest_period`` cannot catch a
   disagreement between two ranked lines; it cannot catch their age either,
   and for the same reason.
6. A NEGATIVE operating profit is ranked, not excluded. It is a fact about
   a business that lost money on its operations, and it belongs at the
   bottom of the list -- the opposite of a non-positive denominator, which
   is a fact about the arithmetic.
7. Enterprise value is converted into the reporting currency at a recorded
   rate before the earnings yield is formed, because EBIT and EV do not share
   a currency for roughly one candidate in seven.
8. ENTERPRISE VALUE IS FORMED HERE, FROM FIGURES OF ONE DATE. The vendor's
   ``enterpriseValue`` is NOT read into the yield: SCREENER-REVIEW-3 (Part
   12) measured that between two fetches of one day, eleven hours apart,
   ``marketCap`` moved for 450 of 473 names and ``enterpriseValue`` for 3 --
   the field is a precomputed number refreshed on the vendor's cadence, and
   the price it embeds matched a close of 2026-06-16 for FGR.PA, the #1 name,
   against a settled close of 2026-08-26. Gate 1 selects names that fell
   recently, which is exactly the case where the embedded price is the
   pre-fall one and the yield is understated. So:

       implied shares   = vendor marketCap / vendor regularMarketPrice
                          (the count the vendor itself used, at the fetch)
       market cap       = implied shares x the SETTLED close of the run date
       enterprise value = market cap (in the reporting currency)
                          + totalDebt - totalCash

   ``totalDebt`` and ``totalCash`` come from the same quote summary, stated
   in the reporting currency, and are the vendor's latest balance sheet as
   of the fetch; both dates are written beside the figure. The vendor's own
   ``enterpriseValue`` travels as a MEMO column and decides nothing.

   The bound of L2 stays, on the parts: a company cannot hold more net cash
   (``totalCash - totalDebt``) than it holds ASSETS. It is not a threshold;
   it is what the arithmetic forbids. A name that fails it loses its YIELD,
   on missing data -- never on value.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from datetime import date
from typing import Mapping, Sequence

from .fundamentals import MAX_REPORT_AGE_DAYS
from .fx import FxTable, major_unit, minor_unit_divisor
from .prices import STATUS_STALE
from .universe import ON_MISSING, ON_VALUE, Merge, Tally

#: In order of MEANING, not of coverage (L3). E5 put the strict ``EBIT`` label
#: first on a coverage argument -- "14 of 15 US candidates carry it" -- and
#: nobody asked what the three labels mean. They are three different numbers:
#: of the 323 candidates carrying all three, only 10 carry the same figure
#: under all of them. Measured against the companies' own 10-K filings,
#: ``us-gaap:OperatingIncomeLoss``, over 32 US names in the ranked list:
#:
#:     Total Operating Income As Reported   30 of 32
#:     Operating Income                     19 of 32
#:     EBIT                                  6 of 32
#:
#: and ``EBIT`` is HIGHER than the as-filed line for 183 of 275 names, which
#: raises the earnings yield. Coverage does not disappear, it becomes the
#: fallback chain: over the 394 candidates of 2026-08-21 the set resolves to
#: the first label for 314 names, the second for 67 and the third for 4.
EBIT_ALIASES: tuple[str, ...] = (
    "Total Operating Income As Reported", "Operating Income", "EBIT",
)

#: A statement reported in thousands against one reported in units differs by
#: exactly this factor, or a power of it. Not an estimate of "how different is
#: too different": a unit slip multiplies ONE figure by a round power of a
#: thousand and leaves its digits alone.
UNIT_FACTOR = 1000.0

#: How close to a power of ``UNIT_FACTOR`` a ratio must be to be read as a
#: unit slip rather than as two different measurements. Stated rather than
#: tuned, and the data says the number does not matter: over all pairwise
#: alias ratios of the 394 candidates the answer is MONC.MI and nothing else
#: at every tolerance from 1e-9 to 1e-2. The gap is wide -- the second-largest
#: alias ratio in the whole set is 281.7x (IP: EBIT -2,817M against Operating
#: Income -10M), a real economic difference sitting a factor of 3.6 below the
#: boundary, and the median ratio is 1.083x with p90 at 1.784x.
UNIT_TOLERANCE = 0.01
NET_PPE_ALIASES: tuple[str, ...] = ("Net PPE", "Net Property Plant And Equipment")

#: The quality leg's denominator. NO alias set, deliberately: measured over
#: the 394 candidates of the 2026-08-21 run, every name presents it under
#: this exact label -- 394 of 394. The numerator is the price leg's EBIT
#: (E43): `EBIT_ALIASES` on the E13 basis, chosen by `choose_ebit`.
TOTAL_ASSETS_LINE = "Total Assets"

#: Sectors for which gross profit over total assets is COMPUTABLE but NOT
#: COMPARABLE: a bank's total assets are its loan book, a property owner's are
#: the portfolio at fair value, and gross profit is not the concept either set
#: of accounts presents. E6 kept this exemption from E3/E5 on that ground
#: alone -- the mechanical ground (a bank presents no classified balance
#: sheet) fell away with the current-asset lines. Measured when the exemption
#: was dropped as a test: not one of the 45 affected names reached the quality
#: leg's top 50, so including them would sort them last as a class on a ratio
#: that does not describe them.
QUALITY_EXEMPT_SECTORS: frozenset[str] = frozenset({"Financial Services", "Real Estate"})

STEP_RANK = "rank"
STEP_SHARE_CLASS = "share_class"

#: The currency share-class turnover is compared in. Arbitrary, and stated:
#: the comparison only needs ONE common unit, not a particular one.
TURNOVER_CURRENCY = "EUR"

#: Trailing window for the median daily turnover that decides which listing
#: of a company survives. Calendar days, matching floors.yaml's
#: median_daily_turnover window.
TURNOVER_WINDOW_DAYS = 90

#: The statement figures whose exact equality identifies one company reported
#: twice. Two share classes of one issuer file ONE set of accounts, so their
#: EBIT, revenue, net PP&E and total assets are the same number to the last
#: digit. Two different companies are not.
FINGERPRINT_LINES: tuple[tuple[str, ...], ...] = (
    EBIT_ALIASES,
    ("Total Revenue", "Operating Revenue"),
    NET_PPE_ALIASES,
    ("Total Assets",),
)

# Why a candidate has no quality leg. Reported, never merged into one bucket.
QUALITY_OK = "OK"
QUALITY_SECTOR = "sector exempt"
#: E46: the owner's list of investment companies, exempt on the quality leg
#: whatever the vendor's sector string says. Its own reason, counted apart
#: from the string exemption, because the two are decided by different
#: things -- a list the owner writes and a label the vendor returns.
QUALITY_INVESTMENT = "investment company (E46)"
QUALITY_NOT_MEANINGFUL = "denominator not positive"
QUALITY_MISSING = "input missing"
#: Not a fourth reason the QUALITY leg is absent -- a reason BOTH legs are.
#: Kept in the same vocabulary because the report counts them in one column.
QUALITY_STALE = "stale accounts"
#: The two lines came from different fiscal year-ends. NOT the same fact as a
#: missing line, and counted apart from it.
QUALITY_MIXED_PERIODS = "periods do not match"

#: E13's NOT MEANINGFUL: the figure is there and how long a period it
#: covers is not recorded, so there is no basis to rank it on. Counted
#: apart from an absent line and apart from a short history -- three
#: different facts, and only one of them is "we do not have the number".
QUALITY_BASIS_UNKNOWN = "period length not known"

#: How a withheld yield says WHY, so a reader and a test find it by the same
#: string rather than by two spellings of the same sentence.
EV_IMPOSSIBLE_NOTE = "enterprise value implies net cash"

# --- ONE PERIOD BASIS (FRAMEWORK-EDITS E13) -------------------------------
#
# THE KEY COMPARES FIGURES ACROSS COMPANIES, so every ranked figure must be
# struck on the same length of period. Nothing asked until 2026-08-24,
# because the vendor path stored annual statements and every ranked name
# was on one basis by construction. A hand-entered or appendix-read file
# need not be: config/manual/PNDORA.CO.yaml holds fourteen QUARTERS, and
# its quality leg read 19.9% where the vendor's annual figures read 87.0%
# -- same company, same ratio, a factor of four, neither number wrong
# (backlog B-8).
#
# E13 settles it. The basis is TRAILING TWELVE MONTHS:
#
#   FLOW lines  -- revenue, gross profit, EBIT, measured OVER a period --
#                  are SUMMED over the four most recent consecutive
#                  quarters. An annual figure already IS twelve months and
#                  is taken as it stands; nothing is summed that does not
#                  need to be.
#   STOCK lines -- total assets, net PP&E, measured AT an instant -- take
#                  the period end the flow's window ENDS on (K6): a flow to
#                  30 June is a ratio with total assets AT 30 June.
#
# SINCE 2026-08-26 THE VENDOR PATH FETCHES THE QUARTERS (build item 8), so
# E13 as written applies to it: four consecutive quarters where the vendor
# has them, and where it does not -- a half-yearly reporter, a hole in the
# quarterly endpoint (#1345), a NaN -- the ANNUAL figure is the fallback
# and the basis column says which, with the reason beside it. A missing
# quarter is DATA MISSING for the twelve-month basis and is never filled
# with a zero or with a year. A figure whose length is not recorded is NOT
# MEANINGFUL and is never ranked on an assumed basis.
#
# THE SUM LIVES HERE AND NOWHERE ELSE. It is written to no file, carries no
# page reference and never reaches section 5, whose figures stay exactly as
# filed in config/manual/<TICKER>.yaml. `vss/appendix.py` still derives
# nothing at all. E13 confines the exception to this module deliberately,
# and it must not leak out of it.

BASIS_ANNUAL = "annual"
#: Four consecutive quarters summed. Named for what it is, so a CSV row
#: cannot be mistaken for a vendor-computed trailing figure.
BASIS_TTM = "ttm-4q"

#: Quarters in a trailing twelve months. E13's own count, taken literally:
#: a HALF-YEARLY reporter has no quarters at all, so it has fewer than four
#: of them and is not ranked. Whether the rules should be restated in TIME
#: rather than in counts for such a reporter is the open question backlog
#: B-7 routed to FRAMEWORK-EDITS as B12, and generalising here would decide
#: it silently. A half-yearly name whose file carries a YYYY-FY period is
#: rankable today with no summing at all -- that period is twelve months.
TTM_QUARTERS = 4

#: What separates two consecutive quarter ends, in days. THIRTEEN WEEKS IS
#: 91 AND FILERS VARY BY A FEW, so contiguity is a window rather than an
#: equality -- the same bounds, for the same reason, that `vss/xbrl.py`
#: uses to decide whether a tagged duration is a quarter at all. A gap
#: outside it is a MISSING QUARTER, and four rows with a hole in them are
#: not a trailing twelve months.
QUARTER_MIN_DAYS = 80
QUARTER_MAX_DAYS = 100

#: Months in each period this basis knows how to use directly -- one place,
#: the store's own declaration.
from .fundamentals import ANNUAL_MONTHS, QUARTER_MONTHS  # noqa: E402


@dataclass(frozen=True)
class Flow:
    """One flow line, put on the basis the key ranks on -- or why it cannot be.

    ``end`` is the END of the window, which is also what the staleness gate
    measures on: a trailing twelve months is as old as the day it stops,
    not as old as its oldest component. Rule 5 asks the age question about
    the rows that were READ, and the window is what was read.
    """

    line: str
    value: float | None
    end: date | None
    basis: str | None
    periods: tuple[date, ...] = ()
    state: str = QUALITY_OK
    detail: str = ""

    @property
    def ok(self) -> bool:
        return self.state == QUALITY_OK and self.value is not None


def ttm_refusal(line: str, quarters: Sequence) -> str | None:
    """Why four consecutive quarters cannot be formed from ``quarters``
    (oldest first, values present), or None when they can.

    A hole is a hole: a quarter the vendor did not return, or returned as
    NaN, is absent from ``quarters`` and shows up as a jump between the
    neighbours it left. Nothing is filled in.
    """
    if not quarters:
        return f"no quarterly {line} from the vendor"
    window = quarters[-TTM_QUARTERS:]
    if len(window) < TTM_QUARTERS:
        return (f"{line} has {len(window)} quarter(s) at the end of its history; "
                f"a trailing twelve months needs {TTM_QUARTERS}")
    for earlier, later in zip(window, window[1:]):
        gap = (later.period_end - earlier.period_end).days
        if not QUARTER_MIN_DAYS <= gap <= QUARTER_MAX_DAYS:
            return (f"{line} jumps {gap} days from {earlier.period_end.isoformat()} "
                    f"to {later.period_end.isoformat()}: a quarter is missing, and "
                    f"four rows with a hole in them are not a trailing twelve months")
    return None


def flow_figure(record, line: str) -> Flow:
    """A flow line on ONE basis: four quarters summed, or annual as it stands.

    E13's basis is tried FIRST -- the four most recent consecutive quarters
    with a value in each -- and the ANNUAL figure is the fallback where the
    vendor has no such quarters (build item 8), with the reason carried in
    ``detail`` so the CSV says why a row is annual. An annual figure NEWER
    than the quarterly window is taken over the window: the newest twelve
    months the record holds, on the same footing E8 settles the year first.

    Never a fifth thing. A series of half-years, of months, or of periods
    whose length nobody recorded does not become a trailing twelve months
    by being added up -- it becomes a number about a window nobody named.
    """
    points = sorted(
        (p for p in getattr(record, "series", ()) or ()
         if p.line == line and p.value is not None),
        key=lambda p: p.period_end,
    )
    if not points:
        return Flow(line, None, None, None, state=QUALITY_MISSING,
                    detail=f"no {line} line")

    newest = points[-1]
    if newest.period_months is None:
        return Flow(line, None, newest.period_end, None,
                    state=QUALITY_BASIS_UNKNOWN,
                    detail=(f"{line} at {newest.period_end.isoformat()} does "
                            f"not record how long a period it covers"))

    quarters = [p for p in points if p.period_months == QUARTER_MONTHS]
    annual = [p for p in points if p.period_months == ANNUAL_MONTHS]
    refusal = ttm_refusal(line, quarters)
    if refusal is None:
        window = quarters[-TTM_QUARTERS:]
        end = window[-1].period_end
        if annual and annual[-1].period_end > end:
            # A newer twelve months exists as a filed year: take it, and
            # say what it was taken over.
            latest = annual[-1]
            return Flow(line, latest.value, latest.period_end, BASIS_ANNUAL,
                        (latest.period_end,),
                        detail=(f"annual {latest.period_end.isoformat()} is newer "
                                f"than the quarterly window ending {end.isoformat()}"))
        return Flow(line, sum(p.value for p in window), end, BASIS_TTM,
                    tuple(p.period_end for p in window))

    if annual:
        latest = annual[-1]
        return Flow(line, latest.value, latest.period_end, BASIS_ANNUAL,
                    (latest.period_end,), detail=f"annual fallback: {refusal}")

    other = [p for p in points
             if p.period_months not in (ANNUAL_MONTHS, QUARTER_MONTHS, None)]
    if other and not quarters:
        months = newest.period_months
        return Flow(line, None, newest.period_end, None, state=QUALITY_MISSING,
                    detail=(f"{line} is reported in {months}-month periods; "
                            f"the basis is four consecutive quarters or an "
                            f"annual figure, and neither is available"))
    return Flow(line, None, newest.period_end, None, state=QUALITY_MISSING,
                detail=refusal)


def stock_at(record, end: date | None, *aliases: str) -> tuple[date | None, float | None]:
    """(period, value) of a STOCK line AT the flow window's end, else the
    latest point -- which K6 then refuses if the two ends differ.

    A balance-sheet figure has no length: it is the position ON a date, and
    E13's twelve months does not apply to it. What applies is K6: the
    denominator must be measured on the day the numerator's window ends,
    and with the quarterly balance sheet stored (item 8) that day is
    usually there to be found. Every line is fetched independently, so
    nothing but this makes two figures in one ratio come from one date.
    """
    found = None
    if end is not None and hasattr(record, "at"):
        found = record.at(end, *aliases)
    if found is None:
        found = record.latest(*aliases)
    return found if found is not None else (None, None)


@dataclass(frozen=True)
class Inputs:
    """Everything one candidate's two components are built from."""

    ticker: str
    ebit: float | None
    ebit_label: str | None
    ebit_period: date | None
    #: Why there is no EBIT although the statement carried one. Set only by
    #: the unit check: two labels for one period that are the same figure in
    #: two units. "We have both and cannot tell which unit was meant" is a
    #: different fact from "the line is not there", and it is said so.
    ebit_unit_conflict: str | None
    total_assets: float | None
    total_assets_period: date | None
    #: THE VENDOR'S OWN enterprise value, a MEMO. Carried into the CSV so a
    #: reader can see what the quote summary said; read by no component.
    enterprise_value_quoted: float | None
    #: Market capitalisation AS THE VENDOR HAD IT AT THE FETCH, in the MAJOR
    #: unit of the quote currency. Divided by ``fetch_day_price`` it gives
    #: the share count the vendor used, which is the only use made of it.
    market_cap_quoted: float | None
    reporting_currency: str | None
    quote_currency: str | None
    sector: str | None
    #: The vendor's quote at the moment of the fetch (``regularMarketPrice``),
    #: in the unit the price series is quoted in -- pence for London. It is
    #: the price ``market_cap_quoted`` embeds, so the two together recover
    #: the vendor's share count. None on a store written before the field
    #: existed: then no count can be implied and the yield is withheld.
    fetch_day_price: float | None = None
    #: ``totalDebt`` and ``totalCash`` from the quote summary, in the
    #: REPORTING currency, as of the fetch (``net_debt_date``). Measured on
    #: six names against their filings: the latest interim balance sheet,
    #: lease liabilities in, to the unit (SCREENER-REVIEW-3 Part 4).
    total_debt: float | None = None
    total_cash: float | None = None
    net_debt_date: date | None = None
    #: The SETTLED close the run prices this name at, in the unit the
    #: series is quoted in, and its date. Supplied by the caller from the
    #: filter-1 candidate row: the ranking never reads a price series.
    settled_close: float | None = None
    settled_close_date: date | None = None
    #: The record's own fetch status. STALE means the figures arrived but the
    #: newest reported period is older than fundamentals.MAX_REPORT_AGE_DAYS.
    status: str | None = None
    #: fundamentals.py's own sentence, carried rather than reconstructed, so
    #: the report says the same thing the fetch said.
    stale_detail: str | None = None
    #: Which path supplied the record: the quote vendor, or a hand-entered
    #: file (vss/manual.py). Carried, never used to decide anything -- the
    #: key ranks on the figures, and the origin is how the CSV says where
    #: they came from.
    origin: str = "yfinance"
    #: THE PERIOD BASIS EVERY FLOW FIGURE ABOVE WAS STRUCK ON (E13):
    #: "annual" when the statements are already twelve months, "ttm" when
    #: four consecutive quarters were summed, None when neither was
    #: possible. A CSV that does not say this cannot be read: a quarter and
    #: a year in one ordering differ by a factor of four (backlog B-8).
    basis: str | None = None
    #: For a "ttm" row, the four period ends that were summed. Empty
    #: otherwise. This is the audit trail for a figure no filing states.
    basis_periods: tuple[date, ...] = ()
    #: Why a leg has no basis, in the words E13 uses. Reported, never
    #: merged with an absent line.
    basis_note: str = ""
    #: The EBIT leg's OWN reason, kept apart from the quality leg's. The
    #: yield's note must be about the yield: a bank presenting neither line
    #: would otherwise have its missing gross profit -- a fact about the
    #: OTHER leg, which is sector-exempt anyway -- reported beside its
    #: missing EBIT.
    ebit_note: str = ""
    #: The EBIT choice's own state, so `score` can tell E13's NOT MEANINGFUL
    #: (length unrecorded) from an absent line without re-deriving it. Both
    #: legs read this numerator (E43).
    ebit_state: str = QUALITY_OK

    @property
    def stale(self) -> bool:
        return self.status == STATUS_STALE

    @property
    def quality_periods_agree(self) -> bool | None:
        """Does the EBIT window END where the stock line was measured?

        On an annual record this is the question it has always been -- do
        the two lines come from ONE fiscal year-end -- because the window
        IS that year. On a trailing twelve months it is the same question
        about the window's end: an operating profit for the year to 30 June
        is a ratio with total assets AT 30 June, and with nothing else. K6's
        finding, unchanged; only what "the period" means has widened.

        None when either is absent -- that is a different question, asked
        first. ``TickerFundamentals.newest_period`` cannot answer this: it is
        the MAX over every stored row, so a record whose ranked lines are a
        year apart still reports the newer date and still reads as OK. SHL.DE
        on the 2026-08-21 run was exactly that.
        """
        if self.ebit_period is None or self.total_assets_period is None:
            return None
        return self.ebit_period == self.total_assets_period


@dataclass(frozen=True)
class Scored:
    ticker: str
    inputs: Inputs
    operating_profitability: float | None
    quality_state: str
    earnings_yield: float | None
    enterprise_value: float | None      # in the REPORTING currency, BUILT here
    fx_pair: str | None
    fx_rate: float | None
    note: str = ""
    #: The parts the enterprise value was built from (rule 8), so the CSV
    #: prints them beside the ratio rather than the ratio alone.
    implied_shares: float | None = None
    #: implied shares x the settled close, MAJOR unit of the quote currency.
    market_cap_settled: float | None = None


@dataclass(frozen=True)
class Ranked:
    scored: Scored
    quality_rank: int | None
    ey_rank: int
    combined: int | None

    @property
    def ticker(self) -> str:
        return self.scored.ticker


@dataclass
class RankingResult:
    #: Two-legged, ranked on the sum of both placings.
    main: list[Ranked] = field(default_factory=list)
    #: One-legged, ranked on earnings yield alone. Its own section, never
    #: interleaved -- E5(a), carried into E6 unchanged.
    yield_only: list[Ranked] = field(default_factory=list)
    #: Neither component computable.
    unrankable: list[Scored] = field(default_factory=list)
    #: Excluded because the accounts are too old to divide into a price from
    #: today. Its own list, never folded into ``unrankable``: the figures were
    #: there, and "we chose not to use them" is a different fact from "they
    #: were not there".
    stale: list[Scored] = field(default_factory=list)
    scored: dict[str, Scored] = field(default_factory=dict)
    tally: Tally = field(default_factory=lambda: Tally(STEP_RANK))
    fx: FxTable | None = None
    #: Filled by the caller when share classes were collapsed first.
    share_class_merges: list = field(default_factory=list)
    share_class_tally: Tally | None = None

    def reason_counts(self) -> dict[str, int]:
        counts: dict[str, int] = {}
        for item in self.scored.values():
            counts[item.quality_state] = counts.get(item.quality_state, 0) + 1
        return counts


# --- inputs ---------------------------------------------------------------


def is_unit_slip(first: float, second: float,
                 *, tolerance: float = UNIT_TOLERANCE) -> bool:
    """Are these the same figure in two units? (L3)

    A statement reported in thousands against one reported in units differs by
    a round power of a thousand and by nothing else, so this asks the exact
    question rather than "are these very different". MONC.MI carries
    ``Operating Income`` 913,356,000 and ``Total Operating Income As Reported``
    913,356 for the SAME year end: identical digits, ratio 1000.000.

    Measured over every pairwise alias ratio of the 394 candidates of
    2026-08-21, this is true of MONC.MI and of nothing else, at every
    tolerance from 1e-9 to 1e-2.
    """
    if not first or not second:
        return False
    ratio = abs(first / second)
    if ratio <= 0:
        return False
    power = round(math.log(ratio, UNIT_FACTOR))
    if power == 0:
        return False
    target = UNIT_FACTOR ** power
    return abs(ratio - target) <= tolerance * target


@dataclass(frozen=True)
class EbitChoice:
    """The operating profit on the ranking basis, or why there is none."""

    value: float | None
    label: str | None
    period: date | None
    unit_conflict: str | None
    basis: str | None
    periods: tuple[date, ...]
    state: str
    detail: str


def choose_ebit(record) -> EbitChoice:
    """The operating profit on ONE basis, or why not.

    TWO rules, and the second is not in the review that asked for the first.

    1. THE LABEL IS CHOSEN ON MEANING, per ``EBIT_ALIASES``.

    2. THE PERIOD IS CHOSEN FIRST. ``latest()`` answers per label, and the
       labels stop in different years: 9 of the 394 candidates carry
       ``Total Operating Income As Reported`` for a year end between 2021 and
       2024 while both other labels carry 2025. Taking the first label present
       at whatever year IT ends in would hand those names a figure up to five
       years old with a current one sitting beside it in the same store --
       and, since the staleness gate now measures the rows the key actually
       reads (L4), EIGHT of them would be excluded as stale. One of the eight
       is NVR, place 20. So the newest year end any label reports is settled
       first, and meaning decides within it.

    4. AND THE WHOLE THING IS ON ONE PERIOD BASIS (E13). Each alias is put
       on trailing twelve months FIRST -- summed from four consecutive
       quarters, or taken as it stands when it is already annual -- and only
       then compared with the others. An alias that cannot be put on the
       basis does not win by being newest.

    3. AND THEN THE UNIT IS CHECKED. Two labels for that one year end whose
       ratio is a round power of a thousand are one figure in two units, and
       which unit the statement meant cannot be read off anything stored. The
       EBIT is DATA MISSING, named -- never a number, and never the other
       label picked on a guess. This is K6's shape: *we have both and they do
       not belong together* is a different fact from *one of them is absent*.
    """
    found: dict[str, Flow] = {}
    refused: dict[str, Flow] = {}
    for alias in EBIT_ALIASES:
        flow = flow_figure(record, alias)
        if flow.ok:
            found[alias] = flow
        elif flow.state != QUALITY_MISSING or flow.end is not None:
            refused[alias] = flow
    if not found:
        # The line may be ABSENT, or present and impossible to put on one
        # basis. Those are different facts and the second one has a reason
        # worth carrying: E13's INPUT MISSING and NOT MEANINGFUL both land
        # here, and a reader must be able to tell which.
        if refused:
            worst = max(refused.values(), key=lambda f: f.end or date.min)
            return EbitChoice(None, None, worst.end, None, None, (),
                              worst.state, worst.detail)
        # The plain absence, in the words it has always used. A REASON is
        # only added where there is one beyond "the line is not there".
        return EbitChoice(None, None, None, None, None, (), QUALITY_MISSING, "")

    # THE WINDOW END IS SETTLED FIRST, then meaning within it -- unchanged
    # from L3, and now measured on the end of the twelve months rather than
    # on a year end, which for an annual figure is the same date.
    newest = max(flow.end for flow in found.values())
    at_newest = {alias: flow for alias, flow in found.items()
                 if flow.end == newest}
    label = next(alias for alias in EBIT_ALIASES if alias in at_newest)
    chosen = at_newest[label]

    for other, other_flow in at_newest.items():
        if other == label or not is_unit_slip(chosen.value, other_flow.value):
            continue
        return EbitChoice(
            None, None, newest, (
                f"{label} {chosen.value:,.0f} and {other} "
                f"{other_flow.value:,.0f} for {newest.isoformat()} are one "
                f"figure in two units"), None, (), QUALITY_MISSING, "")
    # The chosen flow's own note travels: on an annual fallback it says why
    # the four quarters could not be formed (item 8).
    return EbitChoice(chosen.value, label, newest, None, chosen.basis,
                      chosen.periods, QUALITY_OK, chosen.detail)


def extract_inputs(ticker: str, record, *,
                   close: tuple[date, float] | None = None,
                   fetched: date | None = None) -> Inputs:
    """Pull one candidate's raw figures. Absent means None, never zero.

    ``close`` is ``(date, settled close)`` from the filter-1 candidate row,
    in the unit the series is quoted in; ``fetched`` is the date of the
    fundamentals fetch, which is the date ``totalDebt`` and ``totalCash``
    carry. Neither is read off the record: the record holds what the
    vendor said at the fetch, and the price the yield is struck on is the
    run's, not the vendor's (rule 8).
    """
    close_date, close_value = close if close is not None else (None, None)
    if record is None:
        return Inputs(
            ticker=ticker, ebit=None, ebit_label=None, ebit_period=None,
            ebit_unit_conflict=None,
            total_assets=None, total_assets_period=None,
            enterprise_value_quoted=None, market_cap_quoted=None,
            reporting_currency=None, quote_currency=None, sector=None,
            origin="none", basis=None,
            settled_close=close_value, settled_close_date=close_date,
            net_debt_date=fetched,
        )

    ebit = choose_ebit(record)

    # FLOW through the basis, STOCK at the window's end. The quality leg
    # divides one by the other (E43: the same EBIT the price leg divides),
    # which is exactly the ratio B-8 found reading four times low when the
    # flow was a quarter and the stock a balance sheet.
    total_assets_period, total_assets = stock_at(record, ebit.period, TOTAL_ASSETS_LINE)

    return Inputs(
        ticker=ticker,
        ebit=ebit.value,
        ebit_label=ebit.label,
        ebit_period=ebit.period,
        ebit_unit_conflict=ebit.unit_conflict,
        total_assets=total_assets,
        total_assets_period=total_assets_period,
        enterprise_value_quoted=record.value("enterpriseValue"),
        market_cap_quoted=record.value("marketCap"),
        reporting_currency=record.text("financialCurrency"),
        quote_currency=record.text("currency"),
        sector=record.text("sector"),
        fetch_day_price=record.value("regularMarketPrice"),
        total_debt=record.value("totalDebt"),
        total_cash=record.value("totalCash"),
        net_debt_date=fetched,
        settled_close=close_value,
        settled_close_date=close_date,
        status=getattr(record, "status", None),
        stale_detail=getattr(record, "error", None),
        origin=getattr(record, "origin", "yfinance"),
        basis=ebit.basis,
        basis_periods=ebit.periods if ebit.basis == BASIS_TTM else (),
        basis_note=ebit.detail,
        ebit_note=ebit.detail,
        ebit_state=ebit.state,
    )


def currency_pairs(inputs: Sequence[Inputs]) -> list[tuple[str | None, str | None]]:
    """The conversions a run needs: quote currency to reporting currency."""
    return [(i.quote_currency, i.reporting_currency) for i in inputs]


# --- one company, two listings --------------------------------------------
#
# ERIC-A.ST and ERIC-B.ST are one business. Ranked separately they took slots
# 5 and 6, and phase 6 would have proposed both for the same review.
#
# The IDENTITY test is measured, never guessed from the ticker string: two
# share classes of one issuer file ONE set of accounts, so their EBIT,
# revenue, net PP&E and total assets agree exactly, along with the reporting
# currency and the sector. Two different companies do not agree on four float
# figures at once -- which is why this test separates EQT (US gas) from EQT.ST
# (Swedish private equity) although a name match would not.
#
# The SURVIVOR is the most traded listing, measured as median daily turnover
# out of the stored price series. THE COMPARISON IS MADE IN THE GROUP'S OWN
# CURRENCY WHEN IT HAS ONE, and an exchange rate is asked for only when a
# group spans two -- which on 2026-08-21 is two of the eight groups. Both
# Stockholm lines of one Swedish company are already in one unit, and turning
# two SEK figures into two EUR figures cannot change which is larger (L6).


def company_fingerprint(record) -> tuple | None:
    """A measured identity for one issuer, or None if it cannot be measured.

    Every line must be present. A fingerprint built from partial data would
    match on absence, which is the one thing an absent line must never do.
    """
    if record is None:
        return None
    figures = []
    for aliases in FINGERPRINT_LINES:
        found = record.latest(*aliases)
        if found is None:
            return None
        figures.append((found[0].isoformat(), found[1]))
    currency = record.text("financialCurrency")
    sector = record.text("sector")
    if not currency:
        return None
    return (currency, sector, tuple(figures))


def median_turnover_major(
    frame,
    as_of,
    quote_currency: str | None,
    *,
    window_days: int = TURNOVER_WINDOW_DAYS,
) -> float | None:
    """Median daily close x volume over the trailing window, NO conversion.

    Returned in the MAJOR unit of the quote currency. The price series is
    quoted in the MINOR unit -- pence for London -- so it is divided first.
    Skipping that would make a London listing look a hundred times the size
    of a Stockholm one and hand it every contest it entered.

    No exchange rate is applied here, because a rate is only needed when a
    contest crosses two currencies, and most of them do not (L6).
    """
    from datetime import timedelta

    import pandas as pd

    from .metrics import index_dates

    if frame is None or len(frame) == 0:
        return None
    if "Close" not in frame.columns or "Volume" not in frame.columns:
        return None
    cutoff = as_of - timedelta(days=window_days)
    values = [
        float(close) * float(volume)
        for close, volume, day in zip(
            frame["Close"].to_numpy(), frame["Volume"].to_numpy(), index_dates(frame.index)
        )
        if cutoff < day <= as_of and pd.notna(close) and pd.notna(volume)
    ]
    if not values:
        return None
    values.sort()
    middle = len(values) // 2
    median = (values[middle] if len(values) % 2
              else (values[middle - 1] + values[middle]) / 2)
    return median / minor_unit_divisor(quote_currency)


def median_turnover(
    frame,
    as_of,
    quote_currency: str | None,
    fx: FxTable,
    *,
    window_days: int = TURNOVER_WINDOW_DAYS,
    target: str = TURNOVER_CURRENCY,
) -> float | None:
    """The same figure converted into ``target``. None if the rate is absent."""
    major = median_turnover_major(frame, as_of, quote_currency,
                                  window_days=window_days)
    if major is None:
        return None
    rate = fx.get(major_unit(quote_currency), target)
    if rate is None:
        return None
    return rate.convert(major)


def _group_turnover(
    members: Sequence,
    turnover_major: Mapping[str, float | None],
    quote_currency: Mapping[str, str | None],
    fx: FxTable,
) -> tuple[list[tuple[float | None, object]], str, str]:
    """(measured, basis, unit) for ONE company's listings.

    THE RATE IS ONLY FETCHED FOR WHAT NEEDS IT (L6). The contest is inside a
    group, and most groups are already in one currency: on 2026-08-21 six of
    the eight are two Stockholm lines of one Swedish company. Converting two
    SEK figures into two EUR figures cannot change which is larger, so
    requiring a rate there made six computable comparisons fail whenever one
    Swedish rate happened to be missing -- and the fallback that then took
    over has a known direction.
    """
    values = [turnover_major.get(c.ticker) for c in members]
    if any(value is None for value in values):
        return [(None, c) for c in members], \
            "no turnover for every listing -- first by ticker", ""

    units = {major_unit(quote_currency.get(c.ticker)) for c in members}
    if len(units) == 1:
        unit = next(iter(units)) or ""
        return (list(zip(values, members)),
                f"highest median daily turnover ({unit})", unit)

    converted = []
    for value, member in zip(values, members):
        rate = fx.get(quote_currency.get(member.ticker), TURNOVER_CURRENCY)
        converted.append((None if rate is None else rate.convert(value), member))
    if any(value is None for value, _ in converted):
        return [(None, c) for c in members], \
            "no turnover for every listing -- first by ticker", ""
    return (converted,
            f"highest median daily turnover ({TURNOVER_CURRENCY})",
            TURNOVER_CURRENCY)


def collapse_share_classes(
    candidates: Sequence,
    fundamentals: Mapping,
    turnover_major: Mapping[str, float | None],
    quote_currency: Mapping[str, str | None],
    fx: FxTable,
) -> tuple[list, list[Merge], Tally]:
    """One row per company. The most traded listing survives.

    Reported in the same shape as the phase 1 dedup layer: what was kept, what
    was folded in, and on what basis the winner was chosen.
    """
    tally = Tally(STEP_SHARE_CLASS, count_in=len(candidates))
    groups: dict[tuple, list] = {}
    ungrouped: list = []
    for candidate in candidates:
        key = company_fingerprint(fundamentals.get(candidate.ticker))
        if key is None:
            ungrouped.append(candidate)
            continue
        groups.setdefault(key, []).append(candidate)

    kept, merges = list(ungrouped), []
    for key, members in groups.items():
        if len(members) == 1:
            kept.append(members[0])
            continue
        measured, basis, unit = _group_turnover(
            members, turnover_major, quote_currency, fx)
        if all(value is not None for value, _ in measured):
            measured.sort(key=lambda pair: (-pair[0], pair[1].ticker))
        else:
            # Deterministic, and SAID to be a fallback: a report must never
            # imply a liquidity judgement that was not made. It also has a
            # KNOWN DIRECTION -- for a Nordic A/B pair the A line is almost
            # always the illiquid voting class and sorts first -- which is why
            # the branch above exists to keep it from firing on a comparison
            # that needed no rate at all.
            measured.sort(key=lambda pair: pair[1].ticker)
        winner = measured[0][1]
        kept.append(winner)
        for value, loser in measured[1:]:
            detail = ""
            if measured[0][0] is not None and value is not None:
                detail = (f"{measured[0][0]:,.0f} vs {value:,.0f} "
                          f"{unit}/day")
            merges.append(
                Merge(kept=winner.ticker, dropped=loser.ticker, on="share_class",
                      basis=basis, detail=detail,
                      kept_source=winner.marknad, dropped_source=loser.marknad)
            )
            tally.reject(ON_VALUE, "same company, less traded listing")

    kept.sort(key=lambda c: c.ticker)
    tally.count_out = len(kept)
    return kept, merges, tally


# --- components -----------------------------------------------------------


@dataclass(frozen=True)
class EvParts:
    """The enterprise value the yield divides by, and what it was built from.

    Every field is None when ``note`` says why the value could not be
    formed. ``market_cap_settled`` is in the MAJOR unit of the quote
    currency; ``enterprise_value`` is in the REPORTING currency, the unit
    EBIT, ``totalDebt`` and ``totalCash`` are stated in.
    """

    implied_shares: float | None
    market_cap_settled: float | None
    enterprise_value: float | None
    note: str | None


def enterprise_value_parts(inputs: Inputs, rate) -> EvParts:
    """Rule 8: enterprise value from ONE date, never the vendor's field.

        implied shares   = marketCap / regularMarketPrice     (both at the fetch)
        market cap       = implied shares x settled close     (the run date)
        enterprise value = rate(market cap) + totalDebt - totalCash

    The share count is the vendor's own -- recovered, not looked up, so it
    is exactly the count the vendor priced. For FGR.PA that is every issued
    share including treasury, 98.0m against 95.1m outstanding
    (SCREENER-REVIEW-3 Part 4); the count is then wrong in the same way
    the vendor's was, and CONSISTENTLY so, which a hand-picked count from
    the report would not be. What changes is the DATE of the price on it.

    THE CASE. FGR.PA on 2026-08-26: vendor enterpriseValue 22,575m EUR,
    which is 129.29 EUR x 98.0m shares + 15,775m debt - 5,870m cash -- and
    129.29 is the close of 2026-06-16, to 0.05%. The settled close was
    117.50, so the same parts give 21,420m and a yield of 11.9% rather than
    11.3%. Seventeen of the twenty head places move when every name is put
    on its own settled close (Part 12.3).

    Minor units: the price series and ``regularMarketPrice`` are quoted in
    pence for London; ``marketCap`` is in pounds. Both prices are divided
    to the major unit before the count is implied and the cap is re-struck.
    """
    quote = inputs.quote_currency
    if inputs.market_cap_quoted is None:
        return EvParts(None, None, None, "no market cap")
    if inputs.fetch_day_price is None or inputs.fetch_day_price <= 0:
        return EvParts(None, None, None,
                       "no fetch-day quote to imply the vendor's share count "
                       "(regularMarketPrice absent)")
    if inputs.settled_close is None or inputs.settled_close <= 0:
        return EvParts(None, None, None, "no settled close to price the shares at")
    if rate is None:
        # Never fall back to parity: a missing rate treated as 1.0 is an error
        # the size of the exchange rate itself.
        return EvParts(None, None, None,
                       f"no fx rate {major_unit(quote)}->"
                       f"{major_unit(inputs.reporting_currency)}")
    if inputs.total_debt is None or inputs.total_cash is None:
        return EvParts(None, None, None,
                       "no total debt or total cash in the quote summary")
    divisor = minor_unit_divisor(quote)
    implied_shares = inputs.market_cap_quoted / (inputs.fetch_day_price / divisor)
    market_cap_settled = implied_shares * (inputs.settled_close / divisor)
    enterprise_value = (rate.convert(market_cap_settled)
                        + inputs.total_debt - inputs.total_cash)
    return EvParts(implied_shares, market_cap_settled, enterprise_value, None)


def implied_net_cash_note(inputs: Inputs, rate=None) -> str | None:
    """Is the net cash the enterprise value is built from arithmetically possible?

    Enterprise value is market capitalisation plus net debt, so the net
    cash inside it is

        net cash = totalCash - totalDebt

    and a company cannot hold more net cash than it holds ASSETS. That is not
    a threshold, a tolerance or a judgement about how much cash is plausible:
    it is the one comparison the arithmetic itself forbids, and the bound is
    generous by construction -- net cash equal to the entire balance sheet
    already passes.

    THE CASE THAT FOUND IT (L2). LISP.SW, rank 14 of the 2026-08-21 run and
    the highest earnings yield in the whole ranked list, carried a VENDOR
    ``enterpriseValue`` of 3,539,840,512 CHF against a market cap of
    21,179,160,576 -- 17.6bn CHF of implied net cash against 9.1bn CHF of
    total assets, 1.9 times the balance sheet. Recomputed from the parts the
    enterprise value was 22,614,660,640 and the yield 4.3% rather than 27.6%.
    The error was sixfold and it pointed ONE WAY: too low an enterprise
    value makes a name look cheap and floats it up the list.

    Rule 8 now builds the enterprise value from those same parts, so the
    vendor's field cannot smuggle an impossible figure in. What the bound
    guards against now is the parts themselves -- a ``totalCash`` the quote
    summary got wrong -- and it is kept because the direction of the error
    it catches has not changed. ``totalCash``, ``totalDebt`` and total
    assets are all in the REPORTING currency, so no rate is applied; the
    ``rate`` parameter is accepted for the callers that pass one and unused.

    Returns the sentence to withhold the yield with, or None when the figure
    is possible or cannot be judged.
    """
    if inputs.total_cash is None or inputs.total_debt is None:
        return None
    if inputs.total_assets is None or inputs.total_assets <= 0:
        # No bound to check against. An absent figure does not convict and
        # does not acquit -- it means the question was not asked.
        return None
    net_cash = inputs.total_cash - inputs.total_debt
    if net_cash <= inputs.total_assets:
        return None
    currency = major_unit(inputs.reporting_currency) or ""
    return (
        f"{EV_IMPOSSIBLE_NOTE} {net_cash:,.0f} {currency} against "
        f"total assets {inputs.total_assets:,.0f} {currency} "
        f"({net_cash / inputs.total_assets:.1f}x) -- not possible"
    ).strip()


def stale_note(as_of: date, periods: Sequence[date],
               *, max_age_days: int = MAX_REPORT_AGE_DAYS) -> str | None:
    """Are the rows THIS candidate was actually scored on too old? (L4)

    ``periods`` is the set of fiscal year-ends that fed a component that
    COMPUTED -- nothing else. Measuring anything wider is exactly what was
    wrong before: ``fundamentals.newest_period`` is the MAX over every stored
    row, so a name whose whole ranking key is a year older than its Net PPE
    line still read ``OK``. SHL.DE did that at 690 days while COLO-B.CO was
    excluded at the same 690 days.

    Measuring anything wider would also swallow K6. AUTO.L's gross profit is
    from 2024-03-31 and its total assets from 2026-03-31; that is
    ``periods do not match`` -- a statement about two lines that do not belong
    together -- and neither line fed anything, so neither is counted here. If
    the older one were, the name would be reported as stale and K6's finding
    would disappear behind this one.
    """
    if not periods:
        return None
    oldest = min(periods)
    age = (as_of - oldest).days
    if age <= max_age_days:
        return None
    return (f"the lines this key reads are from {oldest.isoformat()}, "
            f"{age} days before {as_of.isoformat()}")


def score(inputs: Inputs, fx: FxTable, as_of: date,
          investment_companies: frozenset[str] = frozenset()) -> Scored:
    """Both components for one candidate, with every gap named.

    ``investment_companies`` is E46's list: a ticker in it has no quality
    leg, whatever its sector string, and lands in the yield-only section.

    TWO staleness questions are asked, and they are not the same one. The
    record's own fetch-time flag says every row it holds is old; the gate at
    the bottom says the rows THIS KEY READ are old, which the flag cannot
    answer because it is a max over rows no leg touches. The first is asked
    first because a flagged record's legs would otherwise compute out of
    accounts up to two years older than the price they are divided into. The
    second is asked last, because the only way to know which rows were used is
    to use them.
    """
    if inputs.stale:
        return Scored(
            ticker=inputs.ticker, inputs=inputs, operating_profitability=None,
            quality_state=QUALITY_STALE, earnings_yield=None,
            enterprise_value=None, fx_pair=None, fx_rate=None,
            note=inputs.stale_detail or "newest reported period older than the limit",
        )

    # --- quality: operating profitability (E43)
    operating_profitability = None
    if inputs.ticker in investment_companies:
        # E46: the list decides, before the string is consulted.
        quality_state = QUALITY_INVESTMENT
    elif inputs.sector and inputs.sector in QUALITY_EXEMPT_SECTORS:
        quality_state = QUALITY_SECTOR
    elif inputs.ebit_state == QUALITY_BASIS_UNKNOWN:
        # E13's NOT MEANINGFUL. The figure is there; how long a period it
        # covers is not, and a ratio struck on an assumed basis is a number
        # about a window nobody named. Counted apart from an absent line.
        quality_state = QUALITY_BASIS_UNKNOWN
    elif inputs.ebit is None or inputs.total_assets is None:
        quality_state = QUALITY_MISSING
    elif not inputs.quality_periods_agree:
        # Two fiscal year-ends in one quotient is not a ratio of anything.
        # DATA MISSING, not a number -- and counted apart from an absent line,
        # because "we have both and they do not belong together" is a
        # different fact from "one of them is not there" (K6).
        quality_state = QUALITY_MIXED_PERIODS
    elif inputs.total_assets <= 0:
        # Not clamped, not floored, not sign-flipped -- E5(c), carried into
        # E6. Total assets did not go non-positive for a single one of the 394
        # candidates measured, which is the whole reason this denominator
        # replaced the old one; the state is kept because a balance sheet that
        # reported it would be telling us something we cannot rank.
        quality_state = QUALITY_NOT_MEANINGFUL
    else:
        # A NEGATIVE operating profit passes through as a negative ratio and
        # ranks last. An operating loss is a fact about the business, not
        # about the arithmetic, and the one thing that must not happen to it
        # is being confused with a missing line.
        quality_state = QUALITY_OK
        operating_profitability = inputs.ebit / inputs.total_assets

    # --- earnings yield
    earnings_yield = enterprise_value = None
    fx_pair = fx_rate = None
    implied_shares = market_cap_settled = None
    note = ""
    rate = fx.get(inputs.quote_currency, inputs.reporting_currency)
    parts = enterprise_value_parts(inputs, rate)
    if parts.note is not None:
        note = parts.note
    elif (impossible := implied_net_cash_note(inputs)) is not None:
        # The figure is kept so the impossible number is in the CSV rather
        # than merely alleged in a note; only the yield is withheld. A name
        # landing here is rejected on MISSING data -- the yield could not be
        # measured -- and never on value: nothing here judges the business
        # (L2).
        fx_pair, fx_rate = rate.pair, rate.value
        implied_shares, market_cap_settled = parts.implied_shares, parts.market_cap_settled
        enterprise_value = parts.enterprise_value
        note = impossible
    elif inputs.ebit is None:
        note = (inputs.ebit_unit_conflict or inputs.ebit_note or "no EBIT")
    else:
        fx_pair, fx_rate = rate.pair, rate.value
        implied_shares, market_cap_settled = parts.implied_shares, parts.market_cap_settled
        enterprise_value = parts.enterprise_value
        if enterprise_value > 0:
            earnings_yield = inputs.ebit / enterprise_value
        else:
            note = "enterprise value not positive"

    # --- staleness, measured on the rows that were actually read
    #
    # A period counts only where the component it feeds COMPUTED. The quality
    # leg's two dates are ignored for a sector-exempt name (that leg was never
    # evaluated) and for a name whose two dates disagree (that is K6's finding
    # about the lines, not a statement about their age). EBIT's date counts
    # only where a yield was formed from it.
    read_periods: list[date] = []
    if quality_state == QUALITY_OK:
        read_periods += [p for p in (inputs.ebit_period,
                                     inputs.total_assets_period) if p is not None]
    if earnings_yield is not None and inputs.ebit_period is not None:
        read_periods.append(inputs.ebit_period)

    too_old = stale_note(as_of, read_periods)
    if too_old is not None:
        # Excluded whole. Not a leg withheld: the accounts these figures came
        # from are too old to divide into a price from today, and that is true
        # of both legs at once.
        return Scored(
            ticker=inputs.ticker, inputs=inputs, operating_profitability=None,
            quality_state=QUALITY_STALE, earnings_yield=None,
            enterprise_value=None, fx_pair=None, fx_rate=None, note=too_old,
        )

    return Scored(
        ticker=inputs.ticker, inputs=inputs,
        operating_profitability=operating_profitability, quality_state=quality_state,
        earnings_yield=earnings_yield, enterprise_value=enterprise_value,
        fx_pair=fx_pair, fx_rate=fx_rate, note=note,
        implied_shares=implied_shares, market_cap_settled=market_cap_settled,
    )


# --- ranking --------------------------------------------------------------


def competition_ranks(values: Sequence[float]) -> list[int]:
    """1-2-2-4: equal values share the better rank -- E5(d).

    Highest value is rank 1. Both components are "more is better".
    """
    order = sorted(range(len(values)), key=lambda i: -values[i])
    ranks = [0] * len(values)
    previous = None
    for position, index in enumerate(order, start=1):
        if previous is not None and values[index] == values[previous]:
            ranks[index] = ranks[previous]
        else:
            ranks[index] = position
        previous = index
    return ranks


def rank(scored: Sequence[Scored]) -> RankingResult:
    """Split into the two sections and rank each -- E5(a), kept by E6."""
    result = RankingResult(scored={s.ticker: s for s in scored})
    result.tally = Tally(STEP_RANK, count_in=len(scored))

    # Staleness is decided before either leg is consulted. A stale record's
    # legs would compute; that is exactly why it must not reach them.
    stale = [s for s in scored if s.quality_state == QUALITY_STALE]
    live = [s for s in scored if s.quality_state != QUALITY_STALE]

    both = [s for s in live
            if s.operating_profitability is not None and s.earnings_yield is not None]
    ey_only = [s for s in live
               if s.operating_profitability is None and s.earnings_yield is not None]
    neither = [s for s in live if s.earnings_yield is None]

    if both:
        quality_ranks = competition_ranks(
            [s.operating_profitability for s in both])                  # type: ignore[misc]
        ey_ranks = competition_ranks([s.earnings_yield for s in both])  # type: ignore[misc]
        rows = [
            Ranked(s, quality_ranks[i], ey_ranks[i], quality_ranks[i] + ey_ranks[i])
            for i, s in enumerate(both)
        ]
        # Ascending on the sum; an equal sum breaks alphabetically -- a stated
        # arbitrary rule rather than an unstated one.
        rows.sort(key=lambda r: (r.combined, r.ticker))
        result.main = rows

    if ey_only:
        ranks = competition_ranks([s.earnings_yield for s in ey_only])  # type: ignore[misc]
        rows = [Ranked(s, None, ranks[i], None) for i, s in enumerate(ey_only)]
        rows.sort(key=lambda r: (r.ey_rank, r.ticker))
        result.yield_only = rows

    result.stale = sorted(stale, key=lambda s: s.ticker)
    for _ in result.stale:
        # A VALUE we have, judged too old -- the same shape prices.py and
        # fundamentals.py already give a stale close and a stale statement.
        result.tally.reject(ON_VALUE, "accounts older than the staleness limit")

    result.unrankable = sorted(neither, key=lambda s: s.ticker)
    for scored in result.unrankable:
        # Both reasons land in the MISSING column -- the yield was not
        # measurable -- but they are not the same fact and are not counted as
        # one. A name whose quality leg computed and whose enterprise value
        # was refused by the bound in rule 8 is here for a reason that has
        # nothing to do with an absent line.
        result.tally.reject(
            ON_MISSING,
            "quality leg computed, no earnings yield"
            if scored.operating_profitability is not None
            else "neither component computable",
        )
    result.tally.count_out = len(result.main) + len(result.yield_only)
    return result


def fetched_date_for(fetched: date | Mapping[str, date | None] | None,
                     ticker: str) -> date | None:
    """One fetch date for ``ticker``: the mapping's entry for it, or the
    single date given for every name, or None."""
    if isinstance(fetched, Mapping):
        return fetched.get(ticker)
    return fetched


def rank_candidates(
    candidates: Sequence,
    fundamentals: Mapping,
    fx: FxTable,
    as_of: date,
    *,
    closes: Mapping[str, tuple[date, float]] | None = None,
    fetched: date | Mapping[str, date | None] | None = None,
    investment_companies: frozenset[str] = frozenset(),
) -> RankingResult:
    """``as_of`` is REQUIRED: without it the staleness gate cannot be asked.

    It has no default on purpose. A default would let a caller drop the one
    argument the gate needs and get a full ranking back with no sign that a
    check had been skipped.

    ``closes`` maps each ticker to ``(date, settled close)`` -- the price
    every yield is struck on (rule 8). A name absent from it has no yield,
    and the row says "no settled close" rather than reaching for the
    vendor's price. ``fetched`` is the fundamentals fetch date, which the
    net-debt legs carry -- one date for every name, or a mapping from
    ticker to that name's own fetch date, since under FRAMEWORK-EDITS E49
    one store holds several fetches and a name absent from the mapping
    carries None.
    """
    closes = closes or {}
    inputs = [extract_inputs(c.ticker, fundamentals.get(c.ticker),
                             close=closes.get(c.ticker),
                             fetched=fetched_date_for(fetched, c.ticker))
              for c in candidates]
    result = rank([score(i, fx, as_of, investment_companies) for i in inputs])
    result.fx = fx
    return result
