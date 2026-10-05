"""Report rendering: a partial run must never read like a full one."""

from dataclasses import dataclass
from datetime import date, datetime

import pytest

from vss import report as REP
from vss.config import WatchlistEntry
from vss.metrics import Metrics
from vss.rules import TickerAssessment, Verdict

RUN_TS = datetime(2026, 8, 20, 22, 30)
AS_OF = date(2026, 8, 20)


@dataclass
class FakeRow:
    entry: WatchlistEntry
    metrics: Metrics
    assessment: TickerAssessment
    source: str = "live"
    fetched_at: datetime | None = None
    error: str | None = None
    pct_to_mbp: float | None = None
    pct_to_stop: float | None = None


def row(ticker="AAA", close_date=AS_OF, verdicts=(Verdict("NO_ACTION", "NO ACTION"),), **kw):
    return FakeRow(
        entry=WatchlistEntry(
            ticker=ticker, name=f"{ticker} Co", currency="SEK", status="WATCH-GATED",
            fv_base=200.0, tier=2, stop_price=80.0,
        ),
        metrics=Metrics(last_close=100.0, last_close_date=close_date, drawdown=0.25),
        assessment=TickerAssessment(ticker=ticker, verdicts=tuple(verdicts), mbp=140.0),
        **kw,
    )


# --- scoped runs ----------------------------------------------------------


def test_full_run_may_generalise_about_every_ticker():
    out = REP.render([row()], run_ts=RUN_TS, as_of=AS_OF)
    assert "ALL TICKERS" in out
    assert "Every ticker cleared the staleness gate" in out
    assert "PARTIAL RUN" not in out


def test_scoped_run_never_claims_every_ticker_cleared():
    out = REP.render(
        [row("AAA")], run_ts=RUN_TS, as_of=AS_OF, ticker_filter="AAA", watchlist_size=9
    )
    assert "Every ticker" not in out
    assert "Every unblocked ticker" not in out


def test_scoped_run_is_labelled_in_title_banner_and_section():
    out = REP.render(
        [row("AAA")], run_ts=RUN_TS, as_of=AS_OF, ticker_filter="AAA", watchlist_size=9
    )
    assert "SCOPED to AAA" in out
    assert "PARTIAL RUN" in out
    assert "1 of 9 tickers" in out
    assert "ALL TICKERS" not in out
    assert "## TICKER AAA" in out


def test_scoped_banner_pluralises():
    two = REP.render([row()], run_ts=RUN_TS, as_of=AS_OF, ticker_filter="AAA", watchlist_size=2)
    many = REP.render([row()], run_ts=RUN_TS, as_of=AS_OF, ticker_filter="AAA", watchlist_size=5)
    assert "other 1 watchlist entry was not" in two
    assert "other 4 watchlist entries were not" in many


# --- freshness errs toward the oldest close -------------------------------


def test_freshness_leads_with_the_oldest_close_not_the_newest():
    """One fresh ticker must not make a mostly-stale watchlist look current."""
    rows = [row("FRESH", close_date=AS_OF)] + [
        row(f"OLD{i}", close_date=date(2026, 8, 1)) for i in range(9)
    ]
    line = REP.freshness_line(rows, AS_OF)
    assert "oldest 19d old" in line
    assert line.startswith("closes 2026-08-01..2026-08-20")


def test_freshness_single_date_reports_one_age():
    line = REP.freshness_line([row(close_date=date(2026, 8, 18))], AS_OF)
    assert line.startswith("close 2026-08-18 (2d old)")


def test_freshness_flags_degraded_sources():
    assert "degraded" in REP.freshness_line([row(source="cache")], AS_OF)
    assert "degraded" not in REP.freshness_line([row(source="live")], AS_OF)


def test_freshness_with_no_data_at_all():
    assert "no price data" in REP.freshness_line([row(close_date=None)], AS_OF)


# --- section order is fixed -----------------------------------------------


def test_sections_appear_in_the_required_order():
    out = REP.render([row()], run_ts=RUN_TS, as_of=AS_OF)
    assert out.index("**Run:**") < out.index("**Data freshness:**")
    assert out.index("**Data freshness:**") < out.index("## BLOCKERS")
    assert out.index("## BLOCKERS") < out.index("## ACTIONS")
    assert out.index("## ACTIONS") < out.index("## ALL TICKERS")


def test_dry_run_banner_present_only_on_dry_runs():
    assert "DRY RUN" in REP.render([row()], run_ts=RUN_TS, as_of=AS_OF, dry_run=True)
    assert "DRY RUN" not in REP.render([row()], run_ts=RUN_TS, as_of=AS_OF, dry_run=False)


# --- E32: a superseded MBP is marked in every table it prints in -----------


def superseded_row(**kw):
    """A row whose mbp was struck under the definition E32 supersedes."""
    from vss.config import MbpBasisRecord
    r = row(**kw)
    r.entry = WatchlistEntry(
        ticker=r.entry.ticker, name=r.entry.name, currency=r.entry.currency,
        status="HELD", fv_base=200.0, tier=2, stop_price=80.0,
        mbp_basis=MbpBasisRecord(definition="fv_base_x_tier",
                                 struck="2026-08-22"),
    )
    r.assessment = TickerAssessment(
        ticker=r.entry.ticker, verdicts=r.assessment.verdicts, mbp=140.0,
        mbp_superseded=True,
    )
    return r


def test_e32_the_actions_table_marks_a_superseded_mbp():
    """The actions table only lists rows carrying a verdict, so give it one."""
    r = superseded_row(verdicts=(Verdict("AT_BELOW_MBP", "AT/BELOW MBP",
                                         "close 100.00 <= mbp 140.00"),))
    out = REP.render([r], run_ts=RUN_TS, as_of=AS_OF)
    actions = out.split("\n## ")[2]
    assert actions.startswith("ACTIONS"), "section order changed"
    assert "SUPERSEDED DEFINITION, E32" in actions
    assert "struck 2026-08-22" in actions


def test_e32_the_full_table_marks_a_superseded_mbp():
    """A row with no verdict never reaches ACTIONS, so this is the full
    table on its own."""
    out = REP.render([superseded_row()], run_ts=RUN_TS, as_of=AS_OF)
    full = out.split("\n## ")[3]
    assert full.startswith("ALL TICKERS"), "section order changed"
    assert "SUPERSEDED DEFINITION, E32" in full
    assert "struck 2026-08-22" in full


def test_e90_a_stored_basis_row_no_longer_marks_a_record_backed_figure(tmp_path):
    """THE SEAM under E90 (2026-08-30): a record-backed fv_base yields
    base x cushion, UNMARKED, whatever the entry's stored `mbp_basis` row
    claims -- the basis row is a record of what was struck, not an engine.
    E32's mark still renders where an assessment carries it (the stored
    history), which the table tests beside this one pin. (Item 9: the
    fv_base reaches the seam only through a run record that replays to
    it, so a synthetic one is written for the synthetic 200.)"""
    import json
    import pandas as pd
    from tests._records import synthetic_record
    from vss.config import MbpBasisRecord
    from vss.fetch import FetchResult
    from vss.runner import build_row

    record = tmp_path / "AAA.json"
    record.write_text(json.dumps(synthetic_record("AAA", "SEK", 200.0).to_dict()))
    entry = WatchlistEntry(
        ticker="AAA", name="AAA Co", currency="SEK", status="HELD",
        fv_base=200.0, tier=2, stop_price=80.0,
        mbp_basis=MbpBasisRecord(definition="fv_base_x_tier",
                                 struck="2026-08-22"),
        run_record=str(record),
    )
    frame = pd.DataFrame(
        {"Close": [100.0] * 5, "High": [100.0] * 5,
         "Low": [100.0] * 5, "Volume": [1000] * 5},
        index=pd.to_datetime([f"2026-08-{d:02d}" for d in (14, 17, 18, 19, 20)]),
    )
    row = build_row(entry, FetchResult(ticker="AAA", frame=frame,
                                       source="cache"), AS_OF)
    assert row.assessment.mbp == 150.0            # 200 x 0.75 (E90)
    assert row.assessment.mbp_superseded is False
    detail = [v.detail for v in row.assessment.verdicts
              if v.code == "AT_BELOW_MBP"][0]
    assert "SUPERSEDED DEFINITION, E32" not in detail

    out = REP.render([row], run_ts=RUN_TS, as_of=AS_OF, dry_run=True)
    assert "DRY RUN" in out


def test_e32_a_row_with_no_basis_record_is_still_marked():
    """ABSENCE DOES NOT MEAN LIVE -- and the cell says the date is missing
    rather than inventing one."""
    r = row()
    r.assessment = TickerAssessment(ticker="AAA", verdicts=r.assessment.verdicts,
                                    mbp=140.0, mbp_superseded=True)
    out = REP.render([r], run_ts=RUN_TS, as_of=AS_OF)
    assert "SUPERSEDED DEFINITION, E32" in out
    assert "date not recorded" in out


def test_e32_an_unsuperseded_mbp_prints_clean():
    out = REP.render([row()], run_ts=RUN_TS, as_of=AS_OF)
    assert "SUPERSEDED DEFINITION" not in out


# --- E37: the non-USD bias is PRINTED beside every non-USD fair value ----


def test_a_non_usd_fair_value_carries_E37_s_declaration():
    """E29 accepted the currency asymmetry knowingly and did not record its
    SIZE. A bias nobody has measured is indistinguishable from one nobody
    has, and this line is the whole of E37."""
    from vss.report import (NON_USD_MARK, _fv_base_cell,
                            _rate_declaration_line)
    from vss.valuation import (NON_USD_BIAS_DECLARATION, rate_declaration)

    class _E:
        def __init__(self, ticker, currency, fv_base):
            self.ticker, self.currency, self.fv_base = ticker, currency, fv_base

    class _R:
        def __init__(self, entry):
            self.entry = entry

    eur = _E("SAP.DE", "EUR", 185.0)
    usd = _E("MSFT", "USD", 280.0)
    none = _E("JD.L", "GBX", None)
    assert _fv_base_cell(eur).endswith(NON_USD_MARK)
    assert not _fv_base_cell(usd).endswith(NON_USD_MARK)
    assert _fv_base_cell(none) == "--"

    line = _rate_declaration_line([_R(eur), _R(usd), _R(none)])
    assert NON_USD_BIAS_DECLARATION in line
    assert "`SAP.DE`" in line and "MSFT" not in line
    # a run with no non-USD fair value prints nothing rather than a blank
    assert _rate_declaration_line([_R(usd)]) == ""

    assert rate_declaration("SEK") == NON_USD_BIAS_DECLARATION
    assert rate_declaration("usd") == "r 9.5% flat"
    assert rate_declaration(None) == "r 9.5% flat"


def test_E39_a_held_name_with_a_nulled_fv_base_is_named_as_superseded():
    """Build 2 item 4: the approved E39 diff nulls fv_base/tier/mbp on both
    held names and leaves the stop. The report must say that a bare dash
    on a HELD row is a nulled fair value, not a missing analysis."""
    held = row("SAP.DE")
    held.entry = WatchlistEntry(ticker="SAP.DE", name="SAP SE", currency="EUR",
                                status="HELD", fv_base=None, tier=None,
                                stop_price=165.0)
    out = REP.render([held, row("AAA")], run_ts=RUN_TS, as_of=AS_OF)
    assert "E39: `SAP.DE` — HELD with `fv_base` NULLED" in out
    assert "`AAA`" not in out.split("## BLOCKERS")[0].split("E39:")[-1]
    assert "re-strike pending" in out
    # a WATCH name with no fv_base is not an E39 case
    assert "E39:" not in REP.render([row("AAA")], run_ts=RUN_TS, as_of=AS_OF)


# --- E12 line (build item 5) --------------------------------------------------


def _pipeline_row(ticker, dd_at_entry=None, peak_date=None, today=0.13):
    return FakeRow(
        entry=WatchlistEntry(ticker=ticker, name=f"{ticker} Co", currency="DKK",
                             status="PIPELINE", dd_at_entry=dd_at_entry,
                             peak_date=peak_date),
        metrics=Metrics(last_close=100.0, last_close_date=AS_OF, drawdown=today),
        assessment=TickerAssessment(ticker=ticker, verdicts=(Verdict("NO_ACTION", "NO ACTION"),)),
    )


def test_the_report_says_which_pipeline_names_read_gate_1_as_frozen():
    rows = [_pipeline_row("PNDORA.CO", 0.1564, date(2025, 8, 22)),
            _pipeline_row("OLD.ST")]
    out = REP.render(rows, run_ts=RUN_TS, as_of=AS_OF)
    assert "E12" in out
    assert "`PNDORA.CO` 15.6% against the 52-week closing high of 2025-08-22 (today 13.0%)" in out
    assert "FROZEN AT ENTRY" in out
    assert "No `dd_at_entry`/`peak_date` recorded for `OLD.ST` (today 13.0%)" in out


def test_no_pipeline_names_means_no_e12_line():
    out = REP.render([row()], run_ts=RUN_TS, as_of=AS_OF)
    assert "E12" not in out


# --- E63: the distance above the 52-week low, beside the drawdown -----------


def _status_row(ticker, status, **metrics):
    return FakeRow(
        entry=WatchlistEntry(ticker=ticker, name=f"{ticker} Co", currency="USD",
                             status=status, fv_base=200.0, tier=2, stop_price=30.0),
        metrics=Metrics(last_close=63.78, last_close_date=AS_OF, drawdown=0.265,
                        **metrics),
        assessment=TickerAssessment(ticker=ticker,
                                    verdicts=(Verdict("NO_ACTION", "NO ACTION"),)),
    )


def test_E63_the_full_table_and_the_held_and_watch_priced_line_carry_the_52_week_low():
    rows = [
        _status_row("CTSH", "WATCH-PRICED", low_52w=38.73,
                    low_52w_date=date(2026, 6, 30), pct_above_52w_low=0.647),
        _status_row("HLD", "HELD", covers_52_weeks=False),
        _status_row("PIPE", "PIPELINE", low_52w=10.0,
                    low_52w_date=date(2026, 5, 1), pct_above_52w_low=0.28),
        _status_row("GATED", "WATCH-GATED", low_52w=10.0,
                    low_52w_date=date(2026, 5, 1), pct_above_52w_low=0.28),
    ]
    out = REP.render(rows, run_ts=RUN_TS, as_of=AS_OF)
    # Beside the drawdown, on every row of the full table.
    assert "| 52w high | DD | 52w low | vs 52wL |" in out
    assert "| 26.5% | 38.73 | 64.7% |" in out
    assert "| 26.5% | -- | -- |" in out
    # Named for HELD and WATCH-PRICED, and only for them.
    lines = [line for line in out.splitlines() if line.startswith("*E63")]
    assert len(lines) == 1
    (line,) = lines
    assert "`CTSH` 64.7% above its 52-week closing low of 38.73 (2026-06-30)" in line
    assert "`HLD` DATA MISSING" in line
    assert "PIPE" not in line and "GATED" not in line
    assert "never applied" in line
    assert out.index("*E12") < out.index("*E63")


def test_no_held_or_watch_priced_names_means_no_e63_line():
    out = REP.render([row()], run_ts=RUN_TS, as_of=AS_OF)
    assert "| 52w low | vs 52wL |" in out            # the column is on every report
    assert not [line for line in out.splitlines() if line.startswith("*E63")]
