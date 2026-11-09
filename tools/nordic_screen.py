"""The weekly NORDIC SCREEN: every active Nordic company valued by the method's
core and ranked on fv/price. Private (EODHD data); never published.

    .venv/bin/python tools/nordic_screen.py                 # refresh EODHD (files > 6 days), price, value, rank
    .venv/bin/python tools/nordic_screen.py --no-refresh    # value and rank on the files on disk
    .venv/bin/python tools/nordic_screen.py --notify        # and send the summary to ntfy

WHY. reference/BACKTEST-NORDIC-2026-11-07.md: over twelve test dates
2010-2021 the cheaper two fifths of Nordic companies by the method's
fv/price beat the dearer two fifths by +13.8 pp over 3 years (10 of 12
years, p = 0.0002) and +21.0 pp over 5 (9 of 12) -- attempt #9, after the
reviews' currency (K1), vendor-adjustment (M4) and level-break (2026-11-08
M2) fixes; +12.8 / +20.7 without the last, +17.1 / +35.6 before them all. The pre-registered confirmation on
2022-23 was NOT CONFIRMED (p = 0.49), run before the fixes and not repeated.
ATTEMPT #24 (2026-11-09): fv/price does not sort by decile in both markets
and both halves (rank 0.65 / 0.54). The list keeps the fv/price order
because fv against price is the method's own buy line (E167, beslutat av
sessionen 2026-11-09); it is not a claim that the cheap group wins.
This screen applies the same engine (`tools/backtest/nordic.py`'s
translation, `method.evaluate`) to TODAY and lists the cheapest 40%.

WHAT IT IS NOT. A buy. A name here is a candidate for the review process
(intake, a hand-read store, the gates); the backtest valued by machine, and
so does this. EODHD is a secondary source (E21, E151).

INPUTS. Fundamentals: data/eodhd/fundamentals/ (the files are re-fetched
when older than 6 days, ~16,000 calls a week, while the EODHD plan runs; a
figure enters only once known -- report date + 1 weekday). Price: the last
close from Yahoo (the EODHD plan has no daily prices). Size: market cap
>= 300 MUSD at today's rate; financials and real estate out.

OUTPUT. reports/NORDIC-SCREEN-<date>.md and data/nordic-screen/<date>.json;
a name new in the cheapest 40% since the last run is marked NEW.
"""
from __future__ import annotations

import argparse
import csv
import gzip
import json
import statistics
import subprocess
import sys
from datetime import date, datetime
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "tools"))

from tools.backtest import method as M  # noqa: E402
from tools.backtest import nordic as N  # noqa: E402
from tools.backtest import value as V  # noqa: E402
from vss import valuation as VA  # noqa: E402
from vss import withholding as WH  # noqa: E402

OUT_JSON = ROOT / "data" / "nordic-screen"
OUT_MD = ROOT / "reports"
TOP_SHARE = 0.40
REFRESH_DAYS = 6
STALE_DAYS = 200      # newest known report older than this: flagged


def prices(symbols: list[str]) -> dict[str, tuple[str, float]]:
    """symbol -> (date, last close), from Yahoo in batches. Missing = no price."""
    import yfinance as yf
    out = {}
    for i in range(0, len(symbols), 200):
        batch = symbols[i:i + 200]
        try:
            df = yf.download(batch, period="10d", auto_adjust=False, group_by="ticker",
                             threads=True, progress=False)
        except Exception:  # noqa: BLE001 -- a failed batch leaves its names unpriced
            continue
        for s in batch:
            try:
                col = df[s]["Close"] if len(batch) > 1 else df["Close"]
                col = col.dropna()
                if len(col):
                    out[s] = (col.index[-1].date().isoformat(), float(col.iloc[-1]))
            except Exception:  # noqa: BLE001
                continue
    return out


def fx_today() -> dict[str, float]:
    import yfinance as yf
    out = {"USD": 1.0}
    for cur, t in N.FX_TICKER.items():
        try:
            col = yf.download(t, period="10d", progress=False, auto_adjust=False)["Close"].dropna()
            out[cur] = float(col.iloc[-1].iloc[0] if hasattr(col.iloc[-1], "iloc") else col.iloc[-1])
        except Exception:  # noqa: BLE001
            pass
    return out


def tracked() -> dict[str, str]:
    """ticker -> where it already stands (watchlist status / queue)."""
    out = {}
    try:
        for e in yaml.safe_load((ROOT / "config" / "watchlist.yaml").read_text())["tickers"]:
            out[e["ticker"]] = str(e.get("status") or "watchlist")
    except Exception:  # noqa: BLE001
        pass
    try:
        for e in (yaml.safe_load((ROOT / "config" / "queue.yaml").read_text()) or {}).get("names", []):
            out.setdefault(e["ticker"], "queue")
    except Exception:  # noqa: BLE001
        pass
    return out


def newest_known(facts: dict, day: date) -> tuple[str | None, str | None]:
    """(newest period end, the day it became known) visible on `day`."""
    best = None
    for node in facts["facts"]["us-gaap"].values():
        for e in node["units"].get("USD", []):
            if e["filed"] < day.isoformat() and (best is None or e["end"] > best[0]):
                best = (e["end"], e["filed"])
    return best or (None, None)


#: IFRS 16: lease principal is a FINANCING flow, so OCF - capex leaves rent
#: out, and EODHD has no lease-payment line. The screen charges this share of
#: the period's lease liability a year as extra capex and takes the lease
#: liability out of debt (rent paid once, not twice). 0.35 is the low middle
#: of fifteen issuers' own principal / liability, 2025 (0.18 Lundbeck - 0.63
#: Proact, median 0.36; reference/screens/NORDIC-SIFT-2026-11-09.md). Before
#: 2026-11-09 a name under LEASE_SHARE_MAX was valued as if it paid no rent:
#: corrected by hand, nearly every service name's fv fell, some by more than
#: half (figures in the private sift). A DATA rule
#: (E164) and the screen's only: the backtest's translation is unchanged.
LEASE_PAYMENT_RATE = 0.35
#: a newest year (or last four quarters) whose capex is under this share of
#: the three years before is a vendor gap, not a saving (Stillfront, Vitec, GN
#: 2025: capitalised development dropped from the line, FCF doubled)
CAPEX_GAP = 0.25


def _years(d: dict, statement: str, freq: str) -> dict:
    return ((d.get("Financials") or {}).get(statement) or {}).get(freq) or {}


def capex_gap(d: dict) -> str | None:
    """A refusal when the newest capex is a vendor gap; else None."""
    cf_y, inc_y = _years(d, "Cash_Flow", "yearly"), _years(d, "Income_Statement", "yearly")
    capex = {pe: abs(v) for pe, e in cf_y.items()
             if isinstance(e, dict) and (v := N._num(e.get("capitalExpenditures"))) is not None}
    ends = sorted(capex)
    if len(ends) < 4:
        return None

    def check(newest: float, before: list[str], what: str) -> str | None:
        mean = sum(capex[p] for p in before) / len(before)
        rev = N._num((inc_y.get(before[-1]) or {}).get("totalRevenue")) or 0.0
        if mean > 0.01 * rev and newest < CAPEX_GAP * mean:
            return (f"capex fault: {what} capex {newest / mean:.0%} of the three years "
                    f"before (vendor gap suspected)")
        return None

    hit = check(capex[ends[-1]], ends[-4:-1], ends[-1][:4])
    if hit:
        return hit
    cf_q = _years(d, "Cash_Flow", "quarterly")
    qs = sorted(pe for pe, e in cf_q.items()
                if isinstance(e, dict) and N._num(e.get("capitalExpenditures")) is not None)[-4:]
    if len(qs) == 4:
        prior = [p for p in ends if p < qs[0]][-3:]
        if len(prior) == 3:
            return check(sum(abs(N._num(cf_q[q]["capitalExpenditures"])) for q in qs),
                         prior, f"last four quarters to {qs[-1][:7]}")
    return None


def charge_leases(d: dict) -> None:
    """IN PLACE: capex += LEASE_PAYMENT_RATE x the period's lease liability
    (pro rata for a quarter); debt total -= the lease liability."""
    for freq, months in (("yearly", 12), ("quarterly", 3)):
        bs = _years(d, "Balance_Sheet", freq)
        for pe, e in _years(d, "Cash_Flow", freq).items():
            lease = N._num((bs.get(pe) or {}).get("capitalLeaseObligations"))
            capex = N._num(e.get("capitalExpenditures")) if isinstance(e, dict) else None
            if lease and capex is not None:
                e["capitalExpenditures"] = str(abs(capex) + LEASE_PAYMENT_RATE * lease * months / 12)
        for pe, b in bs.items():
            total = N._num(b.get("shortLongTermDebtTotal")) if isinstance(b, dict) else None
            lease = N._num(b.get("capitalLeaseObligations")) if isinstance(b, dict) else None
            if total is not None and lease:
                b["shortLongTermDebtTotal"] = str(max(0.0, total - lease))


def value_all(day: date) -> list[dict]:
    names = [r for r in N.universe() if r["delisted"] != "True"]
    px = prices([r["symbol"] for r in names])
    fx = fx_today()
    tax = M.tax_for
    rows, seen = [], {}
    try:
        for r in names:
            sym = r["symbol"]
            if sym not in px:
                continue
            d = json.loads(gzip.decompress((N.FUND / f"{sym}.json.gz").read_bytes()))
            g = d.get("General") or {}
            if N.excluded(g, sym):
                continue
            gap = capex_gap(d)          # before the lease charge, which would hide it
            charge_leases(d)
            facts = N.facts_from_eodhd(sym, d)
            sh = N.shares_known(facts, day)          # EODHD counts are on today's basis
            cur = g.get("CurrencyCode") or r.get("Currency")
            rate = fx.get(cur)
            price_day, price = px[sym]
            if not sh or rate is None or sh * price * rate < N.SIZE_MIN_USD:
                continue
            company = g.get("Name") or sym
            cap = sh * price
            if company in seen and seen[company] >= cap:
                continue
            country = N.COUNTRY[r["suffix"]]
            M.tax_for = lambda y, c=country: VA.STATUTORY_TAX_RATE[c]
            heavy = N.lease_heavy(d, day)
            if heavy is not None:
                row = {"status": f"leases {heavy:.0%} of assets: rent not in the data"}
            elif gap:
                row = {"status": gap}
            else:
                try:
                    row = M.evaluate(facts, day, ticker=sym, cik=sym, sic=None, policy="latest")
                except Exception as exc:  # noqa: BLE001
                    row = {"status": f"error: {type(exc).__name__}: {exc}"[:160]}
            if row.get("shares") and abs(row["shares"] / sh - 1) > 0.01:
                k = row["shares"] / sh
                row["shares"] = sh
                for key in ("fv_base", "fv_bear", "fv_ex_programme"):
                    if row.get(key) is not None:
                        row[key] *= k
            if row.get("status") == "ok":
                M.with_price(row, price, None)
                row.pop("cap_check", None)
            period, known = newest_known(facts, day)
            dps = N._num((d.get("Highlights") or {}).get("DividendShare"))
            dy = dps / price if dps and price > 0 else None
            out = {"symbol": sym, "company": company, "sector": g.get("GicSector"),
                   "country": country, "currency": cur, "price": price, "price_date": price_day,
                   "market_cap_usd": cap * rate, "status": row.get("status"),
                   "fv_base": row.get("fv_base"), "fv_bear": row.get("fv_bear"),
                   "fv_over_price": row.get("fv_over_price"), "g_base": row.get("g_base"),
                   "growth_source": row.get("growth_source"), "net_debt": row.get("net_debt"),
                   "quality": row.get("quality") or {},
                   "passes_quality": V.passes_quality(row) if row.get("quality") else None,
                   "measured_kill": V.measured_kill(row) if row.get("kills") is not None else None,
                   "newest_period": period, "known_since": known,
                   "dividend_yield": dy, "withholding_drag": WH.drag(dy, country)}
            if company in seen:
                rows = [x for x in rows if x["company"] != company]
            seen[company] = cap
            rows.append(out)
    finally:
        M.tax_for = tax
    return rows


def previous_top(day: date) -> set[str]:
    """The cheapest 40% of the last run BEFORE `day` (a re-run the same day
    is not a comparison)."""
    files = sorted(f for f in OUT_JSON.glob("*.json") if f.stem < day.isoformat())
    if not files:
        return set()
    return {r["symbol"] for r in json.loads(files[-1].read_text())["rows"] if r.get("top")}


def render(day: date, rows: list[dict], before: set[str], where: dict[str, str]) -> tuple[str, list[str]]:
    valued = sorted((r for r in rows if r.get("fv_over_price")), key=lambda r: -r["fv_over_price"])
    k = int(len(valued) * TOP_SHARE)
    for i, r in enumerate(valued):
        r["rank"] = i + 1
        r["top"] = i < k
        r["new"] = r["top"] and bool(before) and r["symbol"] not in before
    top = valued[:k]
    q = lambda v: "✓" if v is True else "✗" if v is False else "?"
    L = [f"# Nordisk screen {day.isoformat()}", "",
         f"{len(rows)} aktiva nordiska bolag över 300 MUSD (finans och fastighet undantagna); "
         f"{len(valued)} värderade av metodens kärna; listan är de billigaste {TOP_SHARE:.0%} "
         f"({len(top)}) på fv/kurs. Ordningen är metodens köplinje, inte ett bevisat urval: "
         f"försök #24 (2026-11-09) fann att fv/kurs inte sorterar avkastningen i båda "
         f"marknaderna och båda halvorna (rangkorrelation 0,65 Norden, 0,54 USA; "
         f"reports/attempts/A24-RESULT.md), och bekräftelsen 2022–2023 gav INTE BEKRÄFTAT. "
         f"**Kandidater för granskning, inte köp.**", "",
         "Källskatt/år = direktavkastning × källskatt (FI 35, DK 27, NO 25 %): en ren kostnad i ISK "
         f"så länge ISK-värdet är under fribeloppet ({WH.ALLOWANCE_SEK_2026:,} kr 2026). "
         "Påverkar inte fv eller ordningen.", "",
         "| # | Bolag | Ticker | Kurs | fv bas | fv/kurs | Tillväxt | Q1 Q2 Q3 Q4 | Stopp | Källskatt/år | Senaste rapport | Följs | |",
         "|---:|---|---|---:|---:|---:|---:|---|---|---:|---|---|---|"]
    for r in top:
        qual = " ".join(q(r["quality"].get(x)) for x in ("Q1", "Q2", "Q3", "Q4"))
        wh = f"{r['withholding_drag'] * 100:.1f} %" if r.get("withholding_drag") else ""
        stale = ""
        if r.get("known_since") and (day - date.fromisoformat(r["known_since"])).days > STALE_DAYS:
            stale = " (gammal)"
        L.append(f"| {r['rank']} | {r['company'][:28]} | {r['symbol']} | {r['price']:,.2f} | "
                 f"{r['fv_base']:,.2f} | {r['fv_over_price']:.2f} | "
                 f"{(r['g_base'] or 0) * 100:.1f}% | {qual} | {'JA' if r['measured_kill'] else ''} | "
                 f"{wh} | "
                 f"{r.get('newest_period') or '?'}{stale} | {where.get(r['symbol'], '')} | "
                 f"{'NY' if r['new'] else ''} |")
    fetched = sorted((N.FUND.glob("*.json.gz")), key=lambda f: f.stat().st_mtime)
    if fetched:
        age = (datetime.now().timestamp() - fetched[-1].stat().st_mtime) / 86400
        L += ["", f"Boksluten hämtades senast för {age:.0f} dagar sedan (EODHD). Kurserna är från "
                  f"{max(r['price_date'] for r in rows)} (Yahoo). En rapport som kommit efter "
                  f"hämtningen syns först vid nästa prenumerationsmånad."]
    refused = [r for r in rows if not r.get("fv_over_price")]
    reasons: dict[str, int] = {}
    for r in refused:
        key = (r.get("status") or "no price")[:40]
        reasons[key] = reasons.get(key, 0) + 1
    L += ["", f"Ej värderade: {len(refused)} — " + "; ".join(f"{k} ({v})" for k, v in
                                                          sorted(reasons.items(), key=lambda x: -x[1])[:6])]
    best = [r for r in top if r.get("passes_quality") and not r.get("measured_kill")][:10]
    note = [f"Nordisk screen {day}: {len(top)} billigaste av {len(valued)}; "
            f"{sum(r['new'] for r in top)} nya; klarar Q1–Q4 utan stopp:"]
    note += [f"{r['symbol']} fv/kurs {r['fv_over_price']:.2f}" + (" NY" if r["new"] else "")
             + (f" ({where[r['symbol']]})" if r["symbol"] in where else "") for r in best]
    return "\n".join(L) + "\n", note


def stale_warning(refresh_rc: int | None) -> str | None:
    """A loud line when the EODHD refresh failed or the files are older than
    a refresh cycle (the subscription runs one month a year): the ranking is
    then on old reports and must say so (independent review M3)."""
    fetched = sorted(N.FUND.glob("*.json.gz"), key=lambda f: f.stat().st_mtime)
    age = ((datetime.now().timestamp() - fetched[-1].stat().st_mtime) / 86400) if fetched else None
    parts = []
    if refresh_rc not in (None, 0):
        parts.append(f"EODHD-hämtningen misslyckades (kod {refresh_rc})")
    if age is None or age > REFRESH_DAYS + 2:
        parts.append("boksluten är " + (f"{age:.0f} dagar gamla" if age is not None else "inte hämtade"))
    return ("VARNING: " + "; ".join(parts) + " -- rankingen bygger på gamla rapporter") if parts else None


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--no-refresh", action="store_true",
                    help="value and rank on the EODHD files on disk; fetch "
                         "nothing from the vendor")
    ap.add_argument("--notify", action="store_true",
                    help="send the summary to ntfy (the Saturday timer)")
    return ap


def main(argv=None) -> int:
    a = build_parser().parse_args(argv)
    day = date.today()
    refresh_rc = None
    if not a.no_refresh:
        refresh_rc = subprocess.run([sys.executable, str(ROOT / "tools" / "fetch_eodhd.py"),
                                     "--refresh-nordic", str(REFRESH_DAYS), "--budget", "30000"],
                                    check=False).returncode
    rows = value_all(day)
    before = previous_top(day)
    md, note = render(day, rows, before, tracked())
    warn = stale_warning(refresh_rc)
    if warn:
        md, note = f"> **{warn}**\n\n" + md, [warn] + note
    OUT_MD.mkdir(parents=True, exist_ok=True)
    OUT_JSON.mkdir(parents=True, exist_ok=True)
    (OUT_MD / f"NORDIC-SCREEN-{day.isoformat()}.md").write_text(md, encoding="utf-8")
    (OUT_JSON / f"{day.isoformat()}.json").write_text(json.dumps(
        {"date": day.isoformat(), "generated": datetime.now().isoformat(timespec="seconds"),
         "rows": rows}, default=str), encoding="utf-8")
    print("\n".join(note))
    if a.notify:
        from vss.watch import post_ntfy
        print(post_ntfy(note, title=f"vss nordisk screen {day}"))
    return 0


if __name__ == "__main__":
    sys.exit(main())
