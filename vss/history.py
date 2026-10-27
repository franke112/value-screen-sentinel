"""The issuer's own multi-year history, and what E142-E145 derive from it.

`config/history/<TICKER>.yaml` carries up to ten fiscal years read from the
issuer's multi-year summaries (two annual reports) or from SEC companyfacts.
Nothing here values a company: it derives the four things the rulings take
from history and the record cannot -- the organic growth (E144), the
acquirer's return on added capital (E142), the cycle and the bear level
(E143), and the quality tests (E145) -- and states how each was formed.

A hand-read row carries the row as printed; `check` reads the PDF text and
confirms every value is in it, in order (E131's principle: the machine does
the read-back). A companyfacts row carries its tag and no quote.
"""

from __future__ import annotations

import re
import statistics
import subprocess
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml

from .manual import UNIT_SCALE

HISTORY_DIR = Path("config/history")
PDF_TEXT_CACHE = Path("data/cache/history-text")

MONEY_FIELDS = ("revenue", "operating_profit", "operating_profit_adjusted",
                "invested_capital", "goodwill", "equity", "net_debt",
                "operating_cash_flow", "capex", "acquisitions_paid")
FIELDS = MONEY_FIELDS + ("organic_growth_pct", "shares")

#: E144(1): a year counts as deal-free, and its revenue growth as an
#: organic PROXY, where neither it nor the year before paid more than this
#: share of revenue for acquisitions.
PROXY_DEAL_SHARE = 0.01
#: E144(2)-(4).
GROWTH_CAP = 0.04
GROWTH_CAP_HIGH = 0.08
GROWTH_CAP_HIGH_YEARS = 7
GROWTH_FLOOR = -0.03
MIN_ORGANIC_YEARS = 5
#: E143(3).
CYCLICAL_REVENUE_FALL = 0.10
CYCLICAL_MARGIN_RATIO = 2.0
#: E145.
Q1_TANGIBLE_ROIC = 0.15
Q3_LEVERAGE = 3.0
Q3_LEVERAGE_STABLE = 4.5
Q3_STABLE_FALL = 0.15
Q2_PEAK_FALL = 0.50
#: E142(5): the bear window.
WORST_WINDOW = 5


class HistoryError(Exception):
    """A history file that cannot be read, or one whose rows do not check."""


@dataclass(frozen=True)
class Row:
    field: str
    source: str
    years: tuple[int, ...]
    values: tuple[float, ...]
    quote: str = ""
    unit: str | None = None
    tag: str = ""


@dataclass(frozen=True)
class History:
    ticker: str
    currency: str
    money_unit: str
    sources: dict[str, dict[str, Any]]
    rows: tuple[Row, ...]
    business: dict[str, Any] | None = None
    fiscal_year_end: str = "12-31"
    path: str = ""
    #: E141 decision on one name: revenue that passes a commodity price
    #: through (a fuel retailer) is not a measure of growth or of the
    #: cycle. The reason is written in the file; the effect is that the
    #: organic PROXY and the revenue/margin cycle tests are not run.
    revenue_pass_through: str = ""
    #: year -> field -> value in WHOLE units (money) or a whole count
    #: (shares) or a FRACTION (organic growth). Newer source wins.
    years: dict[int, dict[str, float]] = field(default_factory=dict)

    def series(self, name: str) -> dict[int, float]:
        return {y: v[name] for y, v in sorted(self.years.items()) if name in v}

    @property
    def span(self) -> tuple[int, int] | None:
        ys = sorted(self.years)
        return (ys[0], ys[-1]) if ys else None


def _scale(unit: str | None, where: str) -> float:
    if unit is None:
        return 1.0
    if unit not in UNIT_SCALE:
        raise HistoryError(f"{where}: unit {unit!r} is not one of {'|'.join(UNIT_SCALE)}")
    return UNIT_SCALE[unit]


def _source_rank(rows: list[Row]) -> dict[str, int]:
    """Newer report wins: a source ranks by the latest year it prints."""
    latest: dict[str, int] = {}
    for r in rows:
        latest[r.source] = max(latest.get(r.source, 0), max(r.years))
    return latest


def parse(raw: dict[str, Any], *, path: str = "") -> History:
    ticker = raw.get("ticker")
    if not ticker:
        raise HistoryError(f"{path}: no ticker")
    money_unit = raw.get("money_unit")
    if money_unit not in UNIT_SCALE:
        raise HistoryError(f"{path}: money_unit {money_unit!r} is not one of "
                           f"{'|'.join(UNIT_SCALE)}")
    sources = dict(raw.get("sources") or {})
    rows: list[Row] = []
    for i, r in enumerate(raw.get("rows") or ()):
        where = f"{path} row {i + 1} ({r.get('field')})"
        if r.get("field") not in FIELDS:
            raise HistoryError(f"{where}: field is not one of {', '.join(FIELDS)}")
        if r.get("source") not in sources:
            raise HistoryError(f"{where}: source {r.get('source')!r} is not in sources:")
        years = tuple(int(y) for y in r.get("years") or ())
        values = tuple(float(v) for v in r.get("values") or ())
        if not years or len(years) != len(values):
            raise HistoryError(f"{where}: {len(years)} years against {len(values)} values")
        kind = sources[r["source"]].get("kind", "pdf")
        if kind == "pdf" and not r.get("quote"):
            raise HistoryError(f"{where}: a hand-read row carries its row as printed (quote:)")
        rows.append(Row(field=r["field"], source=r["source"], years=years,
                        values=values, quote=str(r.get("quote") or ""),
                        unit=r.get("unit"), tag=str(r.get("tag") or "")))
    rank = _source_rank(rows)
    years: dict[int, dict[str, float]] = {}
    won: dict[tuple[int, str], int] = {}
    summed: dict[tuple[int, str], str] = {}
    for r in rows:
        if r.field == "organic_growth_pct":
            scale, name = 0.01, "organic_growth"
        elif r.field == "shares":
            scale, name = _scale(r.unit or "whole", f"{path} {r.field}"), "shares"
        else:
            scale, name = _scale(r.unit or money_unit, f"{path} {r.field}"), r.field
        for y, v in zip(r.years, r.values):
            key = (y, name)
            if key in won and won[key] > rank[r.source]:
                continue
            # Capex printed as two lines of ONE statement (property and
            # intangibles) is their sum; any other repeat replaces.
            if (key in summed and summed[key] == r.source
                    and name in ("capex", "acquisitions_paid")):
                years[y][name] += v * scale
                continue
            won[key] = rank[r.source]
            summed[key] = r.source
            years.setdefault(y, {})[name] = v * scale
    return History(ticker=ticker, currency=str(raw.get("currency") or ""),
                   money_unit=money_unit, sources=sources, rows=tuple(rows),
                   business=raw.get("business"),
                   fiscal_year_end=str(raw.get("fiscal_year_end") or "12-31"),
                   path=path, years=years,
                   revenue_pass_through=str(raw.get("revenue_pass_through") or ""))


def load(ticker: str, *, directory: Path = HISTORY_DIR) -> History | None:
    """The history file, or None where the name has none."""
    p = Path(directory) / f"{ticker}.yaml"
    if not p.exists():
        return None
    return parse(yaml.safe_load(p.read_text(encoding="utf-8")) or {}, path=str(p))


# --- the read-back -------------------------------------------------------

def _norm(text: str) -> str:
    text = (text.replace("–", "-").replace("−", "-")
            .replace("—", "-").replace(" ", " ").replace(" ", " ")
            .replace("’", "'"))
    return re.sub(r"\s+", " ", text).strip()


def pdf_text(file: str, *, cache: Path = PDF_TEXT_CACHE) -> str:
    """pdftotext -layout, whitespace collapsed; cached by file name."""
    src = Path(file)
    if not src.exists():
        raise HistoryError(f"{file}: the source file is not on disk")
    cache.mkdir(parents=True, exist_ok=True)
    out = cache / (src.name + ".txt")
    if not out.exists() or out.stat().st_mtime < src.stat().st_mtime:
        if src.suffix.lower() == ".pdf":
            subprocess.run(["pdftotext", "-layout", str(src), str(out)], check=True)
        else:
            out.write_text(re.sub(r"<[^>]+>", " ", src.read_text(errors="replace")))
    return _norm(out.read_text(errors="replace"))


def _forms(v: float) -> list[str]:
    """The ways a printed number can look."""
    a = abs(v)
    out = []
    for dec in (0, 1, 2, 3):
        if abs(round(a, dec) - a) > 1e-9:
            continue
        s = f"{a:,.{dec}f}"
        out += [s, s.replace(",", " "), s.replace(",", ""), s.replace(",", "."),
                s.replace(",", " ").replace(".", ","), s.replace(",", "").replace(".", ",")]
    seen, res = set(), []
    for s in out:
        if s not in seen:
            seen.add(s)
            res.append(s)
    return res


def _find_values(quote: str, values: tuple[float, ...]) -> str | None:
    """None where every value is in the quote in order, else what failed."""
    q = _norm(quote)
    pos = 0
    for v in values:
        best = None
        for f in _forms(v):
            pats = [re.escape(f)] if v >= 0 else [r"-\s?" + re.escape(f), r"\(" + re.escape(f) + r"\)"]
            for p in pats:
                m = re.compile(r"(?<![\d.,])" + p + r"(?![\d])").search(q, pos)
                if m and (best is None or m.start() < best.start()):
                    best = m
        if best is None and v == 0:
            # a nil printed as a dash
            best = re.compile(r"(?<![\d\w])-(?![\d])").search(q, pos)
        if best is None:
            return f"{v:g} not found in the quote after position {pos}"
        pos = best.end()
    return None


def check(h: History) -> list[str]:
    """Every hand-read row against its PDF. Empty is a PASS."""
    fails: list[str] = []
    texts: dict[str, str] = {}
    for r in h.rows:
        src = h.sources[r.source]
        if src.get("kind", "pdf") != "pdf":
            continue
        f = src.get("file")
        try:
            texts.setdefault(f, pdf_text(f))
        except (HistoryError, subprocess.CalledProcessError) as exc:
            fails.append(f"{r.field} [{r.source}]: {exc}")
            continue
        if _norm(r.quote) not in texts[f]:
            fails.append(f"{r.field} [{r.source}]: the quote is not in {f}: {r.quote!r}")
            continue
        bad = _find_values(r.quote, r.values)
        if bad:
            fails.append(f"{r.field} [{r.source}]: {bad}: {r.quote!r}")
    if h.business:
        src = h.sources.get(h.business.get("source"), {})
        if src.get("kind", "pdf") == "pdf" and h.business.get("quote"):
            f = src.get("file")
            try:
                if _norm(h.business["quote"]) not in texts.setdefault(f, pdf_text(f)):
                    fails.append(f"business: the quote is not in {f}")
            except (HistoryError, subprocess.CalledProcessError) as exc:
                fails.append(f"business: {exc}")
    return fails


# --- E144: organic growth and the derived view ---------------------------

@dataclass(frozen=True)
class OrganicYear:
    year: int
    growth: float
    proxy: bool


def organic_years(h: History) -> list[OrganicYear]:
    """E144(1): the issuer's own organic growth, else the deal-free PROXY."""
    out: list[OrganicYear] = []
    rev = h.series("revenue")
    acq = h.series("acquisitions_paid")
    stated = h.series("organic_growth")
    ys = sorted(set(rev) | set(stated))
    for y in ys:
        if y in stated:
            out.append(OrganicYear(y, stated[y], False))
            continue
        if h.revenue_pass_through:
            continue
        if y in rev and (y - 1) in rev and rev[y - 1] > 0:
            def share(yy):
                if yy not in acq or yy not in rev or rev[yy] <= 0:
                    return None
                return abs(acq[yy]) / rev[yy]
            s0, s1 = share(y), share(y - 1)
            if s0 is not None and s1 is not None and s0 <= PROXY_DEAL_SHARE and s1 <= PROXY_DEAL_SHARE:
                out.append(OrganicYear(y, rev[y] / rev[y - 1] - 1, True))
    return out


def _cagr(rates: list[float]) -> float:
    p = 1.0
    for r in rates:
        p *= 1 + r
    return p ** (1 / len(rates)) - 1


def _rolling(rates: list[float], n: int) -> list[float]:
    return [_cagr(rates[i:i + n]) for i in range(0, len(rates) - n + 1)]


def owner_earnings(h: History) -> dict[int, float]:
    """Operating cash flow less capex, per year, where both are stated."""
    ocf, capex = h.series("operating_cash_flow"), h.series("capex")
    return {y: ocf[y] - abs(capex[y]) for y in ocf if y in capex}


def oe_per_share_cagr(h: History) -> float | None:
    oe, sh = owner_earnings(h), h.series("shares")
    ys = [y for y in sorted(oe) if y in sh and sh[y] > 0]
    if len(ys) < 6:
        return None
    first, last = ys[:3], ys[-3:]
    a = statistics.mean(oe[y] / sh[y] for y in first)
    b = statistics.mean(oe[y] / sh[y] for y in last)
    n = statistics.mean(last) - statistics.mean(first)
    if a <= 0 or b <= 0 or n <= 0:
        return None
    return (b / a) ** (1 / n) - 1


@dataclass(frozen=True)
class DerivedGrowth:
    bear: float
    base: float
    bull: float
    how: str


def derived_growth(h: History) -> DerivedGrowth | None:
    """E144. None where fewer than five organic years: the view stands."""
    org = organic_years(h)
    if len(org) < MIN_ORGANIC_YEARS:
        return None
    rates = [o.growth for o in org]
    organic = _cagr(rates)
    oe = oe_per_share_cagr(h)
    high = sum(1 for r in rates if r > GROWTH_CAP) >= GROWTH_CAP_HIGH_YEARS
    cap = GROWTH_CAP_HIGH if high else GROWTH_CAP
    recent = _cagr(rates[-5:])
    raw = min(organic, recent) if oe is None else min(organic, recent, oe)
    base = max(GROWTH_FLOOR, min(cap, raw))
    worst3 = min(_rolling(rates, 3)) if len(rates) >= 3 else min(rates)
    best5 = max(_rolling(rates, 5)) if len(rates) >= 5 else max(rates)
    bear = min(base, max(GROWTH_FLOOR, worst3))
    bull = max(base, min(cap, best5))
    proxies = sum(1 for o in org if o.proxy)
    how = (f"E144: organic {organic:.2%}/yr over {len(org)} years, last five {recent:.2%} "
           f"({org[0].year}-{org[-1].year}"
           + (f", {proxies} of them PROXY from deal-free years" if proxies else "")
           + ")"
           + (f"; owner earnings per share {oe:.2%}/yr" if oe is not None else
              "; owner earnings per share not derivable")
           + f"; cap {cap:.0%}; worst 3-year {worst3:.2%}, best 5-year {best5:.2%}")
    return DerivedGrowth(bear=bear, base=base, bull=bull, how=how)


# --- E142: return on incremental invested capital ------------------------

def _profit_series(h: History) -> tuple[dict[int, float], str]:
    adj, rep = h.series("operating_profit_adjusted"), h.series("operating_profit")
    if adj and set(rep) <= set(adj):
        return adj, "adjusted operating profit"
    return rep, "operating profit"


def _invested_capital(h: History) -> dict[int, float]:
    ic = h.series("invested_capital")
    if ic:
        return ic
    eq, nd = h.series("equity"), h.series("net_debt")
    return {y: eq[y] + nd[y] for y in eq if y in nd}


@dataclass(frozen=True)
class Roiic:
    value: float
    start: int
    end: int
    how: str


def roiic_window(h: History, first: list[int], last: list[int], tax: float,
                 organic_fallback: float) -> Roiic | None:
    """E142(2) over one window. Each end is the MEAN of its years (three
    for the full window, one for a bear window): a single endpoint year
    carries its one-offs into the answer."""
    profit, label = _profit_series(h)
    ic = _invested_capital(h)
    if any(y not in profit or y not in ic for y in first + last):
        return None
    p0 = statistics.mean(profit[y] for y in first)
    p1 = statistics.mean(profit[y] for y in last)
    c0 = statistics.mean(ic[y] for y in first)
    c1 = statistics.mean(ic[y] for y in last)
    m0, m1 = round(statistics.mean(first)), round(statistics.mean(last))
    org = {o.year: o.growth for o in organic_years(h)}
    factor, assumed = 1.0, 0
    for y in range(m0 + 1, m1 + 1):
        if y in org:
            factor *= 1 + org[y]
        else:
            factor *= 1 + organic_fallback
            assumed += 1
    gain = (p1 - p0 * factor) * (1 - tax)
    acq = h.series("acquisitions_paid")
    spent = sum(abs(acq.get(y, 0.0)) for y in range(m0 + 1, m1 + 1))
    added = c1 - c0
    denom = max(added, spent)
    if denom <= 0:
        return None
    value = gain / denom
    def span(ys):
        return f"{ys[0]}" if len(ys) == 1 else f"{ys[0]}-{ys[-1]} mean"
    how = (f"{label} {p0:,.0f} ({span(first)}) -> {p1:,.0f} ({span(last)}); "
           f"organic x{factor:.3f}"
           + (f" ({assumed} of {m1 - m0} years at the view's {organic_fallback:.1%})" if assumed else "")
           + f"; after tax {tax:.1%}: {gain:,.0f} on "
           + (f"capital added {added:,.0f}" if denom == added else f"acquisitions {spent:,.0f}")
           + f" = {value:.2%}")
    return Roiic(value=value, start=first[0], end=last[-1], how=how)


def roiic(h: History, tax: float, organic_fallback: float) -> tuple[Roiic | None, Roiic | None]:
    """E142(2), (5): the full window (three-year means at each end) and the
    worst five-year window (single years)."""
    profit, _ = _profit_series(h)
    ic = _invested_capital(h)
    ys = sorted(y for y in profit if y in ic)
    if len(ys) < 2:
        return None, None
    if len(ys) >= 6:
        full = roiic_window(h, ys[:3], ys[-3:], tax, organic_fallback)
    else:
        full = roiic_window(h, ys[:1], ys[-1:], tax, organic_fallback)
    worst = None
    for s0 in ys:
        e = s0 + WORST_WINDOW
        if e in ys:
            w = roiic_window(h, [s0], [e], tax, organic_fallback)
            if w is not None and (worst is None or w.value < worst.value):
                worst = w
    return full, worst or full


# --- E143: the cycle and the bear level ----------------------------------

@dataclass(frozen=True)
class Cycle:
    cyclical: bool
    level_base: float
    level_bear: float | None   # None: the record's own three years decide
    how: str


def cycle(h: History) -> Cycle:
    rev = h.series("revenue")
    profit, _ = _profit_series(h)
    falls = [rev[y] / rev[y - 1] - 1 for y in rev if (y - 1) in rev and rev[y - 1] > 0]
    margins = {y: profit[y] / rev[y] for y in profit if y in rev and rev[y] > 0}
    why = []
    if h.revenue_pass_through:
        # the cycle read on profit alone: a fall below half its peak
        peak, worst = None, 0.0
        for y in sorted(profit):
            if peak is not None and peak > 0:
                worst = max(worst, 1 - profit[y] / peak)
            peak = profit[y] if peak is None else max(peak, profit[y])
        if worst <= 0.5:
            return Cycle(False, 1.0, None, "not cyclical on profit (revenue is a pass-through: "
                         + h.revenue_pass_through + ")")
        return Cycle(True, 1.0, None, f"CYCLICAL on profit (fell {worst:.0%} from a peak); "
                     "revenue is a pass-through, no margin normalisation")
    if falls and min(falls) < -CYCLICAL_REVENUE_FALL:
        why.append(f"revenue fell {min(falls):.0%} in a year")
    # A margin that ROSE is not a cycle (GDDY, LII, DECK): only a fall
    # from an EARLIER peak to a later trough below half of it counts.
    peak, fall = None, None
    for y in sorted(margins):
        m = margins[y]
        if peak is not None and peak > 0 and (m <= 0 or peak > CYCLICAL_MARGIN_RATIO * m):
            fall = (peak, m) if fall is None or m < fall[1] else fall
        peak = m if peak is None else max(peak, m)
    if fall is not None:
        why.append(f"operating margin fell from {fall[0]:.1%} to {fall[1]:.1%}")
    if not why:
        return Cycle(False, 1.0, None, "not cyclical (E143(3))")
    oe = owner_earnings(h)
    oem = {y: oe[y] / rev[y] for y in oe if y in rev and rev[y] > 0}
    ys = sorted(oem)
    if len(ys) < 5:
        return Cycle(True, 1.0, None,
                     f"CYCLICAL ({'; '.join(why)}), but fewer than five owner-earnings "
                     f"years: no cycle normalisation")
    recent = statistics.mean(oem[y] for y in ys[-3:])
    median = statistics.median(oem.values())
    low = min(oem.values())
    if recent <= 0:
        return Cycle(True, 1.0, 0.0, f"CYCLICAL ({'; '.join(why)}); recent margin not positive")
    base = min(1.0, median / recent)
    bear = max(0.0, low / recent)
    return Cycle(True, base, bear,
                 f"CYCLICAL ({'; '.join(why)}): owner-earnings margin median "
                 f"{median:.1%}, last three {recent:.1%}, lowest {low:.1%} -> base "
                 f"level x{base:.3f}, bear x{bear:.3f}")


# --- E145: the quality tests ---------------------------------------------

@dataclass(frozen=True)
class Test:
    name: str
    passed: bool | None      # None: not determinable from the history
    figure: str


def quality(h: History, *, tax: float, fcf0: float, net_debt: float,
            roiic_base: float | None, repeat_buyer: bool, rate: float) -> tuple[Test, ...]:
    """E145 Q1-Q5. `fcf0` and the net debt are in WHOLE units. The net
    debt is the bridge's: under E117 the rent is already in FCF0, so the
    lease liability is not added a second time."""
    out: list[Test] = []
    profit, label = _profit_series(h)
    ic, gw = _invested_capital(h), h.series("goodwill")
    rocs = []
    for y in profit:
        if y in ic:
            tangible = ic[y] - gw.get(y, 0.0)
            rocs.append(float("inf") if tangible <= 0 else profit[y] * (1 - tax) / tangible)
    if rocs:
        med = statistics.median(rocs)
        out.append(Test("Q1 tangible ROIC", med >= Q1_TANGIBLE_ROIC,
                        f"median {med:.1%} over {len(rocs)} years"
                        + ("" if gw else " (no goodwill row: on all invested capital)")
                        + f" against {Q1_TANGIBLE_ROIC:.0%}"))
    else:
        out.append(Test("Q1 tangible ROIC", None, "no profit and capital years"))
    oe = owner_earnings(h)
    ys = sorted(profit)
    peak, worst_fall, unrecovered = None, 0.0, []
    for i, y in enumerate(ys):
        p = profit[y]
        if peak is not None and peak > 0:
            fall = 1 - p / peak
            worst_fall = max(worst_fall, fall)
            if fall > Q2_PEAK_FALL:
                # a fall the business REPAIRED inside three years (a shut-down
                # year) is not a moat failing; one it did not repair is
                later = [profit[z] for z in ys[i + 1:i + 4]]
                if not later or max(later) < peak:
                    unrecovered.append(y)
        peak = p if peak is None else max(peak, p)
    neg = [y for y, v in oe.items() if v <= 0]
    if profit:
        q2 = (not neg) and not unrecovered
        out.append(Test("Q2 stability", q2,
                        f"owner earnings negative in {neg or 'no year'}; {label} at most "
                        f"{worst_fall:.0%} below its running peak"
                        + (f", not regained within three years after {unrecovered}"
                           if unrecovered else
                           (", regained within three years" if worst_fall > Q2_PEAK_FALL else ""))))
    else:
        out.append(Test("Q2 stability", None, "no profit years"))
    stable = bool(profit) and worst_fall <= Q3_STABLE_FALL
    limit = Q3_LEVERAGE_STABLE if stable else Q3_LEVERAGE
    if fcf0 > 0:
        lev = net_debt / fcf0
        out.append(Test("Q3 debt", lev <= limit,
                        f"net debt {lev:.1f}x FCF0 against {limit:.1f}x"
                        + (" (stable class)" if stable else "")))
    else:
        out.append(Test("Q3 debt", False, "FCF0 not positive"))
    if repeat_buyer:
        out.append(Test("Q4 capital allocation",
                        None if roiic_base is None else roiic_base >= rate,
                        "ROIIC not derivable" if roiic_base is None
                        else f"ROIIC {roiic_base:.1%} against r {rate:.1%}"))
    else:
        out.append(Test("Q4 capital allocation", True, "not a repeat buyer"))
    b = h.business or {}
    out.append(Test("Q5 understandable", bool(b.get("text")),
                    str(b.get("text") or "no sentence in the history file")))
    return tuple(out)


def dump(raw: dict[str, Any]) -> str:
    return yaml.safe_dump(raw, sort_keys=False, allow_unicode=True, width=200)


# --- SEC companyfacts ----------------------------------------------------

XBRL_TAGS: dict[str, tuple[str, ...]] = {
    "revenue": ("Revenues", "RevenueFromContractWithCustomerExcludingAssessedTax",
                "SalesRevenueNet", "RevenuesNetOfInterestExpense",
                "SalesRevenueGoodsNet"),
    "operating_profit": ("OperatingIncomeLoss",),
    "operating_cash_flow": ("NetCashProvidedByUsedInOperatingActivities",
                            "NetCashProvidedByUsedInOperatingActivitiesContinuingOperations"),
    "capex": ("PaymentsToAcquirePropertyPlantAndEquipment",
              "PaymentsToAcquireProductiveAssets"),
    "acquisitions_paid": ("PaymentsToAcquireBusinessesNetOfCashAcquired",
                          "PaymentsToAcquireBusinessesAndInterestInAffiliates",
                          "PaymentsToAcquireBusinessesGross"),
    "equity": ("StockholdersEquity",
               "StockholdersEquityIncludingPortionAttributableToNoncontrollingInterest"),
    "goodwill": ("Goodwill",),
    "shares": ("WeightedAverageNumberOfDilutedSharesOutstanding",),
}
#: E147: a filer that tags no operating profit -- pre-tax profit plus
#: interest expense, as tagged.
XBRL_PRETAX = ("IncomeLossFromContinuingOperationsBeforeIncomeTaxesExtraordinaryItemsNoncontrollingInterest",
               "IncomeLossFromContinuingOperationsBeforeIncomeTaxesMinorityInterestAndIncomeLossFromEquityMethodInvestments",
               # a domestic-only filer (NVR) tags its whole pre-tax line here
               "IncomeLossFromContinuingOperationsBeforeIncomeTaxesDomestic")
XBRL_INTEREST = ("InterestExpense", "InterestExpenseNonoperating", "InterestExpenseDebt")
XBRL_DEBT_WHOLE = ("LongTermDebt",)
XBRL_DEBT_PARTS = ("LongTermDebtNoncurrent", "LongTermDebtCurrent", "DebtCurrent",
                   "ShortTermBorrowings", "CommercialPaper", "SeniorNotes")
XBRL_CASH = ("CashAndCashEquivalentsAtCarryingValue",
             "CashCashEquivalentsRestrictedCashAndRestrictedCashEquivalents")


def _annual_facts(gaap: dict, tag: str, *, duration: bool) -> dict[str, float]:
    """end date -> value, from 10-K FY facts; the latest filing wins."""
    import datetime as _dt
    best: dict[str, tuple[str, float]] = {}
    unit_rows = gaap.get(tag, {}).get("units", {})
    for unit, rows in unit_rows.items():
        if unit not in ("USD", "shares"):
            continue
        for r in rows:
            if r.get("form") not in ("10-K", "10-K/A") or r.get("fp") != "FY":
                continue
            if duration:
                if "start" not in r:
                    continue
                d = (_dt.date.fromisoformat(r["end"]) - _dt.date.fromisoformat(r["start"])).days
                if not 350 <= d <= 380:
                    continue
            elif "start" in r:
                continue
            prev = best.get(r["end"])
            if prev is None or r["filed"] > prev[0]:
                best[r["end"]] = (r["filed"], float(r["val"]))
    return {e: v for e, (_, v) in best.items()}


def from_companyfacts(ticker: str, facts: dict, *, years: int = 11,
                      fetched: str = "") -> dict[str, Any]:
    """A history file's raw form from companyfacts: one row per field per
    tag, the tag named, no quote (the provenance is the tag)."""
    gaap = facts.get("facts", {}).get("us-gaap", {})
    ocf: dict[str, float] = {}
    for t in XBRL_TAGS["operating_cash_flow"]:
        for e, v in _annual_facts(gaap, t, duration=True).items():
            ocf.setdefault(e, v)
    # One fiscal year per label: a filer that moved its year end (HRB,
    # April -> June in 2021) keeps both runs, the later end winning a label.
    by_year: dict[int, str] = {}
    for e in sorted(ocf):
        by_year[int(e[:4])] = e
    ends = [by_year[y] for y in sorted(by_year)][-years:]
    if not ends:
        raise HistoryError(f"{ticker}: companyfacts has no annual operating cash flow")
    label = {e: int(e[:4]) for e in ends}
    rows: list[dict[str, Any]] = []

    def add(fld: str, tag: str, got: dict[str, float], *, unit: str | None = None,
            negate_abs: bool = False):
        ys = [e for e in ends if e in got]
        if not ys:
            return
        row = {"field": fld, "source": "xbrl", "tag": tag,
               "years": [label[e] for e in ys],
               "values": [abs(got[e]) if negate_abs else got[e] for e in ys]}
        if unit:
            row["unit"] = unit
        rows.append(row)

    for fld, tags in XBRL_TAGS.items():
        dur = fld not in ("equity", "goodwill")
        filled: dict[str, float] = {}
        for t in tags:
            got = _annual_facts(gaap, t, duration=dur)
            new = {e: v for e, v in got.items() if e in ends and e not in filled}
            if new:
                add(fld, t, new, unit=("whole" if fld == "shares" else None),
                    negate_abs=fld in ("capex", "acquisitions_paid"))
                filled.update(new)
        if fld == "acquisitions_paid":
            zeros = {e: 0.0 for e in ends if e not in filled}
            if zeros:
                add(fld, "searched: no acquisition element tagged (zero)", zeros)
        if fld == "operating_profit" and len(filled) < len(ends):
            # E147, year by year: the first pre-tax tag and the first
            # interest-expense tag that answer at each end.
            def merged(tags):
                out: dict[str, tuple[float, str]] = {}
                for t in tags:
                    for e, v in _annual_facts(gaap, t, duration=True).items():
                        out.setdefault(e, (v, t))
                return out
            pre = merged(XBRL_PRETAX)
            intr = merged(XBRL_INTEREST + ("InterestExpenseBorrowings",))
            groups: dict[str, dict[str, float]] = {}
            for e in ends:
                if e in filled or e not in pre or e not in intr:
                    continue
                tag = f"E147: {pre[e][1]} + {intr[e][1]}"
                groups.setdefault(tag, {})[e] = pre[e][0] + intr[e][0]
            for tag, got in groups.items():
                add(fld, tag, got)
                filled.update(got)
    # net debt = debt - cash; invested capital = equity + net debt
    cash = {}
    for t in XBRL_CASH:
        cash = _annual_facts(gaap, t, duration=False)
        if cash:
            break
    whole = _annual_facts(gaap, XBRL_DEBT_WHOLE[0], duration=False)
    parts = {t: _annual_facts(gaap, t, duration=False) for t in XBRL_DEBT_PARTS}
    debt: dict[str, float] = {}
    for e in ends:
        if e in whole:
            d = whole[e] + sum(parts[t].get(e, 0.0) for t in ("ShortTermBorrowings", "CommercialPaper"))
        else:
            d = sum(parts[t].get(e, 0.0) for t in XBRL_DEBT_PARTS if t != "DebtCurrent") \
                + (parts["DebtCurrent"].get(e, 0.0) if e not in parts["LongTermDebtCurrent"] else 0.0)
        debt[e] = d
    nd = {e: debt[e] - cash[e] for e in ends if e in cash}
    add("net_debt", "derived: LongTermDebt (or its parts) + short-term borrowings - "
        + (XBRL_CASH[0]), nd)
    return {"ticker": ticker, "currency": "USD", "money_unit": "whole",
            "sources": {"xbrl": {"kind": "sec-xbrl",
                                 "url": "https://data.sec.gov/api/xbrl/companyfacts/",
                                 "fetched": fetched}},
            "rows": rows}


def _cik(ticker: str, watchlist: Path = Path("config/watchlist.yaml")) -> int | None:
    raw = yaml.safe_load(watchlist.read_text(encoding="utf-8")) or {}
    for e in raw.get("tickers") or ():
        if e.get("ticker") == ticker and e.get("cik"):
            return int(e["cik"])
    return None


def summary(h: History) -> str:
    """What the rulings derive from one history, as lines."""
    from .runrecord import tax_country
    from .valuation import STATUTORY_TAX_RATE
    country = tax_country(h.ticker)
    tax = STATUTORY_TAX_RATE.get(country) if country else None
    span = h.span
    out = [f"{h.ticker}: {len(h.years)} years" + (f" {span[0]}-{span[1]}" if span else "")]
    g = derived_growth(h)
    out.append("  growth: " + (f"bear {g.bear:.2%} base {g.base:.2%} bull {g.bull:.2%} -- {g.how}"
                               if g else "fewer than five organic years: the view stands (E144(4))"))
    if tax is not None:
        full, worst = roiic(h, tax, g.base if g else 0.0)
        out.append("  ROIIC base: " + (full.how if full else "not derivable"))
        out.append("  ROIIC bear: " + (worst.how if worst else "not derivable"))
    c = cycle(h)
    out.append("  cycle: " + c.how)
    return "\n".join(out)


def run_history(*, ticker: str, xbrl: bool = False, write: bool = False,
                check_only: bool = False, directory: Path | None = None,
                cik: int | None = None) -> tuple[int, str]:
    directory = Path(directory or HISTORY_DIR)
    if xbrl:
        from datetime import date as _date
        from .xbrl import fetch_company_facts
        cik = cik or _cik(ticker)
        if cik is None:
            return 2, f"{ticker}: no cik on the watchlist entry"
        raw = from_companyfacts(ticker, fetch_company_facts(cik),
                                fetched=_date.today().isoformat())
        h = parse(raw, path=f"{ticker} (companyfacts)")
        text = dump(raw)
        if write:
            directory.mkdir(parents=True, exist_ok=True)
            target = directory / f"{ticker}.yaml"
            if target.exists():
                existing = yaml.safe_load(target.read_text(encoding="utf-8")) or {}
                for keep in ("business", "revenue_pass_through"):
                    if existing.get(keep):
                        raw[keep] = existing[keep]
                # the sources the kept business sentence cites stay
                for k, v in (existing.get("sources") or {}).items():
                    if k != "xbrl":
                        raw["sources"].setdefault(k, v)
                text = dump(raw)
            target.write_text(text, encoding="utf-8")
            return 0, f"wrote {target}\n{summary(h)}"
        return 0, text + "\n" + summary(h)
    h = load(ticker, directory=directory)
    if h is None:
        return 2, f"{ticker}: no {directory}/{ticker}.yaml"
    fails = check(h)
    if check_only:
        if fails:
            return 1, f"{ticker}: {len(fails)} row(s) FAIL\n" + "\n".join("  " + f for f in fails)
        return 0, f"{ticker}: every hand-read row PASSES against its PDF"
    head = (f"read-back: {len(fails)} FAIL" if fails else "read-back: PASS")
    return (1 if fails else 0), head + "\n" + summary(h)
