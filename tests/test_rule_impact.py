"""tools/rule_impact.py (review 2026-11-08 H1, E155): every name, both directions."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))
import rule_impact as RI  # noqa: E402


def test_the_diff_counts_both_directions_and_names_every_mover():
    before = {"A": {"base": 100.0, "tests": {"Q2": False}},
              "B": {"base": 50.0, "tests": {"Q2": True}},
              "C": {"base": 10.0, "tests": {"Q2": True}}}
    after = {"A": {"base": 100.0, "tests": {"Q2": True}},
             "B": {"base": 45.0, "tests": {"Q2": False}},
             "C": {"base": 10.000001, "tests": {"Q2": True}}}
    head, *lines = RI.diff(before, after)
    assert head == ("3 names: base 0 up, 1 down, 2 unchanged; "
                    "tests 1 newly passing, 1 newly failing")
    assert lines == ["- A: Q2 False -> True", "- B: base 50.00 -> 45.00 (-10.0%); Q2 True -> False"]


def test_a_new_strike_flag_is_switched_on_in_the_replay():
    import json
    from vss.runrecord import RunRecord
    raw = json.loads((Path(__file__).resolve().parents[1]
                      / "reference/run-records/CTSH-2026-10-28-organic.json").read_text())
    rec = RI.as_new_strike(RunRecord.from_dict(raw))
    assert rec.e140.e154 and rec.e140.e154_1
    assert abs(rec.strike() - 58.03) < 0.01
