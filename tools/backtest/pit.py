"""Point-in-time clipping of SEC companyfacts (backtest design, step 1).

The engine reads companyfacts as SEC serves it TODAY: every filing up to
now, the latest one winning a period. A backtest that fed it that file would
let it see figures published after the test date and restatements made
after it (design §2, the first two risks). This module cuts the file to
what was on EDGAR on the test date and hands the cut file to the engine's
OWN builders -- nothing here computes a figure.

THE CUT, entry by entry:

1. **Visible:** `filed` strictly BEFORE the test date. The design says
   "filed <= the test date"; a filing made on the test day itself may have
   been accepted after the close the price is taken at (EDGAR accepts to
   17:30 ET, and the price is the 16:00 close), so the day itself is out.
   This is stricter than the design and never looser.
2. **First filed** (policy "first", the design's): for each (taxonomy, tag,
   unit, start, end) only the EARLIEST visible entry stands -- among the
   statement forms where any exist, as the engine's own `_pick` narrows
   the pool. A restatement made before the test date is therefore ALSO
   dropped; the design chose that over "the latest visible", which is what
   the live engine would have seen. Policy "latest" keeps every visible
   entry and lets the engine pick, as it does live.
3. **Share counts keep every visible entry, under either policy.** A split
   reaches the older years only by being re-filed: `history._annual_facts`
   finds a split from the same year filed twice with counts a split apart,
   and the store's `_pick` takes the re-filed (post-split) count. Keeping
   only the first filing would leave every pre-split year on the old count
   against a post-split price -- DECK's 2016-2022 at a sixth (c046701).
   Only splits filed before the test date can show, which is design §2's
   "bara med splitar kända på testdagen".

`frame` is not used by the engine (it is SEC's mark on the LATEST fact for
a calendar period, i.e. a mark set with hindsight); it is stripped anyway
so nothing downstream can come to depend on it.
"""
from __future__ import annotations

import copy
from dataclasses import dataclass
from datetime import date, datetime, time, timezone

import yaml

from vss import history as HI
from vss import manual as M
from vss import xbrl as X

POLICIES = ("first", "latest")

#: Units whose every visible entry is kept (rule 3 above).
ALL_VISIBLE_UNITS = ("shares",)


def _filed(entry: dict) -> date | None:
    try:
        return date.fromisoformat(str(entry.get("filed", ""))[:10])
    except ValueError:
        return None


def visible(entry: dict, as_of: date) -> bool:
    """Was this entry on EDGAR before the close of `as_of`? (rule 1)"""
    filed = _filed(entry)
    return filed is not None and filed < as_of


def clip(facts: dict, as_of: date, *, policy: str = "first") -> dict:
    """A deep copy of `facts` holding only what the engine could have seen."""
    if policy not in POLICIES:
        raise ValueError(f"policy must be one of {POLICIES}, got {policy!r}")
    out = {k: copy.deepcopy(v) for k, v in facts.items() if k != "facts"}
    out["facts"] = {}
    for taxonomy, tags in (facts.get("facts") or {}).items():
        kept_tags = {}
        for tag, node in (tags or {}).items():
            units = {}
            for unit, entries in (node.get("units") or {}).items():
                seen = [dict(e) for e in entries if visible(e, as_of)]
                for e in seen:
                    e.pop("frame", None)
                if policy == "first" and unit not in ALL_VISIBLE_UNITS:
                    seen = first_filed(seen)
                if seen:
                    units[unit] = seen
            if units:
                kept = {k: v for k, v in node.items() if k != "units"}
                kept["units"] = units
                kept_tags[tag] = kept
        if kept_tags:
            out["facts"][taxonomy] = kept_tags
    return out


def first_filed(entries: list[dict]) -> list[dict]:
    """One entry per (start, end): the earliest filed (rule 2)."""
    groups: dict[tuple, list[dict]] = {}
    for e in entries:
        groups.setdefault((e.get("start"), e.get("end")), []).append(e)
    out = []
    for pool in groups.values():
        statements = [e for e in pool if X._is_statement(e)]
        pool = statements or pool
        out.append(min(pool, key=lambda e: (e.get("filed", ""), e.get("accn", ""))))
    return out


def differences(facts: dict, as_of: date) -> int:
    """How many (tag, unit, period) values the two policies set apart."""
    a, b = clip(facts, as_of, policy="first"), clip(facts, as_of, policy="latest")
    n = 0
    for taxonomy, tags in a["facts"].items():
        for tag, node in tags.items():
            for unit, entries in node["units"].items():
                if unit in ALL_VISIBLE_UNITS:
                    continue
                other = b["facts"][taxonomy][tag]["units"][unit]
                latest = {}
                for e in other:
                    key = (e.get("start"), e.get("end"))
                    statements = X._is_statement(e)
                    prev = latest.get(key)
                    rank = (statements, e.get("filed", ""), e.get("accn", ""))
                    if prev is None or rank > prev[0]:
                        latest[key] = (rank, e["val"])
                for e in entries:
                    if latest[(e.get("start"), e.get("end"))][1] != e["val"]:
                        n += 1
    return n


# --- what the engine would have built ------------------------------------

@dataclass(frozen=True)
class PitStore:
    as_of: date
    policy: str
    text: str                 # `vss xbrl --annual` then `--e140-fill`
    parsed: object | None     # `manual.parse_manual`, or None where it refused
    refused: str | None       # the loader's refusal, verbatim
    years: list
    passed_over: list
    gate: object | None       # `manual.section5_gate` on the test date
    #: E34 / E34.1 / E61 / E115: the interest shape, chosen by the basis
    #: year's tags (`interest_shape`); "" is E34's cash pair or none at all.
    interest_source: str = ""
    #: The roll-forward 10-Q carries an operating lease liability the basis
    #: 10-K does not: ASC 842 adopted between them. The bridge then charges
    #: a lease the pre-842 flows already paid as rent (counted twice).
    lease_transition: bool = False
    #: The basis-year fields written as E107 searched zeros because no
    #: element was tagged (`_searched_zeros`).
    searched_zeros: tuple = ()


def interest_shape(year) -> str:
    """The interest shape a session would have chosen, by the rulings' own
    order: E34's cash pair, else E34.1's income-statement net (the element
    or the stated pair), else E61's gross `InterestExpenseNonoperating`,
    else E115's interest paid alone. "" where E34's pair forms or nothing
    does (the gate then refuses FCF0, as it would live).

    LIVE, A SESSION WRITES THIS LINE BY HAND after reading the 10-K (CENTA's
    store carries E34.1 off the printed statement). `vss xbrl --annual`
    never writes it for a US filer, so without this choice almost every US
    store refuses FCF0. The choice reads tags only; it cannot read a
    printed line a filer did not tag.
    """
    f = year.figures
    if "finance_costs_paid" in f and "finance_income_received" in f:
        return ""
    if "net_finance_costs" in f or ("finance_costs_period" in f
                                    and "finance_income_period" in f):
        return M.INTEREST_SOURCE_INCOME_STATEMENT
    if "finance_costs_period" in f and f["finance_costs_period"].tag == X.E61_GROSS_INTEREST_TAG:
        return M.INTEREST_SOURCE_INTEREST_EXPENSE_ONLY
    if "finance_costs_paid" in f:
        return M.INTEREST_SOURCE_CASH_PAID_ONLY
    return ""


def _with_unmapped_zeros(text: str, year, taxonomy) -> str:
    """A zeroed field `manual_yaml` does not emit (no taxonomy field: E81)
    put into the basis year's figures, as `fill_e140_text` puts E140's."""
    mapped = {s.field for s in taxonomy.fields}
    extra = [n for n, f in year.figures.items() if n not in mapped
             and n not in X.E140_FILL_FIELDS and f.zero_basis]
    if not extra:
        return text
    lines = text.split("\n")
    at = lines.index(f"  - fiscal_year: {year.fiscal_year}")
    while lines[at] != "    figures:":
        at += 1
    for name in extra:
        lines[at + 1:at + 1] = X._figure_lines(name, year.figures[name], 6)
    return "\n".join(lines)


def _with_interest_source(text: str, shape: str) -> str:
    """The `interest_source:` line put under `interest_in_ocf:`, as a
    session would have typed it."""
    if not shape:
        return text
    lines = text.split("\n")
    at = lines.index("interest_in_ocf:")
    while not lines[at].startswith("  page:"):
        at += 1
    lines[at + 1:at + 1] = [
        "  # BACKTEST (tools/backtest/pit.py): the shape a session types by",
        "  # hand live, chosen here by the basis year's tags.",
        f"  interest_source: {shape}"]
    return "\n".join(lines)


def run_ts(as_of: date) -> datetime:
    """The engine's clock for a run on the test date: the evening, UTC."""
    return datetime.combine(as_of, time(21, 0), tzinfo=timezone.utc)


def store_at(facts: dict, as_of: date, *, ticker: str, cik: int,
             name: str = "", quote_currency: str = "USD",
             policy: str = "first") -> PitStore:
    """The store `vss xbrl --annual` would have emitted on `as_of`, built by
    the engine's own functions from the clipped facts. Nothing is written."""
    cut = clip(facts, as_of, policy=policy)
    taxonomy = X.pick_taxonomy(cut)
    currency = X.reporting_currency(cut, taxonomy)
    inventory = ticker.upper() in X.E140_INVENTORY_IS_THE_BUSINESS
    years, passed_over = X.build_annual(
        cut, taxonomy=taxonomy, currency=currency,
        inventory_is_business=inventory, searched_on=as_of.isoformat())
    if not years:
        raise X.XbrlError(f"{ticker}: no annual facts visible on {as_of}")
    zeroed = _searched_zeros(years[-1], taxonomy, as_of)
    roll = X.build_roll_forward(cut, years, taxonomy, currency,
                                inventory_is_business=inventory)
    if roll is not None:
        X._searched_zero_only_where_zero(roll, years[-1])
    text = X.manual_yaml(ticker=ticker.upper(),
                         name=name or str(cut.get("entityName") or ticker),
                         cik=int(cik), quote_currency=quote_currency,
                         years=years, run_ts=run_ts(as_of), facts=cut,
                         taxonomy=taxonomy, currency=currency,
                         roll_forward=roll)
    # Live this is two runs: `--annual --write`, then `--e140-fill`, which
    # alone writes each year's `working_capital_change` (manual_yaml emits
    # the taxonomy's fields only). The same function on the same years.
    url = X.API_URL.format(cik=int(cik))
    document = (f"SEC XBRL companyfacts for CIK {int(cik):010d} -- {url}, "
                f"cut to filings before {as_of.isoformat()}")
    text = X.fill_e140_text(text, years, roll, document=document, url=url)
    text = _with_unmapped_zeros(text, years[-1], taxonomy)
    shape = interest_shape(years[-1])
    text = _with_interest_source(text, shape)
    transition = bool(roll is not None
                      and "operating_lease_liabilities" in roll.figures
                      and "operating_lease_liabilities" not in years[-1].figures)
    parsed = gate = refused = None
    try:
        parsed = M.parse_manual(yaml.safe_load(text), path=f"<pit {ticker} {as_of}>")
        gate = M.section5_gate(parsed, as_of=as_of)
    except Exception as exc:  # noqa: BLE001 -- the loader's refusal is the record
        refused = f"{type(exc).__name__}: {exc}"
    return PitStore(as_of, policy, text, parsed, refused, years, passed_over,
                    gate, shape, transition, zeroed)


#: Fields a live session closes by hand with an E25 / E107 searched zero
#: when the filer tags nothing for them: E105's NCI dividends and the
#: bridge legs (E35.1 pension, E68 ARO, E35 leases). Untagged, the record
#: refuses net debt or FCF0.
SEARCHED_ZERO_FIELDS = ("nci_dividends_paid", "pension_deficit",
                        "asset_retirement_obligation",
                        "operating_lease_liabilities", "lease_liabilities")


def _searched_zeros(year, taxonomy, as_of: date) -> tuple[str, ...]:
    """E107 searched zeros on the basis year for `SEARCHED_ZERO_FIELDS` no
    element answers, as `apply_e140` already writes one for acquisitions.

    LIVE, A SESSION WRITES THESE after reading the 10-K, and could find an
    untagged line (a pension deficit under an element the map does not
    read) the tag search cannot. A zero where the filer had a liability
    RAISES the value. Returns the fields zeroed (a column in the row)."""
    ocf = year.figures.get("operating_cash_flow")
    where = (f"the {ocf.form} {ocf.accession} filed {ocf.filed}"
             if ocf is not None else "this year's annual filing")
    zeroed = []
    for spec in taxonomy.fields:
        if (spec.field not in SEARCHED_ZERO_FIELDS or not spec.tags
                or spec.field in year.figures):
            continue
        year.figures[spec.field] = X.Figure(
            value=0.0, tag="", start=None, end=year.end.isoformat(),
            accession=getattr(ocf, "accession", ""), form=getattr(ocf, "form", ""),
            filed=getattr(ocf, "filed", ""), taxonomy=taxonomy.name,
            zero_basis="searched",
            composite=(f"BACKTEST E107 searched zero: SEC XBRL companyfacts for "
                       f"{where}, fiscal year to {year.end.isoformat()}, "
                       f"searched on {as_of.isoformat()} for "
                       f"{', '.join(f'{taxonomy.name}:{t}' for t in spec.tags)}"
                       f" -- none tagged for the year (tools/backtest/pit.py)"))
        zeroed.append(spec.field)
    if "prepaid_delivery_obligation" not in year.figures:
        # E81 has no element in the map at all: a metals stream or prepaid
        # offtake (a miner's) is NOT SEEN by the backtest and enters at zero.
        year.figures["prepaid_delivery_obligation"] = X.Figure(
            value=0.0, tag="", start=None, end=year.end.isoformat(),
            accession=getattr(ocf, "accession", ""), form=getattr(ocf, "form", ""),
            filed=getattr(ocf, "filed", ""), taxonomy=taxonomy.name,
            zero_basis="searched",
            composite=(f"BACKTEST E107 searched zero: {where}, fiscal year to "
                       f"{year.end.isoformat()}, searched on {as_of.isoformat()} "
                       f"for an E81 prepaid delivery obligation -- the tag map "
                       f"has no element for one, so a stream is not seen "
                       f"(tools/backtest/pit.py)"))
        zeroed.append("prepaid_delivery_obligation")
    return tuple(zeroed)


def history_at(facts: dict, as_of: date, *, ticker: str,
               policy: str = "first") -> HI.History:
    """The history file `vss history --xbrl` would have built on `as_of`."""
    raw = HI.from_companyfacts(ticker.upper(), clip(facts, as_of, policy=policy),
                               fetched=as_of.isoformat())
    return HI.parse(raw, path=f"<pit {ticker} {as_of}>")
