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
    assert len(first) == 1 and first[0].startswith("UNDER MBP AAA")
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


def test_a_base_cap_lowers_every_line_and_keeps_the_struck_base():
    from vss import queue as Q
    r = Q.Row.from_dict({"ticker": "CTSH", "kind": "strike", "ccy": "USD", "base": 69.42,
                         "tier": 3, "base_cap": 55.92, "base_cap_why": "E154",
                         "bear": 47.21, "bear_cap": 36.97, "bull": 79.99, "bull_cap": 66.5})
    assert r.base == 55.92 and r.base_struck == 69.42
    assert r.bear == 36.97 and r.bull == 66.5
    assert Q.buy_line(r) == round(55.92 * 0.65, 2)
    higher = Q.Row.from_dict({"ticker": "X", "kind": "strike", "ccy": "USD", "base": 50.0,
                              "base_cap": 60.0})
    assert higher.base == 50.0 and higher.base_struck is None      # a cap never raises


def test_the_builder_drops_a_cap_once_the_name_is_struck_again():
    import sys
    from pathlib import Path
    sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))
    import build_queue as B
    assert B._doc_date("reference/CTSH-STRIKE-2026-10-28-organic.md") == "2026-10-28"
    assert B._doc_date("reference/CTSH-STRIKE-2026-11-20.md") > "2026-11-07"


def test_a_held_position_over_the_section_7_ceiling_is_said_and_a_pending_sell_reminded(tmp_path):
    from vss import queue as Q
    qp = tmp_path / "queue.yaml"
    qp.write_text(yaml.safe_dump({"portfolio_sek": 190000, "names": [
        {"ticker": "ACAD.ST", "kind": "strike", "ccy": "SEK", "base": 158.74, "status": "HELD",
         "tier": 3, "stop": 108.1, "shares": 476, "entry": 117.5},
        {"ticker": "CTSH", "kind": "strike", "ccy": "USD", "base": 55.92, "status": "HELD",
         "exit_pending": {"since": "2026-10-29", "why": "tesstopp"}}]}))
    run = lambda d: Q.run_queue(asof=d, notify=False, queue_path=qp, state_path=tmp_path / "s.json",
                                report_dir=tmp_path, price=lambda t: ("2026-11-06", 124.8),
                                reports=lambda r, a, b: [], headlines=None)
    seen, _, _ = run(date(2026, 11, 7))
    lines = [x for s in seen for x in s.lines]
    assert any(x.startswith("STORLEK ACAD.ST") and "5.2x" in x and "11,400" in x
               and "~91 aktier" in x for x in lines)
    assert any(x.startswith("SÄLJ EJ UTFÖRD CTSH: beslutad 2026-10-29 (9 dagar)") for x in lines)
    seen, _, _ = run(date(2026, 11, 8))                       # said once a week, not nightly
    assert not [x for s in seen for x in s.lines if x.startswith(("STORLEK", "SÄLJ EJ"))]
    seen, _, _ = run(date(2026, 11, 14))
    assert len([x for s in seen for x in s.lines if x.startswith(("STORLEK", "SÄLJ EJ"))]) == 2


def test_a_negative_bear_prints_as_no_less_than_zero():
    """Review 2026-11-08 L1: BKNG's bear is a flow floored at zero less net debt."""
    from vss import queue as Q
    assert Q._bear(-3.86) == "≤0" and Q._bear(0.0) == "≤0"
    assert Q._bear(36.97) == "36.97" and Q._bear(None) == "--"


def test_the_implied_return_label_is_display_only_and_meets_the_hurdle_at_base():
    """B4 (owner 2026-11-08): beside price/base the queue prints the rate at
    which the struck base case meets the price. At price == base that rate
    IS the record's hurdle; below base it is above it; a row with no record
    gets no label. Nothing on the row moves."""
    from vss import queue as Q
    acad = Q.Row(ticker="ACAD.ST", kind="strike", ccy="SEK", base=158.74,
                 source="reference/ACAD.ST-STRIKE-2026-10-27-goodwill.md")
    before = dict(acad.__dict__)
    assert "du kräver 9,5 %" in Q.implied_label(acad, 158.74)
    assert "priset ger ~9,5 %" in Q.implied_label(acad, 158.74)
    assert "priset ger ~13," in Q.implied_label(acad, 79.37)
    assert acad.__dict__ == before
    bare = Q.Row(ticker="X", kind="machine", ccy="USD", base=10.0)
    assert Q.implied_label(bare, 5.0) == ""


def test_an_owner_override_of_e157_prints_beside_the_size_line():
    """Owner 2026-11-08: ACAD.ST kept above E157 -- the line still prints,
    with the override written beside it and no sell order."""
    from vss import queue as Q
    r = Q.Row(ticker="X.ST", kind="strike", ccy="SEK", base=100.0, status="HELD",
              shares=486, override={"rule": "owner", "overrides": "E157",
                                    "reason": "ägarens val", "standing": "EXPIRY",
                                    "expires": "vid nästa rapport"})
    line = Q.ceiling_line(r, 124.80, 248_476)
    assert "~119 aktier" in line and "ÄGARENS UNDANTAG" in line and "ingen säljorder" in line
    plain = Q.ceiling_line(Q.Row(ticker="X.ST", kind="strike", ccy="SEK", base=100.0,
                                 status="HELD", shares=486), 124.80, 248_476)
    assert "UNDANTAG" not in plain


def test_a_data_error_correction_binds_both_ways():
    """E166 / E152(1): a corrected data error is fixed at once in either
    direction -- GDDY's value rose 79.99 -> 92.72."""
    up = Q.Row.from_dict({"ticker": "GDDY", "kind": "strike", "ccy": "USD", "base": 79.99,
                          "bear": 27.9, "bull": 132.86, "base_cap": 92.72, "bear_cap": 34.42,
                          "bull_cap": 151.9, "cap_binds_both_ways": True})
    assert up.base == 92.72 and up.base_struck == 79.99
    assert up.bear == 34.42 and up.bull == 151.9


def test_a_correction_is_said_once_in_the_message(tmp_path):
    row = dict(NO_TIER, ticker="NVR", base=7193.71,
               correction={"since": "2026-11-08", "text": "TITTA ÅTERKALLAD"})
    _, sent, text = _run(tmp_path, [row], {"NVR": 6298.29})
    assert "RÄTTELSE NVR: TITTA ÅTERKALLAD" in sent
    _, sent2, _ = _run(tmp_path, [row], {"NVR": 6298.29}, asof=date(2026, 11, 6))
    assert not any(l.startswith("RÄTTELSE") for l in sent2)


def test_a_value_the_watchlist_marks_void_is_never_read(tmp_path):
    """Review 3, L1: SAP.DE's fv_base 140.37 rests on nothing that stands;
    the queue prints no base, no buy line and no zone from it."""
    row = dict(STRIKE_T3, ticker="SAP.DE", base=140.37, bear=121.04, bull=175.42)
    sent: list = []
    seen, text, _ = Q.run_queue(
        asof=date(2026, 11, 5), queue_path=_queue(tmp_path, [row]),
        state_path=tmp_path / "s.json", report_dir=tmp_path,
        price=lambda t: ("2026-11-04", 100.0), reports=lambda r, s, u: [],
        headlines=None, poster=lambda lines, title=None: sent.append(list(lines)) or "ok",
        voids={"SAP.DE": "pre-E117 strike"})
    s = seen[0]
    assert s.zone == "void" and s.row.base is None
    assert Q.buy_line(s.row) is None and Q.look_line(s.row) is None
    assert "119.31" not in text and "ogiltigt värde: pre-E117 strike" in text
    assert not sent[-1]                                   # price under the old line: no UNDER MBP


def test_the_committed_watchlist_voids_sap():
    assert "SAP.DE" in Q._voids()


def test_hrb_bear_under_zero_stops_the_name(tmp_path):
    """B6 (2026-11-08): HRB's bear -4.65 is a broken value, not a valuation."""
    from vss.valuation import absurd_cases
    assert absurd_cases(-4.65, 68.38).startswith("ABSURD: bear -4.65")
    assert absurd_cases(70.0, 68.38).startswith("ABSURD: bear 70.00 is above base")
    assert absurd_cases(35.82, 72.74) is None
    row = dict(NO_TIER, ticker="HRB", base=68.38, bear=-4.65, bull=96.54, status="WATCH-PRICED")
    seen, sent, text = _run(tmp_path, [row], {"HRB": 52.69})
    assert seen[0].zone == "absurd" and not sent
    assert "stoppad: ABSURD" in text


def test_a_held_name_keeps_its_sell_line_whatever_its_bear():
    """The stop never takes an owned position's sell line away."""
    r = Q.Row.from_dict({"ticker": "X", "kind": "strike", "ccy": "USD", "base": 50.0,
                         "bear": -1.0, "bull": 60.0, "status": "HELD"})
    assert Q.zone(r, 61.0) == "sell:bull"


def test_bear_missing_draws_no_line(tmp_path):
    row = dict(NO_TIER, ticker="NVR", base=7193.71, bear=4783.1,
               bear_missing="deklarerad cyklisk utan nedgång")
    seen, sent, text = _run(tmp_path, [row], {"NVR": 5000.0})
    assert seen[0].zone == "bear-missing" and seen[0].row.bear is None
    assert Q.look_line(seen[0].row) is None and not sent


def test_implied_growth_solves_the_base_case_and_sensitivity_brackets_it():
    """B9: the g the price implies reproduces the price; g -/+ 1.5 pp
    brackets the base at g."""
    import json
    from vss import runrecord as RR, strike as ST
    rec = RR.RunRecord.from_dict(json.load(open("reference/run-records/ACAD.ST-2026-10-27-goodwill.json")))
    g = ST.implied_growth(rec, 124.80)
    assert abs(rec._strike_unchecked(g, case="base") - 124.80) < 0.01
    sv = ST.sensitivity(rec, 124.80, 0.045)
    assert sv["fv_minus"] < sv["fv_g"] < sv["fv_plus"]
    assert round(sv["fv_registered"], 2) == 136.87 and round(sv["fv_g"], 2) == 158.74


def test_the_table_says_what_growth_the_price_implies_not_price_over_base(tmp_path):
    row = dict(STRIKE_T3, ticker="ACAD.ST", base=158.74, bear=110.63, bull=181.95,
               source="reference/ACAD.ST-STRIKE-2026-10-27-goodwill.md")
    _, _, text = _run(tmp_path, [row], {"ACAD.ST": 124.80})
    assert "Kurs/base" not in text and "kursen implicerar" in text and "kravet är 9,5 %" in text


def test_a_failed_report_check_is_said_once_and_its_window_is_searched_again(tmp_path):
    """Granskning 2026-11-09 (2.5): a check that fails must not move the
    name's window forward, and the failure is said, once."""
    asked: list[date] = []
    answers = iter([["(report check failed: AttributeError)"],
                    ["(report check failed: AttributeError)"],
                    ["2026-11-05 10-Q"]])

    def reports(r, since, until):
        asked.append(since)
        return next(answers)

    sent: list[list[str]] = []
    qp = _queue(tmp_path, [STRIKE_T3])
    for d in (date(2026, 11, 5), date(2026, 11, 6), date(2026, 11, 7)):
        Q.run_queue(asof=d, queue_path=qp, state_path=tmp_path / "s.json", report_dir=tmp_path,
                    price=lambda t: ("2026-11-04", 120.0), reports=reports, headlines=None,
                    poster=lambda lines, title=None: sent.append(list(lines)) or "ok")
    assert asked[1] == asked[2] == asked[0]          # the failed nights did not move it
    assert len([ln for ln in sent[0] if ln.startswith("RAPPORTKONTROLL FELADE AAA")]) == 1
    assert sent[1] == []                              # the same failure is not repeated
    assert sent[2] == ["RAPPORT AAA: 2026-11-05 10-Q"]
