"""The build tool that fetches the rates OF A NAMED DATE.

``vss.fx.default_lookup`` asks for five days and takes the LAST close,
whatever ``--asof`` says. SEKUSD=X and NOKUSD=X carry a weekend row and
EURUSD=X does not, so the 2026-08-21 run recorded ten pairs at 08-21 and two
at 08-22. Replaying that manifest reproduces the defect faithfully, which is
why a tool that can build a clean one exists.

The rule under test is the refusal: a pair with no row on the requested date
FAILS and is named, and is never filled from the session next door.
"""

from __future__ import annotations

import importlib.util
import json
from datetime import date
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
_spec = importlib.util.spec_from_file_location(
    "fetch_fx_manifest", ROOT / "tools" / "fetch_fx_manifest.py")
tool = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(tool)

ASOF = date(2026, 8, 21)

#: The real shape of the fault: two pairs carry a weekend row, one does not.
SERIES = {
    "SEKUSD=X": [(date(2026, 8, 20), 0.105924), (ASOF, 0.105542),
                 (date(2026, 8, 23), 0.105789)],
    "EURUSD=X": [(date(2026, 8, 20), 1.167379), (ASOF, 1.167815)],
    "XXXYYY=X": [(date(2026, 8, 20), 2.0), (date(2026, 8, 24), 2.5)],
}


def reader(symbol, start, end):
    return [row for row in SERIES.get(symbol, []) if start <= row[0] < end]


def test_the_weekend_row_is_not_what_gets_recorded():
    """The whole fault, in one assertion: the LAST close is 08-23's."""
    value, symbol = tool.fetch_on("SEK", "USD", ASOF, reader=reader)
    assert (value, symbol) == (0.105542, "SEKUSD=X")
    assert reader("SEKUSD=X", date(2026, 8, 11), date(2026, 8, 24))[-1][1] == 0.105789, \
        "the fixture lost the point: the last row must still be the weekend one"


def test_a_pair_with_no_row_on_the_date_fails_and_says_what_it_saw():
    with pytest.raises(RuntimeError) as caught:
        tool.fetch_on("XXX", "YYY", ASOF, reader=reader)
    said = str(caught.value)
    assert "no close dated 2026-08-21" in said
    assert "2026-08-20" in said, "the window it did see is not named"
    assert "NOT filled from a neighbouring session" in said


def test_a_pair_the_feed_does_not_know_fails_rather_than_returning_something():
    with pytest.raises(RuntimeError):
        tool.fetch_on("AAA", "BBB", ASOF, reader=reader)


def test_the_pair_list_comes_from_a_stored_manifest_and_nowhere_else(tmp_path):
    manifest = tmp_path / "m.json"
    manifest.write_text(json.dumps({"fx": {"SEK->USD": {}, "EUR->USD": {}}}),
                        encoding="utf-8")
    assert tool.pairs_from_manifest(manifest) == [("EUR", "USD"), ("SEK", "USD")]


def test_the_written_manifest_replays_through_the_real_reader(tmp_path, monkeypatch):
    """It is only useful if ``vss.fx`` can read it back, so read it back."""
    from vss.fx import read_manifest_rates

    monkeypatch.setattr(tool, "default_reader", reader)
    like = tmp_path / "like.json"
    like.write_text(json.dumps({"fx": {"SEK->USD": {}, "EUR->USD": {}}}), encoding="utf-8")
    out = tmp_path / "out.json"
    assert tool.main(["--asof", ASOF.isoformat(), "--like", str(like),
                      "--out", str(out)]) == 0

    rates = read_manifest_rates(out)
    assert set(rates) == {"SEK->USD", "EUR->USD"}
    assert all(rate.as_of == ASOF for rate in rates.values())
    assert rates["SEK->USD"].value == pytest.approx(0.105542)


def test_a_failed_pair_is_named_in_the_file_and_the_exit_code_says_so(tmp_path, monkeypatch):
    monkeypatch.setattr(tool, "default_reader", reader)
    like = tmp_path / "like.json"
    like.write_text(json.dumps({"fx": {"XXX->YYY": {}, "EUR->USD": {}}}), encoding="utf-8")
    out = tmp_path / "out.json"
    assert tool.main(["--asof", ASOF.isoformat(), "--like", str(like),
                      "--out", str(out)]) == 2
    document = json.loads(out.read_text(encoding="utf-8"))
    assert list(document["fx"]) == ["EUR->USD"]
    assert "XXX->YYY" in document["fx_failed"]
    assert document["fx_rate_dates"] == [ASOF.isoformat()]
