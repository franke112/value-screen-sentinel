"""Build the STATIC, dated universe CSVs under config/universe/.

This is a BUILD tool, not part of the vss package. ``vss screen`` never
fetches index membership at runtime -- it reads the committed CSVs. Run this
by hand when a list needs refreshing, then commit the result:

    python tools/build_universe.py --asof 2026-08-22

Every list gets a sibling ``.meta.json`` recording where it came from, when,
how many rows arrived and how many were expected. A list that is an
APPROXIMATION of the index it names says so in its metadata; nothing in the
CSV pretends to a provenance it does not have.

Sources (tier A):
  sp500        Wikipedia "List of S&P 500 companies" -- 503 share classes.
  stoxx600     iShares STOXX Europe 600 UCITS ETF (DE) daily holdings CSV.
               The fund replicates the index physically and full-size, so its
               Equity rows ARE the constituent list, and it carries the one
               field a name-string can never be guessed from: Asset Class.
  omxs-large-mid  APPROXIMATION. Nasdaq's official Stockholm segment file is
               behind a login, so this is the Yahoo equity screener for the
               Stockholm exchange cut at Nasdaq's own Mid Cap floor
               (EUR 150m). It is a market-cap cut, not index membership.

Sources (tier B) -- the MID-CAP widening, 2026-08-31:
  sp400        Wikipedia "List of S&P 400 companies" -- the S&P MidCap 400.
               Disjoint from the S&P 500 by construction, so it adds 400
               names and duplicates none of tier A.
  nordic-mid   APPROXIMATION, and the same rule as omxs-large-mid applied to
               the three Nordic venues Stockholm is not: Oslo, Copenhagen and
               Helsinki, cut at Nasdaq's Mid Cap floor of EUR 150m converted
               at a rate READ AND RECORDED at build time (E98: a converted
               figure names its rate and its date). A large minority of the
               rows are already in STOXX 600 and are dropped by dedup, not
               by this file -- the file is what the venue holds, and the
               overlap is a fact for the universe report to state.

Tier B is a TIER, not a file. `floors.yaml` has always named "S&P MidCap 400,
OBX / OMXC / OMXH Large+Mid" as its content and "membership is again the
floor"; these two lists are that sentence, built. The empty
`tier-b-2026-08-22.csv` placeholder stays where it is: it is dated, it says
what it was for, and a dated artifact is not edited after the fact.

ISIN is left EMPTY on every row. No free source checked here carries it:
Yahoo's ISIN lookup returns "-", the European iShares files omit it, and
Wikidata's 7,251 (isin, exchange, ticker) triples mix ADR and ordinary ISINs
onto the same listing. A wrong ISIN would silently MERGE two different
companies in dedup, which is worse than no ISIN at all. Coverage is reported
as 0 rather than faked.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
import re
import sys
import time
from datetime import date, datetime, timezone
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from vss.universe import SCHEMA  # noqa: E402  (path set above)

SP500_URL = "https://en.wikipedia.org/wiki/List_of_S%26P_500_companies"
SP400_URL = "https://en.wikipedia.org/wiki/List_of_S%26P_400_companies"
EXSA_URL = (
    "https://www.ishares.com/ch/professionals/en/products/251931/"
    "ishares-stoxx-europe-600-ucits-etf-de-fund/1495092304805.ajax"
    "?fileType=csv&fileName=EXSA_holdings&dataType=fund"
)
USER_AGENT = "Mozilla/5.0 (X11; Linux x86_64) vss-universe-build/0.1"

#: iShares exchange name -> Yahoo suffix. Exact strings from the holdings file.
EXCHANGE_SUFFIX = {
    "London Stock Exchange": ".L",
    "Xetra": ".DE",
    "Deutsche Boerse Xetra": ".DE",
    "Nyse Euronext - Euronext Paris": ".PA",
    "SIX Swiss Exchange": ".SW",
    "Nasdaq Omx Nordic": ".ST",
    "Borsa Italiana": ".MI",
    "Euronext Amsterdam": ".AS",
    "Bolsa De Madrid": ".MC",
    "Oslo Bors Asa": ".OL",
    "Omx Nordic Exchange Copenhagen A/S": ".CO",
    "Nasdaq Omx Helsinki Ltd.": ".HE",
    "Warsaw Stock Exchange/Equities/Main Market": ".WA",
    "Nyse Euronext - Euronext Brussels": ".BR",
    "Wiener Boerse Ag": ".VI",
    "Irish Stock Exchange - All Market": ".IR",
    "Nyse Euronext - Euronext Lisbon": ".LS",
}

#: Human market label per suffix, for the ``marknad`` column.
MARKET_NAME = {
    ".L": "London", ".DE": "Xetra", ".PA": "Paris", ".SW": "Zurich",
    ".ST": "Stockholm", ".MI": "Milan", ".AS": "Amsterdam", ".MC": "Madrid",
    ".OL": "Oslo", ".CO": "Copenhagen", ".HE": "Helsinki", ".WA": "Warsaw",
    ".BR": "Brussels", ".VI": "Vienna", ".IR": "Dublin", ".LS": "Lisbon",
}

#: Nordic venues write share classes without a separator ("VOLVB"); Yahoo
#: writes them with a hyphen ("VOLV-B.ST"). We do not guess which form is
#: right -- both candidates go to Yahoo and the one that returns a quote wins.
NORDIC_SUFFIXES = (".ST", ".CO", ".HE", ".OL")

#: Nasdaq Nordic's own Mid Cap floor. Large Cap is >= EUR 1bn, Mid Cap
#: EUR 150m-1bn, so Large+Mid is everything at or above the Mid floor.
OMXS_MIN_MARKET_CAP_EUR = 150_000_000
#: The Yahoo screener reports ``intradaymarketcap`` in the instrument's OWN
#: quoting currency, not in USD -- verified against the tail of the Stockholm
#: result set, which came back in SEK. The EUR floor is therefore converted
#: to SEK at a rate read at build time and RECORDED in the metadata, so the
#: cut can be reproduced knowing exactly what rate produced it.
EURSEK_TICKER = "EURSEK=X"
EURSEK_FALLBACK = 11.7

QUOTE_URL = "https://query2.finance.yahoo.com/v7/finance/quote"
QUOTE_BATCH = 150
QUOTE_FIELDS = (
    "symbol", "quoteType", "currency", "longName", "shortName",
    "fullExchangeName", "firstTradeDateMilliseconds",
)


# --- helpers ---------------------------------------------------------------


def http_get(url: str) -> bytes:
    import urllib.request

    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(req, timeout=90) as resp:
        return resp.read()


def yahoo_quotes(symbols: list[str]) -> dict[str, dict]:
    """Bulk quote lookup. Symbols Yahoo does not know are simply ABSENT.

    That absence is the point: it is how a candidate ticker is proved
    invalid without guessing from the string.
    """
    from yfinance.data import YfData

    data = YfData()
    out: dict[str, dict] = {}
    for start in range(0, len(symbols), QUOTE_BATCH):
        chunk = symbols[start : start + QUOTE_BATCH]
        for attempt in range(4):
            try:
                payload = data.get_raw_json(
                    QUOTE_URL,
                    params={"symbols": ",".join(chunk), "fields": ",".join(QUOTE_FIELDS)},
                )
                for row in payload.get("quoteResponse", {}).get("result", []) or []:
                    if row.get("symbol"):
                        out[row["symbol"]] = row
                break
            except Exception as exc:  # noqa: BLE001 - build tool, report and retry
                wait = 2 ** attempt
                print(f"  quote batch {start}: {type(exc).__name__} {exc}; retry in {wait}s",
                      file=sys.stderr)
                time.sleep(wait)
        print(f"  quotes {min(start + QUOTE_BATCH, len(symbols))}/{len(symbols)}",
              file=sys.stderr)
        time.sleep(0.4)
    return out


def nordic_variants(base: str) -> list[str]:
    """['VOLVB'] -> ['VOLVB', 'VOLV-B']. Order is preference order."""
    out = [base]
    if len(base) > 3 and base[-1] in "ABCD" and "-" not in base:
        out.append(f"{base[:-1]}-{base[-1]}")
    return out


def candidates(local: str, suffix: str) -> list[str]:
    # London writes several tickers with a trailing dot ("RR.", "BP.").
    # On Yahoo that dot is the suffix separator, so "RR." + ".L" is "RR.L".
    stem = local.strip().rstrip(".").upper().replace(" ", "-")
    stems = nordic_variants(stem) if suffix in NORDIC_SUFFIXES else [stem]
    seen, out = set(), []
    for s in stems:
        for form in (s, s.replace(".", "-")):
            sym = f"{form}{suffix}"
            if sym not in seen:
                seen.add(sym)
                out.append(sym)
    return out


def listing_date(quote: dict) -> str:
    ms = quote.get("firstTradeDateMilliseconds")
    if not ms:
        return ""
    return datetime.fromtimestamp(ms / 1000, tz=timezone.utc).date().isoformat()


# --- source lists ----------------------------------------------------------


def build_sp500() -> tuple[list[dict], dict]:
    html = http_get(SP500_URL).decode("utf-8", "replace")
    table = pd.read_html(io.StringIO(html))[0]
    rows = []
    for _, r in table.iterrows():
        symbol = str(r["Symbol"]).strip()
        rows.append(
            {
                "ticker_lokal": symbol,
                "candidates": [symbol.replace(".", "-")],
                "namn": str(r["Security"]).strip(),
                "marknad": "US",
                "instrumenttyp": "",  # not in the source list; filled from Yahoo
                "valuta": "",
                "instrumenttyp_source": "yahoo quoteType",
            }
        )
    meta = {
        "list": "sp500",
        "index": "S&P 500",
        "source_url": SP500_URL,
        "source_kind": "index constituent list",
        "expected_rows": 503,
        "approximation": False,
        "instrumenttyp_source": "yahoo quoteType (the Wikipedia table has no instrument-type column)",
        "instrumenttyp_caveat": (
            "Yahoo reports ADRs as quoteType EQUITY, so the ADR exclusion cannot "
            "fire on this list. NO DATA -- reported, never guessed from the name."
        ),
        "valuta_source": "yahoo currency",
        "listdatum_source": "yahoo firstTradeDate (first trade, not index admission)",
    }
    return rows, meta


def build_stoxx600() -> tuple[list[dict], dict]:
    raw = http_get(EXSA_URL).decode("utf-8-sig", "replace")
    lines = raw.splitlines()
    header = next(i for i, line in enumerate(lines) if line.startswith("Ticker,"))
    asof_line = lines[0]
    frame = pd.read_csv(io.StringIO("\n".join(lines[header:])))
    # The file ends with a stray non-breaking space, which pandas reads as a
    # one-cell row. Drop rows with no usable ticker AND no name -- but never
    # drop a row that has either, so a real holding can never vanish quietly.
    frame = frame[
        frame["Ticker"].notna()
        & frame["Ticker"].astype(str).str.replace("\xa0", "", regex=False).str.strip().ne("")
        & frame["Name"].notna()
    ]

    rows = []
    for _, r in frame.iterrows():
        local = str(r["Ticker"]).strip()
        exchange = str(r.get("Exchange", "")).strip()
        suffix = EXCHANGE_SUFFIX.get(exchange, "")
        rows.append(
            {
                "ticker_lokal": local,
                "candidates": candidates(local, suffix) if suffix else [],
                "namn": str(r["Name"]).strip(),
                "marknad": MARKET_NAME.get(suffix, exchange or "UNKNOWN"),
                # The source list's OWN instrument type. This is the field the
                # exclusion rule reads; it is never inferred from the name.
                "instrumenttyp": str(r.get("Asset Class", "")).strip(),
                "valuta": str(r.get("Market Currency", "")).strip(),
                "instrumenttyp_source": "ishares Asset Class",
            }
        )
    meta = {
        "list": "stoxx600",
        "index": "STOXX Europe 600",
        "source_url": EXSA_URL,
        "source_kind": (
            "physically replicating full-size index ETF holdings "
            "(iShares STOXX Europe 600 UCITS ETF (DE), EXSA)"
        ),
        "source_asof_line": asof_line,
        "expected_rows": 600,
        "approximation": False,
        "instrumenttyp_source": "ishares Asset Class (Equity / Cash / FX / Futures)",
        "valuta_source": "ishares Market Currency",
        "listdatum_source": "yahoo firstTradeDate",
        "note": (
            "Non-equity rows (cash, FX, futures) are written through unchanged so "
            "the exclusion step is exercised on real data and shows in the report."
        ),
    }
    return rows, meta


#: The three Nordic venues Stockholm is not, and the pair each one's market
#: cap is quoted in. Helsinki quotes in EUR, so its floor needs no conversion
#: and its recorded rate is exactly 1.0 -- a UNIT, not a rate (E98).
NORDIC_VENUES = (
    ("OSL", ".OL", "Oslo", "EURNOK=X"),
    ("CPH", ".CO", "Copenhagen", "EURDKK=X"),
    ("HEL", ".HE", "Helsinki", None),
)


def eur_rate(pair: str | None) -> tuple[float, str]:
    """EUR -> local at build time, or (1.0, "quoted in EUR") for a EUR venue.

    RECORDED, never assumed. E98: a figure converted from one currency to
    another names the rate that converted it and the date that rate is from,
    and a venue that quotes in the target currency is a UNIT and not a rate
    -- which is why the EUR case returns a stated 1.0 rather than silently
    skipping the multiplication.
    """
    import yfinance as yf

    if pair is None:
        return 1.0, "quoted in EUR -- no conversion (E98: a unit is not a rate)"
    try:
        frame = yf.Ticker(pair).history(period="5d", interval="1d")
        rate = float(frame["Close"].dropna().iloc[-1])
        return rate, f"{pair} close {frame.index[-1].date().isoformat()}"
    except Exception as exc:  # noqa: BLE001 - build tool
        raise SystemExit(
            f"{pair} lookup failed ({exc}). A market-cap floor converted at an "
            f"unknown rate is not a floor; the list is not written."
        ) from exc


def eursek_rate() -> tuple[float, str]:
    """EUR/SEK at build time, so the market-cap cut is reproducible."""
    import yfinance as yf

    try:
        frame = yf.Ticker(EURSEK_TICKER).history(period="5d", interval="1d")
        rate = float(frame["Close"].dropna().iloc[-1])
        stamp = frame.index[-1].date().isoformat()
        return rate, f"{EURSEK_TICKER} close {stamp}"
    except Exception as exc:  # noqa: BLE001 - build tool
        print(f"  EUR/SEK lookup failed ({exc}); using fallback", file=sys.stderr)
        return EURSEK_FALLBACK, "hardcoded fallback (live lookup failed)"


def build_omxs() -> tuple[list[dict], dict]:
    import yfinance as yf

    rate, rate_source = eursek_rate()
    floor_sek = int(OMXS_MIN_MARKET_CAP_EUR * rate)
    query = yf.EquityQuery(
        "and",
        [
            yf.EquityQuery("eq", ["exchange", "STO"]),
            yf.EquityQuery("gt", ["intradaymarketcap", floor_sek]),
        ],
    )
    quotes, offset = [], 0
    while True:
        page = yf.screen(
            query, offset=offset, size=100,
            sortField="intradaymarketcap", sortAsc=False,
        )
        got = page.get("quotes", []) or []
        quotes.extend(got)
        total = page.get("total", 0)
        offset += len(got)
        print(f"  screener {offset}/{total}", file=sys.stderr)
        if not got or offset >= total:
            break
        time.sleep(0.5)

    rows = []
    for q in quotes:
        symbol = str(q.get("symbol", "")).strip()
        if not symbol:
            continue
        rows.append(
            {
                "ticker_lokal": symbol[:-3] if symbol.endswith(".ST") else symbol,
                "candidates": [symbol],
                "namn": (q.get("longName") or q.get("shortName") or "").strip(),
                "marknad": "Stockholm",
                "instrumenttyp": str(q.get("quoteType", "")).strip(),
                "valuta": str(q.get("currency", "")).strip(),
                "instrumenttyp_source": "yahoo quoteType",
            }
        )
    meta = {
        "list": "omxs-large-mid",
        "index": "Nasdaq Stockholm Large Cap + Mid Cap",
        "source_url": "yfinance equity screener, exchange=STO",
        "source_kind": "APPROXIMATION -- market-cap cut, not index membership",
        "expected_rows": None,
        "approximation": True,
        "approximation_rule": (
            f"Yahoo equity screener for exchange STO with intraday market cap > "
            f"SEK {floor_sek:,}, i.e. Nasdaq's own Mid Cap floor of EUR "
            f"{OMXS_MIN_MARKET_CAP_EUR:,} converted at EUR/SEK {rate:.4f}."
        ),
        "fx_rate_eursek": round(rate, 4),
        "fx_rate_source": rate_source,
        "approximation_caveat": (
            "Segment membership is reviewed by Nasdaq annually; a live market-cap "
            "cut therefore disagrees with the official segment at the margins, and "
            "it does not separate the Main Market from First North. Nasdaq's "
            "official segment file is behind a login on indexes.nasdaqomx.com."
        ),
        "instrumenttyp_source": "yahoo quoteType",
        "valuta_source": "yahoo currency",
        "listdatum_source": "yahoo firstTradeDate",
    }
    return rows, meta


def build_sp400() -> tuple[list[dict], dict]:
    """The S&P MidCap 400, from the same Wikipedia table shape as the 500.

    The two indices are DISJOINT by construction -- a company is in one or
    the other, never both -- so this adds 400 names and duplicates nothing
    already in tier A. Nothing here relies on that: dedup runs anyway.
    """
    html = http_get(SP400_URL).decode("utf-8", "replace")
    table = next(t for t in pd.read_html(io.StringIO(html)) if "Symbol" in t.columns)
    rows = []
    for _, r in table.iterrows():
        symbol = str(r["Symbol"]).strip()
        rows.append(
            {
                "ticker_lokal": symbol,
                "candidates": [symbol.replace(".", "-")],
                "namn": str(r["Security"]).strip(),
                "marknad": "US",
                "instrumenttyp": "",  # not in the source list; filled from Yahoo
                "valuta": "",
                "instrumenttyp_source": "yahoo quoteType",
            }
        )
    meta = {
        "list": "sp400",
        "index": "S&P MidCap 400",
        "source_url": SP400_URL,
        "source_kind": "index constituent list",
        "expected_rows": 400,
        "approximation": False,
        "instrumenttyp_source": "yahoo quoteType (the Wikipedia table has no instrument-type column)",
        "instrumenttyp_caveat": (
            "Yahoo reports ADRs as quoteType EQUITY, so the ADR exclusion cannot "
            "fire on this list. NO DATA -- reported, never guessed from the name."
        ),
        "valuta_source": "yahoo currency",
        "listdatum_source": "yahoo firstTradeDate (first trade, not index admission)",
        "disjoint_note": (
            "The S&P 500 and the S&P MidCap 400 share no constituent, so this "
            "list overlaps tier A's sp500 file nowhere. Dedup still runs."
        ),
    }
    return rows, meta


def build_nordic_mid() -> tuple[list[dict], dict]:
    """Oslo + Copenhagen + Helsinki, cut at Nasdaq's EUR 150m Mid Cap floor.

    THE SAME RULE AS `omxs-large-mid`, applied to the three Nordic venues
    Stockholm is not. It is an APPROXIMATION for the same reason: the
    official segment files are behind a login, so this is a live market-cap
    cut and it disagrees with the official segment at the margins.

    ONE FILE, THREE VENUES, and each venue's conversion recorded separately
    -- Oslo quotes in NOK, Copenhagen in DKK, Helsinki in EUR, and a single
    "the floor was EUR 150m" line would hide the fact that three different
    rates produced three different local floors (E98).

    A large minority of these rows are ALREADY in STOXX 600 and will be
    dropped by dedup. That is deliberate: the file records what the venue
    holds at the floor, and the overlap is a fact for the universe report to
    count, not something to quietly pre-filter here.
    """
    import yfinance as yf

    rows: list[dict] = []
    conversions: dict[str, dict] = {}
    for exchange, suffix, market, pair in NORDIC_VENUES:
        rate, rate_source = eur_rate(pair)
        floor_local = int(OMXS_MIN_MARKET_CAP_EUR * rate)
        conversions[market] = {
            "exchange": exchange,
            "floor_eur": OMXS_MIN_MARKET_CAP_EUR,
            "floor_local": floor_local,
            "currency_pair": pair or "none (EUR venue)",
            "rate": round(rate, 6),
            "rate_source": rate_source,
        }
        query = yf.EquityQuery(
            "and",
            [
                yf.EquityQuery("eq", ["exchange", exchange]),
                yf.EquityQuery("gt", ["intradaymarketcap", floor_local]),
            ],
        )
        quotes, offset = [], 0
        while True:
            page = yf.screen(
                query, offset=offset, size=100,
                sortField="intradaymarketcap", sortAsc=False,
            )
            got = page.get("quotes", []) or []
            quotes.extend(got)
            total = page.get("total", 0)
            offset += len(got)
            print(f"  {exchange} screener {offset}/{total}", file=sys.stderr)
            if not got or offset >= total:
                break
            time.sleep(0.5)
        for q in quotes:
            symbol = str(q.get("symbol", "")).strip()
            if not symbol:
                continue
            local = symbol[: -len(suffix)] if symbol.endswith(suffix) else symbol
            rows.append(
                {
                    "ticker_lokal": local,
                    "candidates": [symbol],
                    "namn": (q.get("longName") or q.get("shortName") or "").strip(),
                    "marknad": market,
                    "instrumenttyp": str(q.get("quoteType", "")).strip(),
                    "valuta": str(q.get("currency", "")).strip(),
                    "instrumenttyp_source": "yahoo quoteType",
                }
            )
        conversions[market]["rows"] = sum(1 for r in rows if r["marknad"] == market)

    meta = {
        "list": "nordic-mid",
        "index": "Oslo Bors + Nasdaq Copenhagen + Nasdaq Helsinki, Large+Mid",
        "source_url": "yfinance equity screener, exchange=OSL|CPH|HEL",
        "source_kind": "APPROXIMATION -- market-cap cut, not index membership",
        "expected_rows": None,
        "approximation": True,
        "approximation_rule": (
            f"Yahoo equity screener per venue with intraday market cap above "
            f"Nasdaq's own Mid Cap floor of EUR "
            f"{OMXS_MIN_MARKET_CAP_EUR:,}, converted to each venue's quoting "
            f"currency at a rate read at build time. Per-venue rates and "
            f"local floors are in `conversions` below (E98)."
        ),
        "conversions": conversions,
        "approximation_caveat": (
            "Segment membership is reviewed annually by each exchange; a live "
            "market-cap cut therefore disagrees with the official segment at the "
            "margins, and it does not separate the main market from First North "
            "or Euronext Growth. The official segment files are behind a login."
        ),
        "overlap_note": (
            "Roughly a fifth of these rows are already in the STOXX 600 file "
            "(tier A). They are written through unchanged and dropped by DEDUP, "
            "so the overlap is counted in the universe report rather than "
            "hidden by a pre-filter here."
        ),
        "instrumenttyp_source": "yahoo quoteType",
        "valuta_source": "yahoo currency",
        "listdatum_source": "yahoo firstTradeDate",
    }
    return rows, meta


# --- writing ---------------------------------------------------------------


def resolve_and_write(rows: list[dict], meta: dict, tier: str, out_dir: Path,
                      asof: date) -> dict:
    wanted: list[str] = []
    for row in rows:
        wanted.extend(row["candidates"])
    print(f"{meta['list']}: {len(rows)} rows, {len(wanted)} candidate symbols",
          file=sys.stderr)
    quotes = yahoo_quotes(sorted(set(wanted)))

    written, unmapped = [], 0
    for row in rows:
        hit = next((quotes[c] for c in row["candidates"] if c in quotes), None)
        if hit is None:
            unmapped += 1
        written.append(
            {
                "ticker_yahoo": hit["symbol"] if hit else "",
                "ticker_lokal": row["ticker_lokal"],
                "isin": "",
                "namn": row["namn"] or (hit.get("longName", "") if hit else ""),
                "marknad": row["marknad"],
                "tier": tier,
                "listdatum": listing_date(hit) if hit else "",
                "valuta": row["valuta"] or (hit.get("currency", "") if hit else ""),
                "instrumenttyp": row["instrumenttyp"]
                or (hit.get("quoteType", "") if hit else ""),
            }
        )

    path = out_dir / f"{meta['list']}-{asof.isoformat()}.csv"
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(SCHEMA), lineterminator="\n")
        writer.writeheader()
        writer.writerows(written)

    digest = hashlib.sha256(path.read_bytes()).hexdigest()
    meta = dict(meta)
    meta.update(
        {
            "file": path.name,
            "tier": tier,
            "retrieved": asof.isoformat(),
            "rows": len(written),
            "rows_without_yahoo_mapping": unmapped,
            "isin_populated": 0,
            "isin_note": (
                "No free source checked carries ISIN for these venues; a guessed "
                "ISIN would silently merge two companies in dedup. Left empty."
            ),
            "sha256": digest,
            "built_by": "tools/build_universe.py",
        }
    )
    (out_dir / f"{meta['list']}-{asof.isoformat()}.meta.json").write_text(
        json.dumps(meta, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    print(f"  wrote {path.name}: {len(written)} rows, {unmapped} unmapped",
          file=sys.stderr)
    return meta


def write_empty(name: str, tier: str, out_dir: Path, asof: date, note: str) -> None:
    path = out_dir / f"{name}-{asof.isoformat()}.csv"
    with path.open("w", encoding="utf-8", newline="") as handle:
        csv.writer(handle, lineterminator="\n").writerow(SCHEMA)
    (out_dir / f"{name}-{asof.isoformat()}.meta.json").write_text(
        json.dumps(
            {
                "list": name,
                "tier": tier,
                "file": path.name,
                "retrieved": asof.isoformat(),
                "rows": 0,
                "expected_rows": None,
                "approximation": False,
                "source_url": None,
                "note": note,
                "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
                "built_by": "tools/build_universe.py",
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    print(f"  wrote {path.name}: empty, schema only", file=sys.stderr)


#: list name -> (builder, TIER). The tier is the LIST's, not the tool's:
#: before the mid-cap widening every list was tier A and `resolve_and_write`
#: hardcoded "A", which would have written the S&P 400 into tier A and
#: silently widened the SCHEDULED Saturday run, which loads tier A only.
BUILDERS = {
    "sp500": (build_sp500, "A"),
    "stoxx600": (build_stoxx600, "A"),
    "omxs-large-mid": (build_omxs, "A"),
    "sp400": (build_sp400, "B"),
    "nordic-mid": (build_nordic_mid, "B"),
}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--asof", default=date.today().isoformat(),
                        help="date stamped into the filenames (default: today)")
    parser.add_argument("--out", default=str(ROOT / "config" / "universe"))
    parser.add_argument("--only", action="append", choices=sorted(BUILDERS),
                        help="build just this list (repeatable)")
    parser.add_argument("--skip-empty", action="store_true",
                        help="do not (re)write the empty tier B and C files")
    args = parser.parse_args(argv)

    asof = date.fromisoformat(args.asof)
    out_dir = Path(args.out)
    out_dir.mkdir(parents=True, exist_ok=True)

    for name in args.only or sorted(BUILDERS):
        print(f"== {name}", file=sys.stderr)
        builder, tier = BUILDERS[name]
        rows, meta = builder()
        resolve_and_write(rows, meta, tier, out_dir, asof)

    # Tier B is no longer written empty: `sp400` and `nordic-mid` populate it.
    # The dated 2026-08-22 placeholder stays on disk unedited -- it says what
    # it was for, and a dated artifact is not rewritten after the fact.
    if not args.skip_empty:
        write_empty("tier-c", "C", out_dir, asof,
                    "Tier C is not populated in phase 1. Schema only. Its floors "
                    "live in config/universe/floors.yaml, not in this file.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
