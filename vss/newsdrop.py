"""THE NEWS-DROP SCREEN (reference/NEWS-DROP-DESIGN-2026-10-29.md, §5) --
SHADOW MODE: it finds and sorts, writes no watchlist and places nothing.

    vss newsdrop [--asof YYYY-MM-DD] [--limit N] [--no-notify]

NOTIFY (owner, 2026-10-29: "skapa ntfy om ngt e värt för mig att titta på").
One ntfy message per run, and only when a DROP or EARLY flag survived the
machine's sorting -- class no-news, own-other, series or unread. Every B is
sorted away and every rise is logged only, so a day of report drops sends
nothing. Same topic and secret as `vss watch` (VSS_NTFY_URL).

Every name of the S&P 500 and Stockholm lists under ``config/universe/`` is
read off the vendor for the last three months. A name is FLAGGED when, at
the last close:

- **drop**: its 5-day total return less its index's is -10% or worse
  (design decision 1);
- **early**: its 1-day return less its index's is -5% or worse -- watched,
  classified now, but the drop rule still governs a buy;
- **rise**: +10% over 5 days -- LOGGED ONLY; the backtest
  (reference/news-drops/BACKTEST.md) found no support for buying it.

and it TRADES like a large company: a median daily turnover of 50m in its
own currency over the 60 days before (the backtest's size check -- a
mis-tagged float or a recycled ticker cannot pass it).

Index: ^SP500TR for US names, ^OMX (price, the only OMXS30 series with
history at the vendor, as the shadow book's benchmark note says) for Stockholm.

THE MECHANICAL CLASS (design §2, rule 1), from the company's own filings in
the 5-day window: an SEC 8-K item 2.02 or a 10-Q/10-K, or a Nordic
interim/annual report or profit warning, is **B-report**; 8-K items 1.03,
2.06, 4.01, 4.02, 5.02 are **B-other**; any other own filing is
**own-other**; nothing is **no-news**. A Stockholm name with no issuer in
``config/nordic_issuers.yaml`` is **unread**. B is a hard no in this track;
the rest goes to a session for the fine class (A1-A3, C) before any fair
value is looked at.

THE DEEP READ (owner 2026-10-30): every fall the sorting keeps gets the
week's headlines and the method's fv off the SEC tags (Q1-Q4, §4.2 kills,
buy line 0.80 x fv). Only a fall under fv, or one the machine cannot value,
reaches the phone.

Writes ``reports/NEWSDROP-<date>.md`` (the owner's morning read, a summary
first), ``data/newsdrop/<date>.json`` and ``data/newsdrop/NEWSDROP-<date>.md``
and appends every flag to ``data/newsdrop/log.jsonl`` -- the shadow log the
six-month test is read from (design §8b).
"""
from __future__ import annotations

import csv
import gzip
import json
import time
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from dataclasses import asdict, dataclass, field
from datetime import date, datetime, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo

import pandas as pd

OUT_DIR = Path("data/newsdrop")
#: the morning paper: where the owner reads every run's reports
REPORTS_DIR = Path("reports")
UNIVERSE_DIR = Path("config/universe")
LISTS = (("sp500-", "US", "^SP500TR"), ("omxs-large-mid-", "Stockholm", "^OMX"))
DROP = -0.10
EARLY = -0.05
RISE = 0.10
WINDOW = 5
MIN_TURNOVER = 50e6
B_OTHER_ITEMS = frozenset({"1.03", "2.06", "4.01", "4.02", "5.02"})
REPORT_FORMS = frozenset({"10-Q", "10-K", "10-Q/A", "10-K/A", "10-KT"})
NORDIC_WARNING_WORDS = ("profit warning", "vinstvarning", "revised guidance",
                        "lowers", "sänker", "justerar ned")
NEW_YORK = ZoneInfo("America/New_York")
#: A drop in the days before a report is mostly the market guessing at the
#: report -- information (2026-10-29: FICO, RDDT and CTVA all reported within
#: a week of their flag). Read as B until the report is out.
PRE_REPORT_DAYS = 10
#: A one-day move this large inside the window is what an unadjusted
#: spin-off or split looks like in a vendor series (CTVA's "-84%" on its
#: 2026-10-01 separation). The flag stands with the class `series` until the
#: series is read.
SERIES_BREAK = -0.40
#: 8-K item 2.01, completion of an acquisition or DISPOSITION: a spin-off
#: is filed under it.
DISPOSITION_ITEM = "2.01"
MATCH_CACHE = OUT_DIR / "nordic_matches.json"


@dataclass
class Flag:
    ticker: str
    name: str
    market: str
    kind: str                     # drop | early | rise
    close_date: str
    move_5d: float
    move_1d: float
    turnover: float
    mclass: str = ""              # B-report | B-other | B-pre-report | series | own-other | no-news | unread
    own: list = field(default_factory=list)
    #: the next report date the vendor knows of, where it is within
    #: PRE_REPORT_DAYS of the close
    report_soon: str = ""
    #: a split, or a one-day move a spin-off would make, inside the window
    series_note: str = ""
    #: how a Stockholm name was found on the Nordic feed when it has no
    #: entry in config/nordic_issuers.yaml
    feed_match: str = ""
    #: the close on the flag day, the price the machine's fv is read against
    close: float = 0.0
    #: news headlines from the window (Google News), for the ones worth a look
    headlines: list = field(default_factory=list)
    #: the method's fv off the SEC tags (tools/backtest/method.py, M1-M8)
    machine: dict = field(default_factory=dict)
    #: under-buy-line | under-fv | over-fv | quality-fails | hard-kill | no-fv
    verdict: str = ""


# --- the universe ------------------------------------------------------------

def universe(directory: Path = UNIVERSE_DIR) -> list[tuple[str, str, str, str]]:
    """(yahoo ticker, name, market, index) from the newest file of each list."""
    out = []
    for prefix, market, index in LISTS:
        files = sorted(directory.glob(f"{prefix}*.csv"))
        if not files:
            raise FileNotFoundError(f"no {prefix}*.csv under {directory}")
        with files[-1].open(newline="") as fh:
            for row in csv.DictReader(fh):
                if row.get("instrumenttyp", "EQUITY") != "EQUITY":
                    continue
                out.append((row["ticker_yahoo"], row["namn"], market, index))
    return out


# --- prices --------------------------------------------------------------------

def _history(ticker: str) -> pd.DataFrame | None:
    from .fetch import fetch_live
    try:
        frame = fetch_live(ticker, period="3mo")
    except Exception:  # noqa: BLE001 -- a miss is counted, not fatal
        return None
    frame.index = pd.to_datetime([pd.Timestamp(i).date() for i in frame.index])
    return frame[~frame.index.duplicated()]


def moves(frame: pd.DataFrame, index: pd.Series, asof: date):
    """(close date, 5-day excess, 1-day excess, median 60-day turnover) at
    the last close on or before ``asof``; None where the series is short."""
    px = frame["Close"].astype(float)
    both = pd.concat([px, index], axis=1, join="inner").dropna()
    both = both[both.index <= pd.Timestamp(asof)]
    if len(both) < WINDOW + 2:
        return None
    p, i = both.iloc[:, 0], both.iloc[:, 1]
    r5 = p.iloc[-1] / p.iloc[-1 - WINDOW] - i.iloc[-1] / i.iloc[-1 - WINDOW]
    r1 = p.iloc[-1] / p.iloc[-2] - i.iloc[-1] / i.iloc[-2]
    turnover = (frame["Close"] * frame["Volume"]).astype(float)
    turnover = turnover[turnover.index < both.index[-1]].tail(60).median()
    return both.index[-1].date(), float(r5), float(r1), float(turnover)


def series_note(frame: pd.DataFrame, close_day: date) -> str:
    """A split or a spin-off-sized one-day move in the 5-day window, or ""."""
    win = frame[frame.index <= pd.Timestamp(close_day)].tail(WINDOW + 1)
    notes = []
    if "Stock Splits" in win.columns:
        for day, ratio in win["Stock Splits"].items():
            if ratio and float(ratio) not in (0.0, 1.0):
                notes.append(f"split {float(ratio):g} on {day.date()}")
    one_day = win["Close"].astype(float).pct_change().dropna()
    for day, r in one_day.items():
        if r <= SERIES_BREAK:
            notes.append(f"{r:+.0%} in one day on {day.date()} (spin-off or unadjusted split?)")
    return "; ".join(notes)


def next_report(ticker: str, close_day: date) -> str:
    """The vendor's next earnings date where it falls within PRE_REPORT_DAYS
    after the close, else "". A missing calendar is "" -- not evidence."""
    import yfinance as yf
    try:
        cal = yf.Ticker(ticker).calendar
        dates = cal.get("Earnings Date") if isinstance(cal, dict) else None
    except Exception:  # noqa: BLE001
        return ""
    for d in dates or []:
        d = d if isinstance(d, date) else pd.Timestamp(d).date()
        # the close day itself counts: a report after the close (RDDT
        # 2026-10-29) is still to come for the price that was read
        if close_day <= d <= close_day + timedelta(days=PRE_REPORT_DAYS):
            return d.isoformat()
    return ""


# --- the company's own filings ---------------------------------------------------

def _sec_get(url: str) -> bytes:
    from .xbrl import user_agent
    req = urllib.request.Request(url, headers={"User-Agent": user_agent(),
                                               "Accept-Encoding": "gzip"})
    with urllib.request.urlopen(req, timeout=60) as r:
        raw = r.read()
        if (r.headers.get("Content-Encoding") or "") == "gzip":
            raw = gzip.decompress(raw)
    time.sleep(0.12)
    return raw


def sec_ciks(cache: Path = OUT_DIR / "company_tickers.json") -> dict[str, int]:
    """Ticker -> CIK from SEC's own list, refreshed once a day."""
    if not cache.exists() or date.fromtimestamp(cache.stat().st_mtime) < date.today():
        cache.parent.mkdir(parents=True, exist_ok=True)
        cache.write_bytes(_sec_get("https://www.sec.gov/files/company_tickers.json"))
    rows = json.loads(cache.read_text()).values()
    return {r["ticker"].upper(): int(r["cik_str"]) for r in rows}


def sec_filings(cik: int, since: date, until: date) -> list[tuple[str, str, str]]:
    """(effective trading date, form, items) filed in (since, until]: after
    16:00 New York counts for the next day."""
    recent = json.loads(_sec_get(f"https://data.sec.gov/submissions/CIK{cik:010d}.json"))["filings"]["recent"]
    out = []
    for form, filed, acc, items in zip(recent["form"], recent["filingDate"],
                                       recent["acceptanceDateTime"], recent["items"]):
        day = filed
        try:
            t = datetime.fromisoformat(acc.replace("Z", "+00:00")).astimezone(NEW_YORK)
            day = (t.date() + timedelta(days=1)).isoformat() if t.hour >= 16 else t.date().isoformat()
        except ValueError:
            pass
        # insider and holder forms (3/4/5, 144, 13G) are other people's
        # filings about the company, not the company saying something
        if since.isoformat() < day <= until.isoformat() and (
                form.startswith(("8-K", "10-", "SC 13D", "6-K"))):
            out.append((day, form, items or ""))
    return out


def sec_class(own: list[tuple[str, str, str]]) -> str:
    items = {i.strip() for _, form, it in own if form.startswith("8-K")
             for i in it.split(",") if i.strip()}
    if "2.02" in items or any(form in REPORT_FORMS for _, form, _ in own):
        return "B-report"
    if items & B_OTHER_ITEMS:
        return "B-other"
    if DISPOSITION_ITEM in items:
        return "series"
    if any(form.startswith("8-K") for _, form, _ in own):
        return "own-other"
    return "no-news"


def _norm(name: str) -> str:
    import re
    s = re.sub(r"\((publ\.?|PUBL\.?)\)", "", name).lower()
    s = re.sub(r"[^a-z0-9åäöæø]+", " ", s).strip()
    # the feed writes "Intrum" for the universe's "Intrum AB (publ)": a legal
    # form at the end is not part of the name
    return re.sub(r"\s+(ab|asa|a s|oyj|plc|ltd|inc|sa|nv|se)$", "", s).strip()


def feed_issuer(ticker: str, name: str):
    """The Nordic feed's issuer for a Stockholm name: the stored entry where
    there is one, else the ONE candidate whose company string equals the
    universe name once '(publ)' and punctuation are taken out, on a
    Stockholm market. `nordic.resolve` lets the owner pick because the
    strings can differ ("PANDORA" / "Pandora A/S"); here nothing is written
    to config -- an exact match is used for the shadow class and named on
    the row, and no match leaves the name `unread`. Cached per ticker."""
    from . import nordic as N
    try:
        return N.issuer_for(ticker), "config"
    except Exception:  # noqa: BLE001 -- not configured
        pass
    cache = json.loads(MATCH_CACHE.read_text()) if MATCH_CACHE.exists() else {}
    hit = cache.get(ticker)
    if hit is None:
        search = name.replace("(publ)", "").replace("(publ.)", "").strip()
        cands = [c for c in N.resolve(ticker, search)
                 if _norm(c.company) == _norm(name) and "Stockholm" in c.market]
        hit = {"market": cands[0].market, "company": cands[0].company} if len(cands) == 1 else {}
        cache[ticker] = hit
        MATCH_CACHE.parent.mkdir(parents=True, exist_ok=True)
        MATCH_CACHE.write_text(json.dumps(cache, indent=1, ensure_ascii=False))
    if not hit:
        return None, "no exact match on the feed"
    return N.Issuer(ticker=ticker, market=hit["market"], company=hit["company"]), \
        f"auto: '{hit['company']}' ({hit['market']})"


def nordic_class(ticker: str, since: date, until: date, name: str = "") -> tuple[str, list, str]:
    from . import nordic as N
    issuer, how = feed_issuer(ticker, name or ticker)
    if issuer is None:
        return "unread", [], how
    releases, _ = N.fetch_releases(issuer, limit=40)
    rels = [r for r in releases
            if since.isoformat() < r.released_date <= until.isoformat()]
    own = [f"{r.released_date} {r.category}: {r.headline}" for r in rels]
    if any(r.is_report_category for r in rels) or any(
            w in r.headline.lower() for r in rels for w in NORDIC_WARNING_WORDS):
        return "B-report", own, how
    return ("own-other" if rels else "no-news"), own, how


# --- the run -------------------------------------------------------------------

def scan(asof: date, limit: int | None = None, workers: int = 4) -> tuple[list[Flag], dict]:
    names = universe()[:limit] if limit else universe()
    indexes = {ix: _history(ix) for ix in {n[3] for n in names}}
    idx_close = {k: (v["Close"].astype(float) if v is not None else None) for k, v in indexes.items()}
    with ThreadPoolExecutor(workers) as pool:
        frames = list(pool.map(lambda n: _history(n[0]), names))
    flags, counts = [], {"names": len(names), "no_prices": 0, "too_small": 0, "short": 0}
    for (ticker, name, market, ix), frame in zip(names, frames):
        if frame is None or idx_close[ix] is None:
            counts["no_prices"] += 1
            continue
        got = moves(frame, idx_close[ix], asof)
        if got is None:
            counts["short"] += 1
            continue
        day, r5, r1, turnover = got
        kind = ("drop" if r5 <= DROP else "early" if r1 <= EARLY else
                "rise" if r5 >= RISE else "")
        if not kind:
            continue
        if not turnover >= MIN_TURNOVER:
            counts["too_small"] += 1
            continue
        f = Flag(ticker, name, market, kind, day.isoformat(), r5, r1, turnover,
                 close=float(frame["Close"].loc[pd.Timestamp(day)]))
        f.series_note = series_note(frame, day)
        flags.append(f)
    _classify(flags)
    for f in flags:
        if f.series_note and not f.mclass.startswith("B-"):
            f.mclass = "series"
        if f.kind != "rise" and f.mclass in ("no-news", "own-other", "unread"):
            f.report_soon = next_report(f.ticker, date.fromisoformat(f.close_date))
            if f.report_soon:
                f.mclass = "B-pre-report"
    deepen(flags)
    return flags, counts


def _classify(flags: list[Flag]) -> None:
    ciks = None
    for f in flags:
        until = date.fromisoformat(f.close_date)
        since = until - timedelta(days=8)        # five trading days, with a weekend
        try:
            if f.market == "US":
                ciks = ciks if ciks is not None else sec_ciks()
                cik = ciks.get(f.ticker.replace("-", ".").upper()) or ciks.get(f.ticker.upper())
                if cik is None:
                    f.mclass, f.own = "unread", ["not in SEC's ticker list: read by hand"]
                    continue
                own = sec_filings(cik, since, until)
                f.mclass, f.own = sec_class(own), [f"{d} {form} {it}".strip() for d, form, it in own]
            else:
                f.mclass, f.own, f.feed_match = nordic_class(f.ticker, since, until, f.name)
        except Exception as exc:  # noqa: BLE001 -- the flag stands, unread
            f.mclass, f.own = "unread", [f"read failed: {type(exc).__name__}: {exc}"[:200]]


# --- the deep read: why it fell, and what the method says it is worth ------------
#
# Owner 2026-10-30: read the news, read the reports, and say whether the
# price is under the base fv by the Warren method. Done for every fall the
# sorting kept (`worth_a_look`). The fv is the backtest's rules on the SEC
# tags (M1-M8), not a strike: no hand legs, no events ledger, no growth view.
# It decides what reaches the owner's phone; a buy still needs the session's
# fine class and a real strike (design §2, §4).

#: design §4: buy at or under 0.80 x fv
BUY_LINE = 0.80
FACTS_DIR = OUT_DIR / "companyfacts"
ITEM_WORDS = {"1.01": "avtal", "1.02": "avtal sagt upp", "1.03": "konkurs",
              "2.01": "förvärv/avyttring klar", "2.02": "rapport", "2.03": "ny skuld",
              "2.05": "omstrukturering", "2.06": "nedskrivning", "3.01": "börsnotering",
              "4.01": "revisor byts", "4.02": "räkenskaper gäller inte", "5.02": "VD/CFO/styrelse",
              "5.07": "stämma", "7.01": "presentation (Reg FD)", "8.01": "övrigt besked",
              "9.01": "bilagor"}
#: where a fall is worth the owner's phone: under fv, or the machine could
#: not say (then only a person can)
NOTIFY_VERDICTS = ("under-buy-line", "under-fv", "no-fv")
VERDICT_WORDS = {"under-buy-line": "UNDER KÖPGRÄNS (0,80 × fv)", "under-fv": "under fv",
                 "over-fv": "över fv", "quality-fails": "faller på Q1-Q4",
                 "hard-kill": "hårt stopp (§4.2)", "no-fv": "inget maskin-fv"}


def headlines(name: str, until: date, n: int = 6, market: str = "US") -> list[str]:
    """The newest headlines naming the company in the week to ``until``."""
    import urllib.parse
    import xml.etree.ElementTree as ET
    from email.utils import parsedate_to_datetime
    # the bare name is a word too often (HP: horsepower); ask for the market's news
    query = f'"{_norm(name)}" (stock OR shares OR aktie OR aktien) when:7d'
    lang = "hl=sv&gl=SE&ceid=SE:sv" if market == "Stockholm" else "hl=en-US&gl=US&ceid=US:en"
    url = f"https://news.google.com/rss/search?q={urllib.parse.quote(query)}&{lang}"
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=30) as r:
        root = ET.fromstring(r.read())
    out = []
    for item in root.iter("item"):
        try:
            day = parsedate_to_datetime(item.findtext("pubDate")).date()
        except (TypeError, ValueError):
            continue
        if day <= until + timedelta(days=1):
            out.append((day, (item.findtext("title") or "").strip()))
    out.sort(reverse=True)
    return [f"{d.isoformat()} {t}" for d, t in out[:n]]


def items_in_words(own: list[str]) -> list[str]:
    """'2026-10-28 8-K 5.02,9.01' -> '2026-10-28 8-K: VD/CFO/styrelse'."""
    out = []
    for line in own:
        parts = line.split(" ", 2)
        if len(parts) == 3 and parts[1].startswith("8-K"):
            words = [ITEM_WORDS.get(i.strip(), i.strip()) for i in parts[2].split(",")
                     if i.strip() != "9.01"]
            out.append(f"{parts[0]} {parts[1]}: {', '.join(words)}")
        else:
            out.append(line)
    return out


def company_facts(cik: int) -> tuple[dict, int | None]:
    """SEC companyfacts and the SIC code, cached for the day."""
    gz = FACTS_DIR / f"CIK{cik:010d}.json.gz"
    if not gz.exists() or date.fromtimestamp(gz.stat().st_mtime) < date.today():
        gz.parent.mkdir(parents=True, exist_ok=True)
        gz.write_bytes(gzip.compress(_sec_get(
            f"https://data.sec.gov/api/xbrl/companyfacts/CIK{cik:010d}.json")))
    sub = json.loads(_sec_get(f"https://data.sec.gov/submissions/CIK{cik:010d}.json"))
    sic = int(sub["sic"]) if str(sub.get("sic") or "").isdigit() else None
    return json.loads(gzip.decompress(gz.read_bytes())), sic


def machine_value(ticker: str, cik: int, asof: date, price: float) -> dict:
    from tools.backtest import method as ME     # the repo root is the working directory
    facts, sic = company_facts(cik)
    row = ME.with_price(ME.evaluate(facts, asof, ticker=ticker, cik=cik, sic=sic),
                        price, None)
    keep = ("status", "fv_base", "fv_bear", "g_base", "growth_source", "cyclical",
            "net_debt", "quality", "fv_over_price", "notes")
    out = {k: row.get(k) for k in keep}
    out["kills"] = [k["rule"] for k in row.get("kills") or [] if k["state"] == "FAIL"]
    return out


#: an fv this many times the price is a share count or a series that does not
#: match the price (CTVA 2026-10-29: fv 50.72 at 11.47 after the Vylor
#: spin-off), not a bargain -- a person reads it
ABSURD_FV_OVER_PRICE = 3.0


def verdict(m: dict, price: float) -> str:
    if not m or m.get("status") != "ok" or not m.get("fv_base"):
        return "no-fv"
    if m.get("kills"):
        return "hard-kill"
    if not all(m.get("quality", {}).values()):
        return "quality-fails"
    if price > 0 and m["fv_base"] / price > ABSURD_FV_OVER_PRICE:
        m["status"] = (f"fv {m['fv_base']:.2f} is over {ABSURD_FV_OVER_PRICE:.0f}x the price: "
                       "read the series and the share count")
        return "no-fv"
    if price <= BUY_LINE * m["fv_base"]:
        return "under-buy-line"
    return "under-fv" if price < m["fv_base"] else "over-fv"


def deepen(flags: list[Flag]) -> None:
    ciks = None
    for f in worth_a_look(flags):
        close_day = date.fromisoformat(f.close_date)
        try:
            f.headlines = headlines(f.name, close_day, market=f.market)
        except Exception as exc:  # noqa: BLE001 -- the read goes on without them
            f.headlines = [f"nyheter kunde inte läsas: {type(exc).__name__}"]
        if f.market != "US":
            f.machine = {"status": "no machine fv outside SEC filers: strike by hand"}
        else:
            try:
                ciks = ciks if ciks is not None else sec_ciks()
                cik = ciks.get(f.ticker.replace("-", ".").upper()) or ciks.get(f.ticker.upper())
                f.machine = (machine_value(f.ticker, cik, close_day, f.close) if cik
                             else {"status": "not in SEC's ticker list"})
            except Exception as exc:  # noqa: BLE001
                f.machine = {"status": f"{type(exc).__name__}: {exc}"[:200]}
        f.verdict = verdict(f.machine, f.close)


def deep_lines(f: Flag) -> list[str]:
    """The morning paper's paragraph on one fall."""
    m = f.machine
    L = [f"### {f.ticker} {f.name[:40]} -- {VERDICT_WORDS.get(f.verdict, f.verdict)}", "",
         f"{f.move_5d * 100:+.1f} % på 5 dagar mot index ({f.move_1d * 100:+.1f} % sista dagen), "
         f"stängning {f.close:.2f}, klass {f.mclass}."]
    if m.get("fv_base") and f.verdict != "no-fv":
        q = m.get("quality") or {}
        L += ["", f"Maskin-fv {m['fv_base']:.2f} (bear {m['fv_bear']:.2f}), köpgräns "
              f"{BUY_LINE * m['fv_base']:.2f}; tillväxt {m['g_base'] * 100:.1f} % "
              f"({m['growth_source']}){', cyklisk' if m.get('cyclical') else ''}. "
              f"Q1-Q4: {' '.join(f'{k}{chr(10003) if v else chr(10007)}' for k, v in q.items()) or '–'}. "
              f"Hårda stopp: {', '.join(m['kills']) or 'inga'}."]
    else:
        L += ["", f"Inget maskin-fv: {m.get('status') or '–'}."]
    if f.own:
        L += ["", "Egna besked: " + "; ".join(items_in_words(f.own))]
    if f.headlines:
        L += ["", "Nyheter:"] + [f"- {h}" for h in f.headlines]
    return L + [""]


SORTED_AWAY = {"B-report": "rapport i fönstret", "B-pre-report": "rapport inom 10 dagar",
               "B-other": "bokföring, revisor eller VD/CFO"}


def today(flags: list[Flag]) -> list[str]:
    """The morning-paper summary: what to read, what was sorted away and why."""
    look = sorted(worth_a_look(flags), key=lambda f: f.move_5d)
    falls = [f for f in flags if f.kind in ("drop", "early")]
    L = ["## I dag", ""]
    if look:
        hot = [f for f in look if f.verdict in NOTIFY_VERDICTS]
        L.append(f"**{len(hot)} av {len(look)} under maskin-fv eller utan fv** -- be sessionen "
                 "klassa dem:" if hot else
                 f"**{len(look)} fall utan egen förklaring, men inget under maskin-fv.**")
        L += [f"- **{f.ticker}** {f.name[:40]}: {f.move_5d * 100:+.1f} % på 5 dagar "
              f"({f.move_1d * 100:+.1f} % i går), {f.mclass} -- "
              f"{VERDICT_WORDS.get(f.verdict, f.verdict or '–')}" + _fv_note(f) for f in look]
    else:
        L.append("**Inget att titta på.** Varje fall hade en egen förklaring i bolagets besked.")
    away = {}
    for f in falls:
        if f.mclass in SORTED_AWAY:
            away.setdefault(SORTED_AWAY[f.mclass], []).append(f.ticker)
    if away:
        L += ["", "Bortsorterat:"]
        L += [f"- {why}: {', '.join(t)}" for why, t in away.items()]
    rises = sorted((f for f in flags if f.kind == "rise"), key=lambda f: -f.move_5d)[:5]
    if rises:
        L += ["", "Störst upp (bara för kännedom): " + ", ".join(
            f"{f.ticker} {f.move_5d * 100:+.0f} %" for f in rises)]
    return L + [""]


def _fv_note(f: Flag) -> str:
    fv = (f.machine or {}).get("fv_base")
    return f" (kurs {f.close:.2f}, fv {fv:.2f})" if fv else ""


def render(asof: date, flags: list[Flag], counts: dict) -> str:
    look = sorted(worth_a_look(flags), key=lambda f: f.move_5d)
    deep = (["## Varför det föll och vad det är värt", "",
             "Maskin-fv: metodens regler på SEC-taggarna (M1-M8, backtestets räknare) -- inga "
             "handben, ingen händelselogg, ingen tillväxtsyn. Ett köp kräver sessionens klass "
             "och en riktig strike.", ""] + [x for f in look for x in deep_lines(f)]
            if look else [])
    L = [f"# Nyhetsfall {asof.isoformat()} -- SKUGGLÄGE", ""] + today(flags) + deep + [
         "## Detaljer", "",
         f"{counts['names']} namn lästa; utan kurs {counts['no_prices']}, för kort serie "
         f"{counts['short']}, flaggade men för små {counts['too_small']}.", "",
         "Klass B är ett hårt nej i spåret (B-pre-report: rapport inom "
         f"{PRE_REPORT_DAYS} dagar). `series`: split eller avknoppning i fönstret -- läs "
         "serien först. Övriga går till sessionen för den fina klassen (design §2) "
         "innan något fv tittas på.", ""]
    for kind, title in (("drop", "Fall ≥ 10 % på 5 dagar (köpregeln)"),
                        ("early", "Tidig flagga: ≥ 5 % på en dag"),
                        ("rise", "Uppgång ≥ 10 % (loggas bara)")):
        rows = [f for f in flags if f.kind == kind]
        L += [f"### {title} -- {len(rows)}", ""]
        if not rows:
            L += ["Inga.", ""]
            continue
        L += ["| Ticker | Bolag | Marknad | 5 d | 1 d | Klass | Egna besked i fönstret | Övrigt |",
              "|---|---|---|---:|---:|---|---|---|"]
        for f in sorted(rows, key=lambda f: f.move_5d):
            L.append(f"| {f.ticker} | {f.name[:30]} | {f.market} | {f.move_5d * 100:+.1f} | "
                     f"{f.move_1d * 100:+.1f} | {f.mclass} | {'; '.join(f.own)[:160] or '–'} | "
                     + "; ".join(x for x in (f.report_soon and f"rapport {f.report_soon}",
                                             f.series_note, f.feed_match) if x) + " |")
        L.append("")
    return "\n".join(L)


#: the classes a person should look at; everything else is sorted away
LOOK_AT = ("no-news", "own-other", "series", "unread")


def worth_a_look(flags: list[Flag]) -> list[Flag]:
    return [f for f in flags if f.kind in ("drop", "early") and f.mclass in LOOK_AT]


def notify_lines(asof: date, flags: list[Flag]) -> list[str]:
    out = []
    for f in sorted(worth_a_look(flags), key=lambda f: f.move_5d):
        if f.verdict not in NOTIFY_VERDICTS:
            continue
        why = (f.headlines[:1] or items_in_words(f.own[:1]) or [f.series_note])[0]
        out.append(f"{f.ticker} {f.name[:28]}: {f.move_5d * 100:+.1f}% 5d -- "
                   f"{VERDICT_WORDS[f.verdict]}{_fv_note(f)}" + (f" -- {why[:90]}" if why else ""))
    if out:
        out.append(f"reports/NEWSDROP-{asof.isoformat()}.md -- be sessionen klassa")
    return out


def run_newsdrop(*, asof: date, limit: int | None = None, notify: bool = True,
                 out_dir: Path = OUT_DIR,
                 reports_dir: Path | None = REPORTS_DIR) -> tuple[int, str]:
    flags, counts = scan(asof, limit=limit)
    out_dir.mkdir(parents=True, exist_ok=True)
    payload = {"asof": asof.isoformat(), "counts": counts, "flags": [asdict(f) for f in flags]}
    (out_dir / f"{asof.isoformat()}.json").write_text(json.dumps(payload, indent=1))
    text = render(asof, flags, counts)
    (out_dir / f"NEWSDROP-{asof.isoformat()}.md").write_text(text + "\n")
    if reports_dir is not None:
        reports_dir.mkdir(parents=True, exist_ok=True)
        (reports_dir / f"NEWSDROP-{asof.isoformat()}.md").write_text(text + "\n")
    with (out_dir / "log.jsonl").open("a") as log:
        for f in flags:
            log.write(json.dumps({"logged": asof.isoformat(), **asdict(f)}) + "\n")
    if notify:
        from .watch import post_ntfy
        lines = notify_lines(asof, flags)
        sent = post_ntfy(lines, title=f"vss newsdrop: {len(lines) - 1} under fv"
                         if lines else None)
        text += f"\n\nntfy: {sent}"
    return 0, text
