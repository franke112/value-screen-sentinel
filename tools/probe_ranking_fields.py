"""PROBE: what a Greenblatt or Piotroski ranking key could actually read.

A BUILD-TIME measurement tool, like tools/build_universe.py. Not part of the
vss package and never called by it. It answers one question --
which fields exist, for what share of a sample -- so a ranking key can be
chosen against what is there rather than against what one wishes were there.

Coverage is reported PER FIELD, never per ticker, and split three ways:

  quote summary   the .info blob: one request, trailing-twelve-month figures,
                  no history at all
  annual, latest  the line item in the most recent annual statement column
  annual, YoY     the SAME line item non-null in the two most recent annual
                  columns -- which is what Piotroski's year-on-year tests need

Phase 3 showed quarterly history is unreliable (5-7 columns for most names,
none for some), so nothing here reads it. The annual and the year-over-year
numbers are reported separately because they are different questions: a field
can be present today and absent a year ago, and every Piotroski limb dies on
the second case.

    python tools/probe_ranking_fields.py [--sample 30] [--seed 20260822]
"""

from __future__ import annotations

import argparse
import csv
import random
import sys
import time
from collections import defaultdict
from pathlib import Path

import yfinance as yf

CANDIDATES = Path("data/screener_runs/2026-08-21/filter2-candidates.csv")

# concept -> (statement, [line-item aliases in preference order])
# Aliases were read off real statements, not guessed: ACN carries no bare
# "EBIT" line but does carry "Operating Income", so both are reported.
STATEMENT_FIELDS = {
    # --- Greenblatt ---
    "EBIT (strict label)":        ("income",  ["EBIT"]),
    "EBIT (or Operating Income)": ("income",  ["EBIT", "Operating Income",
                                               "Total Operating Income As Reported"]),
    "total assets":               ("balance", ["Total Assets"]),
    "current liabilities":        ("balance", ["Current Liabilities",
                                               "Total Current Liabilities",
                                               "Current Liabilities Net Minority Interest"]),
    "net PP&E (tangible fixed)":  ("balance", ["Net PPE",
                                               "Net Property Plant And Equipment"]),
    # Net working capital = current assets - current liabilities, so the
    # Greenblatt denominator needs BOTH legs. Current assets was not in the
    # five fields originally listed; it is measured here because without it
    # the ROIC denominator cannot be built at all.
    "current assets":             ("balance", ["Current Assets",
                                               "Total Current Assets"]),
    # --- Piotroski ---
    "net income":                 ("income",  ["Net Income",
                                               "Net Income Common Stockholders",
                                               "Net Income Including Noncontrolling Interests"]),
    "operating cash flow":        ("cash",    ["Operating Cash Flow",
                                               "Cash Flow From Continuing Operating Activities"]),
    "gross profit":               ("income",  ["Gross Profit"]),
    "revenue":                    ("income",  ["Total Revenue", "Operating Revenue"]),
    "long-term debt":             ("balance", ["Long Term Debt",
                                               "Long Term Debt And Capital Lease Obligation"]),
    "shares outstanding":         ("balance", ["Ordinary Shares Number", "Share Issued"]),
}

# Piotroski's gross margin needs BOTH legs in the same year.
DERIVED = {"gross margin (profit/revenue)": ("gross profit", "revenue")}

# concept -> .info key. Market cap has no statement line; the statement-only
# concepts have no quote-summary key. Both gaps are reported as "n/a".
QUOTE_FIELDS = {
    "market cap": "marketCap",
    "net income": "netIncomeToCommon",
    "operating cash flow": "operatingCashflow",
    "revenue": "totalRevenue",
    "gross margin (profit/revenue)": "grossMargins",
    "shares outstanding": "sharesOutstanding",
    "long-term debt": "totalDebt",          # TOTAL debt, not long-term -- noted
    "EBIT (or Operating Income)": "ebitda",  # EBITDA, not EBIT -- noted
}

NOT_THE_SAME_THING = {
    "long-term debt": "quote summary has totalDebt (short + long), not long-term alone",
    "EBIT (or Operating Income)": "quote summary has ebitda, not EBIT",
}


def stratified(rows, sample, seed):
    """Spread the sample over every market present, then fill by market size."""
    by_market = defaultdict(list)
    for row in rows:
        by_market[row["marknad"]].append(row["ticker"])
    rng = random.Random(seed)
    picked, pools = [], {}
    for market in sorted(by_market):
        pool = sorted(by_market[market])
        rng.shuffle(pool)
        pools[market] = pool
        picked.append((market, pool.pop()))          # one from every market
    order = sorted(pools, key=lambda m: -len(by_market[m]))
    while len(picked) < sample:
        progressed = False
        for market in order:
            if len(picked) >= sample:
                break
            if pools[market]:
                picked.append((market, pools[market].pop()))
                progressed = True
        if not progressed:
            break
    return picked


def present(frame, aliases):
    """(latest-year present, year-over-year present, alias used)."""
    if frame is None or getattr(frame, "empty", True):
        return False, False, None
    columns = list(frame.columns)
    for alias in aliases:
        if alias not in frame.index:
            continue
        values = [frame.loc[alias, c] for c in columns[:2]]
        import pandas as pd

        latest = len(values) >= 1 and pd.notna(values[0])
        yoy = len(values) >= 2 and pd.notna(values[0]) and pd.notna(values[1])
        if latest:
            return latest, yoy, alias
    return False, False, None


def main(argv=None):
    parser = argparse.ArgumentParser()
    parser.add_argument("--sample", type=int, default=30)
    parser.add_argument("--seed", type=int, default=20260822)
    parser.add_argument("--candidates", default=str(CANDIDATES))
    args = parser.parse_args(argv)

    rows = list(csv.DictReader(open(args.candidates, encoding="utf-8")))
    picked = stratified(rows, args.sample, args.seed)
    print(f"sample: {len(picked)} tickers over "
          f"{len({m for m, _ in picked})} markets, seed {args.seed}", file=sys.stderr)

    quote_hits = defaultdict(int)
    latest_hits = defaultdict(int)
    yoy_hits = defaultdict(int)
    alias_used = defaultdict(lambda: defaultdict(int))
    statement_rows = defaultdict(int)
    per_ticker = []
    currency_basis = []

    for index, (market, ticker) in enumerate(picked, 1):
        handle = yf.Ticker(ticker)
        try:
            info = handle.info or {}
        except Exception as exc:
            print(f"  {ticker}: info failed {exc}", file=sys.stderr)
            info = {}
        frames = {}
        for name, getter in (("income", "income_stmt"), ("balance", "balance_sheet"),
                             ("cash", "cashflow")):
            try:
                frames[name] = getattr(handle, getter)
            except Exception:
                frames[name] = None
            if frames[name] is not None and not getattr(frames[name], "empty", True):
                statement_rows[name] += 1

        for concept, key in QUOTE_FIELDS.items():
            if info.get(key) is not None:
                quote_hits[concept] += 1

        found = {}
        for concept, (statement, aliases) in STATEMENT_FIELDS.items():
            latest, yoy, alias = present(frames.get(statement), aliases)
            found[concept] = (latest, yoy)
            if latest:
                latest_hits[concept] += 1
                alias_used[concept][alias] += 1
            if yoy:
                yoy_hits[concept] += 1

        for concept, (a, b) in DERIVED.items():
            latest = found[a][0] and found[b][0]
            yoy = found[a][1] and found[b][1]
            if latest:
                latest_hits[concept] += 1
            if yoy:
                yoy_hits[concept] += 1

        per_ticker.append((market, ticker))
        currency_basis.append(
            (ticker, info.get("financialCurrency"), info.get("currency"))
        )
        print(f"  {index}/{len(picked)} {ticker}", file=sys.stderr)
        time.sleep(0.3)

    n = len(picked)

    def pct(count):
        return f"{count / n:>6.1%}" if n else "     -"

    print("\n" + "=" * 78)
    print(f"FIELD COVERAGE -- {n} tickers, "
          f"{len({m for m, _ in picked})} markets, seed {args.seed}")
    print("=" * 78)
    print("\nSAMPLE")
    for market in sorted({m for m, _ in picked}):
        names = [t for m, t in picked if m == market]
        print(f"  {market:<14}{', '.join(names)}")

    print(f"\nSTATEMENTS RETURNED AT ALL (of {n})")
    for name in ("income", "balance", "cash"):
        print(f"  {name:<10}{statement_rows[name]:>4}{pct(statement_rows[name])}")

    header = (f"\n  {'field':<30}{'quote':>8}{'annual':>9}{'YoY':>9}   source note")
    for title, concepts in (
        ("GREENBLATT", ["EBIT (strict label)", "EBIT (or Operating Income)",
                        "total assets", "current assets", "current liabilities",
                        "market cap", "net PP&E (tangible fixed)"]),
        ("PIOTROSKI", ["net income", "operating cash flow",
                       "gross margin (profit/revenue)", "gross profit", "revenue",
                       "total assets", "long-term debt", "shares outstanding"]),
    ):
        print(f"\n{title}")
        print(header)
        print("  " + "-" * 74)
        for concept in concepts:
            quote = pct(quote_hits[concept]) if concept in QUOTE_FIELDS else "     n/a"
            if concept == "market cap":
                annual = yoy = "     n/a"
            else:
                annual = pct(latest_hits[concept])
                yoy = pct(yoy_hits[concept])
            note = NOT_THE_SAME_THING.get(concept, "")
            print(f"  {concept:<30}{quote:>8}{annual:>9}{yoy:>9}   {note}")

    print("\nCURRENCY BASIS -- the trap in any ratio that crosses the two sources")
    print("  EBIT comes from the statements, in financialCurrency.")
    print("  market cap and enterprise value come from the quote summary, in the")
    print("  QUOTE currency's major unit -- verified: for a .L name quoted in GBp,")
    print("  marketCap / sharesOutstanding is price/100, i.e. GBP not pence.")
    print("  Where the two currencies differ, EBIT / EV crosses them and is wrong by")
    print("  the FX rate. It does not cancel the way a same-statement ratio does.")
    mixed = [(t, a, b) for t, a, b in currency_basis if a and b and a != b]
    print(f"\n  in this sample: {len(mixed)} of {n} report in a currency other than")
    print("  the one they are quoted in")
    for ticker, reports, quoted in mixed:
        print(f"      {ticker:<12}reports {reports:<4} quoted {quoted}")

    print("\nWHICH LINE LABEL SUPPLIED THE FIGURE")
    for concept in STATEMENT_FIELDS:
        used = alias_used[concept]
        if used:
            parts = ", ".join(f"{a} x{c}" for a, c in sorted(used.items(),
                                                             key=lambda kv: -kv[1]))
            print(f"  {concept:<30}{parts}")
        else:
            print(f"  {concept:<30}(never found)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
