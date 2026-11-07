"""`vss queue`: the lines, the zones, and the rule that a change is said once."""
from __future__ import annotations

from datetime import date

import yaml

from vss import queue as Q


def _queue(tmp_path, rows):
    p = tmp_path / "queue.yaml"
    p.write_text(yaml.safe_dump({"names": rows}))
    return p


def _run(tmp_path, rows, prices, *, asof=date(2026, 11, 5), reports=None):
    sent: list[list[str]] = []
    seen, text, _ = Q.run_queue(
        asof=asof, queue_path=_queue(tmp_path, rows),
        state_path=tmp_path / "state.json", report_dir=tmp_path,
        price=lambda t: ("2026-11-04", prices.get(t)),
        reports=lambda r, s, u: (reports or {}).get(r.ticker, []),
        headlines=None, poster=lambda lines, title=None: sent.append(list(lines)) or "ok")
    return seen, sent[-1], text


STRIKE_T3 = {"ticker": "AAA", "kind": "strike", "ccy": "USD", "base": 100.0, "tier": 3,
             "status": "WATCH-PRICED"}
NO_TIER = {"ticker": "BBB", "kind": "strike", "ccy": "USD", "base": 100.0, "status": "PIPELINE"}
ROUGH = {"ticker": "CCC", "kind": "rough", "ccy": "SEK", "base": 100.0, "status": "OFF-WATCHLIST"}


def test_buy_line_is_base_times_tier_cushion():
    r = Q.Row.from_dict(STRIKE_T3)
    assert Q.buy_line(r) == 65.0 and Q.look_line(r) is None


def test_look_line_without_tier_is_wider_for_a_rough_value():
    assert Q.look_line(Q.Row.from_dict(NO_TIER)) == 85.0
    assert Q.look_line(Q.Row.from_dict(ROUGH)) == 75.0
    assert Q.buy_line(Q.Row.from_dict(ROUGH)) is None


def test_a_zone_is_said_once_not_every_night(tmp_path):
    _, first, _ = _run(tmp_path, [STRIKE_T3], {"AAA": 60.0})
    assert len(first) == 1 and first[0].startswith("KÖPLINJE AAA")
    _, second, _ = _run(tmp_path, [STRIKE_T3], {"AAA": 59.0}, asof=date(2026, 11, 6))
    assert second == []


def test_leaving_and_reentering_a_zone_is_said_again(tmp_path):
    _run(tmp_path, [NO_TIER], {"BBB": 80.0})
    _run(tmp_path, [NO_TIER], {"BBB": 90.0}, asof=date(2026, 11, 6))
    _, again, _ = _run(tmp_path, [NO_TIER], {"BBB": 84.0}, asof=date(2026, 11, 7))
    assert len(again) == 1 and again[0].startswith("TITTA BBB")


def test_a_dropped_name_gets_no_price_line_but_its_report_is_said(tmp_path):
    row = dict(NO_TIER, ticker="DDD", status="DROPPED")
    seen, sent, _ = _run(tmp_path, [row], {"DDD": 10.0},
                         reports={"DDD": ["2026-11-04 10-Q"]})
    assert seen[0].zone == "dropped"
    assert sent == ["RAPPORT DDD: 2026-11-04 10-Q"]


def test_a_gated_name_in_its_zone_is_not_sent_until_the_gate_lifts(tmp_path):
    row = dict(NO_TIER, ticker="GGG", status="WATCH-GATED", gate_until="2026-11-10",
               gate_event="Q3 report")
    seen, sent, text = _run(tmp_path, [row], {"GGG": 70.0})
    assert seen[0].zone == "look" and sent == []
    assert "GGG" in text                     # shown in the report all the same
    _, lifted, _ = _run(tmp_path, [row], {"GGG": 70.0}, asof=date(2026, 11, 10))
    assert any(x.startswith("SPÄRR GGG") for x in lifted)
    _, after, _ = _run(tmp_path, [row], {"GGG": 70.0}, asof=date(2026, 11, 11))
    assert after == []                       # the gate is told once


def test_a_held_name_sells_at_its_hand_line_and_at_bull(tmp_path):
    row = {"ticker": "HHH", "kind": "strike", "ccy": "SEK", "base": 158.74, "bull": 181.95,
           "tier": 3, "status": "HELD",
           "sell_at": [{"price": 150, "action": "halve the position"}]}
    _, sent, _ = _run(tmp_path, [row], {"HHH": 151.0})
    assert sent == ["SÄLJ HHH 151.00 >= 150: halve the position"]
    _, bull, _ = _run(tmp_path, [row], {"HHH": 183.0}, asof=date(2026, 11, 6))
    assert bull and bull[0].startswith("SÄLJ HHH 183.00 >= bull")


def test_a_report_line_is_said_once(tmp_path):
    rep = {"AAA": ["2026-11-04 8-K item 2.02 (results)"]}
    _, first, _ = _run(tmp_path, [STRIKE_T3], {"AAA": 90.0}, reports=rep)
    _, second, _ = _run(tmp_path, [STRIKE_T3], {"AAA": 90.0}, reports=rep,
                        asof=date(2026, 11, 6))
    assert first == ["RAPPORT AAA: 2026-11-04 8-K item 2.02 (results)"] and second == []


def test_no_price_is_no_zone_and_no_alert(tmp_path):
    seen, sent, _ = _run(tmp_path, [STRIKE_T3], {})
    assert seen[0].zone == "no-price" and sent == []


def test_the_queue_file_parses_and_every_row_has_a_base():
    rows = Q.load_queue()
    assert len(rows) >= 50
    for r in rows:
        assert r.base is not None and r.kind in ("strike", "machine", "rough"), r.ticker
    gbx = [r for r in rows if r.ccy == "GBX"]
    assert gbx and all(r.base > 100 for r in gbx)     # pence, never pounds


def test_a_hand_look_at_replaces_the_cushion_line(tmp_path):
    row = dict(NO_TIER, ticker="DDH", look_at=142.61, base=184.54)
    assert Q.look_line(Q.Row.from_dict(row)) == 142.61
    seen, sent, _ = _run(tmp_path, [row], {"DDH": 152.28})
    assert seen[0].zone == "above" and sent == []
