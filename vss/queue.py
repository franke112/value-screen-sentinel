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

from .valuation import TIER_CUSHION_E90, absurd_cases

ROOT = Path(__file__).resolve().parents[1]
QUEUE_PATH = ROOT / "config" / "queue.yaml"
STATE_PATH = ROOT / "data" / "queue_state.json"
REPORT_DIR = ROOT / "reports"
#: one source with the MBP (E90); a copy here could drift from it (review 2026-11-07 L2)
TIER_CUSHION = TIER_CUSHION_E90
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
    #: a LOWER base a later ruling gives before the name is struck again
    #: (E154's working capital): every line reads the lower one, and the
    #: struck base is kept beside it. Dropped by the builder at the next strike.
    base_cap: float | None = None
    base_cap_why: str | None = None
    base_struck: float | None = None
    bear_cap: float | None = None
    bull_cap: float | None = None
    #: a HELD position, for the section 7 ceiling (H4 of the review 2026-11-07)
    shares: float | None = None
    entry: float | None = None
    #: a sell decided but not yet executed: {since: date, why: text} (L3)
    exit_pending: dict | None = None
    #: the owner set a rule aside for this name (2026-11-08): {rule: owner,
    #: overrides: E-number, reason, standing, expires, since}. Written, never
    #: inferred; the line it touches still prints, with the override beside it.
    override: dict | None = None
    #: a value correction the owner must hear of (E166, 2026-11-08): {since,
    #: text}. Said ONCE, in the report and the ntfy message -- a signal sent
    #: earlier on a value since corrected is withdrawn, or confirmed, here.
    correction: dict | None = None
    #: the caps are a DATA-ERROR correction (E152(1): fixed at once either
    #: way), so they bind upward as well as downward.
    cap_binds_both_ways: bool = False
    #: the watchlist's `fv_void` reason: the value is not read at all
    void: str | None = None
    #: B7: a declared cyclical with no downturn in its history -- the bear is
    #: DATA MISSING and no buy or look line is drawn
    bear_missing: str | None = None

    @classmethod
    def from_dict(cls, d: dict) -> "Row":
        kw = {k: d[k] for k in cls.__dataclass_fields__ if k in d}
        kw["sell_at"] = kw.get("sell_at") or []
        cap = kw.get("base_cap")
        both = bool(kw.get("cap_binds_both_ways"))
        if kw.get("bear_missing"):
            kw["bear"] = None
        if cap is not None and kw.get("base") is not None and (
                float(cap) < float(kw["base"]) or (both and float(cap) != float(kw["base"]))):
            kw["base_struck"], kw["base"] = kw["base"], float(cap)
            for case in ("bear", "bull"):        # the same ruling moves the other cases
                c = kw.get(f"{case}_cap")
                if c is not None and kw.get(case) is not None and (
                        float(c) < float(kw[case]) or both):
                    kw[case] = float(c)
        return cls(**kw)


def load_queue(path: Path = QUEUE_PATH) -> list[Row]:
    return [Row.from_dict(d) for d in (yaml.safe_load(path.read_text()) or {}).get("names", [])]


def portfolio_sek(path: Path = QUEUE_PATH) -> float | None:
    """The portfolio's securities in SEK (queue.yaml's top-level
    `portfolio_sek`, from the owner's Avanza overview; the savings-account
    buffer is not in it), for the section 7 ceiling."""
    v = (yaml.safe_load(path.read_text()) or {}).get("portfolio_sek")
    return float(v) if v else None


#: FRAMEWORK section 7 as E157 rules it (2026-11-08): one name is at most 6%
#: of the whole portfolio -- a fifth of the ~30% satellite. The old ceiling
#: (1% / the distance to the stop) went with the -8 to -12% stop (E156).
POSITION_SHARE = 0.06
REMIND_DAYS = 7


def ceiling_line(r: Row, price: float | None, portfolio: float | None) -> str | None:
    """A HELD position above the section 7 ceiling (E157), in words; None if
    within it or not measurable (no shares, portfolio or price, or not SEK)."""
    if (r.status != "HELD" or not r.shares or not portfolio
            or price is None or r.ccy != "SEK"):
        return None
    ceiling = POSITION_SHARE * portfolio
    value = r.shares * price
    if value <= ceiling:
        return None
    keep = int(ceiling // price)
    line = (f"STORLEK {r.ticker}: positionen {value:,.0f} SEK är {value / ceiling:.1f}x "
            f"§7-taket {ceiling:,.0f} SEK ({POSITION_SHARE:.0%} av {portfolio:,.0f}, E157) "
            f"-- sälj ner till ~{keep} aktier")
    o = r.override or {}
    if str(o.get("overrides", "")).strip() == "E157":
        line += (f" [ÄGARENS UNDANTAG: {o.get('reason', '')}, {o.get('standing', '')} "
                 f"{o.get('expires', '')}; ingen säljorder]").replace("  ", " ")
    return line


def _due(prev_iso: str | None, asof: date) -> bool:
    return prev_iso is None or (asof - date.fromisoformat(prev_iso)).days >= REMIND_DAYS


# --- lines -----------------------------------------------------------------

def buy_line(r: Row) -> float | None:
    if r.bear_missing:
        return None
    if r.kind == "strike" and r.tier in TIER_CUSHION and r.base and r.base > 0:
        return round(r.base * TIER_CUSHION[r.tier], 2)
    return None


def look_line(r: Row) -> float | None:
    if r.bear_missing:
        return None
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
    if r.void:
        return "void"
    if r.status != "HELD" and absurd_cases(r.bear, r.base):
        return "absurd"                  # B6: no line from a broken value
    if r.status != "HELD" and r.bear_missing:
        return "bear-missing"            # B7: no line without a bear
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


_RECORD = re.compile(r"reference/run-records/[^`\s)]+\.json")
_IMPLIED: dict[tuple[str, float], str] = {}


def implied_label(r: "Row", price: float | None) -> str:
    """DISPLAY ONLY (owner 2026-11-08, B4): beside price/base, the rate at
    which the struck base case meets today's price -- `strike.implied_return`
    on the name's own run record, the one its strike document names -- set
    against the hurdle the record declares. Nothing is valued, tested or
    moved here; a name with no record, or a price the base case cannot
    reach, gets no label. Swedish number style, as the queue's own lines."""
    if not price or not r.source:
        return ""
    key = (r.source, float(price))
    if key in _IMPLIED:
        return _IMPLIED[key]
    out = ""
    try:
        from . import runrecord as RR
        from . import strike as ST
        root = Path(__file__).resolve().parents[1]
        doc = root / r.source
        m = _RECORD.search(doc.read_text(encoding="utf-8")) if doc.exists() else None
        if m and (root / m.group(0)).exists():
            rec = RR.RunRecord.from_dict(json.loads((root / m.group(0)).read_text(encoding="utf-8")))
            irr = ST.implied_return(rec, float(price))
            if irr is not None:
                pct = lambda x: f"{100 * x:.1f}".replace(".", ",")  # noqa: E731
                out = (f"; priset ger ~{pct(irr)} % vid din tillväxtsyn; "
                       f"du kräver {pct(rec.rate.rate)} %")
    except Exception:  # noqa: BLE001 -- a label, never a reason to stop the queue
        out = ""
    _IMPLIED[key] = out
    return out


_SENS: dict = {}


def _pct(x) -> str:
    return "–" if x is None else f"{100 * x:.1f}".replace(".", ",") + " %"


def sensitivity_for(r: "Row", price: float | None) -> dict | None:
    """B9 (owner, 2026-11-08): the name's newest run record (by run_ts),
    struck at the registered g, the derived g and g -/+ 1.5 pp, and the g
    the price implies -- in the queue's TRADING unit (a GBX listing's record
    is in pounds: scaled by the struck base it reproduces). None for a name
    with no record or a void value."""
    if r.kind != "strike" or r.void or not r.base:
        return None
    key = (r.ticker, price)
    if key in _SENS:
        return _SENS[key]
    out = None
    try:
        from . import strike as ST
        _, rec = ST.latest_record(r.ticker)
        if rec is not None:
            reg = _registered_g().get(r.ticker)
            fv0 = rec._strike_unchecked(rec.growth.base, case="base")
            scale = 100.0 if fv0 and 50 < (r.base_struck or r.base) / fv0 < 200 else 1.0
            out = ST.sensitivity(rec, price / scale if price else None, reg)
            for k in ("fv_g", "fv_minus", "fv_plus", "fv_registered"):
                if out.get(k) is not None:
                    out[k] *= scale
    except Exception as exc:  # noqa: BLE001 -- display only; the reason is printed
        out = {"error": f"{type(exc).__name__}: {exc}"[:80]}
    _SENS[key] = out
    return out


def _registered_g() -> dict[str, float]:
    p = ROOT / "config" / "watchlist.yaml"
    return {e["ticker"]: float(e["growth"]["base"]) for e in yaml.safe_load(p.read_text())["tickers"]
            if isinstance(e.get("growth"), dict) and e["growth"].get("base") is not None}


def implied_text(r: "Row", price: float | None) -> str:
    """B9: replaces 'price/base 3.40x' -- what growth the price implies,
    set against the return the owner requires."""
    sv = sensitivity_for(r, price)
    if not sv or "error" in sv or sv.get("implied") is None:
        return "--"
    return f"kursen implicerar {_pct(sv['implied'])} tillväxt; kravet är {_pct(sv['rate'])}"


def _bear(x) -> str:
    """Review 2026-11-08 L1: a share is worth no less than zero to its owner;
    a negative bear (a bear flow floored at zero, net debt left over) prints
    as that, not as a downside figure."""
    return "≤0" if x is not None and x <= 0 else _fmt(x)


def _voids(path: Path | None = None) -> dict[str, str]:
    """The watchlist's VOID values (`fv_void`): ticker -> reason. Read
    fail-closed -- a watchlist that cannot be read stops the queue rather
    than letting a voided value through."""
    p = path or ROOT / "config" / "watchlist.yaml"
    return {e["ticker"]: str(e["fv_void"]) for e in yaml.safe_load(p.read_text())["tickers"]
            if e.get("fv_void")}


def apply_voids(rows: list[Row], voids: dict[str, str]) -> list[Row]:
    """Review 3, L1: the queue never reads a value the watchlist marks void
    -- no base, no bear or bull, no buy or look line."""
    for r in rows:
        if r.ticker in voids:
            r.void = voids[r.ticker]
            r.base = r.bear = r.bull = None
            r.base_struck = None
    return rows


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
              save: bool = True, voids: dict[str, str] | None = None
              ) -> tuple[list[Seen], str, str]:
    rows = apply_voids(load_queue(queue_path), _voids() if voids is None else voids)
    if only:
        rows = [r for r in rows if r.ticker in only]
    names = _company_names()
    for r in rows:
        r.name = r.name or names.get(r.ticker)
    state = json.loads(state_path.read_text()) if state_path.exists() else {}
    last = state.get("_last_run")
    since = date.fromisoformat(last) if last else asof - timedelta(days=FIRST_RUN_DAYS)
    out: list[Seen] = []
    portfolio = portfolio_sek(queue_path)
    for r in rows:
        d, p = price(r.ticker)
        z = zone(r, p)
        prev = state.get(r.ticker, {})
        # Granskning 2026-11-09 (2.5): each name keeps its own window, moved
        # forward only by a check that WORKED -- a failed night is searched
        # again, never skipped.
        own_since = prev.get("reports_checked")
        r_since = date.fromisoformat(own_since) if own_since else since
        if not own_since and any(str(x).startswith("(report check failed")
                                 for x in prev.get("reports", [])):
            r_since = since - timedelta(days=7)   # state from before the fix
        rep = reports(r, r_since, asof)
        failed = [x for x in rep if x.startswith("(report check failed")]
        rep = [x for x in rep if not x.startswith("(report check failed")]
        checked = r_since.isoformat() if failed else asof.isoformat()
        hl = headlines(r, asof) if headlines else []
        due = bool(r.gate_until) and date.fromisoformat(str(r.gate_until)) <= asof
        s = Seen(r, d, p, z, rep, hl, due)
        # a zone entered tonight
        if z != prev.get("zone") and z.startswith(("buy", "look", "sell")):
            if z == "buy" and gate_open(r, asof):
                s.lines.append(f"UNDER MBP {r.ticker} {_fmt(p)} <= {_fmt(buy_line(r))} "
                               f"(base {_fmt(r.base)}, tier {r.tier}; information, "
                               f"E168: kudden är inte visad att hjälpa) -- läs innan order")
            elif z == "look" and gate_open(r, asof):
                s.lines.append(f"TITTA {r.ticker} {_fmt(p)} <= {_fmt(look_line(r))} "
                               f"(base {_fmt(r.base)}, {r.kind}; {implied_text(r, p)}) "
                               f"-- strike den ordentligt")
            elif z.startswith("sell"):
                what = "bull" if z == "sell:bull" else z.split(":")[1]
                act = next((x.get("action") for x in r.sell_at or []
                            if f"{float(x['price']):g}" == what), "bull reached")
                s.lines.append(f"SÄLJ {r.ticker} {_fmt(p)} >= {what}: {act}")
        # a value correction, said once (E166)
        corr_told = prev.get("correction_told")
        if r.correction and corr_told != str(r.correction.get("since")):
            s.lines.append(f"RÄTTELSE {r.ticker}: {r.correction.get('text', '')}")
            corr_told = str(r.correction.get("since"))
        # a gate's date passing, said once
        if due and not prev.get("gate_told"):
            s.lines.append(f"SPÄRR {r.ticker}: {r.gate_until} har passerat -- läs "
                           f"{r.gate_event or 'händelsen'}; kurs {_fmt(p)}, base {_fmt(r.base)} ({z})")
        # a report, said once per line
        told = set(prev.get("reports", []))
        for line in rep:
            if line not in told:
                s.lines.append(f"RAPPORT {r.ticker}: {line}")
        # a failed check, said once per streak (it is retried every night)
        if failed and not prev.get("check_failed_told"):
            s.lines.append(f"RAPPORTKONTROLL FELADE {r.ticker}: {failed[0][1:-1]} "
                           f"-- söks om nästa natt från {r_since.isoformat()}")
        # once a week: a binding size rule broken, a sell not carried out
        size_told, exit_told = prev.get("size_told"), prev.get("exit_told")
        over = ceiling_line(r, p, portfolio)
        if over and _due(size_told, asof):
            s.lines.append(over)
            size_told = asof.isoformat()
        if r.status == "HELD" and r.exit_pending and _due(exit_told, asof):
            since = str(r.exit_pending.get("since", "?"))
            age = ((asof - date.fromisoformat(since)).days if since[:4].isdigit() else None)
            s.lines.append(f"SÄLJ EJ UTFÖRD {r.ticker}: beslutad {since}"
                           + (f" ({age} dagar)" if age is not None else "")
                           + f" -- {r.exit_pending.get('why', '')}".rstrip(" -"))
            exit_told = asof.isoformat()
        state[r.ticker] = {"zone": z, "gate_told": bool(due or prev.get("gate_told")),
                           "reports": sorted(told | set(rep))[-20:], "close": p, "close_date": d,
                           "size_told": size_told, "exit_told": exit_told,
                           "reports_checked": checked,
                           "check_failed_told": bool(failed),
                           "correction_told": corr_told}
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
              "| Namn | Status | Kind | Kurs | Datum | Bear | Base | Bull | Kursen implicerar | Linje | Zon | Spärr |",
              "|---|---|---|---:|---|---:|---:|---:|---:|---|---|---|"]
    for s in sorted(seen, key=ratio):
        r = s.row
        b, lk = buy_line(r), look_line(r)
        line = (f"köp {_fmt(b)}" if b else f"titta {_fmt(lk)}" if lk else "--")
        if r.void:
            line = f"ogiltigt värde: {r.void[:80]}"
        elif r.status != "HELD" and absurd_cases(r.bear, r.base):
            line = "stoppad: " + absurd_cases(r.bear, r.base)
        elif r.bear_missing:
            line = f"bear DATA MISSING: {r.bear_missing[:80]}"
        if r.status == "HELD":
            line = "sälj " + ", ".join([f"{float(x['price']):g}" for x in r.sell_at or []]
                                       + ([f"bull {_fmt(r.bull)}"] if r.bull else []))
        gate = (f"{r.gate_until} {r.gate_event or ''}".strip() if r.gate_until else
                ("utan datum" if r.status in GATED else ""))
        lines.append(f"| {r.ticker} | {r.status} | {r.kind} | {_fmt(s.price)} | {s.close_date or '--'} | "
                     f"{_bear(r.bear)} | {_fmt(r.base)}{' (' + (r.base_cap_why or 'tak') + '; struck ' + _fmt(r.base_struck) + ')' if r.base_struck else ''} | {_fmt(r.bull)} | "
                     f"{implied_text(r, s.price)} | {line} | {s.zone} | {gate} |")
    lines += ["", "## Känslighet (B9): base vid olika tillväxt, och den tillväxt kursen implicerar", "",
              "| Namn | Kurs | Registrerad g → base | Härledd g → base | g − 1,5 pp | g + 1,5 pp | Kursen implicerar | Krav |",
              "|---|---:|---|---|---:|---:|---:|---:|"]
    for s in sorted(seen, key=ratio):
        sv = sensitivity_for(s.row, s.price)
        if not sv:
            continue
        if "error" in sv:
            lines.append(f"| {s.row.ticker} | {_fmt(s.price)} | {sv['error']} | | | | | |")
            continue
        reg = (f"{_pct(sv['registered'])} → {_fmt(sv['fv_registered'])}"
               if sv["registered"] is not None else "–")
        lines.append(f"| {s.row.ticker} | {_fmt(s.price)} | {reg} | {_pct(sv['g'])} → {_fmt(sv['fv_g'])} | "
                     f"{_fmt(sv['fv_minus'])} | {_fmt(sv['fv_plus'])} | {_pct(sv['implied'])} | {_pct(sv['rate'])} |")
    lines += ["", "## Rapporter och rubriker", ""]
    for s in seen:
        if s.reports or s.headlines:
            lines.append(f"### {s.row.ticker}" + (f" -- {s.row.name}" if s.row.name else ""))
            lines += [f"- RAPPORT {x}" for x in s.reports] + [f"- {x}" for x in s.headlines] + [""]
    lines += ["", "*Kön skriver ingenting annat än den här filen och data/queue_state.json. "
              "UNDER MBP är information (E168, försök #25: kudden skilde inte avkastningen) "
              "och kräver en läsning innan order; TITTA betyder att "
              "namnet ska strikas ordentligt, aldrig köp.*", ""]
    return "\n".join(lines)
