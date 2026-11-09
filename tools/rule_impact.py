"""What a rule change does to EVERY name, not only the one that asked for it.

    .venv/bin/python tools/rule_impact.py --save /tmp/before.json   # on the old code
    (change the code)
    .venv/bin/python tools/rule_impact.py --diff /tmp/before.json   # on the new code

Review 2026-11-08 H1 and E155: the rulebook was adjusted name by name -- E148
for BKNG, E148.1 for PHM -- and a ruling's effect was measured, when it was,
on the names the session chose. This tool takes the latest record of every
name the queue holds (the strike document's own record), replays it under
the code as it stands, and runs E145's quality tests on its history file:
fv base, bear, bull, and Q1-Q5 pass / fail / not tested. `--diff` prints
every name whose value or test result moved, with the counts E152(2) asks a
ruling to state: up, down, newly passing, newly failing.

It writes nothing in the repository and judges nothing: a list of what moved.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import replace
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import yaml  # noqa: E402

from vss import history as HI  # noqa: E402
from vss.runrecord import RunRecord  # noqa: E402

def as_new_strike(rec: RunRecord) -> RunRecord:
    """The record as a strike TODAY would carry it, every other input the
    same: a record replays the rules of its date (E87), so a ruling that a
    new strike switches on with a flag is switched on here. A NEW RULING
    BEHIND A FLAG ADDS ITS FLAG HERE, or this tool cannot see it."""
    e = rec.e140
    if e is None:
        return rec
    return replace(rec, e140=replace(e, e154=True, e154_1=True))


RECORD = re.compile(r"reference/run-records/[\w.\-]+\.json")
MOVE = 0.0005          # a relative change below this is rounding, not a move


def latest_records() -> dict[str, Path]:
    q = yaml.safe_load((ROOT / "config/queue.yaml").read_text())
    rows = q["names"] if isinstance(q, dict) and "names" in q else q
    if isinstance(rows, dict):
        rows = next(v for v in rows.values() if isinstance(v, list))
    out = {}
    for r in rows:
        if r.get("kind") != "strike" or not r.get("source"):
            continue
        src = ROOT / r["source"]
        found = RECORD.findall(src.read_text()) if src.exists() else []
        if found:
            out[r["ticker"]] = ROOT / found[-1]
    return out


def snapshot() -> dict[str, dict]:
    snap = {}
    for ticker, path in sorted(latest_records().items()):
        row: dict = {"record": str(path.relative_to(ROOT))}
        try:
            rec = as_new_strike(RunRecord.from_dict(json.loads(path.read_text())))
            row.update({c: rec.strike(getattr(rec.growth, c), case=c) for c in ("bear", "base", "bull")})
        except Exception as exc:  # noqa: BLE001 -- a record that no longer values is itself a result
            row["error"] = f"{type(exc).__name__}: {exc}"[:160]
            snap[ticker] = row
            continue
        h, e = HI.load(ticker), rec.e140
        if h is not None and e is not None and e.e142 is not None and e.tax_rate is not None:
            try:
                parts, legs = rec.e142_parts(), rec.legs()
                tests = HI.quality(h, tax=e.tax_rate, fcf0=parts["fcf0"], net_debt=-legs.net_cash,
                                   roiic_base=e.e142.roiic_base, repeat_buyer=e.e142.repeat_buyer,
                                   rate=rec.rate.rate)
                row["tests"] = {t.name: t.passed for t in tests}
            except Exception as exc:  # noqa: BLE001
                row["tests_error"] = f"{type(exc).__name__}: {exc}"[:160]
        snap[ticker] = row
    return snap


def diff(before: dict, after: dict) -> list[str]:
    lines, up, down, newly_pass, newly_fail = [], 0, 0, 0, 0
    for t in sorted(set(before) | set(after)):
        a, b = before.get(t, {}), after.get(t, {})
        notes = []
        if a.get("error") != b.get("error"):
            notes.append(f"error {a.get('error')!r} -> {b.get('error')!r}")
        x, y = a.get("base"), b.get("base")
        if x is not None and y is not None and abs(y - x) > MOVE * max(abs(x), 1e-9):
            notes.append(f"base {x:,.2f} -> {y:,.2f} ({(y / x - 1) if x else float('nan'):+.1%})")
            up += y > x
            down += y < x
        for name in sorted(set(a.get("tests", {})) | set(b.get("tests", {}))):
            p, q = a.get("tests", {}).get(name), b.get("tests", {}).get(name)
            if p != q:
                notes.append(f"{name} {p} -> {q}")
                newly_pass += q is True and p is not True
                newly_fail += q is False and p is not False
        if notes:
            lines.append(f"- {t}: " + "; ".join(notes))
    head = (f"{len(after)} names: base {up} up, {down} down, "
            f"{len(after) - up - down} unchanged; tests {newly_pass} newly passing, "
            f"{newly_fail} newly failing")
    return [head, *lines]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--save", type=Path, help="write the snapshot of the code as it stands")
    g.add_argument("--diff", type=Path, help="compare the code as it stands with a saved snapshot")
    return ap


def main(argv=None) -> int:
    a = build_parser().parse_args(argv)
    now = snapshot()
    if a.save:
        a.save.write_text(json.dumps(now, indent=1))
        print(f"{len(now)} names saved to {a.save}")
    else:
        print("\n".join(diff(json.loads(a.diff.read_text()), now)))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
