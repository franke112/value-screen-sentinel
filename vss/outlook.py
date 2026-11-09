"""THE OUTLOOK CHECK (owner 2026-11-09): when a name's report comes out, read
it, re-value it, and send ntfy ONLY if something changes the outcome.

    "att de ingestar nyaste rapporter o granskar dessa direkt så fort de
    hittas online ... och sen notifierar om ngt ändrar utgången"

Called by `vss queue` for every name in config/queue.yaml, every night. It
writes data/outlook_state.json and nothing else.

WHAT IS READ

1. THE VALUE, ON THE LAST FOUR QUARTERS. The vendor's quarterly statements
   (Yahoo): cash flow before working capital - capex, summed over the four
   newest quarters; net debt = the vendor's total debt (leases IN, so rent
   stays out of the flow as IFRS 16 prints it, and no rate is guessed) less
   cash; shares at the newest balance sheet; through
   `vss.valuation.equity_value_per_share` at 3 % (r 9.5 %). It is a SCREEN,
   compared only with ITSELF: the reading after a report against the
   reading before it, so a bias of the method cancels and what is left is
   what the report changed. Never a figure for config/manual/ or the
   watchlist.
2. THE MACHINE READING OF THE REPORT: on a new report the document itself
   is fetched (EDGAR, or the Nasdaq Nordic / Oslo feed) and read by `vss
   earnings`, twice, provenance-gated (vss/reportread.py), for EVERY queue
   name; `vss watch --read` does the same for watchlist SEC filings. Both
   land in data/autoread/. A section 4.2 rule that FAILS, or a
   guidance cut, is an outlook change.
3. THE HEADLINES the queue already fetches (Google News, 3 days): a profit
   warning, a cut or raised outlook, a CEO or CFO leaving, a bid, a
   delisting -- in Swedish, Norwegian, Danish, Finnish or English.

WHAT IS SENT (and only this)

- UTSIKT <T>: the value on the last four quarters moved >= 10 % on a new
  quarter -- with before, after and the quarter;
- UTSIKT <T>: the machine reading found a 4.2 rule failed or a guidance cut;
- UTSIKT <T>: a headline of the kinds above, once per headline.

A report that changes none of these is a line in the queue's report and the
morning list ("läst: inget ändrat"), never a notification. The vendor files
a quarter some days after the report: until the newest quarter moves past
the one on file the name stays PENDING and is re-read every night (21 days
at most, then said once in the report).
"""
from __future__ import annotations

import json
import re
from datetime import date, timedelta
from pathlib import Path
from typing import Callable

ROOT = Path(__file__).resolve().parents[1]
STATE_PATH = ROOT / "data" / "outlook_state.json"
AUTOREAD = ROOT / "data" / "autoread"
MOVE = 0.10                 # a value move that is news
PENDING_DAYS = 21
GROWTH = 0.03

#: headline words that change an outlook (lower-case, word-start match)
HEADLINE = re.compile(
    r"\b(profit warning|vinstvarning|resultatvarsel|tulosvaroitus|"
    r"lowers? (its )?(guidance|outlook|forecast)|cuts? (its )?(guidance|outlook|forecast)|"
    r"raises? (its )?(guidance|outlook|forecast)|sänker (sin |sina )?(prognos|utsikter)|"
    r"höjer (sin |sina )?(prognos|utsikter)|nedjusterer|oppjusterer|nedjusterar|"
    r"ceo (steps down|resigns|to step down|departs)|cfo (steps down|resigns|departs)|"
    r"(vd|vd:n|koncernchef|finanschef|cfo) (lämnar|avgår)|ny (vd|koncernchef)|"
    r"takeover|tender offer|public offer|bud på|offentligt uppköpserbjudande|"
    r"to be acquired|agrees? to (be )?(acquire|sell)|delist|avnoter|"
    r"chapter 11|konkurs|bankruptcy|rekonstruktion|going concern)", re.I)


def _rows(df, *names):
    for n in names:
        if df is not None and n in df.index:
            return df.loc[n]
    return None


def reading(ticker: str) -> dict:
    """The value on the last four quarters, from the vendor's quarterly
    statements. {'period', 'base', 'fcf_ttm', 'net_debt', 'shares', 'lease'}
    or {'error'}."""
    import yfinance as yf
    from . import valuation as VA
    t = yf.Ticker(ticker)
    qc, qb = t.quarterly_cashflow, t.quarterly_balance_sheet
    n = 4
    if qc is None or qc.empty or qb is None or qb.empty or len(qc.columns) < 4:
        # a half-year reporter (LSE, Euronext): the newest fiscal year instead
        qc, qb, n = t.cashflow, t.balance_sheet, 1
        if qc is None or qc.empty or qb is None or qb.empty:
            return {"error": "no statements at the vendor"}
    cols = sorted(qc.columns, reverse=True)[:n]
    ocf, cwc, capex = (_rows(qc, *n) for n in (("Operating Cash Flow",), ("Change In Working Capital",),
                                              ("Capital Expenditure",)))
    if ocf is None or capex is None:
        return {"error": "no operating cash flow or capex line"}
    vals = []
    for c in cols:
        o, k = ocf.get(c), capex.get(c)
        if o is None or k is None or o != o or k != k:
            return {"error": f"a quarter ({str(c)[:10]}) has no cash flow or capex"}
        w = cwc.get(c) if cwc is not None else None
        vals.append(float(o) - (float(w) if w is not None and w == w else 0.0) - abs(float(k)))
    b = qb[sorted(qb.columns, reverse=True)[0]]

    def num(*keys):
        for key in keys:
            v = b.get(key)
            if v is not None and v == v:
                return float(v)
        return None
    debt = num("Total Debt") or 0.0                       # the vendor's total, leases in
    cash = num("Cash Cash Equivalents And Short Term Investments", "Cash And Cash Equivalents") or 0.0
    lease = num("Capital Lease Obligations") or 0.0
    shares = b.get("Ordinary Shares Number")
    if shares is None or shares != shares:
        shares = (t.info or {}).get("sharesOutstanding")
    if not shares:
        return {"error": "no share count"}
    info = t.info or {}
    trade, fin = info.get("currency") or "USD", info.get("financialCurrency") or info.get("currency") or "USD"
    pence = trade in ("GBp", "GBX")
    k = 1.0
    if fin != ("GBP" if pence else trade):
        fx = yf.Ticker(f"{fin}{'GBP' if pence else trade}=X").history(period="5d")["Close"]
        if fx.empty:
            return {"error": f"no {fin} rate"}
        k = float(fx.iloc[-1])
    k *= 100 if pence else 1
    # Leases stay DEBT and rent stays out of the flow (IFRS 16 as printed):
    # no rate is guessed, and a reading is only ever compared with itself.
    fcf = sum(vals)
    nd = debt - cash
    try:
        base = VA.equity_value_per_share(fcf0=fcf * k * (1 + GROWTH), growth=GROWTH,
                                         net_cash=-nd * k, shares=float(shares))
    except Exception as exc:  # noqa: BLE001 -- a negative FCF and the like: said, not valued
        return {"error": f"not valued: {type(exc).__name__}: {exc}"[:120], "period": str(cols[0])[:10]}
    return {"period": str(cols[0])[:10] + ("" if n == 4 else " FY"), "base": round(base, 2), "fcf_ttm": round(fcf / 1e6, 1),
            "net_debt": round(nd / 1e6, 1), "shares": float(shares), "lease": round(lease / 1e6, 1)}


def autoread_flags(ticker: str, since: date, root: Path = AUTOREAD) -> list[str]:
    """A 4.2 failure or a guidance cut in the machine readings filed since."""
    out = []
    for f in sorted(root.glob(f"*-{ticker}-*.md")):
        m = re.match(r"(\d{4}-\d{2}-\d{2})-", f.name)
        if not m or date.fromisoformat(m.group(1)) <= since:
            continue
        text = f.read_text(errors="replace")
        sec = text.split("## 4.2 FAILS", 1)[1].split("\n## ", 1)[0] if "## 4.2 FAILS" in text else ""
        if sec and "No 4.2 rule failed" not in sec:
            first = next((ln.strip("-* ") for ln in sec.splitlines() if ln.strip().startswith(("-", "*"))), "a 4.2 rule")
            out.append(f"maskinläsningen {m.group(1)}: 4.2 slår till -- {first[:120]} ({f.name})")
        # the FINAL extracted value only (the YAML block), never a disagreement row
        g = re.search(r'^\s+guidance_action:\s*cut\s*$', text, re.M)
        if g:
            out.append(f"maskinläsningen {m.group(1)} säger prognosen sänkt -- kontrollera i rapporten ({f.name})")
    return out


def headline_flags(headlines: list[str]) -> list[str]:
    return [h for h in headlines if HEADLINE.search(h)]


def check(ticker: str, *, asof: date, new_reports: list[str], headlines: list[str],
          state: dict, read: Callable = reading, autoread_root: Path = AUTOREAD,
          report_reader: Callable | None = None, name: str = "", ccy: str = ""
          ) -> tuple[list[str], list[str]]:
    """(alerts for ntfy, notes for the report); updates state[ticker]."""
    s = state.setdefault(ticker, {})
    alerts, notes = [], []
    # the report itself, read by the model (vss/reportread.py), once per new report
    if report_reader is not None and new_reports:
        notes.append(f"rapporten: {report_reader(ticker, name=name, ccy=ccy)}")
    if new_reports and not s.get("pending_since"):
        s["pending_since"] = asof.isoformat()
    need = "base" not in s or bool(s.get("pending_since"))
    if need:
        r = read(ticker)
        if "error" in r:
            notes.append(f"värdet på fyra kvartal: {r['error']}")
            s.setdefault("errors", 0)
            s["errors"] += 1
        elif "base" not in s:                                   # the first reading: the baseline
            s.update(base=r["base"], period=r["period"], read_on=asof.isoformat())
            notes.append(f"första avläsning: base {r['base']} (fyra kvartal till {r['period']})")
            s.pop("pending_since", None)
        elif r["period"] > s.get("period", ""):                  # a new quarter: compare
            prev = s["base"]
            move = (r["base"] - prev) / abs(prev) if prev else None
            if move is not None and abs(move) >= MOVE:
                alerts.append(f"UTSIKT {ticker}: värdet på fyra kvartal {prev:,.2f} -> {r['base']:,.2f} "
                              f"({move:+.0%}) efter kvartalet till {r['period']} -- läs rapporten")
            else:
                notes.append(f"läst: inget ändrat (base {prev:,.2f} -> {r['base']:,.2f}, kvartalet till {r['period']})")
            s.update(base=r["base"], period=r["period"], read_on=asof.isoformat())
            s.pop("pending_since", None)
        else:
            since = date.fromisoformat(s["pending_since"]) if s.get("pending_since") else asof
            if (asof - since).days > PENDING_DAYS:
                notes.append(f"rapporten finns men leverantören har inte kvartalet efter {s.get('period')} "
                             f"på {PENDING_DAYS} dagar -- läs den för hand")
                s.pop("pending_since", None)
            elif s.get("pending_since"):
                notes.append(f"väntar på kvartalet hos leverantören (senast {s.get('period')})")
    since = date.fromisoformat(s["autoread_checked"]) if s.get("autoread_checked") else asof - timedelta(days=3)
    for a in autoread_flags(ticker, since, autoread_root):
        alerts.append(f"UTSIKT {ticker}: {a}")
    s["autoread_checked"] = asof.isoformat()
    told = set(s.get("headlines_told", []))
    for h in headline_flags(headlines):
        if h not in told:
            alerts.append(f"UTSIKT {ticker}: rubrik -- {h[:160]}")
            told.add(h)
    s["headlines_told"] = sorted(told)[-30:]
    return alerts, notes


def load_state(path: Path = STATE_PATH) -> dict:
    try:
        return json.loads(path.read_text())
    except (OSError, ValueError):
        return {}


def save_state(state: dict, path: Path = STATE_PATH) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(state, indent=1, ensure_ascii=False))
