"""E151: verify machine-read figures by a SECOND, INDEPENDENT machine reading.

    .venv/bin/python tools/cross_verify.py EVO.ST            # report only
    .venv/bin/python tools/cross_verify.py --all --apply     # every store; mark the agreeing

The owner does not check figures by hand (2026-11-07: "det måste gå att
kollas automatiskt"). A figure whose line a machine chose -- `esef-ixbrl` or
`llm-pdf` -- may not be verified by a read-back of itself (E149). It is
verified here, and only here, when ANOTHER FORMAT of the issuer's report,
read by ANOTHER METHOD, prints the same digits:

- an ESEF figure (the tag's displayed text, e.g. '1 062 096') against a
  model's reading of the PDF annual report for that fiscal year (or the
  next year's comparative column), through
  `vss/pdfdraft.py`'s gates (row on the page, value in the row, the column
  naming the year, two runs agreeing);
- an llm-pdf figure for a period against the same period's column in a
  LATER report (a comparative), read the same way.

Digits are compared as printed, never rescaled; an outflow must be negative
in the PDF; a zero is never verified; if ANY second reading disagrees the
figure is not verified, whatever another one says. The value in the store is NOT changed
-- it is the tagged (or first-read) value; the second reading only confirms
it. A disagreement leaves the figure UNVERIFIED and is printed. Model
readings are cached in data/cross-verify/ so a re-run costs nothing.
"""
from __future__ import annotations

import argparse
import glob
import json
import re
import sys
from decimal import Decimal
from pathlib import Path

import yaml

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from vss import pdfdraft as P  # noqa: E402

MANUAL = Path("config/manual")
CACHE = Path("data/cross-verify")
#: store field -> pdfdraft field (the same line)
COMPARABLE = ("net_income", "diluted_eps", "operating_cash_flow", "capex_ppe",
              "capex_intangibles", "lease_payments_capital", "cash_and_equivalents",
              "revenue", "operating_income", "total_equity", "total_assets")
_SHOWN = re.compile(r"displayed '([^']*)'")
_COL = re.compile(r"column '([^']*)'")


def printed(text: str) -> Decimal | None:
    """The digits as printed, sign ignored ("1 062 096", "1,062,096", "5,23")."""
    t = re.sub(r"[\s  ()−–\-]", "", text or "")
    if re.fullmatch(r"\d{1,3}(,\d{3})+(\.\d+)?", t):
        t = t.replace(",", "")
    elif re.fullmatch(r"\d+,\d{1,2}", t):
        t = t.replace(",", ".")
    elif not re.fullmatch(r"\d+(\.\d+)?", t):
        return None
    return Decimal(t)


def _reading(pdf: Path, ticker: str, target: str, runner=None) -> dict:
    """pdfdraft's gated reading for one PDF and period, cached."""
    CACHE.mkdir(parents=True, exist_ok=True)
    key = CACHE / f"{pdf.stem}__{target}.json"
    if key.exists():
        return json.loads(key.read_text(encoding="utf-8"))
    r = (runner or P.run)(pdf, ticker=ticker, target=target, require_unit=False)
    out = {"pdf": f"sources/{pdf.name}", "target": target, "model": r.record["model"],
           "responses_sha256": r.record["responses_sha256"],
           "kept": {n: {k: e.get(k) for k in ("value", "row", "column", "page")}
                    for n, e in r.gated.figures.items()},
           "dropped": r.gated.dropped}
    key.write_text(json.dumps(out, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return out


def annual_pdf(ticker: str, year: int) -> Path | None:
    """The annual report PDF for a fiscal year: English edition, first attachment."""
    found = sorted(glob.glob(f"sources/{ticker}_{year}-FY_annual-financial-report_*_en_a0.pdf"))
    return Path(found[-1]) if found else None


def later_reports(ticker: str, period: str, after: str) -> list[Path]:
    """Reports released after `after` that may print `period` as a comparative:
    the same quarter one year on."""
    m = re.fullmatch(r"(\d{4})-(Q[1-4])", period)
    if not m:
        return []
    nxt = f"{int(m.group(1)) + 1}-{m.group(2)}"
    return [Path(f) for f in sorted(glob.glob(f"sources/{ticker}_{nxt}_*.pdf"))
            if f.split("_")[3] > after]


def compare(name: str, store_value: float, first_digits: Decimal | None, reading: dict | None) -> tuple[bool, str]:
    if reading is None:
        return False, "no second reading of this line"
    if not store_value:
        return False, "a zero is never verified"
    second = printed(str(reading["value"]))
    if first_digits is None or second is None:
        return False, "the printed digits cannot be read"
    if name in P.OUTFLOWS and float(reading["value"]) > 0:
        return False, "the PDF prints the outflow positive"
    if first_digits != second:
        return False, f"DISAGREE: first {first_digits} vs PDF {second} (p.{reading['page']})"
    return True, f"p.{reading['page']} row '{reading['row']}'"


def check_store(path: Path, runner=None) -> list[dict]:
    d = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    ticker = d.get("ticker") or path.stem
    results = []
    for block, key in (("annual", "fiscal_year"), ("periods", "period")):
        for entry in d.get(block) or []:
            label = entry.get(key)
            todo = {n: r for n, r in (entry.get("figures") or {}).items()
                    if isinstance(r, dict) and r.get("status") == "UNVERIFIED"
                    and str(r.get("source") or "").startswith(("esef-ixbrl", "llm-pdf"))
                    and n in COMPARABLE}
            if not todo:
                continue
            readings: list[dict] = []
            if block == "annual":
                # the year's own report, then the next year's comparative column
                for year in (int(label), int(label) + 1):
                    pdf = annual_pdf(ticker, year)
                    if pdf:
                        readings.append(_reading(pdf, ticker, f"{label}-FY", runner))
            else:
                after = str(entry.get("url") or "").split("_")[3] if "_" in str(entry.get("url") or "") else ""
                for pdf in later_reports(ticker, str(label), after):
                    readings.append(_reading(pdf, ticker, str(label), runner))
            for name, raw in todo.items():
                page = str(raw.get("page") or "")
                shown = _SHOWN.search(page)
                if shown:
                    first = printed(shown.group(1))
                else:   # llm-pdf: its own row's printed value
                    first = printed(str(raw.get("value")))
                ok, why = False, "no second document yet"
                verdicts = [compare(name, raw.get("value"), first, rd["kept"].get(name)) + (rd["pdf"],)
                            for rd in readings]
                # ANY disagreement wins: a figure two readings dispute is not confirmed
                clash = [v for v in verdicts if v[1].startswith("DISAGREE")]
                good = [v for v in verdicts if v[0]]
                if clash:
                    ok, why = False, f"{clash[0][2]} {clash[0][1]}"
                elif good:
                    ok, why = True, f"{good[0][2]} {good[0][1]}"
                elif verdicts:
                    why = verdicts[0][1]
                results.append({"ticker": ticker, "block": block, "label": label, "field": name,
                                "ok": ok, "why": why})
    return results


def apply(path: Path, results: list[dict]) -> int:
    """Mark the agreeing figures VERIFIED / two_source, as text, nothing else."""
    lines = path.read_text(encoding="utf-8").split("\n")
    marked = 0
    for r in results:
        if not r["ok"]:
            continue
        key = f"  - {'fiscal_year' if r['block'] == 'annual' else 'period'}: {r['label']}"
        start = next((i for i, l in enumerate(lines) if l.rstrip() == key), None)
        if start is None:
            continue
        at = next((i for i in range(start + 1, len(lines))
                   if lines[i] == f"      {r['field']}:"), None)
        if at is None:
            continue
        end = next((i for i in range(at + 1, len(lines)) if not lines[i].startswith("        ")),
                   len(lines))
        status = next((i for i in range(at + 1, end) if lines[i].strip() == "status: UNVERIFIED"), None)
        page = next((i for i in range(at + 1, end) if lines[i].startswith("        page: ")), None)
        if status is None or page is None:
            continue
        text = yaml.safe_load(lines[page].split("page:", 1)[1])
        lines[page] = "        page: " + json.dumps(
            f"{text} | E151 second reading: {r['why']}", ensure_ascii=False)
        lines[status] = "        status: VERIFIED"
        lines.insert(status + 1, "        verified_kind: two_source")
        marked += 1
    new = "\n".join(lines)
    from vss.manual import parse_manual
    parse_manual(yaml.safe_load(new), path=path)        # fail closed
    path.write_text(new, encoding="utf-8")
    return marked


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("tickers", nargs="*", metavar="TICKER",
                    help="the stores to check (or --all)")
    ap.add_argument("--all", action="store_true",
                    help="every store in config/manual")
    ap.add_argument("--apply", action="store_true",
                    help="mark a figure VERIFIED (two_source) where a second, "
                         "independent reading prints the same digits "
                         "(default: report only). The value is never changed")
    return ap


def main(argv=None) -> int:
    a = build_parser().parse_args(argv)
    paths = ([p for p in sorted(MANUAL.glob("*.yaml")) if p.name != "TEMPLATE.yaml"] if a.all
             else [MANUAL / f"{t}.yaml" for t in a.tickers])
    bad = 0
    for path in paths:
        try:
            results = check_store(path)
        except Exception as exc:  # noqa: BLE001 -- one store never stops the rest
            print(f"{path.stem}: not checked ({type(exc).__name__}: {exc})")
            bad += 1
            continue
        if not results:
            continue
        ok = [r for r in results if r["ok"]]
        print(f"{path.stem}: {len(ok)} of {len(results)} confirmed by a second reading")
        for r in results:
            print(f"  {'OK  ' if r['ok'] else '--  '}{r['label']} {r['field']}: {r['why']}")
        if a.apply and ok:
            print(f"  marked VERIFIED (two_source): {apply(path, results)}")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
