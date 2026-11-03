"""Path 1's pilot: the method's core (`method`) on the step-4 draw.

    .venv/bin/python -m tools.backtest.method_pilot [--date 2018-04-30] [--n 50] [--seed 20261029]

Same draw, same seed, same float line and price path as `pilot`, so the two
tables are row for row the same names. Writes the rows as JSON beside the
data and prints the whole table: it is meant to be READ in full (CLAUDE.md,
bounded output does not apply to a first run).
"""
from __future__ import annotations

import argparse
import json
import sys
from datetime import date

from . import method as M
from . import pilot as PL
from . import universe as U
from . import value as V


def run(as_of: date, n: int, seed: int) -> dict:
    day = PL.trading_day(as_of)
    index = PL.prices(PL.INDEX)
    out = []
    for cand in PL.draw(as_of, n, seed):
        if len(out) >= n:
            break
        facts = PL.company_facts(cand["cik"])
        if facts is None:
            continue
        pf = U.pit_float(facts, day)
        if pf is None or pf[0] < U.FLOAT_MIN:
            continue
        ticker = (cand.get("tickers_today") or [None])[0]
        row = M.evaluate(facts, day, ticker=ticker or f"CIK{cand['cik']}",
                         cik=cand["cik"], sic=cand.get("sic"))
        row.update(company=cand["company"], public_float=pf[0], price=None,
                   returns={}, index_returns={})
        frame = PL.prices(ticker) if ticker else None
        got = PL.unadjusted_close(frame, day) if frame is not None else None
        if got is not None:
            M.with_price(row, got[1], pf[0])
            for h in PL.HORIZONS:
                end = PL.years_after(day, h)
                row["returns"][h] = PL.total_return(frame, day, end)
                row["index_returns"][h] = PL.total_return(index, day, end)
        row["passes_quality"] = V.passes_quality(row) if row["quality"] else None
        row["measured_kill"] = V.measured_kill(row)
        out.append(row)
    result = {"as_of": as_of.isoformat(), "trading_day": day.isoformat(),
              "seed": seed, "rows": out}
    dest = PL.ROOT / "pilot" / f"METHOD-{as_of.isoformat()}.json"
    dest.write_text(json.dumps(result, indent=1, default=str))
    return result


def _f(x, spec):
    return "–" if x is None else format(x, spec)


def table(result: dict) -> list[str]:
    lines = ["| # | Bolag | Status | FCF0 m | g | Cyk | ND m | fv | bear | Kurs | fv/kurs | "
             "utan E142 | Q1-4 | Stopp | EBIT/EV | F | Float/cap | 1 år | 3 år | Index 3 år | Nollor |",
             "|" + "---|" * 21]
    for i, r in enumerate(result["rows"], 1):
        q = "".join({True: "+", False: "x", None: "?"}[r["quality"].get(k)]
                    for k in ("Q1", "Q2", "Q3", "Q4")) if r["quality"] else "–"
        ret = r["returns"]
        lines.append("| " + " | ".join([
            str(i), f"{r['company'][:28]} ({r['ticker']})",
            r["status"][:60] or "–",
            _f(None if r["fcf0"] is None else r["fcf0"] / 1e6, ",.0f"),
            _f(r["g_base"], ".1%") + ("*" if r["growth_source"].startswith("FALLBACK") else ""),
            {True: "C", False: "", None: "?"}[r["cyclical"]],
            _f(None if r["net_debt"] is None else r["net_debt"] / 1e6, ",.0f"),
            _f(r["fv_base"], ",.2f"), _f(r["fv_bear"], ",.2f"), _f(r["price"], ",.2f"),
            _f(r.get("fv_over_price"), ".2f"), _f(r.get("fv_ex_programme"), ",.2f"), q,
            "JA" if r["measured_kill"] else "",
            _f(r.get("ebit_ev"), ".1%"), _f(r["fscore"], "d"),
            _f(r.get("float_over_cap"), ".2f") + ("" if r.get("cap_check", True) else " !"),
            _f(ret.get(1), ".0%"), _f(ret.get(3), ".0%"),
            _f(r["index_returns"].get(3), ".0%"),
            str(r["zeros"]) + (f" (-{r['wc_dropped']} brutto)" if r.get("wc_dropped") else ""),
        ]) + " |")
    return lines


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--date", default="2018-04-30")
    ap.add_argument("--n", type=int, default=50)
    ap.add_argument("--seed", type=int, default=20261029)
    a = ap.parse_args(argv)
    result = run(date.fromisoformat(a.date), a.n, a.seed)
    print("\n".join(table(result)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
