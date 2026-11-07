"""Point-in-time SEC companyfacts -- the clip, and the screener's SEC shadow.

HANDOFF C1 (2026-11-07). The clip was `tools/backtest/pit.py`'s; it lives
here now so the screener can use it, and the backtest imports it from here
with its behaviour unchanged (`tests/test_backtest_pit.py`).

THE CUT, entry by entry (as the backtest design set it):

1. **Visible:** `filed` strictly BEFORE the test date -- a filing made on the
   test day may have been accepted after the close the price is taken at.
2. **First filed** (policy "first"): for each (taxonomy, tag, unit, start,
   end) only the EARLIEST visible entry stands, among the statement forms
   where any exist. Policy "latest" keeps every visible entry.
3. **Share counts keep every visible entry**, under either policy, so a
   split filed before the test date can show.

`frame` is stripped: it is SEC's mark on the LATEST fact for a calendar
period, set with hindsight. The frames API is NOT used anywhere here for
the same reason -- its value is SEC's latest, restatements included.

THE SHADOW (`sec_record`): the same `TickerFundamentals` lines the vendor
store holds -- "Total Revenue", "Total Operating Income As Reported",
"Total Assets" -- built from the clipped facts through the existing
`xbrl.TAGS` quarters and annual windows, so `ranking.extract_inputs` runs on
it unchanged. Nothing is synthesised: a quarter is a tagged discrete
quarter, a year a tagged annual window; no Q4 is derived, and no EBITDA or
free cash flow scalar is made (free cash flow, where wanted, is the named
limb `ocf_minus_capex`).
"""
from __future__ import annotations

import copy
import json
from datetime import date, datetime
from pathlib import Path

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


# --- the screener's SEC shadow (HANDOFF C1) ------------------------------------

SEC_CACHE = Path("data/sec-cache")
ORIGIN = "sec-pit"
REVENUE_LINE = "Total Revenue"
EBIT_LINE = "Total Operating Income As Reported"
ASSETS_LINE = "Total Assets"
ASSETS_TAG = "Assets"
ANNUAL_DAYS = (350, 380)


def cached_facts(cik: int, *, cache: Path = SEC_CACHE, today: date | None = None,
                 fetch=None) -> dict:
    """companyfacts for one CIK, cached under data/sec-cache/<cik>.json and
    refreshed once a day. The clip, not the cache date, is what makes a
    replay honest: a later fetch only ADDS filings, each dated."""
    path = Path(cache) / f"{int(cik)}.json"
    today = today or date.today()
    if path.exists() and date.fromtimestamp(path.stat().st_mtime) >= today:
        return json.loads(path.read_text(encoding="utf-8"))
    facts = (fetch or X.fetch_company_facts)(int(cik))
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(facts), encoding="utf-8")
    return facts


def _annual(cut: dict, tags: tuple[str, ...]) -> dict[date, tuple[float, dict, str]]:
    """end -> (value, the entry, its tag) for annual-length windows, the
    first tag answering a year winning; each window through `xbrl._pick`."""
    out: dict[date, tuple[float, dict, str]] = {}
    for tag in tags:
        groups: dict[str, list] = {}
        for e in X._entries(cut, tag, "USD"):
            if not e.get("start"):
                continue
            days = (date.fromisoformat(e["end"]) - date.fromisoformat(e["start"])).days
            if ANNUAL_DAYS[0] <= days <= ANNUAL_DAYS[1]:
                groups.setdefault(e["end"], []).append(e)
        for end, entries in groups.items():
            d = date.fromisoformat(end)
            if d not in out:
                entry = X._pick(entries)[0]
                out[d] = (float(entry["val"]), entry, tag)
    return out


def _instants(cut: dict, tag: str) -> dict[date, tuple[float, dict, str]]:
    groups: dict[str, list] = {}
    for e in X._entries(cut, tag, "USD"):
        if not e.get("start"):
            groups.setdefault(e["end"], []).append(e)
    out = {}
    for k, v in groups.items():
        entry = X._pick(v)[0]
        out[date.fromisoformat(k)] = (float(entry["val"]), entry, tag)
    return out


#: One SEC row: the series point's columns, then where it came from.
#: (ticker, statement, line, period_end, value, period_months,
#:  filed, accession, taxonomy, tag)
def sec_rows(facts: dict, *, ticker: str, as_of: date, policy: str = "latest") -> list[tuple]:
    """The ranking lines from SEC facts clipped to `as_of`, each with its
    filing date, accession, taxonomy and tag (HANDOFF C3)."""
    cut = clip(facts, as_of, policy=policy)
    rows: list[tuple] = []
    try:
        quarters = X.build_quarters(cut, limit=8)
    except Exception:  # noqa: BLE001 -- a filer the quarter shape cannot read
        quarters = []
    for q in quarters:
        for name, line in (("revenue", REVENUE_LINE), ("op_income", EBIT_LINE)):
            fig = q.figures.get(name)
            if fig is not None and fig.value is not None:
                rows.append((ticker, "income", line, fig.end, float(fig.value), 3,
                             fig.filed, fig.accession, fig.taxonomy, fig.tag))
    for line, tags in ((REVENUE_LINE, X.TAGS["revenue"]), (EBIT_LINE, X.TAGS["op_income"])):
        for end, (v, e, tag) in sorted(_annual(cut, tuple(tags)).items())[-5:]:
            rows.append((ticker, "income", line, end.isoformat(), v, 12,
                         e.get("filed"), e.get("accn"), X.US_GAAP, tag))
    for end, (v, e, tag) in sorted(_instants(cut, ASSETS_TAG).items())[-8:]:
        rows.append((ticker, "balance", ASSETS_LINE, end.isoformat(), v, None,
                     e.get("filed"), e.get("accn"), X.US_GAAP, tag))
    return rows


def sec_record(facts: dict, *, ticker: str, as_of: date, like=None, policy: str = "latest",
               rows: list[tuple] | None = None):
    """The vendor record's ranking lines, from SEC facts clipped to `as_of`.

    `like` is the vendor record: its text and market fields (currency,
    sector, marketCap, enterpriseValue, totalDebt, totalCash) are carried so
    `extract_inputs` differs ONLY in the accounts lines. Policy "latest" is
    what a live screener on `as_of` would have read: every filing visible
    that day, the latest one winning a period."""
    from .fundamentals import STATUS_OK, SeriesPoint, TickerFundamentals

    rows = rows if rows is not None else sec_rows(facts, ticker=ticker, as_of=as_of, policy=policy)
    series = [SeriesPoint(ticker, line, date.fromisoformat(str(end)), value, statement, months)
              for (_, statement, line, end, value, months, *_rest) in rows]
    newest = max((p.period_end for p in series), default=None)
    return TickerFundamentals(
        ticker=ticker, status=STATUS_OK, attempts=0, requests=0,
        fields=tuple(like.fields) if like is not None else (),
        series=tuple(series), newest_period=newest, origin=ORIGIN)


SEC_TABLE_DDL = """
CREATE TABLE IF NOT EXISTS fundamentals_series_sec (
    ticker        TEXT NOT NULL,
    statement     TEXT NOT NULL,
    line          TEXT NOT NULL,
    period_end    TEXT NOT NULL,
    value         REAL,
    period_months INTEGER,
    filed         TEXT,
    accession     TEXT NOT NULL,
    taxonomy      TEXT NOT NULL,
    tag           TEXT NOT NULL,
    written_at    TEXT NOT NULL,
    PRIMARY KEY (ticker, statement, line, period_end, period_months, accession)
);
"""


def write_sec_rows(store_path: Path, rows: list[tuple], *, written_at: str) -> int:
    """HANDOFF C3: SEC rows into the snapshot's fundamentals store, in their
    OWN table -- the vendor table's key (ticker, statement, line,
    period_end) would collide, and the rows carry what the vendor's cannot:
    the filing date and accession. The table is made on this first WRITE,
    as `_migrate_fundamentals` brings a store up to date; a read never
    alters a file. INSERT OR IGNORE: a fact once written is never changed."""
    import sqlite3
    if not rows:
        return 0
    conn = sqlite3.connect(store_path)
    try:
        conn.executescript(SEC_TABLE_DDL)
        before = conn.total_changes
        conn.executemany(
            "INSERT OR IGNORE INTO fundamentals_series_sec (ticker, statement, line, "
            "period_end, value, period_months, filed, accession, taxonomy, tag, written_at) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            [(*r[:6], r[6], r[7] or "", r[8] or "", r[9] or "", written_at) for r in rows])
        conn.commit()
        return conn.total_changes - before
    finally:
        conn.close()


#: How far apart two readings may be and still agree (rounding, a vendor's
#: millions): 2%.
AGREE = 0.02


def _vendor_at(record, line: str, end, months) -> float | None:
    """The vendor's own figure for a line at one period, where it has one."""
    if record is None or end is None:
        return None
    for p in record.series:
        if p.line == line and p.period_end == end and p.value is not None and \
                (months is None or p.period_months == months):
            return float(p.value)
    return None


def check(vendor_inputs, sec_inputs, vendor_record=None) -> str:
    """The `sec_check` cell: what SEC says about the two ranking lines the
    vendor supplied. SHADOW: it decides nothing. Where the two periods
    differ -- SEC cannot form a TTM without a tagged discrete Q4, which
    filers stopped tagging in 2021, and no Q4 is derived here -- the
    vendor's OWN figure for SEC's period is compared, where it has one."""
    parts = []
    for label, a, b, pa, pb in (
            ("ebit", vendor_inputs.ebit, sec_inputs.ebit,
             vendor_inputs.ebit_period, sec_inputs.ebit_period),
            ("assets", vendor_inputs.total_assets, sec_inputs.total_assets,
             vendor_inputs.total_assets_period, sec_inputs.total_assets_period)):
        if pa != pb and b is not None:
            line, months = ((EBIT_LINE, 12 if sec_inputs.basis == "annual" else None)
                            if label == "ebit" else (ASSETS_LINE, None))
            same = _vendor_at(vendor_record, line, pb, months)
            if same is None:
                parts.append(f"{label}: periods differ (vendor {pa}, SEC {pb}), vendor has no {pb}")
                continue
            gap = abs(same - b) / max(abs(b), 1.0)
            parts.append(f"{label}: periods differ (vendor {pa}, SEC {pb}); at {pb} "
                         + ("agree" if gap <= AGREE else f"vendor {same:,.0f} vs SEC {b:,.0f} ({gap:.1%})"))
            continue
        if b is None:
            parts.append(f"{label}: SEC none")
            continue
        if a is None:
            parts.append(f"{label}: vendor none, SEC {b:,.0f} ({pb})")
            continue
        if pa != pb:
            parts.append(f"{label}: periods differ (vendor {pa}, SEC {pb})")
            continue
        gap = abs(a - b) / max(abs(b), 1.0)
        parts.append(f"{label}: agree" if gap <= AGREE
                     else f"{label}: vendor {a:,.0f} vs SEC {b:,.0f} ({gap:.1%})")
    return "; ".join(parts)
