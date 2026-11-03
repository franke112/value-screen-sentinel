"""The universe per test date (backtest design, step 3).

Every company that filed a 10-K in the year before the test date, from
EDGAR's full index -- not today's index, so a company delisted since stays
in (design §2, survivorship).

THE SIZE LINE DEVIATES FROM THE DESIGN, AND WHY. The design sets "market
cap >= 300 MUSD on the test date, shares x unadjusted price". A price on
the test date needs a ticker that still resolves at the price vendor, and a
company delisted since often has none -- so the size filter itself would
drop exactly the companies §2's survivorship row exists to keep. The line
is drawn instead on the PUBLIC FLOAT the filer states on the cover of its
latest 10-K before the test date (`dei:EntityPublicFloat`): point-in-time,
filed by every 10-K filer, and needing no price. It is smaller than market
cap (insider holdings are out) and dated to the filer's last second
quarter, so the line catches somewhat fewer, older-dated names.

Float source, two stages. SEC's frames API (one file per calendar quarter,
all filers) gives the CANDIDATES, at two thirds of the line; a frame keeps
the LATEST filing for a period, so it may hold a value filed after the
test date and cannot be the line itself (`frame_floats`). The line is then
read off each candidate's own companyfacts, cut to the date (`pit_float`),
when those facts are fetched for the run.

Sector line: SIC 6000-6411 (banks, credit, brokers, asset managers,
insurers) and 6798 (REITs) are out -- today's Gate 3 line ("Financial
Services" plus REITs) in SIC terms. SIC is read from the submissions API,
which serves the CURRENT code; a code changed since is not seen.

    .venv/bin/python -m tools.backtest.universe [--date 2018-04-30 ...]
"""
from __future__ import annotations

import argparse
import gzip
import json
import sys
import time
import urllib.request
from datetime import date, timedelta
from pathlib import Path

from vss import xbrl as X

ROOT = Path(__file__).resolve().parents[2] / "data" / "backtest"
TEST_DATES = tuple(date(y, 4, 30) for y in (2016, 2017, 2018, 2019, 2020))
FLOAT_MIN = 300e6
TEN_K_FORMS = ("10-K", "10-KT")
#: today's Gate 3 line in SIC terms
EXCLUDED_SIC = (range(6000, 6412), range(6798, 6799))
PAUSE = 0.12                                  # SEC: at most 10 requests a second


def sec_get(url: str, cache: Path | None = None) -> bytes:
    """GET from SEC with the declared contact; cached on disk where given."""
    if cache is not None and cache.exists():
        return cache.read_bytes()
    request = urllib.request.Request(url, headers={
        "User-Agent": X.user_agent(), "Accept-Encoding": "gzip"})
    for attempt in range(4):
        try:
            with urllib.request.urlopen(request, timeout=60) as r:
                raw = r.read()
                if (r.headers.get("Content-Encoding") or "") == "gzip":
                    raw = gzip.decompress(raw)
            break
        except urllib.error.HTTPError as exc:
            if exc.code == 404:
                raise
            time.sleep(2 ** attempt)
    else:
        raise RuntimeError(f"{url}: four attempts failed")
    time.sleep(PAUSE)
    if cache is not None:
        cache.parent.mkdir(parents=True, exist_ok=True)
        cache.write_bytes(raw)
    return raw


def quarters_between(start: date, end: date) -> list[tuple[int, int]]:
    out, y, q = [], start.year, (start.month - 1) // 3 + 1
    while (y, q) <= (end.year, (end.month - 1) // 3 + 1):
        out.append((y, q))
        y, q = (y + 1, 1) if q == 4 else (y, q + 1)
    return out


def ten_k_filings(as_of: date) -> dict[int, list[tuple[str, str, str]]]:
    """CIK -> [(filed, accession, company)] for 10-Ks filed in the year
    before `as_of` (the day itself out, as in `pit`)."""
    start = as_of - timedelta(days=365)
    out: dict[int, list] = {}
    for y, q in quarters_between(start, as_of):
        raw = sec_get(f"https://www.sec.gov/Archives/edgar/full-index/{y}/QTR{q}/form.idx",
                      ROOT / "edgar-index" / f"{y}-QTR{q}-form.idx")
        lines = raw.decode("latin-1").splitlines()
        body = lines[next(i for i, l in enumerate(lines) if l.startswith("---")) + 1:]
        for line in body:
            form = line[:12].strip()
            if form not in TEN_K_FORMS:
                continue
            # fixed columns: form, company, CIK, date, file name
            parts = line[12:].rsplit(None, 3)
            if len(parts) != 4:
                continue
            company, cik, filed, path = parts
            if not (start.isoformat() <= filed < as_of.isoformat()):
                continue
            accession = path.rsplit("/", 1)[-1].removesuffix(".txt")
            out.setdefault(int(cik), []).append((filed, accession, company.strip()))
    return out


def frame_floats(as_of: date) -> dict[int, tuple[float, str]]:
    """CIK -> (public float, as-of date): the newest float dated before
    `as_of` in the frames of the two years before it.

    A CANDIDATE LIST ONLY. A frame keeps the LATEST filing for a period, so
    its value may come from a filing after `as_of` (Stanley Black & Decker
    re-stated its 2017-06-30 float in a 10-K filed 2019) and its accession
    is not the 10-K's (United Technologies repeats its float in every 10-Q;
    the frame holds the last). Matching on accession dropped both. The
    exact line is `pit_float` on the filer's own facts, cut to the date.
    """
    out: dict[int, tuple[float, str]] = {}
    for y, q in quarters_between(as_of - timedelta(days=730), as_of):
        try:
            raw = sec_get(f"https://data.sec.gov/api/xbrl/frames/dei/EntityPublicFloat/USD/CY{y}Q{q}I.json",
                          ROOT / "frames" / f"EntityPublicFloat-CY{y}Q{q}I.json")
        except urllib.error.HTTPError:
            continue
        for row in json.loads(raw).get("data", []):
            if row["end"] >= as_of.isoformat():
                continue
            prev = out.get(int(row["cik"]))
            if prev is None or row["end"] > prev[1]:
                out[int(row["cik"])] = (float(row["val"]), row["end"])
    return out


def pit_float(facts: dict, as_of: date) -> tuple[float, str, str] | None:
    """(float, as-of date, filed) -- the newest public float the filer had
    filed before `as_of`, the latest filing of that date winning."""
    from . import pit as P
    best = None
    for unit, rows in (facts.get("facts", {}).get("dei", {})
                       .get("EntityPublicFloat", {}).get("units", {}).items()):
        if unit != "USD":
            continue
        for r in rows:
            if not P.visible(r, as_of):
                continue
            key = (r["end"], r["filed"])
            if best is None or key > best[0]:
                best = (key, float(r["val"]))
    return None if best is None else (best[1], best[0][0], best[0][1])


def submission(cik: int) -> dict:
    """SIC, name and tickers for one filer (cached compactly)."""
    cache = ROOT / "submissions" / f"CIK{cik:010d}.json"
    if cache.exists():
        return json.loads(cache.read_text())
    raw = json.loads(sec_get(f"https://data.sec.gov/submissions/CIK{cik:010d}.json"))
    keep = {k: raw.get(k) for k in ("cik", "name", "sic", "sicDescription",
                                    "tickers", "exchanges", "formerNames")}
    cache.parent.mkdir(parents=True, exist_ok=True)
    cache.write_text(json.dumps(keep))
    return keep


def excluded_sic(sic) -> bool:
    try:
        code = int(sic)
    except (TypeError, ValueError):
        return False
    return any(code in r for r in EXCLUDED_SIC)


#: the candidate margin under the line: a float re-stated after the date by
#: up to a third still reaches the exact test
CANDIDATE_MIN = FLOAT_MIN * 2 / 3


def build(as_of: date) -> dict:
    """The CANDIDATES on `as_of`, with every count on the way. The exact
    float line is applied per name once its facts are fetched (`pit_float`)."""
    filers = ten_k_filings(as_of)
    floats = frame_floats(as_of)
    rows, no_float = [], 0
    for cik, filings in filers.items():
        filings.sort()
        filed, accession, company = filings[-1]
        if cik not in floats:
            no_float += 1
            continue
        value, float_date = floats[cik]
        rows.append({"cik": cik, "company": company, "ten_k_filed": filed,
                     "ten_k_accession": accession, "frame_float": value,
                     "frame_float_date": float_date})
    candidates = [r for r in rows if r["frame_float"] >= CANDIDATE_MIN]
    # Four at a time: each worker pauses PAUSE after a request, so SEC sees
    # well under its ten a second; the fetch is network-bound, not paced.
    from concurrent.futures import ThreadPoolExecutor
    with ThreadPoolExecutor(4) as pool:
        list(pool.map(submission, [r["cik"] for r in candidates]))
    kept, financial, sic_missing = [], 0, 0
    for r in candidates:
        sub = submission(r["cik"])
        r["sic"], r["sic_description"] = sub.get("sic"), sub.get("sicDescription")
        r["tickers_today"] = sub.get("tickers") or []
        if not r["sic"]:
            sic_missing += 1
        if excluded_sic(r["sic"]):
            financial += 1
            continue
        kept.append(r)
    over = sum(1 for r in kept if r["frame_float"] >= FLOAT_MIN)
    return {"as_of": as_of.isoformat(),
            "counts": {"ten_k_filers": len(filers),
                       "no_float_in_any_frame": no_float,
                       "with_frame_float": len(rows),
                       f"candidates_frame_float_at_least_{CANDIDATE_MIN / 1e6:.0f}m": len(candidates),
                       "financial_or_reit_excluded": financial,
                       "sic_missing_kept": sic_missing,
                       "candidates": len(kept),
                       f"of_which_frame_float_at_least_{FLOAT_MIN / 1e6:.0f}m": over,
                       "no_ticker_today": sum(1 for r in kept if not r["tickers_today"])},
            "rows": sorted(kept, key=lambda r: r["cik"])}


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--date", action="append", type=date.fromisoformat)
    args = ap.parse_args(argv)
    for as_of in args.date or TEST_DATES:
        u = build(as_of)
        out = ROOT / "universe" / f"{as_of.isoformat()}.json"
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(json.dumps(u, indent=1))
        print(as_of, json.dumps(u["counts"]), flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
