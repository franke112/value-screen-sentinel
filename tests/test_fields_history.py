"""HANDOFF C2: fundamentals_fields_history -- append-only, never pruned,
read as of a date; seeded from VERIFIED manual figures dated by filing."""
from __future__ import annotations

import json
import sqlite3
import sys
from pathlib import Path

from vss import store

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))
import seed_fields_history as SEED  # noqa: E402


def test_append_only_and_read_as_of(tmp_path):
    db = tmp_path / "vss.sqlite"
    rows = [("X", "totalDebt", 100.0, "2026-08-22T16:00:00", "", "yfinance"),
            ("X", "totalDebt", 120.0, "2026-10-01T16:00:00", "", "yfinance")]
    assert store.append_fields_history(db, rows) == 2
    assert store.append_fields_history(db, rows) == 0          # a re-run adds nothing
    assert store.fields_known_at(db, "X", "2026-09-01")["totalDebt"][0] == 100.0
    assert store.fields_known_at(db, "X", "2026-10-01")["totalDebt"][0] == 120.0
    assert store.fields_known_at(db, "X", "2026-08-01") == {}
    n = sqlite3.connect(db).execute("SELECT COUNT(*) FROM fundamentals_fields_history").fetchone()[0]
    assert n == 2


def test_the_seed_takes_verified_figures_dated_by_their_document(tmp_path, monkeypatch):
    man = tmp_path / "manifest.json"
    man.write_text(json.dumps({"downloads": [
        {"file": "EXM.ST_q3.pdf", "released": "2025-11-19T07:00:00Z"},
        {"file": "EXM.ST_q2_2026.pdf", "released": "2026-08-25T07:00:00Z"}]}))
    monkeypatch.setattr(SEED, "MANIFEST", man)
    store_file = tmp_path / "EXM.ST.yaml"
    store_file.write_text("""ticker: EXM.ST
name: Exempel
money_unit: thousands
share_unit: whole
periods:
  - period: 2025-Q3
    period_end: 2025-09-30
    document: "Q3"
    url: "sources/EXM.ST_q3.pdf"
    figures:
      revenue: {value: 743232, page: "p.21", status: VERIFIED}
      operating_income: {value: 80000, page: "p.21", status: UNVERIFIED}
      nci_dividends_paid: {value: 0, page: "sources/EXM.ST_q2_2026.pdf p.24", status: VERIFIED}
      diluted_eps: {value: 1.8, page: "p.21", status: VERIFIED}
  - period: 2025-Q4
    period_end: 2025-12-31
    document: "Q4, not in the manifest"
    url: "sources/EXM.ST_q4.pdf"
    figures:
      revenue: {value: 800000, page: "p.21", status: VERIFIED}
""")
    rows, undated = SEED.rows_for(store_file, SEED.released())
    got = {(r[1], r[4]): r for r in rows}
    assert got[("revenue", "2025-09-30")][2:4] == (743232000.0, "2025-11-19")      # whole units
    assert "stated in thousands" in got[("revenue", "2025-09-30")][5]
    assert ("operating_income", "2025-09-30") not in got                          # UNVERIFIED
    assert got[("nci_dividends_paid", "2025-09-30")][3] == "2026-08-25"           # the later document
    assert got[("diluted_eps", "2025-09-30")][2] == 1.8                           # per share: unscaled
    assert ("revenue", "2025-12-31") not in got and undated == 1                  # no date, not seeded
