"""`vss queue` -- THE QUEUE'S WATCHMAN (owner, 2026-11-05): every name we
have valued, read every night against its lines, and ONE ntfy message when
something changed. It writes reports/QUEUE-<date>.md and data/queue_state.json
and NOTHING ELSE -- never the watchlist, never a store, never a value.

    vss queue                 # the nightly run (timer vss-queue, after vss run)
    vss queue --no-notify     # write the report, POST nothing
    vss queue --only EVO.ST   # one name, for a check

WHAT IS READ (config/queue.yaml, built by tools/build_queue.py):

* the BUY line -- base x the E90 cushion of the name's tier (0.85 / 0.75 /
  0.65), the MBP `vss run` computes. Only a kind=strike row with a tier has
  one.
* the LOOK line -- a name with no tier: base x 0.85 for a strike, x 0.75 for
  a machine or rough value (a rougher number needs the wider margin). It
  means "strike it properly now", never "buy".
* the SELL lines of a held name -- every `sell_at` written by hand, and the
  bull case.
* the GATE -- `gate_until` / `gate_event`: once the date has passed, the
  event is due to be read, and the queue says so once.
* NEW REPORTS -- a US filer's 8-K 2.02 / 10-Q / 10-K from EDGAR; a Nordic
  issuer's report from the Nasdaq Nordic feed; anything else (LSE,
  Euronext, Xetra, Oslo) by the vendor's earnings date passing. And the
  week's headlines naming the company (Google News), in the report only --
  headlines are context, not an alert.

WHAT IS SENT. A line goes out only on a CHANGE: a name enters a zone it
was not in last night (buy, look, sell), a gate date passes, a report
appears. A name sitting under its line is not re-announced every night --
a watcher that repeats itself trains its reader to ignore it.

What is NOT a buy signal here: a DROPPED name gets no price lines at all
(it failed the quality bar; only a new report brings it back for a re-read),
and a WATCH-GATED name in a zone is shown in the report but not sent until
its gate has lifted.
"""
from __future__ import annotations

import json
import re
import urllib.parse
import urllib.request
from dataclasses import dataclass, field
from datetime import date, timedelta
from pathlib import Path
from typing import Callable

import yaml

ROOT = Path(__file__).resolve().parents[1]
QUEUE_PATH = ROOT / "config" / "queue.yaml"
STATE_PATH = ROOT / "data" / "queue_state.json"
REPORT_DIR = ROOT / "reports"
TIER_CUSHION = {1: 0.85, 2: 0.75, 3: 0.65}
LOOK_STRIKE = 0.85
LOOK_ROUGH = 0.75
NORDIC_SUFFIXES = (".ST", ".HE", ".CO")
NO_PRICE_LINES = ("DROPPED",)
GATED = ("WATCH-GATED",)
FIRST_RUN_DAYS = 3


@dataclass
class Row:
    ticker: str
    kind: str
    ccy: str | None
    base: float
    bear: float | None = None
    bull: float | None = None
    status: str = "OFF-WATCHLIST"
    tier: int | None = None
    stop: float | None = None
    gate_until: str | None = None
    gate_event: str | None = None
    sell_at: list = field(default_factory=list)
    note: str | None = None
    look_at: float | None = None      # hand line: overrides base x cushion (a name's own revisit level)
    source: str | None = None
    name: str | None = None

    @classmethod
    def from_dict(cls, d: dict) -> "Row":
        kw = {k: d[k] for k in cls.__dataclass_fields__ if k in d}
        kw["sell_at"] = kw.get("sell_at") or []
        return cls(**kw)


def load_queue(path: Path = QUEUE_PATH) -> list[Row]:
    return [Row.from_dict(d) for d in (yaml.safe_load(path.read_text()) or {}).get("names", [])]


# --- lines -----------------------------------------------------------------

def buy_line(r: Row) -> float | None:
    if r.kind == "strike" and r.tier in TIER_CUSHION and r.base and r.base > 0:
        return round(r.base * TIER_CUSHION[r.tier], 2)
    return None


def look_line(r: Row) -> float | None:
    if buy_line(r) is not None or not r.base or r.base <= 0:
        return None
    if r.look_at is not None:
        return float(r.look_at)
    return round(r.base * (LOOK_STRIKE if r.kind == "strike" else LOOK_ROUGH), 2)


def gate_open(r: Row, asof: date) -> bool:
    if r.status not in GATED:
        return True
    return bool(r.gate_until) and date.fromisoformat(str(r.gate_until)) <= asof


def zone(r: Row, price: float | None) -> str:
    """The one zone a price puts a name in tonight."""
    if price is None:
        return "no-price"
    if r.status == "HELD":
        hits = [s for s in (r.sell_at or []) if price >= float(s["price"])]
        if r.bull and price >= r.bull:
            return "sell:bull"
        if hits:
            return f"sell:{max(float(s['price']) for s in hits):g}"
        return "held"
    if r.status in NO_PRICE_LINES:
        return "dropped"
    b, lk = buy_line(r), look_line(r)
    if b is not None and price <= b:
        return "buy"
    if lk is not None and price <= lk:
        return "look"
    return "above"


# --- the world (each one replaceable in a test) ------------------------------

def last_close(ticker: str) -> tuple[str | None, float | None]:
    """The last settled close, read the way `vss run` reads it: the live
    response MERGED into the nightly cache (E122), never written back. The
    vendor blanks a day's close it served the night before (ZZ-B.ST
    2026-11-04: 115.50 in the cache, NaN live the next morning); the merge
    keeps it."""
    import logging
    from datetime import datetime
    from .fetch import get_history
    logging.getLogger("vss.fetch").setLevel(logging.WARNING)   # the merge narrates every retained day
    try:
        res = get_history(ticker, ROOT / "data" / "cache", now=datetime.now(), write=False)
        h = res.frame["Close"].dropna() if res.frame is not None else []
    except Exception:  # noqa: BLE001
        return None, None
    if not len(h):
        return None, None
    d = h.index[-1]
    return (d.date() if hasattr(d, "date") else d).isoformat(), float(h.iloc[-1])


def reports_since(r: Row, since: date, until: date) -> list[str]:
    """The company's own reports in (since, until], in words."""
    from . import newsdrop as N
    t = r.ticker
    try:
        if "." not in t:
            cik = N.sec_ciks().get(t.upper())
            if cik is None:
                return []
            own = N.sec_filings(cik, since, until)
            hits = [(d, f, i) for d, f, i in own
                    if f in ("10-Q", "10-K", "10-K/A", "20-F", "6-K")
                    or (f.startswith("8-K") and "2.02" in i)]
            return [f"{d} {f}{' item 2.02 (results)' if '2.02' in i else ''}" for d, f, i in hits]
        if t.endswith(NORDIC_SUFFIXES):
            cls, own, _ = N.nordic_class(t, since, until, r.name or t)
            if cls == "B-report":
                return own
        # no filing feed for this exchange: the vendor's earnings date passing
        import pandas as pd
        import yfinance as yf
        cal = yf.Ticker(t).calendar
        for d in (cal.get("Earnings Date") if isinstance(cal, dict) else None) or []:
            d = d if isinstance(d, date) else pd.Timestamp(d).date()
            if since < d <= until:
                return [f"{d.isoformat()} report day (vendor calendar -- no filing feed for this exchange)"]
    except Exception as exc:  # noqa: BLE001
        return [f"(report check failed: {type(exc).__name__})"]
    return []


def news(r: Row, until: date, n: int = 4) -> list[str]:
    import xml.etree.ElementTree as ET
    from email.utils import parsedate_to_datetime
    if not r.name:      # a bare ticker searches the world (KO: Korean pop; MMS: spam)
        return []
    name = re.sub(r"\s*\((publ\.?|class [a-z])\)|,?\s+(inc\.?|corp\.?|corporation|plc|ab|asa|oyj|"
                  r"n\.v\.|se|sa|a/s|company|group|holdings?)\b\.?", "", r.name, flags=re.I).strip()
    q = f'"{name}" when:3d'
    nordic = r.ticker.endswith(NORDIC_SUFFIXES)
    lang = "hl=sv&gl=SE&ceid=SE:sv" if nordic else "hl=en-US&gl=US&ceid=US:en"
    url = f"https://news.google.com/rss/search?q={urllib.parse.quote(q)}&{lang}"
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=20) as resp:
            root = ET.fromstring(resp.read())
    except Exception:  # noqa: BLE001
        return []
    out = []
    for item in root.iter("item"):
        try:
            d = parsedate_to_datetime(item.findtext("pubDate")).date()
        except (TypeError, ValueError):
            continue
        if d <= until + timedelta(days=1):
            out.append((d, (item.findtext("title") or "").strip()))
    out.sort(reverse=True)
    return [f"{d.isoformat()} {t}" for d, t in out[:n]]


# --- the run ---------------------------------------------------------------

@dataclass
class Seen:
    row: Row
    close_date: str | None
    price: float | None
    zone: str
    reports: list[str]
    headlines: list[str]
    gate_due: bool
    lines: list[str] = field(default_factory=list)   # what goes to ntfy


def _fmt(x) -> str:
    return "--" if x is None else f"{x:,.2f}"


def _company_names() -> dict[str, str]:
    p = ROOT / "config" / "watchlist.yaml"
    try:
        return {e["ticker"]: e.get("name") for e in yaml.safe_load(p.read_text())["tickers"]}
    except Exception:  # noqa: BLE001
        return {}


def run_queue(*, asof: date, notify: bool = True, only: list[str] | None = None,
              queue_path: Path = QUEUE_PATH, state_path: Path = STATE_PATH,
              report_dir: Path = REPORT_DIR,
              price: Callable = last_close, reports: Callable = reports_since,
              headlines: Callable = news, poster: Callable | None = None,
              save: bool = True) -> tuple[list[Seen], str, str]:
    rows = load_queue(queue_path)
    if only:
        rows = [r for r in rows if r.ticker in only]
    names = _company_names()
    for r in rows:
        r.name = r.name or names.get(r.ticker)
    state = json.loads(state_path.read_text()) if state_path.exists() else {}
    last = state.get("_last_run")
    since = date.fromisoformat(last) if last else asof - timedelta(days=FIRST_RUN_DAYS)
    out: list[Seen] = []
    for r in rows:
        d, p = price(r.ticker)
        z = zone(r, p)
        rep = reports(r, since, asof)
        hl = headlines(r, asof) if headlines else []
        prev = state.get(r.ticker, {})
        due = bool(r.gate_until) and date.fromisoformat(str(r.gate_until)) <= asof
        s = Seen(r, d, p, z, rep, hl, due)
        # a zone entered tonight
        if z != prev.get("zone") and z.startswith(("buy", "look", "sell")):
            if z == "buy" and gate_open(r, asof):
                s.lines.append(f"KÖPLINJE {r.ticker} {_fmt(p)} <= {_fmt(buy_line(r))} "
                               f"(base {_fmt(r.base)}, tier {r.tier}) -- läs innan order")
            elif z == "look" and gate_open(r, asof):
                s.lines.append(f"TITTA {r.ticker} {_fmt(p)} <= {_fmt(look_line(r))} "
                               f"({_fmt(p / r.base if p and r.base else None)}x base {_fmt(r.base)}, "
                               f"{r.kind}) -- strike den ordentligt")
            elif z.startswith("sell"):
                what = "bull" if z == "sell:bull" else z.split(":")[1]
                act = next((x.get("action") for x in r.sell_at or []
                            if f"{float(x['price']):g}" == what), "bull reached")
                s.lines.append(f"SÄLJ {r.ticker} {_fmt(p)} >= {what}: {act}")
        # a gate's date passing, said once
        if due and not prev.get("gate_told"):
            s.lines.append(f"SPÄRR {r.ticker}: {r.gate_until} har passerat -- läs "
                           f"{r.gate_event or 'händelsen'}; kurs {_fmt(p)}, base {_fmt(r.base)} ({z})")
        # a report, said once per line
        told = set(prev.get("reports", []))
        for line in rep:
            if line not in told and not line.startswith("(report check failed"):
                s.lines.append(f"RAPPORT {r.ticker}: {line}")
        state[r.ticker] = {"zone": z, "gate_told": bool(due or prev.get("gate_told")),
                           "reports": sorted(told | set(rep))[-20:], "close": p, "close_date": d}
        out.append(s)
    lines = [ln for s in out for ln in s.lines]
    sent = "not sent (--no-notify)"
    if notify:
        from .watch import post_ntfy
        sent = (poster or post_ntfy)(lines, title=f"vss kö: {len(lines)} händelse(r)")
    text = render(asof, out, sent)
    if save:
        if not only:
            state["_last_run"] = asof.isoformat()
        state_path.parent.mkdir(parents=True, exist_ok=True)
        state_path.write_text(json.dumps(state, indent=1, ensure_ascii=False))
        report_dir.mkdir(parents=True, exist_ok=True)
        (report_dir / f"QUEUE-{asof.isoformat()}.md").write_text(text, encoding="utf-8")
    return out, text, sent


def render(asof: date, seen: list[Seen], sent: str) -> str:
    lines = [f"# Kön {asof.isoformat()}", "",
             f"{len(seen)} namn. Notis: {sent}.", ""]
    alerts = [ln for s in seen for ln in s.lines]
    lines += ["## Skickat i kväll", ""] + ([f"- {a}" for a in alerts] or ["- inget nytt"]) + [""]

    def ratio(s: Seen):
        return (s.price / s.row.base) if s.price and s.row.base and s.row.base > 0 else 99.0
    lines += ["## Alla namn, billigast mot base först", "",
              "| Namn | Status | Kind | Kurs | Datum | Bear | Base | Bull | Kurs/base | Linje | Zon | Spärr |",
              "|---|---|---|---:|---|---:|---:|---:|---:|---|---|---|"]
    for s in sorted(seen, key=ratio):
        r = s.row
        b, lk = buy_line(r), look_line(r)
        line = (f"köp {_fmt(b)}" if b else f"titta {_fmt(lk)}" if lk else "--")
        if r.status == "HELD":
            line = "sälj " + ", ".join([f"{float(x['price']):g}" for x in r.sell_at or []]
                                       + ([f"bull {_fmt(r.bull)}"] if r.bull else []))
        gate = (f"{r.gate_until} {r.gate_event or ''}".strip() if r.gate_until else
                ("utan datum" if r.status in GATED else ""))
        lines.append(f"| {r.ticker} | {r.status} | {r.kind} | {_fmt(s.price)} | {s.close_date or '--'} | "
                     f"{_fmt(r.bear)} | {_fmt(r.base)} | {_fmt(r.bull)} | "
                     f"{'--' if ratio(s) == 99.0 else f'{ratio(s):.2f}'} | {line} | {s.zone} | {gate} |")
    lines += ["", "## Rapporter och rubriker", ""]
    for s in seen:
        if s.reports or s.headlines:
            lines.append(f"### {s.row.ticker}" + (f" -- {s.row.name}" if s.row.name else ""))
            lines += [f"- RAPPORT {x}" for x in s.reports] + [f"- {x}" for x in s.headlines] + [""]
    lines += ["", "*Kön skriver ingenting annat än den här filen och data/queue_state.json. "
              "En KÖPLINJE är tiers MBP och kräver en läsning innan order; TITTA betyder att "
              "namnet ska strikas ordentligt, aldrig köp.*", ""]
    return "\n".join(lines)
