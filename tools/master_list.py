"""THE MASTER LIST -- every company we have looked at, in four groups, on one
page, to read like the morning paper.

    .venv/bin/python tools/master_list.py           # write reports/HUVUDLISTA.md, print the short version
    .venv/bin/python tools/master_list.py --short   # print the short version only (the session-start hook)

Owner 2026-11-09: "det ska finnas som att läsa morgontidningen den listan" --
one list split into what we own, what we watch, what is valued and waits for
a review, and what we said no to (and why, and what would change it). It is
shown first in every session (a SessionStart hook runs `--short`) and
rebuilt every night after the queue (`vss queue` calls `build()`).

READ-ONLY: it reads config/watchlist.yaml, config/queue.yaml,
data/queue_state.json (the queue's last closes), config/shadow_book.csv and
the private sift verdicts reference/screens/*.yaml, and writes one file in
reports/ (gitignored). It decides nothing; a name moves between groups only
when its status moves in those files.

VALUE KINDS, because they are not equal: `strike` is the method's full
valuation from a hand-read store; `machine` (tools/warren.py) and `rough`
(tools/rough_fv.py) are screens; `sift` is the 2026-11-09 Nordic sift on the
issuer's own Q3 figures. Only a strike is a value to buy on.
"""
from __future__ import annotations

import argparse
import csv
import json
import re
import sys
from datetime import date, timedelta
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "reports" / "HUVUDLISTA.md"
BAR = 1.18          # the sift's bar: price at most 85 % of base
KIND_SV = {"strike": "full värdering", "machine": "maskin", "rough": "grov", "sift": "sållning (grov)"}
GROUPS = ("ÄGDA", "KANDIDATER", "BEVAKAS", "ATT GRANSKA", "NEJ")


def _f(v):
    try:
        return None if v in (None, "", "None") else float(str(v).replace(",", ""))
    except ValueError:
        return None


def _short(s, n=150):
    s = " ".join(str(s or "").split())
    return s if len(s) <= n else s[: n - 1].rstrip() + "…"


def _last_dated(notes: str) -> str:
    """The newest dated sentence of a watchlist note, else its first sentence."""
    text = " ".join(str(notes or "").split())
    best = None
    for m in re.finditer(r"(20\d\d-\d\d-\d\d)[^.]{0,400}\.", text):
        if best is None or m.group(1) >= best.group(1):
            best = m
    if best:
        return best.group(0)
    return text.split(". ")[0]


def load() -> dict[str, dict]:
    wl = {n["ticker"]: n for n in yaml.safe_load((ROOT / "config/watchlist.yaml").read_text())["tickers"]}
    q = {n["ticker"]: n for n in yaml.safe_load((ROOT / "config/queue.yaml").read_text())["names"]}
    try:
        st = json.loads((ROOT / "data/queue_state.json").read_text())
    except (OSError, ValueError):
        st = {}
    shadow: dict[str, dict] = {}
    try:
        for r in csv.DictReader((ROOT / "config/shadow_book.csv").open()):
            if r["ticker"] not in shadow or r["verdict_date"] >= shadow[r["ticker"]]["verdict_date"]:
                shadow[r["ticker"]] = r
    except OSError:
        pass
    sift: dict[str, dict] = {}
    for f in sorted((ROOT / "reference/screens").glob("*.yaml")):
        d = yaml.safe_load(f.read_text()) or {}
        for t, v in (d.get("names") or {}).items():
            if v:
                sift[t] = dict(v, sift_date=str(d.get("date")), sift_source=d.get("source"))

    rows: dict[str, dict] = {}
    for t in set(wl) | set(q) | set(shadow) | set(sift):
        w, e, s, v = wl.get(t, {}), q.get(t, {}), shadow.get(t), sift.get(t)
        status = e.get("status") or w.get("status") or (s and s["verdict"]) or (v and v["verdict"])
        if status == "OFF-WATCHLIST" and v and not w:   # a sift name the queue watches: the sift's verdict
            status = v["verdict"]
        close = _f((st.get(t) or {}).get("close"))
        close_date = (st.get(t) or {}).get("close_date")
        if close is None and v:
            close, close_date = _f(v.get("price")), v.get("sift_date")
        bear, base, bull = (_f(e.get(k)) for k in ("bear", "base", "bull"))
        if _f(e.get("base_cap")) is not None:      # a ruling's cap stands over the struck value (E166)
            bear = _f(e.get("bear_cap")) if _f(e.get("bear_cap")) is not None else bear
            base = _f(e.get("base_cap"))
            bull = _f(e.get("bull_cap")) if _f(e.get("bull_cap")) is not None else bull
        kind = e.get("kind")
        if base is None and _f(w.get("fv_base")) is not None:
            base, kind = _f(w.get("fv_base")), "strike"
            bull = _f(w.get("fv_bull"))
        if base is None and v:
            bear, base, bull, kind = _f(v.get("bear")), _f(v.get("base")), _f(v.get("bull")), "sift"
        why = e.get("note") or (v and v.get("why")) or (s and s.get("decided_by")) or _last_dated(w.get("notes"))
        nxt = None
        if e.get("gate_until") or e.get("gate_event"):
            nxt = (str(e.get("gate_until") or ""), str(e.get("gate_event") or ""))
        elif w.get("catalyst_date") and not w.get("catalyst_resolved"):
            nxt = (str(w["catalyst_date"]), str(w.get("catalyst_event") or ""))
        elif v and v.get("next"):
            nxt = ("", v["next"])
        ratio = base / close if base and close and base > 0 else None
        rows[t] = {"ticker": t, "name": e.get("name") or w.get("name") or (v and v.get("name")) or t,
                   "status": status, "close": close, "close_date": close_date, "bear": bear,
                   "base": base, "bull": bull, "kind": kind, "ratio": ratio, "why": why, "next": nxt,
                   "shares": e.get("shares"), "tier": e.get("tier") or w.get("tier")}
    return rows


def group(r: dict) -> str:
    s = (r["status"] or "").upper()
    if s == "HELD":
        return "ÄGDA"
    if s in ("WATCH-PRICED", "WATCH-GATED", "WATCH"):
        return "BEVAKAS"
    if s == "CANDIDATE":                    # reviewed and worth buying, once struck
        return "KANDIDATER"
    if s in ("PIPELINE", "INTAKE", "CONDITIONAL"):
        return "ATT GRANSKA"
    if s == "OFF-WATCHLIST" and r["ratio"] and r["ratio"] >= BAR:
        return "ATT GRANSKA"
    return "NEJ"


def _n(v):
    if v is None:
        return "–"
    return f"{v:,.0f}".replace(",", " ") if abs(v) >= 1000 else f"{v:.2f}".rstrip("0").rstrip(".")


def _row(r: dict) -> str:
    nxt = " ".join(x for x in (r["next"] or ()) if x) or ""
    ratio = f"{r['ratio']:.2f}" if r["ratio"] else "–"
    kind = KIND_SV.get(r["kind"], "–")
    return (f"| {r['ticker']} | {_short(r['name'], 28)} | {r['status'] or '–'} | {_n(r['close'])} | {_n(r['bear'])} | "
            f"{_n(r['base'])} | {_n(r['bull'])} | {ratio} | {kind} | {_short(r['why'])} | {_short(nxt, 60)} |")


def upcoming(rows: dict, days: int = 21) -> list[tuple[str, dict]]:
    today, out = date.today(), []
    for r in rows.values():
        if not r["next"]:
            continue
        m = re.search(r"20\d\d-\d\d-\d\d", " ".join(r["next"]))
        if m and today <= date.fromisoformat(m.group(0)) <= today + timedelta(days=days):
            out.append((m.group(0), r))
    return sorted(out, key=lambda x: x[0])


def render(rows: dict) -> tuple[str, str]:
    by = {g: [] for g in GROUPS}
    for r in rows.values():
        by[group(r)].append(r)
    for g in by:
        by[g].sort(key=lambda r: -(r["ratio"] or 0))
    today = date.today().isoformat()
    head = ("| Ticker | Namn | Status | Kurs | Bear | Base | Bull | Base/kurs | Värdering | Varför | Nästa |\n"
            "|---|---|---|---:|---:|---:|---:|---:|---|---|---|")
    full = [f"# Huvudlistan {today}", "",
            f"Alla bolag vi har tittat på: **{len(rows)}** -- ägda {len(by['ÄGDA'])}, bevakas {len(by['BEVAKAS'])}, "
            f"kandidater {len(by['KANDIDATER'])}, att granska {len(by['ATT GRANSKA'])}, nej {len(by['NEJ'])}. "
            "Base/kurs över 1,18 = kursen minst 15 % under base. **Bara 'full värdering' är ett värde att köpa på**; "
            "maskin, grov och sållning är skärmar.", ""]
    ev = upcoming(rows)
    if ev:
        full += ["## Kommande händelser (21 dagar)", ""] + [f"- {d} **{r['ticker']}** {r['next'][1]}" for d, r in ev] + [""]
    titles = {"ÄGDA": "Ägda", "KANDIDATER": "Kandidater (granskade, köpvärda -- strikas före köp)", "BEVAKAS": "Bevakas (värderade, väntar på pris eller händelse)",
              "ATT GRANSKA": "Att granska (värderade, inte genomgångna)", "NEJ": "Nej (och varför)"}
    for g in GROUPS:
        full += [f"## {titles[g]} ({len(by[g])})", "", head] + [_row(r) for r in by[g]] + [""]
    full += ["*Byggd av tools/master_list.py ur watchlist, kön, skuggboken och sållningarna. "
             "Ändrar ingenting. Notiser kommer från kön (vss queue) på köp/titta/sälj/spärr/rapport.*"]

    s = [f"HUVUDLISTAN {today}: {len(rows)} bolag -- ägda {len(by['ÄGDA'])}, kandidater {len(by['KANDIDATER'])}, bevakas {len(by['BEVAKAS'])}, "
         f"att granska {len(by['ATT GRANSKA'])}, nej {len(by['NEJ'])}  (hela: reports/HUVUDLISTA.md)"]
    s.append("ÄGDA: " + "; ".join(f"{r['ticker']} {_n(r['close'])} (base {_n(r['base'])})" for r in by["ÄGDA"]))
    if by["KANDIDATER"]:
        s.append("KANDIDATER: " + "; ".join(
            f"{r['ticker']} {_n(r['close'])} (bear {_n(r['bear'])} / base {_n(r['base'])})" for r in by["KANDIDATER"]))
    top = [r for r in by["ATT GRANSKA"] if r["ratio"]][:6]
    s.append("ATT GRANSKA, billigast: " + "; ".join(
        f"{r['ticker']} {r['ratio']:.2f} [{KIND_SV.get(r['kind'], '–')}]" for r in top))
    near = [r for r in by["BEVAKAS"] if r["ratio"] and r["ratio"] >= BAR]
    if near:
        s.append("BEVAKAS under linjen: " + "; ".join(f"{r['ticker']} {r['ratio']:.2f}" for r in near))
    if ev:
        s.append("KOMMANDE: " + "; ".join(f"{d} {r['ticker']} {_short(r['next'][1], 40)}" for d, r in ev[:8]))
    return "\n".join(full) + "\n", "\n".join(s)


def build(write: bool = True) -> str:
    full, short = render(load())
    if write:
        OUT.parent.mkdir(exist_ok=True)
        OUT.write_text(full, encoding="utf-8")
    return short


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--short", action="store_true", help="print the short version, write nothing")
    a = ap.parse_args(argv)
    print(build(write=not a.short))
    return 0


if __name__ == "__main__":
    sys.exit(main())
