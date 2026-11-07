"""Seed `fundamentals_fields_history` (HANDOFF C2) from the manual stores.

    .venv/bin/python tools/seed_fields_history.py            # report only
    .venv/bin/python tools/seed_fields_history.py --write    # append to data/vss.sqlite

VERIFIED figures only (E21). Each is dated by the FILING DATE of the
document it was read from: a `sec-xbrl` figure's page names it ("filed
YYYY-MM-DD"); a hand-read figure takes the LATEST release date that
`sources/manifest.json` records among the files its page and its period
cite (it was known only once all of them were out). A figure
whose document has no recorded date is NOT seeded -- an undated figure
cannot be placed in time, and a guess would be the look-ahead C2 exists to
remove. Money and share counts are written in WHOLE units by the file's own
`money_unit` / `share_unit` declaration, the stated unit kept on the row's
source. Re-running adds nothing already there.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

import yaml

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from vss.manual import FIELDS_BY_NAME, UNIT_SCALE  # noqa: E402
from vss.store import append_fields_history  # noqa: E402

MANUAL = Path("config/manual")
MANIFEST = Path("sources/manifest.json")
DB = Path("data/vss.sqlite")
_FILED = re.compile(r"\bfiled (\d{4}-\d{2}-\d{2})\b")
_SOURCE = re.compile(r"sources/([^\s'\",;)]+)")


def released() -> dict[str, str]:
    doc = json.loads(MANIFEST.read_text(encoding="utf-8")) if MANIFEST.exists() else {}
    return {r["file"]: (r.get("released") or "")[:10] for r in doc.get("downloads", [])
            if (r.get("released") or "")[:10]}


def rows_for(path: Path, dates: dict[str, str]) -> tuple[list[tuple], int]:
    d = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    origin = str(d.get("origin") or "manual")
    money_unit = str(d.get("money_unit") or "whole")
    share_unit = str(d.get("share_unit") or "whole")
    out, undated = [], 0
    for block, key in (("periods", "period"), ("annual", "fiscal_year")):
        for entry in d.get(block) or []:
            files = _SOURCE.findall(str(entry.get("url") or "") + " " + str(entry.get("document") or ""))
            entry_date = next((dates[f] for f in files if f in dates), None)
            for name, raw in (entry.get("figures") or {}).items():
                if not isinstance(raw, dict) or raw.get("status") != "VERIFIED":
                    continue
                value = raw.get("value")
                if not isinstance(value, (int, float)) or isinstance(value, bool):
                    continue
                page = str(raw.get("page") or "")
                m = _FILED.search(page)
                own = [f for f in _SOURCE.findall(page) if f in dates]
                # the LATEST of the documents it stands on: known only once
                # all of them were out (never earlier than it could be)
                known = [dates[f] for f in own] + ([entry_date] if entry_date else [])
                when = m.group(1) if m else (max(known) if known else None)
                if not when:
                    undated += 1
                    continue
                # ONE scale in the table: whole units, by the file's own
                # declaration (as the run record normalises); the unit it
                # was stated in stays on the row
                kind = getattr(FIELDS_BY_NAME.get(name), "kind", None)
                unit = money_unit if kind == "money" else share_unit if kind == "count" else None
                if unit is not None and unit not in UNIT_SCALE:
                    undated += 1
                    continue
                number = float(value) * (UNIT_SCALE[unit] if unit else 1.0)
                out.append((d.get("ticker") or path.stem, name, number, when,
                            str(entry.get("period_end") or ""),
                            f"{origin}:{block}" + (f" (stated in {unit})" if unit and unit != "whole" else "")))
    return out, undated


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--write", action="store_true")
    a = ap.parse_args(argv)
    dates = released()
    total, undated_all = [], 0
    for path in sorted(MANUAL.glob("*.yaml")):
        if path.name == "TEMPLATE.yaml":
            continue
        rows, undated = rows_for(path, dates)
        total += rows
        undated_all += undated
        print(f"{path.stem:12s} {len(rows):4d} dated VERIFIED figure(s), {undated:3d} undated (not seeded)")
    print(f"{len(total)} row(s) to seed; {undated_all} VERIFIED figure(s) undated and left out")
    if a.write:
        print(f"{append_fields_history(DB, total)} new row(s) appended to {DB}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
