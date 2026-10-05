"""Two PRINTED columns: this year's EBIT and free cash flow against their
own five-year medians.

**PRINTED, NEVER FILTERED.** Nothing in this module reaches a gate, a
ranking key, a kill or a verdict. It answers one question a reader of a
ranked row cannot otherwise ask -- *is the figure the key is ranking on a
normal year for this company, or the top of a cycle?* -- and it answers it
beside the row rather than instead of it. A name is never promoted,
demoted, admitted or excluded on either number.

**WHY A MEDIAN AND NOT A MEAN.** Five observations, and the whole point is
the year that is unlike the others: a mean moves toward the outlier and a
median does not. EXE's FY2012 minority distributions were 218m against 4m
in FY2019; a mean of the two decades reads as neither.

**THREE SOURCES, IN THIS ORDER, AND EACH ROW SAYS WHICH IT USED.**

1. **SEC companyfacts**, where a CIK is known. The filer's own tagged
   annual facts -- the same route `vss/xbrl.py` reads, and verified by
   provenance rather than by transcription.
2. **The manual store** `config/manual/<TICKER>.yaml`, where one exists.
   Its `annual:` entries are figures somebody entered with a page.
3. **The fundamentals store**, the vendor's annual statements, which is the
   only source that exists for most of the ranked universe.

A row that reaches none of them prints DATA MISSING and names why. **It is
never filled from a shorter history than the window asks for without
saying so**: three years is a three-year median, said in as many words, and
fewer than three is not a median at all.

**WHY A RATIO AND NOT A DIFFERENCE.** The column is read across companies
of every size in every currency; 1.24 means the same thing on every row and
a currency amount does not.

**WHERE THE MEDIAN IS NOT POSITIVE THE RATIO IS DATA MISSING.** A ratio
against a median of zero is undefined and a ratio against a negative one
inverts its own ordering -- a loss shrinking would read as a rise. E25's
rule about a denominator, applied where the denominator is formed.
"""

from __future__ import annotations

import statistics
from dataclasses import dataclass, field
from datetime import date
from typing import Callable, Mapping, Sequence

#: How many of the newest ANNUAL observations the median is taken over.
MEDIAN_YEARS = 5

#: Fewer than this many and there is no median -- the column says how many
#: it found rather than dividing by whatever was there.
MEDIAN_MINIMUM_YEARS = 3

SOURCE_SEC = "sec-companyfacts"
SOURCE_MANUAL = "manual-store"
SOURCE_VENDOR = "fundamentals-store"
SOURCE_NONE = "none"

#: E43's own alias order, for the vendor path. Imported rather than copied
#: would be circular (`ranking` will read this module), so it is stated here
#: and an AST test holds the two identical.
EBIT_ALIASES: tuple[str, ...] = (
    "Total Operating Income As Reported", "Operating Income", "EBIT",
)

#: The vendor's cash flow lines, in the order they answer.
OCF_ALIASES: tuple[str, ...] = (
    "Operating Cash Flow", "Cash Flow From Continuing Operating Activities",
)
CAPEX_ALIASES: tuple[str, ...] = ("Capital Expenditure", "Purchase Of PPE")

#: The us-gaap and ifrs-full elements each leg is read from, in order. The
#: FIRST element with a usable annual history answers; a filer that tags two
#: is tagging one line twice.
SEC_EBIT_TAGS: tuple[str, ...] = ("OperatingIncomeLoss", "ProfitLossFromOperatingActivities")
SEC_OCF_TAGS: tuple[str, ...] = (
    "NetCashProvidedByUsedInOperatingActivities",
    "NetCashProvidedByUsedInOperatingActivitiesContinuingOperations",
    "CashFlowsFromUsedInOperatingActivities",
)
#: CAPEX IS SUMMED WHERE THE FILER SPLITS IT, and only across elements that
#: are the SAME KIND of spending -- E23's question, answered the same way.
SEC_CAPEX_TAGS: tuple[tuple[str, ...], ...] = (
    ("PaymentsToAcquirePropertyPlantAndEquipment",),
    ("PaymentsToAcquireProductiveAssets",),
    ("PaymentsToAcquirePropertyPlantAndEquipment",
     "PaymentsToAcquireIntangibleAssets"),
    ("PurchaseOfPropertyPlantAndEquipmentIntangibleAssetsOtherThanGoodwill",),
)


@dataclass(frozen=True)
class MedianRatio:
    """One printed column: the newest year against its own median."""

    ratio: float | None = None
    newest: float | None = None
    median: float | None = None
    #: The fiscal years the median was taken over, newest last.
    years: tuple[int, ...] = ()
    source: str = SOURCE_NONE
    #: WHY, whenever `ratio` is None. Never empty on a missing answer.
    note: str = ""

    @property
    def present(self) -> bool:
        return self.ratio is not None

    def column(self) -> str:
        """What the CSV prints: the ratio, or the empty string."""
        return "" if self.ratio is None else f"{self.ratio:.4f}"

    def provenance(self) -> str:
        """What the row says about where the number came from."""
        if self.ratio is None:
            return f"DATA MISSING -- {self.note}" if self.note else "DATA MISSING"
        span = (f"{self.years[0]}-{self.years[-1]}" if len(self.years) > 1
                else str(self.years[0]) if self.years else "?")
        return (f"{len(self.years)}y median {self.median:,.0f} over {span}, "
                f"newest {self.newest:,.0f}, from {self.source}")


def ratio_of(points: "Sequence[tuple[date, float]]", *, source: str,
             leg: str) -> MedianRatio:
    """The newest annual observation over the median of the newest five.

    ``points`` is (period end, value), in any order; the newest
    ``MEDIAN_YEARS`` by period end are taken, and the NEWEST of those is the
    numerator. THE NUMERATOR IS INSIDE THE MEDIAN, deliberately: the
    question is whether this year stands out among the last five, not
    whether it beats the four before it, and excluding it would move the
    denominator every time the newest year moved.
    """
    usable = sorted(((d, v) for d, v in points if v is not None),
                    key=lambda item: item[0])
    # one observation per fiscal year: a restated year filed twice is one
    # year, and the LATER-DATED of two points in the same year wins.
    by_year: dict[int, tuple[date, float]] = {}
    for when, value in usable:
        by_year[when.year] = (when, value)
    window = [by_year[y] for y in sorted(by_year)][-MEDIAN_YEARS:]
    if len(window) < MEDIAN_MINIMUM_YEARS:
        return MedianRatio(
            source=source,
            note=(f"{len(window)} annual {leg} observation(s) and "
                  f"{MEDIAN_MINIMUM_YEARS} are the fewest a median is taken "
                  f"over"))
    values = [v for _, v in window]
    median = statistics.median(values)
    newest = values[-1]
    years = tuple(d.year for d, _ in window)
    if median <= 0:
        return MedianRatio(
            newest=newest, median=median, years=years, source=source,
            note=(f"the {len(values)}-year median {leg} is {median:,.0f} -- a "
                  f"ratio against a median that is not positive is undefined "
                  f"where it is zero and inverts its own ordering where it is "
                  f"negative, so no ratio is printed (E25's rule about a "
                  f"denominator, applied where the denominator is formed)"))
    return MedianRatio(ratio=newest / median, newest=newest, median=median,
                       years=years, source=source)


# --- the three sources ----------------------------------------------------


def _annual_facts(facts: Mapping, tags: "Sequence[str]",
                  ) -> list[tuple[date, float]]:
    """Annual (twelve-month) duration facts for the FIRST tag that has any."""
    for namespace, elements in (facts.get("facts") or {}).items():
        del namespace
        for tag in tags:
            element = elements.get(tag)
            if not element:
                continue
            out: dict[int, tuple[date, float]] = {}
            for rows in (element.get("units") or {}).values():
                for row in rows:
                    start, end = row.get("start"), row.get("end")
                    if not start or not end:
                        continue
                    first, last = date.fromisoformat(start), date.fromisoformat(end)
                    months = (last.year - first.year) * 12 + last.month - first.month
                    if not 11 <= months <= 13:      # a YEAR, not a quarter
                        continue
                    if row.get("form", "").startswith(("10-K", "20-F")):
                        out[last.year] = (last, float(row["val"]))
            if out:
                return [out[y] for y in sorted(out)]
    return []


def from_sec(facts: Mapping) -> tuple[MedianRatio, MedianRatio]:
    """Both legs off one companyfacts document."""
    ebit_points = _annual_facts(facts, SEC_EBIT_TAGS)
    if not ebit_points:
        # A FACT ABOUT THE FILER, not a coverage gap to be worked around.
        # NVR tags no operating income element of any kind -- it presents
        # pre-tax income and the homebuilding/mortgage split, and its
        # facts hold only `IncomeLossFromContinuingOperationsBeforeIncome
        # Taxes...`, which is a DIFFERENT quantity. Naming the elements
        # looked for is what lets a reader tell the two apart.
        ebit = MedianRatio(
            source=SOURCE_SEC,
            note=(f"the filer tags no annual operating income element: "
                  f"{', '.join(SEC_EBIT_TAGS)} are all absent. A pre-tax "
                  f"income element is NOT read in their place -- it is a "
                  f"different quantity, and E43's leg is the operating line"))
    else:
        ebit = ratio_of(ebit_points, source=SOURCE_SEC, leg="EBIT")
    ocf = _annual_facts(facts, SEC_OCF_TAGS)
    capex_by_year: dict[int, float] = {}
    for group in SEC_CAPEX_TAGS:
        legs = [_annual_facts(facts, (tag,)) for tag in group]
        if not all(legs):
            continue
        years = set.intersection(*({d.year for d, _ in leg} for leg in legs))
        if not years:
            continue
        capex_by_year = {
            y: sum(v for leg in legs for d, v in leg if d.year == y)
            for y in years}
        break
    if not ocf or not capex_by_year:
        missing = "operating cash flow" if not ocf else "capital expenditure"
        return ebit, MedianRatio(
            source=SOURCE_SEC,
            note=(f"no annual {missing} element is tagged: us-gaap and "
                  f"ifrs-full have no free cash flow element at all (it is a "
                  f"non-GAAP APM -- see reference_figures), so the leg is "
                  f"built from the two the filer DOES tag, and one is absent"))
    fcf = ratio_of([(d, v - abs(capex_by_year[d.year]))
                    for d, v in ocf if d.year in capex_by_year],
                   source=SOURCE_SEC, leg="free cash flow")
    return ebit, fcf


def from_manual(parsed) -> tuple[MedianRatio, MedianRatio]:
    """Both legs off a `config/manual/<TICKER>.yaml` -- its `annual:` block.

    THE STORE'S OWN CAPEX QUESTION IS E23's and is not re-asked here: the
    combined line where the filer prints one, the split pair summed where it
    prints two, and DATA MISSING where it prints neither.
    """
    ebit_points: list[tuple[date, float]] = []
    fcf_points: list[tuple[date, float]] = []
    for entry in getattr(parsed, "annual", ()) or ():
        end = getattr(entry, "period_end", None)
        if end is None:
            continue
        income = entry.value("operating_income")
        if income is not None:
            ebit_points.append((end, float(income)))
        ocf = entry.value("operating_cash_flow")
        combined = entry.value("capex_combined")
        ppe, intangibles = entry.value("capex_ppe"), entry.value("capex_intangibles")
        capex = (combined if combined is not None
                 else None if ppe is None and intangibles is None
                 else (ppe or 0.0) + (intangibles or 0.0))
        if ocf is not None and capex is not None:
            fcf_points.append((end, float(ocf) - abs(float(capex))))
    return (ratio_of(ebit_points, source=SOURCE_MANUAL, leg="EBIT"),
            ratio_of(fcf_points, source=SOURCE_MANUAL, leg="free cash flow"))


def from_vendor(fundamentals) -> tuple[MedianRatio, MedianRatio]:
    """Both legs off a `TickerFundamentals` -- the vendor's annual rows."""
    ebit = ratio_of(fundamentals.annual_series(*EBIT_ALIASES),
                    source=SOURCE_VENDOR, leg="EBIT")
    ocf = dict(fundamentals.annual_series(*OCF_ALIASES))
    capex = dict(fundamentals.annual_series(*CAPEX_ALIASES))
    if not ocf or not capex:
        missing = "Operating Cash Flow" if not ocf else "Capital Expenditure"
        return ebit, MedianRatio(
            source=SOURCE_VENDOR,
            note=(f"the fundamentals store holds no `{missing}` row for this "
                  f"name. The annual cash flow statement joined the fetch on "
                  f"2026-09-04 and a store written before that carries none: "
                  f"the column fills on the next fundamentals fetch, and is "
                  f"DATA MISSING rather than estimated until it does"))
    return ebit, ratio_of([(d, v - abs(capex[d])) for d, v in ocf.items()
                           if d in capex],
                          source=SOURCE_VENDOR, leg="free cash flow")


def medians_for(ticker: str, *, fundamentals=None, parsed=None,
                facts: Callable[[], Mapping] | None = None,
                ) -> tuple[MedianRatio, MedianRatio]:
    """The two columns for one name, taking the first source that answers.

    Each leg is settled INDEPENDENTLY: a filer may tag its operating income
    and not its capex, and taking both legs from whichever source answered
    first would throw away an EBIT history that was there. Every returned
    value names the source it came from.
    """
    attempts: list[tuple[MedianRatio, MedianRatio]] = []
    if facts is not None:
        try:
            attempts.append(from_sec(facts()))
        except Exception as exc:              # noqa: BLE001 -- named, not hidden
            attempts.append((MedianRatio(source=SOURCE_SEC,
                                         note=f"the SEC route failed: "
                                              f"{type(exc).__name__}: {exc}"),) * 2)
    if parsed is not None:
        attempts.append(from_manual(parsed))
    if fundamentals is not None:
        attempts.append(from_vendor(fundamentals))
    if not attempts:
        empty = MedianRatio(note=f"no source was offered for {ticker}")
        return empty, empty
    ebit = next((a[0] for a in attempts if a[0].present), attempts[0][0])
    fcf = next((a[1] for a in attempts if a[1].present), attempts[0][1])
    return ebit, fcf
