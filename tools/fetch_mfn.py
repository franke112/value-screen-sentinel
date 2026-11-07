"""Fetch Nordic reports (annual, interim, year-end) as PDF from MFN's public feed.

    .venv/bin/python tools/fetch_mfn.py ZZ-B.ST EVO.ST          # fetch for named tickers
    .venv/bin/python tools/fetch_mfn.py --queue                  # every non-US name in config/queue.yaml
    .venv/bin/python tools/fetch_mfn.py --queue --dry-run        # list, write nothing
    .venv/bin/python tools/fetch_mfn.py EVO.ST --since 2016-01-01 --kinds annual
    .venv/bin/python tools/fetch_mfn.py --queue --days 45     # the nightly timer (vss-mfn.timer, 22:40)

WHY MFN. The PDFs Avanza shows are the issuers' own press releases,
distributed through MFN or Cision. MFN carries both (Cision items come through
with source "cis"), is public, needs no login, and serves a JSON feed per
issuer: ``https://mfn.se/all/a/<slug>.json`` with tags such as
``sub:report:annual``, ``sub:report:interim`` and ``sub:report:interim:q4``.
Avanza's own API carries no report files (checked 2026-11-07).

WHAT IT WRITES: PDFs into ``sources/``, named like their neighbours,
``<TICKER>_<period>_<kind>_<date>_<lang>_a<n>.pdf``. ``period`` is read from
the title ("Q2 2026", "third quarter 2025", "Annual report 2025") and is the
period AS THE ISSUER NAMES IT -- for an offset fiscal year (ACAD) that is the
issuer's label, not a calendar quarter. A title that names no period gets
``UNKNOWN``. A file already on disk is never fetched again, and a report the
Nasdaq feed already put in ``sources/`` for that ticker, kind and date is
skipped.

It writes nothing else: no manual figures, no watchlist, no history.
The ticker -> MFN issuer mapping is cached in ``config/mfn_entities.yaml``
(checked by hand when the lookup is ambiguous: the tool says so and skips).
"""
from __future__ import annotations

import argparse
import re
import sys
import time
from datetime import date
from pathlib import Path

import requests
import yaml

ROOT = Path(__file__).resolve().parents[1]
SOURCES = ROOT / "sources"
ENTITIES = ROOT / "config" / "mfn_entities.yaml"
QUEUE = ROOT / "config" / "queue.yaml"
WATCHLIST = ROOT / "config" / "watchlist.yaml"
UA = {"User-Agent": "vss-research/1.0 (personal value-investing tool)"}
NORDIC = (".ST", ".HE", ".OL", ".CO", ".IC")
PAUSE = 0.5          # seconds between requests: a polite client

MONTHS = "january february march april may june july august september october november december"
WORDS = {"first": 1, "second": 2, "third": 3, "fourth": 4,
         "första": 1, "andra": 2, "tredje": 3, "fjärde": 4}


ANNUAL_TITLE = r"annual report|årsredovisning|vuosikertomus|(?<!del)årsrapport|årsberetning"


# --- naming ----------------------------------------------------------------

def kind_of(tags: list[str], title: str) -> str | None:
    t = title.lower()
    if re.search(ANNUAL_TITLE, t):
        return "annual-financial-report"
    if "sub:report:interim:q4" in tags or re.search(r"year[- ]end|bokslut|tilinpäätöstiedote|financial statement", t):
        return "financial-statement-release"
    if "sub:report:annual" in tags and "sub:report:interim" not in tags:
        return "annual-financial-report"
    if "sub:report:interim" in tags:
        if re.search(r"\bq2\b|half[- ]year|second quarter|andra kvartal|halvår|puolivuosi", t):
            return "half-year-financial-report"
        return "interim-report-q1-and-q3"
    if "sub:report:annual" in tags:
        return "annual-financial-report"
    return None


def period_of(title: str, kind: str) -> str:
    t = title.lower()
    m = re.search(r"\bq([1-4])\b[^0-9]{0,12}(20\d\d)", t) or re.search(r"(20\d\d)[^0-9]{0,6}\bq([1-4])\b", t)
    if m:
        a, b = m.groups()
        q, y = (a, b) if len(a) == 1 else (b, a)
        return f"{y}-Q{q}"
    m = re.search(r"\b(first|second|third|fourth|första|andra|tredje|fjärde)\s+(quarter|kvartalet)\D{0,12}(20\d\d)", t)
    if m:
        return f"{m.group(3)}-Q{WORDS[m.group(1)]}"
    m = re.search(r"(20\d\d)", t)
    if m:
        y = m.group(1)
        if kind == "annual-financial-report" or kind == "financial-statement-release":
            return f"{y}-FY"
        if kind == "half-year-financial-report":
            return f"{y}-Q2"
    return "UNKNOWN"


def local_symbol(ticker: str) -> str:
    """ZZ-B.ST -> 'ZZ B', EVO.ST -> 'EVO', MEKKO.HE -> 'MEKKO'."""
    return ticker.rsplit(".", 1)[0].replace("-", " ").upper()


# --- MFN -------------------------------------------------------------------

def _get(url: str, **kw):
    time.sleep(PAUSE)
    r = requests.get(url, headers=UA, timeout=30, **kw)
    r.raise_for_status()
    return r


def find_entity(ticker: str, name: str | None) -> tuple[dict | None, str]:
    """Search MFN by name, then by symbol; keep a hit whose tickers carry our symbol."""
    sym = local_symbol(ticker)
    tried = []
    for q in [x for x in (name, sym) if x]:
        q = re.sub(r"\s*\b(AB|ASA|Oyj|A/S|plc|\(publ\.?\)|publ)\b\.?", "", q, flags=re.I).strip()
        tried.append(q)
        hits = _get("https://mfn.se/search/companies", params={"query": q}).json() or []
        ok = [h for h in hits if any(t.split(":", 1)[-1].upper() == sym for t in h.get("tickers", []))]
        if len(ok) == 1:
            return ok[0], f"matched {sym} via {q!r}"
        if len(ok) > 1:
            return None, f"ambiguous: {[h['slug'] for h in ok]} for {sym}"
    return None, f"no MFN issuer carries {sym} (searched {tried})"


def feed(slug: str, since: date):
    url = f"https://mfn.se/all/a/{slug}.json?limit=100"
    while url:
        d = _get(url).json()
        items = d.get("items") or []
        for it in items:
            if it["content"]["publish_date"][:10] < since.isoformat():
                return
            yield it
        url = d.get("next_url") if items else None


# --- main ------------------------------------------------------------------

def names_from_config() -> dict[str, str | None]:
    out: dict[str, str | None] = {}
    for e in yaml.safe_load(WATCHLIST.read_text())["tickers"]:
        out[e["ticker"]] = e.get("name")
    for e in (yaml.safe_load(QUEUE.read_text()) or {}).get("names", []):
        out.setdefault(e["ticker"], e.get("name"))
        if e.get("name"):
            out[e["ticker"]] = out[e["ticker"]] or e["name"]
    return out


def existing(ticker: str) -> set[str]:
    """Publish dates already in sources/ for this ticker, from any feed: the
    Nasdaq feed names kinds its own way, so the date is what is compared."""
    got = set()
    for f in SOURCES.glob(f"{ticker}_*"):
        p = f.name.split("_")
        if len(p) >= 5:
            got.add(p[3])
    return got


def run(tickers: list[str], since: date, kinds: set[str], lang: str, dry: bool) -> int:
    names = names_from_config()
    cache = (yaml.safe_load(ENTITIES.read_text()) if ENTITIES.exists() else None) or {}
    wrote = 0
    for t in tickers:
        ent = cache.get(t)
        if not ent:
            hit, why = find_entity(t, names.get(t))
            if not hit:
                print(f"{t:10s} SKIP  {why}")
                continue
            ent = cache[t] = {"slug": hit["slug"], "name": hit["name"], "entity_id": hit["entity_id"],
                              "isins": hit.get("isins", []), "found": why}
        have = existing(t)
        picked: dict[tuple[str, str], dict] = {}
        for it in feed(ent["slug"], since):
            tags = it["properties"].get("tags", [])
            title = it["content"]["title"]
            if "sub:report" not in tags and not (
                    ":regulatory" in tags and re.search(ANNUAL_TITLE, title.lower())):
                continue        # some issuers' annual reports carry no report tag (ZZ-B 2020, 2021)
            k = kind_of(tags, title)
            if not k or ("annual" if k == "annual-financial-report" else "interim") not in kinds:
                continue
            d = it["content"]["publish_date"][:10]
            key = (k, d)
            lg = it["properties"].get("lang", "")
            if key not in picked or (lg == lang and picked[key]["properties"].get("lang") != lang):
                picked[key] = it
        n_new = 0
        for (k, d), it in sorted(picked.items(), key=lambda x: x[0][1]):
            if d in have:
                continue
            title = it["content"]["title"]
            per = period_of(title, k)
            lg = it["properties"].get("lang") or "xx"
            atts = [a for a in it["content"].get("attachments") or [] if a.get("content_type") == "application/pdf"]
            if not atts:
                print(f"{t:10s} NOPDF {d} {k} {title[:60]}")
                continue
            for i, a in enumerate(atts):
                f = SOURCES / f"{t}_{per}_{k}_{d}_{lg}_a{i}.pdf"
                if f.exists():
                    continue
                print(f"{t:10s} {'WOULD' if dry else 'GET  '} {f.name}  <- {title[:50]}")
                if not dry:
                    body = _get(a["url"]).content
                    if not body.startswith(b"%PDF"):
                        print(f"{t:10s} NOTPDF {a['url']}")
                        continue
                    f.write_bytes(body)
                    wrote += 1
                n_new += 1
        print(f"{t:10s} done  mfn:{ent['slug']}  {len(picked)} reports since {since}, {n_new} new file(s)")
    if not dry:
        ENTITIES.write_text("# ticker -> MFN issuer, found by tools/fetch_mfn.py; edit by hand if wrong\n"
                            + yaml.safe_dump(cache, sort_keys=True, allow_unicode=True))
    return wrote


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("tickers", nargs="*")
    ap.add_argument("--queue", action="store_true", help="every Nordic name in config/queue.yaml")
    ap.add_argument("--since", default=None, help="YYYY-MM-DD (default: five years back)")
    ap.add_argument("--days", type=int, default=None, help="look back N days (the nightly timer: 45)")
    ap.add_argument("--kinds", default="annual,interim", help="annual, interim, or both")
    ap.add_argument("--lang", default="en", help="preferred language when a report comes in two")
    ap.add_argument("--dry-run", action="store_true")
    a = ap.parse_args(argv)
    ts = list(a.tickers)
    if a.queue:
        ts += [e["ticker"] for e in yaml.safe_load(QUEUE.read_text())["names"]
               if e["ticker"].endswith(NORDIC) and e["ticker"] not in ts]
    if not ts:
        ap.error("name tickers or pass --queue")
    today = date.today()
    if a.days is not None:
        since = date.fromordinal(today.toordinal() - a.days)
    else:
        since = date.fromisoformat(a.since) if a.since else today.replace(year=today.year - 5)
    n = run(ts, since, set(a.kinds.split(",")), a.lang, a.dry_run)
    print(f"{n} file(s) written to sources/")
    return 0


if __name__ == "__main__":
    sys.exit(main())
