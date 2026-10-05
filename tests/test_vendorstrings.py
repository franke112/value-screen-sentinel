"""The vendor strings E51 and E96 decide on, kept where pruning cannot reach.

CODE-REVIEW-2026-09-01 D3. The defect was not in either limb — both are pure
and both were right. It was that their INPUT lived only inside the dated
fundamentals stores that `screenwatch.prune_snapshots(keep=4)` deletes, and
that E49's retention carries series rows and not fields, so the string did
not travel. E96's owner ticker list is empty, so E96 rested on that string
alone, and 61 names were excluded by it.

**The test that matters is `test_the_string_limb_still_removes_a_name_when_every_store_is_gone`.**
It runs step 0 against a snapshot with NO fundamentals store at all — the
state four weekly runs from any given fetch — and asks whether E96 still
fires. Before the fix it could not: there was nowhere else to look.
"""

from __future__ import annotations

from datetime import date
from pathlib import Path

import pytest
import yaml

from tests.test_screen import (AS_OF, dislocated, exclusions,  # noqa: F401
                               prepare, reader_for, universe)
from vss import vendorstrings as VS

DAY = date(2026, 8, 21)
LATER = date(2026, 8, 31)


# --- the table itself ------------------------------------------------------


def test_a_string_recorded_is_a_string_read_back(tmp_path: Path):
    db = tmp_path / "t.sqlite"
    VS.record(db, {"NHY.OL": ("Basic Materials", "Aluminum")}, observed=DAY)
    assert VS.read(db) == {"NHY.OL": ("Basic Materials", "Aluminum")}


def test_a_ticker_with_no_string_at_all_is_not_stored(tmp_path: Path):
    """An absent classification is a fact about the FETCH. There is nothing
    to remember about it, and a row would imply there was."""
    db = tmp_path / "t.sqlite"
    assert VS.record(db, {"AAA": (None, None), "BBB": ("", "  ")},
                     observed=DAY) == 0
    assert VS.read(db) == {}


def test_recording_the_same_string_twice_does_not_move_first_seen(tmp_path: Path):
    """Idempotent. `first_seen` says when the string was FIRST true, and the
    whole value of the column is that a replay can trust it."""
    db = tmp_path / "t.sqlite"
    VS.record(db, {"AAA": ("S", "Copper")}, observed=DAY)
    VS.record(db, {"AAA": ("S", "Copper")}, observed=LATER)
    assert VS.summary(db) == {"tickers": 1, "rows": 1,
                              "first_seen": DAY.isoformat(),
                              "last_seen": LATER.isoformat()}


def test_a_reclassification_keeps_both_and_the_NEWEST_wins(tmp_path: Path):
    """EXO.AS is the live case: Farm & Heavy Construction Machinery on
    2026-08-21, Asset Management on 2026-08-26."""
    db = tmp_path / "t.sqlite"
    VS.record(db, {"EXO.AS": ("Industrials", "Farm & Heavy Construction Machinery")},
              observed=DAY)
    VS.record(db, {"EXO.AS": ("Financial Services", "Asset Management")},
              observed=LATER)
    assert VS.summary(db)["rows"] == 2
    assert VS.read(db)["EXO.AS"] == ("Financial Services", "Asset Management")


def test_a_replay_sees_only_what_was_known_by_then(tmp_path: Path):
    """E49's rule -- a later-dated store is never read backwards -- applied
    to this table. Without it a replay of an old date would be struck on a
    classification that did not exist yet."""
    db = tmp_path / "t.sqlite"
    VS.record(db, {"EXO.AS": ("Industrials", "Farm & Heavy Construction Machinery")},
              observed=DAY)
    VS.record(db, {"EXO.AS": ("Financial Services", "Asset Management")},
              observed=LATER)
    assert VS.read(db, before=DAY)["EXO.AS"][1] == "Farm & Heavy Construction Machinery"
    assert VS.read(db, before=LATER)["EXO.AS"][1] == "Asset Management"
    assert VS.read(db, before=date(2026, 8, 20)) == {}


def test_an_absent_database_reads_empty_rather_than_raising(tmp_path: Path):
    assert VS.read(tmp_path / "nothing.sqlite") == {}
    assert VS.summary(tmp_path / "nothing.sqlite")["tickers"] == 0


def test_an_empty_table_is_described_as_a_FINDING_naming_the_fix(tmp_path: Path):
    """An empty table silently readmits every name the string limb is the
    only thing excluding, so a run must not print it as a count of zero."""
    lines = "\n".join(VS.describe(tmp_path / "nothing.sqlite"))
    assert "EMPTY" in lines
    assert "E96 is not being applied at all" in lines
    assert "backfill-vendor-strings" in lines


def test_a_populated_table_describes_its_size_and_its_dates(tmp_path: Path):
    db = tmp_path / "t.sqlite"
    VS.record(db, {"AAA": ("S", "Copper")}, observed=DAY)
    lines = "\n".join(VS.describe(db))
    assert "1 ticker(s)" in lines and DAY.isoformat() in lines
    assert "EMPTY" not in lines


def test_stores_are_laid_OVER_the_table_newest_wins(tmp_path: Path):
    """Belt and braces: a machine whose data/vss.sqlite was replaced still
    gets what is on disk, and a fresh fetch reaches step 0 in its own run."""
    merged = VS.merge_with_stores(
        {"AAA": ("S", "old"), "BBB": ("S", "kept")},
        [(DAY, {"AAA": ("S", "older")}), (LATER, {"AAA": ("S", "newest")})])
    assert merged["AAA"] == ("S", "newest")
    assert merged["BBB"] == ("S", "kept")


def test_the_backfill_stamps_each_store_with_ITS_OWN_date(tmp_path: Path):
    """Not the day the backfill ran -- otherwise every `first_seen` would be
    today and no replay could ever be honest again."""
    from vss import snapshot as snapshot_store

    root = tmp_path / "snaps"
    for day, industry in ((DAY, "Copper"), (LATER, "Copper")):
        path = root / day.isoformat() / "fundamentals.sqlite"
        conn = snapshot_store.connect_fundamentals(path)
        with conn:
            conn.execute("INSERT INTO fundamentals_fields VALUES (?,?,?,?,?)",
                         ("AAA", "industry", "OK", None, industry))
            conn.execute("INSERT INTO fundamentals_fields VALUES (?,?,?,?,?)",
                         ("AAA", "sector", "OK", None, "Basic Materials"))
        conn.close()

    db = tmp_path / "t.sqlite"
    outcome = VS.backfill_from_stores(db, root)
    assert [name for name, _ in outcome["stores"]] == [DAY.isoformat(),
                                                       LATER.isoformat()]
    assert VS.summary(db)["first_seen"] == DAY.isoformat()
    assert VS.read(db, before=DAY)["AAA"] == ("Basic Materials", "Copper")


def test_the_backfill_is_idempotent(tmp_path: Path):
    from vss import snapshot as snapshot_store

    root = tmp_path / "snaps"
    path = root / DAY.isoformat() / "fundamentals.sqlite"
    conn = snapshot_store.connect_fundamentals(path)
    with conn:
        conn.execute("INSERT INTO fundamentals_fields VALUES (?,?,?,?,?)",
                     ("AAA", "industry", "OK", None, "Copper"))
    conn.close()
    db = tmp_path / "t.sqlite"
    VS.backfill_from_stores(db, root)
    first = VS.summary(db)
    VS.backfill_from_stores(db, root)
    assert VS.summary(db) == first


# --- the limb, end to end, with the stores GONE ----------------------------


def _commodity_list(tmp_path: Path, industries) -> Path:
    path = tmp_path / "commodity.yaml"
    path.write_text(yaml.safe_dump({"industries": list(industries),
                                    "sectors": [], "tickers": [],
                                    "exempt": []}), encoding="utf-8")
    return path


def test_the_string_limb_still_removes_a_name_when_every_store_is_gone(
        universe: Path, tmp_path: Path, exclusions: Path):
    """**THE ONE THAT MATTERS.**

    Four weekly runs after a fetch, every store that ever held the string is
    deleted -- and an E96 name is never a filter-1 survivor, so it is never
    re-fetched and the string is never re-written. This is that state: a
    price snapshot with NO fundamentals store beside it, anywhere.

    Break `filter1`'s read of the durable table and this goes red: the name
    comes back into the universe, which is precisely what would have happened
    on 2026-09-05 to ANTO.L, KGH.WA, LUMI.ST, MRNA, SCA-A.ST, SCA-B.ST,
    SNM-SDB.ST and UPM.HE.
    """
    from vss import screen

    root = prepare(universe, tmp_path, {"SAP.DE": dislocated(),
                                        "VOLV-B.ST": dislocated()})
    # The state after pruning: prices, and no fundamentals store anywhere.
    assert not list(root.rglob("fundamentals.sqlite"))

    db = tmp_path / "durable.sqlite"
    VS.record(db, {"VOLV-B.ST": ("Basic Materials", "Aluminum")}, observed=DAY)

    run = screen.filter1(
        as_of=AS_OF, universe_dir=universe, snapshot_root=root,
        exclusions_path=exclusions,
        commodity_price_path=_commodity_list(tmp_path, ["Aluminum"]),
        runs_root=tmp_path / "runs", db_path=db)

    assert [h.ticker for h in run.commodity.hits] == ["VOLV-B.ST"]
    assert [c.ticker for c in run.result.candidates] == []


def test_without_the_table_and_without_a_store_the_name_comes_BACK(
        universe: Path, tmp_path: Path, exclusions: Path):
    """The defect itself, pinned as a fact rather than left as a memory: with
    no durable table and no store, nothing removes the name. This is what the
    test above prevents, and it is why an EMPTY table is reported as a
    finding rather than as a count of zero."""
    from vss import screen

    root = prepare(universe, tmp_path, {"SAP.DE": dislocated(),
                                        "VOLV-B.ST": dislocated()})
    run = screen.filter1(
        as_of=AS_OF, universe_dir=universe, snapshot_root=root,
        exclusions_path=exclusions,
        commodity_price_path=_commodity_list(tmp_path, ["Aluminum"]),
        runs_root=tmp_path / "runs", db_path=tmp_path / "empty.sqlite")

    assert run.commodity.hits == []
    assert [c.ticker for c in run.result.candidates] == ["VOLV-B.ST"]
    # ...and the run SAYS the limb had no input, rather than printing zero.
    assert "the durable table is EMPTY" in run.report
    assert "E96 is not being applied at all" in run.report


def test_the_filter1_report_names_where_the_strings_came_from(
        universe: Path, tmp_path: Path, exclusions: Path):
    from vss import screen

    root = prepare(universe, tmp_path, {"SAP.DE": dislocated(),
                                        "VOLV-B.ST": dislocated()})
    db = tmp_path / "durable.sqlite"
    VS.record(db, {"VOLV-B.ST": ("Industrials", "Farm & Heavy Construction Machinery")},
              observed=DAY)

    run = screen.filter1(
        as_of=AS_OF, universe_dir=universe, snapshot_root=root,
        exclusions_path=exclusions, runs_root=tmp_path / "runs", db_path=db)
    assert "THE VENDOR STRINGS THE TWO LIMBS BELOW READ" in run.report
    assert "1 ticker(s), 1 classification(s)" in run.report


# --- the nightly watcher reads the same source, the same way ---------------


def test_the_watcher_reads_the_durable_table(tmp_path: Path):
    from vss.pricewatch import industry_strings

    db = tmp_path / "durable.sqlite"
    VS.record(db, {"NHY.OL": ("Basic Materials", "Aluminum"),
                   "EXE": ("Energy", "Oil & Gas E&P")}, observed=DAY)
    strings = industry_strings(snapshot_root=tmp_path / "no-snaps", db_path=db)
    assert strings == {"NHY.OL": "Aluminum", "EXE": "Oil & Gas E&P"}


def test_the_watcher_and_step_0_agree_on_which_string_wins(tmp_path: Path):
    """One ruling, one precedence. Until 2026-09-01 `filter1` took the NEWEST
    classification (it built its map with `dict.update` oldest-first) and
    `industry_strings` took the OLDEST (`if ticker not in out`), so the two
    limbs of one ruling could disagree the moment a vendor reclassified."""
    from vss.pricewatch import industry_strings

    db = tmp_path / "durable.sqlite"
    VS.record(db, {"EXO.AS": ("Industrials", "Farm & Heavy Construction Machinery")},
              observed=DAY)
    VS.record(db, {"EXO.AS": ("Financial Services", "Asset Management")},
              observed=LATER)
    assert industry_strings(snapshot_root=tmp_path / "no-snaps",
                            db_path=db)["EXO.AS"] == "Asset Management"
    assert VS.read(db)["EXO.AS"][1] == "Asset Management"


def test_no_strings_anywhere_RAISES_rather_than_watching_everything(
        tmp_path: Path):
    """D4: with an empty map `readiness.assess` applies only the owner ticker
    lists, and E96's is empty -- so every E96 name in the top twenty would be
    watched and could fire. Returning `{}` made that indistinguishable from a
    universe containing no such name."""
    from vss.pricewatch import IndustryStringsUnavailable, industry_strings

    with pytest.raises(IndustryStringsUnavailable) as caught:
        industry_strings(snapshot_root=tmp_path / "no-snaps",
                         db_path=tmp_path / "empty.sqlite")
    assert "E96 is not being applied at all" in str(caught.value)
    assert "backfill-vendor-strings" in str(caught.value)


def test_a_fetch_records_the_strings_it_just_saw(
        universe: Path, tmp_path: Path, exclusions: Path):
    """The only moment they exist: an E51/E96 name is never a filter-1
    survivor, so it is never fetched again, so a string not kept now is a
    string lost when this store is pruned."""
    from vss import screen

    root = prepare(universe, tmp_path, {"SAP.DE": dislocated(),
                                        "VOLV-B.ST": dislocated()})
    db = tmp_path / "durable.sqlite"

    run = screen.fetch_fundamentals(
        as_of=AS_OF, universe_dir=universe, snapshot_root=root,
        exclusions_path=exclusions, reader=reader_for({}),
        sleep=lambda _: None, db_path=db)

    assert VS.read(db)["VOLV-B.ST"] == ("Technology", "Software")
    assert "VENDOR STRINGS KEPT FOR E51 / E96" in run.report
