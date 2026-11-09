"""vss/outlook.py: a report is news only when it changes the outcome."""
from datetime import date

from vss import outlook as O


def _reader(*readings):
    it = iter(readings)
    return lambda t: next(it)


def test_the_first_reading_is_the_baseline_and_sends_nothing():
    st = {}
    a, n = O.check("X", asof=date(2026, 11, 9), new_reports=[], headlines=[], state=st,
                   read=_reader({"period": "2026-09-30", "base": 50.0}))
    assert a == [] and "första avläsning" in n[0] and st["X"]["base"] == 50.0


def test_a_new_quarter_that_moves_the_value_10_pct_is_sent_and_a_smaller_one_is_not():
    st = {"X": {"base": 100.0, "period": "2026-06-30"}}
    a, _ = O.check("X", asof=date(2026, 11, 9), new_reports=["2026-11-08 10-Q"], headlines=[],
                   state=st, read=_reader({"period": "2026-09-30", "base": 112.0}))
    assert len(a) == 1 and "+12%" in a[0]
    st = {"X": {"base": 100.0, "period": "2026-06-30"}}
    a, n = O.check("X", asof=date(2026, 11, 9), new_reports=["2026-11-08 10-Q"], headlines=[],
                   state=st, read=_reader({"period": "2026-09-30", "base": 104.0}))
    assert a == [] and n[0].startswith("läst: inget ändrat")


def test_a_report_the_vendor_has_not_filed_yet_waits_and_is_read_again():
    st = {"X": {"base": 100.0, "period": "2026-06-30"}}
    O.check("X", asof=date(2026, 11, 9), new_reports=["2026-11-08 10-Q"], headlines=[],
            state=st, read=_reader({"period": "2026-06-30", "base": 100.0}))
    assert st["X"]["pending_since"] == "2026-11-09"
    a, _ = O.check("X", asof=date(2026, 11, 12), new_reports=[], headlines=[],
                   state=st, read=_reader({"period": "2026-09-30", "base": 70.0}))
    assert a and "-30%" in a[0] and "pending_since" not in st["X"]


def test_an_outlook_headline_is_sent_once_and_an_ordinary_one_never():
    st = {"X": {"base": 1.0, "period": "2026-09-30"}}
    hl = ["2026-11-09 Acme lowers its guidance for 2026", "2026-11-09 Acme opens a store in Oslo",
          "2026-11-09 Bolaget sänker sin prognos", "2026-11-09 Acme CEO steps down"]
    a, _ = O.check("X", asof=date(2026, 11, 9), new_reports=[], headlines=hl, state=st, read=_reader())
    assert len(a) == 3 and not any("Oslo" in x for x in a)
    a2, _ = O.check("X", asof=date(2026, 11, 10), new_reports=[], headlines=hl, state=st, read=_reader())
    assert a2 == []


def test_a_machine_reading_with_a_failed_42_rule_is_an_outlook_change(tmp_path):
    (tmp_path / "2026-11-09-X-0001.md").write_text(
        "# vss earnings\n\n## 4.2 FAILS VALIDATION - VERIFY AGAINST SOURCE\n\n"
        "- **4.2.3** 2+ guidance cuts within trailing 4 quarters: FAILED\n\n## OTHER\n")
    (tmp_path / "2026-11-09-Y-0002.md").write_text(
        "## 4.2 FAILS VALIDATION\n\nNo 4.2 rule failed on the figures extracted.\n\n## X\n")
    assert O.autoread_flags("X", date(2026, 11, 8), tmp_path)
    assert O.autoread_flags("Y", date(2026, 11, 8), tmp_path) == []


def test_a_new_report_is_handed_to_the_reader_once_and_its_alert_is_read(tmp_path):
    calls = []

    def reader(t, name="", ccy=""):
        calls.append(t)
        (tmp_path / "2026-11-09-X-77.md").write_text(
            "## 4.2 FAILS VALIDATION\n\n- **4.2.1** revenue down four quarters: FAILED\n\n## END\n")
        return "läst"
    st = {"X": {"base": 1.0, "period": "2026-09-30"}}
    a, n = O.check("X", asof=date(2026, 11, 9), new_reports=["2026-11-09 Q3"], headlines=[], state=st,
                   read=_reader({"period": "2026-09-30", "base": 1.0}), autoread_root=tmp_path,
                   report_reader=reader)
    assert calls == ["X"] and "rapporten: läst" in n[0]
    assert any("4.2 slår till" in x for x in a)
    a2, _ = O.check("X", asof=date(2026, 11, 10), new_reports=[], headlines=[], state=st,
                    read=_reader({"period": "2026-09-30", "base": 1.0}), autoread_root=tmp_path,
                    report_reader=reader)
    assert calls == ["X"] and a2 == []
