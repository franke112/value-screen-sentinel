"""Fetch the vendor price data the tests read, from Yahoo, yourself.

The owner's copies are NOT in this repository: Yahoo Finance's terms allow
personal use, not redistribution. This script rebuilds each file listed in
tests/fixtures/VENDOR-DATA.json with yfinance, on the same dates and in the
same columns. Run it once:

    .venv/bin/python tools/fetch_test_fixtures.py

What to expect: the files will be CLOSE to the owner's, not identical --
Yahoo revises adjusted history, and the series-sanity files exist because
of vendor artefacts (a phantom split, a gap) that Yahoo may since have
fixed. A test that then fails on an exact figure is telling you exactly
that. tests/fixtures/ranking-acceptance/ cannot be rebuilt at all (it is a
point-in-time snapshot) and its tests stay skipped.
"""
import json
from datetime import date, timedelta
from pathlib import Path

import yfinance as yf

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "tests" / "fixtures" / "VENDOR-DATA.json"


def main() -> int:
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    for f in manifest["files"]:
        path = ROOT / f["path"]
        end = date.fromisoformat(f["end"]) + timedelta(days=1)
        frame = yf.Ticker(f["ticker"]).history(
            start=f["start"], end=end.isoformat(),
            auto_adjust=f.get("auto_adjust", False), actions=True)
        if frame.empty:
            print(f"{f['ticker']}: Yahoo returned nothing -- skipped")
            continue
        cols = [c for c in f["columns"][1:] if c in frame.columns]
        out = frame[cols]
        if f["columns"][0] == "Date" and len(f["columns"]) == 3:
            out.index = out.index.strftime("%Y-%m-%d")  # the series-sanity shape
        out.index.name = "Date"
        path.parent.mkdir(parents=True, exist_ok=True)
        out.to_csv(path)
        print(f"{f['ticker']}: {len(out)} rows -> {f['path']} "
              f"(owner's copy had {f['rows']})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
