"""Build config/queue.yaml -- THE QUEUE: every name we have valued, with its
bear / base / bull, its buy line, its gate and the event that lifts it.

    .venv/bin/python tools/build_queue.py          # print the diff summary
    .venv/bin/python tools/build_queue.py --write  # write config/queue.yaml

WHERE EACH FIELD COMES FROM, so a re-run never loses hand work:

* ``kind: strike`` entries are HARVESTED: the newest reference/<T>-STRIKE-*.md
  (newest by git commit time, NOT by filename -- "-check" sorts before
  "-e142" although it is the later pass) that carries the standard line
  ``fv_base: x -> **base** (bear b, bull u)``; a few older strikes state the
  values in another form and are listed in LEGACY below. Status, tier,
  stop and the gate's date and event come from config/watchlist.yaml.
* ``kind: machine`` (tools/warren.py, the newsdrop screen) and ``kind: rough``
  (tools/rough_fv.py) entries are HAND entries: the builder keeps them as
  they stand.
* Hand fields on ANY entry -- ``sell_at``, ``look_at`` (a revisit level
  that replaces base x cushion), ``gate_until``/``gate_event``
  where the watchlist has none, ``note`` -- are kept across re-runs.

Values are in the TRADING unit: a GBX listing's GBP strike is x100 here, so
the queue never compares pence with pounds (the AUTO.L display of 4.99
against 544.60 is the trap this avoids).
"""
from __future__ import annotations

import argparse
import re
import subprocess
import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
QUEUE = ROOT / "config" / "queue.yaml"
WATCHLIST = ROOT / "config" / "watchlist.yaml"
LINE = re.compile(r"fv_base:\*\*.*?->\s*\*\*([-\d.,]+)\*\*\s*\(bear ([-\d.,]+), bull ([-\d.,]+)\)")
# strikes written before the standard line existed: (bear, base, bull, file)
LEGACY = {
    "SAP.DE": (121.04, 140.37, 175.42, "reference/SAP.DE-STRIKE-2026-08-30-e91.md"),
    "RKT.L": (23.88, 32.20, None, "reference/RKT.L-STRIKE-2026-08-30.md"),
}
TIER_CUSHION = {1: 0.85, 2: 0.75, 3: 0.65}   # E90, as vss run applies it
HAND_FIELDS = ("sell_at", "look_at", "note", "gate_until", "gate_event", "name",
               "base_cap", "base_cap_why", "bear_cap", "bull_cap",
               "shares", "entry", "exit_pending", "override", "correction",
               "cap_binds_both_ways", "bear_missing")
#: a base cap stands until the name is struck again under the ruling that set
#: it; a strike doc dated after the cap's date carries the ruling itself
CAP_SINCE = "base_cap_since"


def _num(s: str) -> float:
    return float(s.replace(",", ""))


def _commit_time(path: Path) -> int:
    out = subprocess.run(["git", "log", "-1", "--format=%ct", "--", str(path)],
                         cwd=ROOT, capture_output=True, text=True).stdout.strip()
    return int(out) if out else int(path.stat().st_mtime)


def harvest() -> dict[str, dict]:
    found: dict[str, tuple[int, dict]] = {}
    for f in (ROOT / "reference").glob("*-STRIKE-*.md"):
        ticker = f.name.split("-STRIKE")[0]
        if ticker.startswith("RESTRIKE"):
            continue
        for line in f.open(encoding="utf-8"):
            m = LINE.search(line)
            if m:
                base, bear, bull = (_num(x) for x in m.groups())
                t = _commit_time(f)
                if ticker not in found or t > found[ticker][0]:
                    found[ticker] = (t, {"bear": bear, "base": base, "bull": bull,
                                         "source": str(f.relative_to(ROOT))})
                break
    out = {t: v for t, (_, v) in found.items()}
    for t, (bear, base, bull, src) in LEGACY.items():
        out.setdefault(t, {"bear": bear, "base": base, "bull": bull, "source": src})
    return out


def _doc_date(source: str) -> str:
    """The date in a strike doc's name (<T>-STRIKE-YYYY-MM-DD...)."""
    import re
    m = re.search(r"STRIKE-(\d{4}-\d{2}-\d{2})", source or "")
    return m.group(1) if m else "9999-99-99"


def build(existing: list[dict]) -> list[dict]:
    wl = {e["ticker"]: e for e in yaml.safe_load(WATCHLIST.read_text())["tickers"]}
    old = {e["ticker"]: e for e in existing}
    rows: list[dict] = []
    for ticker, v in sorted(harvest().items()):
        w = wl.get(ticker, {})
        ccy = w.get("currency") or old.get(ticker, {}).get("ccy")
        k = 100.0 if ccy == "GBX" else 1.0
        row = {"ticker": ticker, "kind": "strike", "ccy": ccy,
               "bear": None if v["bear"] is None else round(v["bear"] * k, 2),
               "base": round(v["base"] * k, 2),
               "bull": None if v["bull"] is None else round(v["bull"] * k, 2),
               "source": v["source"],
               "status": w.get("status", "OFF-WATCHLIST"),
               "tier": w.get("tier"),
               "stop": w.get("stop_price")}
        if w.get("catalyst_date") and not w.get("catalyst_resolved"):
            row["gate_until"] = str(w["catalyst_date"])
            row["gate_event"] = str(w.get("catalyst_event") or "").split(" -- ")[0][:120]
        prev = old.get(ticker, {})
        recapped = (prev.get(CAP_SINCE) is not None
                    and _doc_date(v["source"]) <= str(prev[CAP_SINCE]))
        for f in HAND_FIELDS + (CAP_SINCE,):
            if f in ("base_cap", "base_cap_why", "bear_cap", "bull_cap", CAP_SINCE,
                     "cap_binds_both_ways") and not recapped:
                continue
            if prev.get(f) is not None and f not in row:
                row[f] = prev[f]
        rows.append(row)
    strike_names = {r["ticker"] for r in rows}
    for e in existing:                      # machine and rough entries: kept as written
        if e["ticker"] not in strike_names:
            w = wl.get(e["ticker"])
            if w:
                e["status"] = w.get("status")
            rows.append(e)
    return sorted(rows, key=lambda r: r["ticker"])


HEADER = """\
# THE QUEUE -- every name we have valued (owner, 2026-11-05).
# Built by tools/build_queue.py: kind=strike rows are HARVESTED from the
# newest reference/<T>-STRIKE-*.md and the watchlist; kind=machine and
# kind=rough rows and the hand fields (sell_at, note, gate_*) are kept.
# Read nightly by `vss queue`, which NOTIFIES and writes nothing else.
#
# Values are in the TRADING unit (GBX listings x100). The buy line is the
# watchlist's MBP rule (base x E90 cushion by tier); a name with no tier has
# a LOOK line instead (base x 0.85 for a strike, x 0.75 for machine/rough),
# which says "strike it properly now", never "buy".
#
# portfolio_sek: the securities in the portfolio, from the owner's Avanza
# kontoöversikt 2026-11-08: 248,476 SEK = shares 62,100 + Avanza Zero
# 186,376; the buffer on the savings account is NOT in it. For the section 7
# ceiling (E157: one name at most 6% of it) on every HELD row with shares.
# WAS 190,000 until 2026-11-08: not the owner's figure but a session's
# estimate in the ACAD note of 2026-11-02 (commit 830febd): the ~56,454 SEK
# position taken as a ~30% sleeve, 56,454 / 0.30 = ~188,000 -> "~190k".
# The core in that base: Avanza Zero alone since 2026-11-04; until then Avanza
# Zero + Avanza USA (Avanza USA sold in full 2026-11-04, 38,584.74 SEK, with
# 36,147.72 SEK of Avanza Zero; 74,200 SEK to the buffer account BUFFER-ACCOUNT).
# Source: Avanza transaktioner 2026-11-08. Hand fields
# base_cap / bear_cap / bull_cap: a lower value a later ruling gives before
# the next strike (E154), dropped by this builder once the name is struck
# again; exit_pending: a sell decided and not yet carried out, reminded weekly;
# override: the owner set a rule aside for the name {rule, overrides, reason,
# standing, expires, since}, printed beside the line it touches.
"""


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--write", action="store_true")
    a = ap.parse_args(argv)
    whole = (yaml.safe_load(QUEUE.read_text()) or {}) if QUEUE.exists() else {}
    existing = whole.get("names", [])
    rows = build(existing)
    top = {k: v for k, v in whole.items() if k != "names"}     # portfolio_sek and the like: kept
    text = HEADER + yaml.safe_dump({**top, "names": rows}, sort_keys=False, allow_unicode=True, width=100)
    if a.write:
        QUEUE.write_text(text, encoding="utf-8")
        print(f"wrote {QUEUE.relative_to(ROOT)}: {len(rows)} names")
    else:
        for r in rows:
            print(f"{r['ticker']:10s} {r['kind']:7s} {r.get('status',''):13s} "
                  f"{r.get('bear')} / {r['base']} / {r.get('bull')}  tier={r.get('tier')} "
                  f"gate={r.get('gate_until','')}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
