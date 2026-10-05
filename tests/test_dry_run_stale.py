"""A dry run refuses on a close more than one trading day old (owner,
2026-09-19). Found when yfinance dropped the 2026-09-17/18 rows for every
continental European name and SAP.DE and LIAB.ST (HELD) were served their
2026-09-16 close as "live"."""
from datetime import date, datetime
from types import SimpleNamespace

from vss import rules as R
from vss.runner import EXIT_STALE_DRY_RUN, stale_for_dry_run


def _row(ticker, close_date, as_of, *, status="HELD", stop=112.0, fv=68.97,
         tier=2, close=123.40, holidays=frozenset()):
    """A row carrying the REAL assessment, as build_row makes it."""
    a = R.assess(ticker=ticker, status=status, last_close=close if close_date else None,
                 last_close_date=close_date, drawdown=0.1, fv_base=fv, tier=tier,
                 stop_price=stop, catalyst_date=None, catalyst_resolved=None,
                 catalyst_event=None, as_of=as_of, holidays=holidays)
    return SimpleNamespace(entry=SimpleNamespace(ticker=ticker, status=status,
                                                 stop_price=stop),
                           assessment=a, source="live", closed_days=holidays,
                           retained=None,
                           metrics=SimpleNamespace(last_close_date=close_date,
                                                   last_close=close if close_date else None))


def test_the_limit_is_one_trading_day():
    assert R.MAX_CLOSE_AGE_TRADING_DAYS_LEVEL == 1
    assert EXIT_STALE_DRY_RUN not in (0, 1, 2)


def test_the_2026_09_19_case_refuses():
    # Saturday run; newest close Wednesday 09-16 -> Thu, Fri = 2 sessions.
    out = stale_for_dry_run([_row("LIAB.ST", date(2026, 9, 16), date(2026, 9, 19))],
                            date(2026, 9, 19))
    assert len(out) == 1 and "LIAB.ST" in out[0] and "2026-09-16" in out[0]
    assert "123.40" in out[0] and "LEVEL NOT CHECKED" in out[0]


def test_friday_close_on_a_weekend_or_monday_passes():
    for as_of in (date(2026, 9, 19), date(2026, 9, 21)):
        assert stale_for_dry_run([_row("GDDY", date(2026, 9, 18), as_of)], as_of) == []


def test_friday_close_on_tuesday_refuses():
    as_of = date(2026, 9, 22)
    assert stale_for_dry_run([_row("GDDY", date(2026, 9, 18), as_of)], as_of)


def test_no_close_at_all_refuses():
    as_of = date(2026, 9, 19)
    assert stale_for_dry_run([_row("X", None, as_of)], as_of)


# --- the nightly gate: ONE session for a name carrying a level -------------

def _assess(**kw):
    base = dict(ticker="LIAB.ST", status="HELD", last_close=123.40,
                last_close_date=date(2026, 9, 16), drawdown=0.1, fv_base=68.97,
                tier=2, stop_price=112.0, catalyst_date=None,
                catalyst_resolved=None, catalyst_event=None,
                as_of=date(2026, 9, 18))
    base.update(kw)
    return R.assess(**base)


def test_a_held_name_two_sessions_stale_is_blocked_and_says_so():
    a = _assess()
    assert a.blocked and not a.verdicts
    reason = " ".join(b.reason for b in a.blockers)
    assert "123.40" in reason and "2026-09-16" in reason and "2 trading days" in reason
    assert "LEVEL NOT CHECKED" in reason and "stop 112.00" in reason and "MBP" in reason


def test_a_name_with_no_level_keeps_three_sessions():
    a = _assess(ticker="X", status="DROPPED", fv_base=None, tier=None, stop_price=None)
    assert not any(b.code == R.STALE_DATA for b in a.blockers)


def test_a_name_with_only_an_mbp_is_held_to_one_session():
    a = _assess(ticker="SAP.DE", status="WATCH-PRICED", stop_price=None)
    assert any(b.code == R.STALE_DATA for b in a.blockers)


def test_the_dry_run_refusal_ignores_a_name_with_no_level():
    as_of = date(2026, 9, 19)
    row = _row("NOVO-B.CO", date(2026, 9, 10), as_of, status="DROPPED",
               stop=None, fv=None, tier=None)
    assert stale_for_dry_run([row], as_of) == []


# --- the exchange calendar: no block for a session that never was ----------

def test_easter_monday_does_not_block_a_stockholm_name():
    from vss.calendars import load_market_calendars
    cal = load_market_calendars()
    last, as_of = date(2026, 4, 2), date(2026, 4, 6)      # Thu close, Easter Monday
    closed = cal.closed_weekdays(cal.market_of_ticker("LIAB.ST"), last, as_of)
    assert closed == {date(2026, 4, 3), date(2026, 4, 6)}
    assert not _row("LIAB.ST", last, as_of, holidays=closed).assessment.blocked
    # ... and without the calendar it would have been blocked
    assert _row("LIAB.ST", last, as_of).assessment.blocked


def test_an_unmapped_suffix_is_counted_naively_and_says_so():
    as_of = date(2026, 9, 22)
    a = _row("X.ZZ", date(2026, 9, 18), as_of, holidays=None).assessment
    assert "no exchange calendar" in " ".join(b.reason for b in a.blockers)


# --- the push ---------------------------------------------------------------

def test_the_push_lists_every_blocked_name_with_a_level_and_nothing_else():
    from vss.runner import block_push_lines
    as_of = date(2026, 9, 22)
    rows = [_row("LIAB.ST", date(2026, 9, 16), as_of),
            _row("SAP.DE", date(2026, 9, 16), as_of, status="WATCH-PRICED", stop=None,
                 fv=140.3746376700501, tier=1, close=186.56),
            _row("NOVO-B.CO", date(2026, 9, 10), as_of, status="DROPPED",
                 stop=None, fv=None, tier=None),
            _row("GDDY", date(2026, 9, 21), as_of, status="WATCH-PRICED", stop=None,
                 fv=129.03, tier=3, close=97.46)]
    lines = block_push_lines(rows, as_of)
    assert [l.split(":")[0] for l in lines] == ["LIAB.ST", "SAP.DE"]
    assert "123.40 on 2026-09-16, 4 session(s) old" in lines[0]
    assert "stop 112.00" in lines[0] and "NOT CHECKED" in lines[0]
    # THE UNROUNDED record replay, which is what the live row uses:
    # 140.3746376700501 x 0.85 = 119.3184 -> 119.32.
    assert "MBP 119.32" in lines[1]
    # ... and the negative: a level computed from the DISPLAYED 140.37 would
    # be 119.31, and must never appear (owner, 2026-09-20 -- asserting the
    # wrong-but-consistent answer is worse than no test).
    assert "119.31" not in lines[1]


def test_a_push_that_did_not_go_is_reported_next_night(tmp_path):
    from datetime import datetime
    from vss.runner import read_previous_push, unsent_nights, write_push_record
    p = tmp_path / "push.json"
    assert unsent_nights(read_previous_push(p)) == []
    write_push_record(as_of=date(2026, 9, 21), run_ts=datetime(2026, 9, 21, 22, 30),
                      lines=["LIAB.ST: ..."], outcome="NOT SENT: URLError: down", path=p)
    nights = unsent_nights(read_previous_push(p))
    assert len(nights) == 1 and nights[0]["lines"] == ["LIAB.ST: ..."]
    # an unset topic is a push that did not go
    rec = read_previous_push(p)
    write_push_record(as_of=date(2026, 9, 22), run_ts=datetime(2026, 9, 22, 22, 30),
                      lines=["x"], outcome="not sent: NTFY_TOPIC is not set",
                      path=p, previous=rec)
    assert len(unsent_nights(read_previous_push(p))) == 2


def test_three_consecutive_failures_keep_every_night_then_one_send_clears_them(tmp_path):
    """Owner, 2026-09-20: if night 1's names vanish once night 2 also fails,
    that is the same silent loss as a close seen and then overwritten."""
    from datetime import datetime
    from vss.runner import read_previous_push, unsent_nights, write_push_record
    p = tmp_path / "push.json"
    for day in (21, 22, 23):
        write_push_record(as_of=date(2026, 9, day),
                          run_ts=datetime(2026, 9, day, 22, 30),
                          lines=[f"LIAB.ST: night {day - 20} ..."],
                          outcome="NOT SENT: URLError: down", path=p,
                          previous=read_previous_push(p))
    nights = unsent_nights(read_previous_push(p))
    assert [n["as_of"] for n in nights] == ["2026-09-21", "2026-09-22", "2026-09-23"]
    assert "night 1" in nights[0]["lines"][0]        # the FIRST night survived
    # a re-run of the same night replaces that night, never doubles it
    write_push_record(as_of=date(2026, 9, 23), run_ts=datetime(2026, 9, 23, 23, 0),
                      lines=["LIAB.ST: night 3 ..."], outcome="NOT SENT: again",
                      path=p, previous=read_previous_push(p))
    assert len(unsent_nights(read_previous_push(p))) == 3
    # and one that sends clears the whole backlog
    write_push_record(as_of=date(2026, 9, 24), run_ts=datetime(2026, 9, 24, 22, 30),
                      lines=["LIAB.ST: night 4 ..."], outcome="sent 1 line(s) (HTTP 200)",
                      path=p, previous=read_previous_push(p))
    assert unsent_nights(read_previous_push(p)) == []


def test_a_night_with_nothing_to_send_leaves_the_backlog_alone(tmp_path):
    from datetime import datetime
    from vss.runner import read_previous_push, unsent_nights, write_push_record
    p = tmp_path / "push.json"
    write_push_record(as_of=date(2026, 9, 21), run_ts=datetime(2026, 9, 21, 22, 30),
                      lines=["LIAB.ST: ..."], outcome="NOT SENT: down", path=p)
    write_push_record(as_of=date(2026, 9, 22), run_ts=datetime(2026, 9, 22, 22, 30),
                      lines=[], outcome="nothing to send", path=p,
                      previous=read_previous_push(p))
    assert len(unsent_nights(read_previous_push(p))) == 1


def test_a_level_is_never_computed_from_the_rounded_display_figure():
    """The stored fv_base is a 2dp DISPLAY figure; the MBP stands on the
    record's unrounded replay (E90). 140.3746376700501 x 0.85 = 119.32;
    140.37 x 0.85 = 119.31, and that figure must never reach a level."""
    from vss import rules as R
    assert R.compute_mbp_e90(140.3746376700501, 1) == 119.32
    assert R.compute_mbp_e90(140.37, 1) == 119.31          # the wrong path
    assert R.compute_mbp_e90(140.3746376700501, 1) != R.compute_mbp_e90(140.37, 1)


def test_the_night_count_is_consecutive_and_a_rerun_does_not_advance_it():
    from vss.runner import block_push_lines, block_streaks
    as_of = date(2026, 9, 22)
    rows = [_row("LIAB.ST", date(2026, 9, 16), as_of)]
    first = block_streaks(rows, None, as_of)
    assert first == {"LIAB.ST|STALE_DATA": 1}
    rerun = block_streaks(rows, {"as_of": as_of.isoformat(), "streaks": first}, as_of)
    assert rerun == first                                   # same night, same count
    nextnight = block_streaks(rows, {"as_of": "2026-09-21", "streaks": first},
                              date(2026, 9, 22))
    assert nextnight == {"LIAB.ST|STALE_DATA": 2}
    assert "night 2" in block_push_lines(rows, as_of, nextnight)[0]
    # a code that did not block tonight is dropped: the count is CONSECUTIVE
    assert block_streaks([], {"as_of": "2026-09-21", "streaks": nextnight},
                         date(2026, 9, 22)) == {}


def test_prepare_reports_a_blocker_instead_of_swallowing_it(tmp_path):
    """`vss prepare` read `b.detail` on a Blocker, which has `code` and
    `reason` -- inside a try that only NOTES the exception, so a review
    session on a blocked name silently lost its price section and every
    blocker check (found 2026-09-20 by grepping after the overview crash)."""
    import pandas as pd
    from vss import prepare as P
    from vss.config import WatchlistEntry

    cache = tmp_path / "cache"
    cache.mkdir()
    days = pd.date_range("2026-08-03", "2026-09-16", freq="B", tz="Europe/Stockholm")
    frame = pd.DataFrame({"Open": 120.0, "High": 125.0, "Low": 119.0,
                          "Close": 123.40, "Volume": 1000}, index=days)
    frame.index.name = "Date"
    frame.to_csv(cache / "LIAB.ST.csv")
    (cache / "LIAB.ST.meta.json").write_text(
        '{"ticker": "LIAB.ST", "fetched_at": "2026-09-16T22:30:00+02:00",'
        ' "rows": 1, "period": "6y", "auto_adjust": false}')

    entry = WatchlistEntry(ticker="LIAB.ST", name="Lindab", currency="SEK",
                           status="HELD", stop_price=112.0)
    out = P.Prepared(ticker="LIAB.ST", name="Lindab", status="HELD",
                     as_of="2026-09-21", dry_run=True)
    P.step_compute(entry, out, manual_dir=tmp_path, cache_dir=cache,
                   now=datetime(2026, 9, 21, 22, 30), as_of=date(2026, 9, 21))
    blockers = [c for c in out.checks if c.name.startswith("blocker ")]
    assert any("STALE_DATA" in c.name for c in blockers), out.steps[-1].notes
    assert any("123.40" in (c.detail or "") for c in blockers)
    assert out.context.get("price", {}).get("last_close") == 123.40


# --- E121(c): an unsuffixed ticker must be a US listing ---------------------

def test_an_unsuffixed_ticker_quoted_in_anything_but_usd_is_refused(tmp_path):
    """E121(c): the calendar for a suffixless ticker is the NYSE's, which
    rests on the vendor's convention. The convention is checked, not assumed."""
    import pytest
    from vss.config import ConfigError, load_watchlist
    p = tmp_path / "w.yaml"
    p.write_text("tickers:\n  - ticker: LIAB\n    name: Lindab\n"
                 "    currency: SEK\n    status: PIPELINE\n")
    with pytest.raises(ConfigError) as exc:
        load_watchlist(p)
    assert "E121(c)" in str(exc.value) and "NYSE" in str(exc.value)
    # the same name WITH its suffix loads
    p.write_text("tickers:\n  - ticker: LIAB.ST\n    name: Lindab\n"
                 "    currency: SEK\n    status: PIPELINE\n")
    assert load_watchlist(p)[0].ticker == "LIAB.ST"
