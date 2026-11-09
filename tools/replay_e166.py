"""E166 re-valuation (sweep 2026-11-08, A4): each US queue name's latest run
record replayed with ONLY its working capital replaced by the figure tied to
the cash flow statement (vss/cfrecon.py, read from the filled store). The
balance-sheet date, the shares, the bridge and every other leg are the
record's own. E154 and E154.1 are switched on, as the rules in force today
(the queue already carries their effect through base_cap for the records
struck before them), so the only cause of a move is the working capital.

    .venv/bin/python tools/replay_e166.py            # table only
    .venv/bin/python tools/replay_e166.py --write    # + new records
"""
from __future__ import annotations

import argparse
import copy
import glob
import json
import subprocess
import sys
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

import yaml  # noqa: E402

from vss import runrecord as R  # noqa: E402

US = ("ACN ALV AOS BKNG CENTA CPRT CROX CTSH DECK DHI GDDY GNTX HRB LII LOPE "
      "MUSA NVR PEP SFM TPR ULTA ZTS").split()
STAMP = "2026-11-08-e166"


def latest(t: str) -> Path:
    return Path(max(glob.glob(str(ROOT / f"reference/run-records/{t}-*.json")),
                    key=lambda p: json.load(open(p)).get("run_ts", "")))


def tied_figures(t: str) -> tuple[dict, dict | None]:
    """{period_end: figure} for fiscal years, and the roll-forward's."""
    raw = yaml.safe_load((ROOT / f"config/manual/{t}.yaml").read_text())
    years = {str(a["period_end"]): a["figures"]["working_capital_change"]
             for a in raw.get("annual", [])
             if "working_capital_change" in (a.get("figures") or {})}
    rf = ((raw.get("roll_forward") or {}).get("figures") or {}).get("working_capital_change")
    return years, rf


def cases(raw: dict) -> dict:
    rec = R.RunRecord.from_dict(raw)
    out = {}
    for case in ("bear", "base", "bull"):
        g = raw["growth"].get(case)
        out[case] = None if g is None else rec.strike(g, case=case)
    return out


def replay(t: str) -> dict:
    path = latest(t)
    old = json.load(open(path))
    before = copy.deepcopy(old)
    before["e140"]["e154"] = True
    before["e140"]["e154_1"] = True
    after = copy.deepcopy(before)
    years, rf = tied_figures(t)
    money = R.UNIT_SCALE[old.get("money_unit", "whole")]
    ends = {}
    for name, fig in years.items():
        ends[name] = fig
    moved = []
    fy = R.RunRecord.from_dict(old)
    for y, label_end in zip(after["e140"]["years"], _year_ends(old)):
        fig = ends.get(label_end)
        if fig is None or fig.get("verified_kind") != "tied_statement":
            raise SystemExit(f"{t}: {y['label']} ({label_end}) is not tied in the store")
        new = float(fig["value"]) / money
        if abs(new - float(y["working_capital"])) > 0.5:
            moved.append(f"{y['label']} {float(y['working_capital']):,.0f} -> {new:,.0f}")
        y["working_capital"] = new
        _input(after, f"{y['label']} working_capital_change", new, fig["page"])
    if after["e140"].get("rolled_from"):
        if rf is None or rf.get("verified_kind") != "tied_statement":
            raise SystemExit(f"{t}: the roll-forward's working capital is not tied")
        new = float(rf["value"]) / money
        oldv = after["e140"].get("wc_since_year_end")
        if oldv is None or abs(new - float(oldv)) > 0.5:
            moved.append(f"year to date {float(oldv or 0):,.0f} -> {new:,.0f}")
        after["e140"]["wc_since_year_end"] = new
        after["e140"]["wc_since_page"] = rf["page"]
    return {"ticker": t, "prior": path, "old": old, "after": after,
            "before_v": cases(before), "after_v": cases(after), "moved": moved,
            "structural": (R.structural_wc(R.RunRecord.from_dict(after).e140.years)
                           if hasattr(R, "structural_wc") else None)}


def _year_ends(raw: dict) -> list[str]:
    """Each E140 year's period end, from the record's own inputs pages."""
    store = yaml.safe_load((ROOT / f"config/manual/{raw['ticker']}.yaml").read_text())
    by_fy = {f"annual FY{a['fiscal_year']}": str(a["period_end"])
             for a in store.get("annual", [])}
    return [by_fy[y["label"]] for y in raw["e140"]["years"]]


def _input(raw: dict, name: str, value: float, page: str) -> None:
    for i in raw.get("inputs", []):
        if i.get("name") == name:
            i["value"] = value
            i["provenance"] = page
            i["verified"] = "VERIFIED (tied_statement)"
            return


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--write", action="store_true")
    a = ap.parse_args()
    commit = subprocess.run(["git", "rev-parse", "--short", "HEAD"], cwd=ROOT,
                            capture_output=True, text=True).stdout.strip()
    rows = []
    for t in US:
        r = replay(t)
        rows.append(r)
        b, n = r["before_v"], r["after_v"]
        print(f"{t:6} bear {b['bear']:10.2f} -> {n['bear']:10.2f} | base {b['base']:10.2f} -> "
              f"{n['base']:10.2f} ({(n['base'] / b['base'] - 1) * 100:+6.1f}%) | bull "
              f"{b['bull']:10.2f} -> {n['bull']:10.2f} | {'; '.join(r['moved']) or 'unchanged'}")
        if a.write:
            new = r["after"]
            new["run_ts"] = datetime.now().astimezone().isoformat(timespec="seconds")
            new["tool_commit"] = f"tools/replay_e166.py, {commit}"
            new["notes"] = (f"E166 (2026-11-08) replay of {r['prior'].relative_to(ROOT)}: "
                            f"working capital tied to the cash flow statement "
                            f"(vss/cfrecon.py, config/manual/{t}.yaml); E154 and E154.1 on "
                            f"as today's rules; every other input unchanged. Moved: "
                            f"{'; '.join(r['moved']) or 'nothing'}")
            out = ROOT / f"reference/run-records/{t}-{STAMP}.json"
            out.write_text(json.dumps(new, indent=2, ensure_ascii=False) + "\n")
            assert abs(R.replay(new) - n["base"]) < 1e-9
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
