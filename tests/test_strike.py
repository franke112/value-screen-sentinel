"""`vss strike` -- the front door on what the dated scripts in tools/ do.

Built 2026-09-20 on the owner's answers: the section 5 gate is BINDING by
default and `--ignore-gate` prints its use in both the strike doc and the
record's notes, because "a front door gets used routinely; a sweep's
behaviour as the default would become silent within a few quarters".
"""
from datetime import date, datetime
from pathlib import Path

import pytest

from vss import strike as S
from vss.config import load_watchlist

REPO = Path(__file__).resolve().parents[1]
#: E140(4): a strike needs an events ledger no older than a week, and the
#: 27 ledgers are dated 2026-10-27 -- so the tests strike on that day.
RUN_TS = datetime(2026, 10, 27, 12, 0).astimezone()
AS_OF = date(2026, 10, 27)


def pre_e140_records(tmp_path: Path, ticker: str = "CTSH") -> Path:
    """A records directory holding only the records struck BEFORE E140, so
    the prior a test strikes against is fixed whatever has been struck
    since."""
    import json
    from vss import runrecord as R
    out = tmp_path / "records"
    out.mkdir(exist_ok=True)
    for path in S.RECORDS_DIR.glob(f"{ticker}-*.json"):
        raw = json.loads(path.read_text())
        if not raw.get("e140"):
            (out / path.name).write_bytes(path.read_bytes())
    return out


def entry(ticker: str):
    return next((e for e in load_watchlist(REPO / "config" / "watchlist.yaml")
                 if e.ticker == ticker), None)


# --- refusal 1: no registered growth view (E28) ---------------------------

def test_a_name_with_no_view_anywhere_is_REFUSED_and_writes_nothing(tmp_path):
    """PHM has a store and no growth view: E28 says a view written after the
    solve is void, so a strike may not invent one."""
    with pytest.raises(S.StrikeError) as exc:
        S.strike_one("PHM", as_of=AS_OF, run_ts=RUN_TS,
                     stamp="test", entry=entry("PHM"), records_dir=tmp_path)
    assert "NO REGISTERED GROWTH VIEW" in str(exc.value) and "E28" in str(exc.value)
    assert not list(tmp_path.iterdir())


def test_the_view_comes_from_the_prior_record_when_there_is_one():
    prior_path, prior = S.latest_record("CTSH")
    assert prior is not None
    got = S.growth_for(entry("CTSH"), prior)
    assert (got.base, got.bear, got.bull) == (prior.growth.base,
                                              prior.growth.bear, prior.growth.bull)


def test_a_first_strike_takes_the_view_from_the_entry(tmp_path):
    """No prior record: E109's machine-readable block on the entry."""
    got = S.growth_for(entry("GDDY"), None)
    assert got.base == 0.03 and got.bear == 0.01 and got.bull == 0.08
    assert got.view_file.endswith("GDDY.md")


# --- refusal 2: the gate is binding by default ----------------------------

def test_the_gate_is_binding_by_default(monkeypatch, tmp_path):
    from vss import manual as M

    class Refused:
        refused = True
        refusals = (type("R", (), {"kind": "UNVERIFIED", "subject": "revenue"})(),)

    monkeypatch.setattr(M, "section5_gate", lambda *a, **k: Refused())
    with pytest.raises(S.StrikeError) as exc:
        S.strike_one("CTSH", as_of=AS_OF, run_ts=RUN_TS,
                     stamp="test", entry=entry("CTSH"))
    assert "GATE REFUSES" in str(exc.value) and "--ignore-gate was not given" in str(exc.value)
    assert "UNVERIFIED: revenue" in str(exc.value)


def test_ignore_gate_strikes_and_says_so_in_BOTH_the_record_and_the_doc(monkeypatch):
    from vss import manual as M

    class Refused:
        refused = True
        refusals = (type("R", (), {"kind": "UNVERIFIED", "subject": "revenue"})(),)

    monkeypatch.setattr(M, "section5_gate", lambda *a, **k: Refused())
    struck = S.strike_one("CTSH", as_of=AS_OF, run_ts=RUN_TS,
                          stamp="test", entry=entry("CTSH"), ignore_gate=True)
    assert struck.ignored_gate
    assert "--ignore-gate" in struck.record.notes
    assert "E21" in struck.record.notes
    doc = S.document(struck)
    assert "--ignore-gate" in doc and "UNVERIFIED: revenue" in doc


# --- the no-watchlist-write guard ----------------------------------------

def test_the_guard_stops_a_run_that_touched_the_watchlist():
    with pytest.raises(S.StrikeError) as exc:
        S.assert_no_watchlist_write("a", "b")
    assert "never writes fv_base, tier, mbp, stop_price or status" in str(exc.value)


def test_a_real_run_leaves_the_watchlist_byte_identical(tmp_path):
    before = (REPO / "config" / "watchlist.yaml").read_bytes()
    code, report = S.run_strike(ticker="CTSH", dry_run=True, now=RUN_TS,
                                records_dir=pre_e140_records(tmp_path),
                                docs_dir=tmp_path)
    assert code == 0
    assert (REPO / "config" / "watchlist.yaml").read_bytes() == before
    assert "no record written" in report


# --- the front door agrees with the dated script -------------------------

def test_the_prior_record_stands_and_the_new_strike_is_E142s(tmp_path):
    """E87: the E117 pass struck CTSH at 84.1646 and that record still
    replays to it -- a record is a statement on the rules of its date. The
    strike made today carries E140's block and E142's legs: FCF0 is the
    three-year mean ex working capital with the acquisition mean NOT
    deducted, rolled a year (E143(1)); the repeat buyer's programme is
    valued at its own ROIIC, which on CTSH's history is below zero and
    counts as zero (E142(3)); DyFlex, still pending, is in the bridge and
    is credited back at that same zero."""
    struck = S.strike_one("CTSH", as_of=AS_OF, run_ts=RUN_TS, stamp="test",
                          entry=entry("CTSH"),
                          records_dir=pre_e140_records(tmp_path))
    assert struck.prior is not None and struck.prior.e140 is None
    assert struck.prior.strike() == pytest.approx(84.164613, abs=1e-5)
    block = struck.record.e140
    assert block is not None and block.e142 is not None
    flow = struck.record.normalised_flow()
    assert flow.repeat_buyer and flow.acquisitions_mean == pytest.approx(674_666_666.67, rel=1e-6)
    assert flow.fcf0 == pytest.approx(flow.mean + flow.interest_added_back - flow.nci)
    assert block.e142.repeat_buyer and block.e142.roiic_base < 0
    assert struck.record.dates.balance_sheet == date(2026, 6, 30)
    assert [d.name.split()[0] for d in block.deals] == ["DyFlex"]
    parts = struck.record.e142_parts()
    assert parts["deal_credit"] == 0.0 and parts["programme"] < 0
    assert struck.fv == pytest.approx(73.96, abs=0.01)   # 73.82 before E146 credited the pension leg after tax


# --- the table: link 5 ----------------------------------------------------

def test_the_table_prints_the_tier_on_BOTH_sides():
    """Owner, 2026-09-20: E77 re-scores at a report, and a tier moving 2 to 3
    shifts the MBP further than the value does -- without both tiers printed
    that reads as the value falling."""
    struck = S.strike_one("CTSH", as_of=AS_OF, run_ts=RUN_TS,
                          stamp="test", entry=entry("CTSH"))
    struck.tier_before, struck.tier_after = 2, 3
    text = S.table(struck)
    assert "tier 2 -> 3" in text
    assert "of which the tier" in text          # what the tier alone did
    assert f"{round(struck.fv * 0.65, 2):,.2f}" in text   # base x 0.65


def test_the_table_carries_the_legs_and_what_the_sides_stand_on():
    struck = S.strike_one("CTSH", as_of=AS_OF, run_ts=RUN_TS,
                          stamp="test", entry=entry("CTSH"))
    text = S.table(struck)
    for wanted in ("fv_base", "bear", "bull", "g*", "WHICH LEG MOVED",
                   "basis window end", "settled close",
                   "store's newest period"):
        assert wanted in text, wanted
    assert "unchanged:" in text                 # nothing moved in this store


def test_a_quarter_that_landed_after_the_basis_is_named():
    """CTSH's basis is FY2025 and its store holds 2026-06-30: E19 chooses ONE
    window, and the table says the newer quarter was not read."""
    struck = S.strike_one("CTSH", as_of=AS_OF, run_ts=RUN_TS,
                          stamp="test", entry=entry("CTSH"))
    assert "a quarter has landed that this strike did not read" in S.table(struck)


# --- writing --------------------------------------------------------------

def test_it_writes_a_record_and_a_doc_and_nothing_else(tmp_path):
    records, docs = tmp_path / "records", tmp_path / "docs"
    docs.mkdir()
    for path in S.RECORDS_DIR.glob("CTSH-*.json"):
        records.mkdir(exist_ok=True)
        (records / path.name).write_bytes(path.read_bytes())
    code, report = S.run_strike(ticker="CTSH", stamp="2026-10-27-test",
                                now=RUN_TS, records_dir=records, docs_dir=docs)
    assert code == 0
    assert (records / "CTSH-2026-10-27-test.json").exists()
    assert (docs / "CTSH-STRIKE-2026-10-27-test.md").exists()
    assert sorted(p.name for p in docs.iterdir()) == ["CTSH-STRIKE-2026-10-27-test.md"]
    assert "The watchlist was NOT written" in report


def test_the_latest_record_is_chosen_by_run_ts_not_by_filename(tmp_path):
    import json
    src = sorted(S.RECORDS_DIR.glob("CTSH-*.json"))[0]
    raw = json.loads(src.read_text())
    (tmp_path / "CTSH-2026-01-01.json").write_text(json.dumps(raw))
    older = dict(raw)
    older["run_ts"] = "2020-01-01T00:00:00+00:00"
    (tmp_path / "CTSH-2099-12-31.json").write_text(json.dumps(older))
    path, record = S.latest_record("CTSH", tmp_path)
    assert path.name == "CTSH-2026-01-01.json"


# --- refusal 4: the events ledger (E140(4)) --------------------------------

def test_no_events_ledger_is_REFUSED_and_writes_nothing(tmp_path):
    """E140(4): no value is struck without a ledger of the deals after the
    basis -- CENTA's 2026-10-20 strike missed four."""
    with pytest.raises(S.StrikeError) as exc:
        S.strike_one("CTSH", as_of=AS_OF, run_ts=RUN_TS, stamp="test",
                     entry=entry("CTSH"), records_dir=pre_e140_records(tmp_path),
                     events_dir=tmp_path / "no-ledgers")
    assert "NO EVENTS LEDGER" in str(exc.value) and "Nothing was written" in str(exc.value)


def test_a_ledger_older_than_a_week_is_REFUSED(tmp_path):
    with pytest.raises(S.StrikeError) as exc:
        S.strike_one("CTSH", as_of=date(2026, 11, 4), run_ts=RUN_TS,
                     stamp="test", entry=entry("CTSH"),
                     records_dir=pre_e140_records(tmp_path))
    assert "past E140(4)'s 7" in str(exc.value)


def test_the_doc_prints_the_E140_parts_and_both_deal_ends(tmp_path):
    struck = S.strike_one("CENTA", as_of=AS_OF, run_ts=RUN_TS, stamp="test",
                          entry=entry("CENTA"),
                          records_dir=pre_e140_records(tmp_path, "CENTA"))
    doc = S.document(struck)
    assert "E140 FCF0:** mean of" in doc and "repeat buyer" in doc
    assert "bridge rolled (E140.1(3)):** 2025-09-27 -> 2026-06-27" in doc
    assert "already in the balance sheet: Champion" in doc
    assert "deals at LOW end" in S.table(struck)
    assert struck.record.at_deal_end("low") > struck.fv
