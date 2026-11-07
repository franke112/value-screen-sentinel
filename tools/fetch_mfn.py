"""Fetch Nordic reports (annual, interim, year-end) as PDF from MFN's public feed.

    .venv/bin/python tools/fetch_mfn.py ZZ-B.ST EVO.ST          # fetch for named tickers
    .venv/bin/python tools/fetch_mfn.py --queue                  # every non-US name in config/queue.yaml
    .venv/bin/python tools/fetch_mfn.py --queue --dry-run        # list, write nothing
    .venv/bin/python tools/fetch_mfn.py EVO.ST --since 2016-01-01 --kinds annual
    .venv/bin/python tools/fetch_mfn.py --queue --days 45     # the nightly timer (vss-mfn.timer, 22:40)
    .venv/bin/python tools/fetch_mfn.py --queue --since 2015-01-01 --record-only   # back-fill entries only

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

ESEF PACKAGES. An annual report filed under ESEF also comes as a zipped
XBRL report package; MFN serves it as ``.xbri`` or ``.zip`` declared
``application/octet-stream`` or ``application/zip``. It is accepted BY ITS
BYTES -- ``PK`` plus a ``META-INF/taxonomyPackage.xml`` inside -- never by its
name, and saved as ``.zip`` (the extension follows the bytes, as in
``vss/nordic.py``). First North issuers (Zinzino) have none: ESEF does not
apply to an MTF.

PROVENANCE. Every file written gets a ``sources/manifest.json`` entry in the
record shape of ``vss/nordic.py`` ``_record_for`` (URL, SHA-256, bytes,
release time, declared vs actual type, ``downloaded_at``), with
``source: mfn``. A file already on disk under the name this tool would give
it, with NO entry, is fetched again and compared: byte-identical -> the entry
is written and marked ``recorded_after_the_fact``; different -> no entry, and
the run says so (fail closed: nothing is attributed to a URL whose bytes do
not match).

It writes nothing else: no manual figures, no watchlist, no history.
The ticker -> MFN issuer mapping is cached in ``config/mfn_entities.yaml``
(checked by hand when the lookup is ambiguous: the tool says so and skips).
"""
from __future__ import annotations

import argparse
import hashlib
import io
import re
import sys
import time
import zipfile
from datetime import date, datetime
from pathlib import Path

import requests
import yaml

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from vss import nordic  # noqa: E402

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


# --- what arrived ------------------------------------------------------------

ORIGIN = "mfn"
PRIMARY_SOURCE_BASIS = (
    "the issuer's own regulatory release, as distributed by its newswire and "
    "carried on MFN's public feed (source 'cis' = Cision); the attachment is "
    "the document the issuer published"
)
#: Declared types under which an ESEF package has been served. Only a
#: candidate: the BYTES decide (`classify`).
PACKAGE_DECLARED = frozenset({"application/octet-stream", "application/zip",
                              "application/x-zip-compressed"})


def is_esef_package(body: bytes, _depth: int = 0) -> bool:
    """A ZIP holding an XBRL report package's META-INF/taxonomyPackage.xml --
    or a wrapper holding exactly ONE such package (EVO's 2024 filing came as
    a validator's bundle with the package under Submission/)."""
    if not body.startswith(b"PK"):
        return False
    try:
        with zipfile.ZipFile(io.BytesIO(body)) as z:
            names = z.namelist()
            if any(n.replace("\\", "/").endswith("META-INF/taxonomyPackage.xml") for n in names):
                return True
            if _depth:
                return False
            inner = [n for n in names if n.lower().endswith((".zip", ".xbri"))]
            return len(inner) == 1 and is_esef_package(z.read(inner[0]), 1)
    except zipfile.BadZipFile:
        return False


def classify(body: bytes) -> str | None:
    """'pdf', 'esef' or None, from the bytes alone."""
    if body.startswith(b"%PDF"):
        return "pdf"
    if is_esef_package(body):
        return "esef"
    return None


EXT = {"pdf": ".pdf", "esef": ".zip"}
CONTENT_TYPE = {"pdf": "application/pdf", "esef": "application/zip"}


def release_for(it: dict, kind: str) -> nordic.Release:
    """The MFN feed item as the `nordic.Release` that `_record_for` records."""
    c, author = it["content"], it.get("author") or {}
    tags = it["properties"].get("tags", [])
    return nordic.Release(
        disclosure_id=it.get("news_id"),
        category_id=None,
        category=kind,
        headline=c["title"],
        language=it["properties"].get("lang") or "xx",
        market=", ".join(author.get("tickers") or []),
        company=author.get("name") or "",
        released=c["publish_date"],
        message_url=it.get("url") or "",
        origin=ORIGIN,
        primary_source_basis=PRIMARY_SOURCE_BASIS,
        extra=(("source", ORIGIN),
               ("mfn_news_id", it.get("news_id")),
               ("mfn_feed_source", it.get("source")),
               ("mfn_tags", list(tags)),
               ("lei", list(author.get("leis") or []))),
    )


def record(it: dict, kind: str, period: str, att_index: int, att: dict,
           name: str, body: bytes, what: str, stamp: datetime) -> dict:
    declared = att.get("content_type") or ""
    actual = CONTENT_TYPE[what]
    mismatch = None
    if declared != actual:
        mismatch = (f"the feed declared {declared or 'nothing'} and the bytes are "
                    f"{actual}" + (" (an ESEF report package)" if what == "esef" else "")
                    + "; the extension follows the bytes")
    rec = nordic._record_for(
        release_for(it, kind),
        nordic.Attachment(index=att_index, mimetype=declared,
                          file_name=att.get("file_title") or "", url=att["url"]),
        ticker=name.split("_", 1)[0], period=period, name=name, kind=actual,
        size=len(body), digest=hashlib.sha256(body).hexdigest(), stamp=stamp,
        mismatch=mismatch)
    if what == "esef":
        rec["esef_package"] = True
    return rec


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


def existing(ticker: str) -> dict[str, set[str]]:
    """Files already in sources/ for this ticker, by publish date. The
    Nasdaq feed names kinds its own way, so the date is what is compared;
    a date is taken by ANOTHER feed when a file on it is not one this tool
    names for that report (`mine`)."""
    got: dict[str, set[str]] = {}
    for f in SOURCES.glob(f"{ticker}_*"):
        p = f.name.split("_")
        if len(p) >= 5:
            got.setdefault(p[3], set()).add(f.name)
    return got


def mine(name: str, stem: str) -> bool:
    """`stem` is ``<T>_<per>_<kind>_<date>_<lang>_a``; this tool's own files
    are that stem plus an index and .pdf or .zip."""
    return re.fullmatch(re.escape(stem) + r"\d+\.(pdf|zip)", name) is not None


def run(tickers: list[str], since: date, kinds: set[str], lang: str, dry: bool,
        record_only: bool = False) -> tuple[int, list[str]]:
    names = names_from_config()
    cache = (yaml.safe_load(ENTITIES.read_text()) if ENTITIES.exists() else None) or {}
    manifest = nordic.load_manifest(SOURCES)
    wrote = recorded = 0
    problems: list[str] = []
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
        siblings: dict[tuple[str, str], list[dict]] = {}
        for it in feed(ent["slug"], since):
            tags = it["properties"].get("tags", [])
            title = it["content"]["title"]
            if "sub:report" not in tags and not (
                    ":regulatory" in tags and re.search(ANNUAL_TITLE, title.lower())):
                continue        # some issuers' annual reports carry no report tag (ZZ-B 2020, 2021)
            k = kind_of(tags, title)
            if not k or ("annual" if k == "annual-financial-report" else "interim") not in kinds:
                continue
            leis = (it.get("author") or {}).get("leis")
            if leis and ent.get("leis") != leis:
                ent["leis"] = list(leis)
            d = it["content"]["publish_date"][:10]
            key = (k, d)
            siblings.setdefault(key, []).append(it)
            lg = it["properties"].get("lang", "")
            if key not in picked or (lg == lang and picked[key]["properties"].get("lang") != lang):
                picked[key] = it
        n_new = 0

        def stem_of(item, k, d):
            return (f"{t}_{period_of(item['content']['title'], k)}_{k}_{d}_"
                    f"{item['properties'].get('lang') or 'xx'}_a")

        date_stems: dict[str, set[str]] = {}
        for (k, d), items in siblings.items():
            date_stems.setdefault(d, set()).update(stem_of(x, k, d) for x in items)

        def backfill(src, k, per, j, a, name, want) -> None:
            """On disk under this tool's name, no entry: fetch again and
            compare before recording. Never writes the file."""
            nonlocal recorded
            f = SOURCES / name
            if not f.exists() or nordic.manifest_entry(manifest, name) is not None:
                return
            if dry:
                print(f"{t:10s} WOULD-RECORD {name}")
                return
            body = _get(a["url"]).content
            on_disk = f.read_bytes()
            if hashlib.sha256(body).digest() != hashlib.sha256(on_disk).digest():
                print(f"{t:10s} DIFFERS {name}: on disk is not what {a['url']} serves now; NO entry written")
                problems.append(name)
                return
            rec = record(src, k, per, j, a, name, on_disk, want,
                         datetime.fromtimestamp(f.stat().st_mtime).astimezone())
            rec["downloaded_at_basis"] = "the file's modification time on disk"
            rec["recorded_after_the_fact"] = (
                f"the file was on disk with no manifest entry (fetched by tools/fetch_mfn.py "
                f"before it wrote entries); on {date.today()} the feed URL was fetched again "
                f"and its bytes are identical to the file's, so the entry was written from "
                f"the feed item and the bytes on disk")
            manifest["downloads"].append(rec)
            recorded += 1
            print(f"{t:10s} RECORD {name}")

        for (k, d), it in sorted(picked.items(), key=lambda x: x[0][1]):
            title = it["content"]["title"]
            per = period_of(title, k)
            stem = stem_of(it, k, d)
            # 1. back-fill: every language edition's files already on disk
            for sib in siblings[(k, d)]:
                sstem, sper = stem_of(sib, k, d), period_of(sib["content"]["title"], k)
                atts = sib["content"].get("attachments") or []
                sp = [(j, a) for j, a in enumerate(atts) if a.get("content_type") == "application/pdf"]
                sz = [(j, a) for j, a in enumerate(atts) if a.get("content_type") in PACKAGE_DECLARED]
                for i, (j, a) in enumerate(sp):
                    backfill(sib, k, sper, j, a, f"{sstem}{i}.pdf", "pdf")
                for i, (j, a) in enumerate(sz):
                    backfill(sib, k, sper, j, a, f"{sstem}{i}.zip", "esef")
            if record_only:
                continue
            # 2. download. Another feed (Nasdaq) has this report when a file
            # on its date is no MFN edition's: its PDF is not fetched twice,
            # but its ESEF package is taken unless one is on disk
            other = [n for n in have.get(d, ())
                     if not any(mine(n, st) for st in date_stems.get(d, ()))]
            all_atts = it["content"].get("attachments") or []
            pdfs = [(j, a) for j, a in enumerate(all_atts) if a.get("content_type") == "application/pdf"]
            # ESEF packages: from this item; from a sibling language edition
            # only when this one carries none (both editions often carry the
            # same package under two URLs)
            pkgs = []
            for sib in [it] + [x for x in siblings[(k, d)] if x is not it]:
                pkgs = [(sib, j, a) for j, a in enumerate(sib["content"].get("attachments") or [])
                        if a.get("content_type") in PACKAGE_DECLARED]
                if pkgs:
                    break
            if any(n.endswith(".zip") for n in have.get(d, ()) if n not in other):
                pkgs = []       # an MFN edition's package is already here
            if other:
                pdfs = []
                if any(n.endswith(".zip") for n in other):
                    pkgs = []
                if not pkgs:
                    continue
            if not pdfs and not pkgs:
                if not have.get(d):
                    print(f"{t:10s} NOPDF {d} {k} {title[:60]}")
                continue
            jobs = [(it, j, a, f"{stem}{i}.pdf", "pdf") for i, (j, a) in enumerate(pdfs)]
            jobs += [(sib, j, a, f"{stem}{i}.zip", "esef") for i, (sib, j, a) in enumerate(pkgs)]
            for src, j, a, name, want in jobs:
                f = SOURCES / name
                if f.exists():
                    continue
                if dry:
                    print(f"{t:10s} WOULD {name}  <- {title[:50]}")
                    n_new += 1
                    continue
                body = _get(a["url"]).content
                got = classify(body)
                if got != want:
                    print(f"{t:10s} NOT{want.upper()} {a['url']} (bytes are {got or 'neither PDF nor an ESEF package'}); skipped")
                    continue
                print(f"{t:10s} GET   {name}  <- {title[:50]}")
                n_new += 1
                f.write_bytes(body)
                manifest["downloads"].append(
                    record(src, k, per, j, a, name, body, want, datetime.now().astimezone()))
                wrote += 1
                nordic.save_manifest(manifest, SOURCES)   # after each file: a crash loses nothing
        if not dry:
            nordic.save_manifest(manifest, SOURCES)
        print(f"{t:10s} done  mfn:{ent['slug']}  {len(picked)} reports since {since}, {n_new} new file(s)")
    if not dry:
        ENTITIES.write_text("# ticker -> MFN issuer, found by tools/fetch_mfn.py; edit by hand if wrong\n"
                            + yaml.safe_dump(cache, sort_keys=True, allow_unicode=True))
    if recorded:
        print(f"{recorded} manifest entr(y/ies) recorded after the fact")
    if problems:
        print(f"{len(problems)} file(s) on disk DIFFER from the feed and have no entry: {problems}")
    return wrote, problems


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("tickers", nargs="*")
    ap.add_argument("--queue", action="store_true", help="every Nordic name in config/queue.yaml")
    ap.add_argument("--since", default=None, help="YYYY-MM-DD (default: five years back)")
    ap.add_argument("--days", type=int, default=None, help="look back N days (the nightly timer: 45)")
    ap.add_argument("--kinds", default="annual,interim", help="annual, interim, or both")
    ap.add_argument("--lang", default="en", help="preferred language when a report comes in two")
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--record-only", action="store_true",
                    help="write manifest entries for files already on disk (after a "
                         "byte-for-byte compare with the feed); download nothing")
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
    n, problems = run(ts, since, set(a.kinds.split(",")), a.lang, a.dry_run, a.record_only)
    print(f"{n} file(s) written to sources/")
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())
