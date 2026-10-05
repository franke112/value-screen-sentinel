"""The screen command: reports, the snapshot run, and the standing rules."""

from __future__ import annotations

import csv
from datetime import date, datetime
from pathlib import Path

import pandas as pd
import pytest

from vss import filters, rules, screen
from vss.__main__ import build_parser
from vss.snapshot import read_manifest, verify
from vss.universe import SCHEMA, UniverseError

AS_OF = date(2026, 8, 21)
SCREENER_MODULES = ("vss/universe.py", "vss/prices.py", "vss/snapshot.py",
                    "vss/fundamentals.py", "vss/filters.py", "vss/fx.py",
                    "vss/ranking.py", "vss/pipeline.py", "vss/screen.py")


@pytest.fixture()
def universe(tmp_path: Path) -> Path:
    directory = tmp_path / "universe"
    directory.mkdir()
    rows = [
        ["SAP.DE", "SAP", "DE0007164600", "SAP SE", "Xetra", "A", "1998-04-09", "EUR", "Equity"],
        ["VOLV-B.ST", "VOLVB", "", "Volvo AB", "Stockholm", "A", "1999-01-04", "SEK", "Equity"],
        ["EXSA.DE", "EXSA", "", "iShares STOXX 600", "Xetra", "A", "", "EUR", "ETF"],
        ["", "NOMAP", "", "Unmapped Co", "Lisbon", "A", "", "EUR", "Equity"],
        ["MID.ST", "MID", "", "Mid Cap AB", "Stockholm", "B", "", "SEK", "Equity"],
    ]
    with (directory / "test-list.csv").open("w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle, lineterminator="\n")
        writer.writerow(SCHEMA)
        writer.writerows(rows)
    (directory / "instrument_types.yaml").write_text(
        "include:\n  equity: [Equity]\nexclude:\n  etf: [ETF]\nunknown_action: keep\n",
        encoding="utf-8",
    )
    (directory / "floors.yaml").write_text(
        "tiers:\n  A: {}\n  C:\n    market_cap:\n      min: 300000000\n      currency: EUR\n",
        encoding="utf-8",
    )
    return directory


# E52 (2026-08-27): a series shorter than five years is rejected at the
# listing-age floor before any band is reached, so every fixture that means
# to exercise a LATER step has to clear it first. 2000 calendar rows is a
# little over five and a half years.
def frame(days: int = 2000, last: date = AS_OF) -> pd.DataFrame:
    index = pd.to_datetime([last - pd.Timedelta(days=days - 1 - i) for i in range(days)])
    return pd.DataFrame(
        {"Open": [10.0] * days, "High": [11.0] * days, "Low": [9.0] * days,
         "Close": [10.0] * days, "Volume": [1000.0] * days},
        index=index,
    )


def downloader(available: dict[str, pd.DataFrame]):
    def download(tickers, period):
        present = {t: available[t] for t in tickers if t in available}
        if not present:
            return pd.DataFrame()
        return pd.concat(present, axis=1, sort=False)

    return download


# --- --universe-report -----------------------------------------------------


def test_universe_report_counts_per_market(universe: Path):
    report = screen.universe_report(universe, ("A",))
    assert "COUNT PER MARKET" in report
    assert "Xetra" in report and "Stockholm" in report
    assert "TOTAL" in report


def test_universe_report_shows_exclusions_by_reason(universe: Path):
    report = screen.universe_report(universe, ("A",))
    assert "EXCLUDED PER REASON" in report
    assert "etf" in report


def test_universe_report_counts_the_unmapped(universe: Path):
    report = screen.universe_report(universe, ("A",))
    assert "WITHOUT A VALID YAHOO MAPPING" in report
    assert "Lisbon:NOMAP" in report


def test_universe_report_splits_value_from_missing(universe: Path):
    report = screen.universe_report(universe, ("A",))
    assert "rej(value)" in report and "rej(missing)" in report
    assert "[value" in report and "[missing" in report


def test_universe_report_states_the_isin_coverage(universe: Path):
    report = screen.universe_report(universe, ("A",))
    assert "isin coverage: 1/2" in report


def test_universe_report_shows_the_tier_floors_with_currency(universe: Path):
    report = screen.universe_report(universe, ("A",))
    assert "TIER FLOORS" in report
    assert "'currency': 'EUR'" in report


def test_tier_b_is_only_loaded_when_asked(universe: Path):
    assert "MID.ST" not in screen.universe_report(universe, ("A",))
    assert "Mid Cap" not in screen.universe_report(universe, ("A",))
    both = screen.universe_report(universe, ("A", "B"))
    assert "tiers=A,B" in both


# --- --snapshot-only -------------------------------------------------------


def test_snapshot_only_fetches_stores_and_reports(universe: Path, tmp_path: Path):
    result = screen.snapshot_only(
        as_of=AS_OF, universe_dir=universe, snapshot_root=tmp_path / "snaps",
        download=downloader({"SAP.DE": frame(), "VOLV-B.ST": frame()}),
        sleep=lambda _: None, now=datetime(2026, 8, 22, 10, 0),
    )
    assert result.path.exists()
    assert read_manifest(result.path)["asof"] == "2026-08-21"
    assert "FETCH STATUS" in result.report
    assert "COVERAGE PER MARKET" in result.report
    assert "OK" in result.report
    assert verify(result.path, universe) == []


def test_snapshot_only_filters_nothing(universe: Path, tmp_path: Path):
    """Both survivors are stored whatever their prices look like."""
    result = screen.snapshot_only(
        as_of=AS_OF, universe_dir=universe, snapshot_root=tmp_path / "s",
        download=downloader({"SAP.DE": frame(), "VOLV-B.ST": frame()}),
        sleep=lambda _: None,
    )
    assert set(result.outcome.frames) == {"SAP.DE", "VOLV-B.ST"}
    steps = [t.step for t in result.load.tallies] + [result.outcome.tally.step]
    assert "dislocation" not in steps and "rank" not in steps


def test_a_ticker_that_did_not_arrive_is_named_in_the_report(universe: Path, tmp_path: Path):
    result = screen.snapshot_only(
        as_of=AS_OF, universe_dir=universe, snapshot_root=tmp_path / "s",
        download=downloader({"SAP.DE": frame()}), sleep=lambda _: None,
    )
    assert "NOT OK" in result.report
    assert "VOLV-B.ST" in result.report
    assert "NO_DATA" in result.report


def test_the_report_carries_the_yield_table(universe: Path, tmp_path: Path):
    result = screen.snapshot_only(
        as_of=AS_OF, universe_dir=universe, snapshot_root=tmp_path / "s",
        download=downloader({"SAP.DE": frame()}), sleep=lambda _: None,
    )
    assert "YIELD -- rows in and out of every step" in result.report
    assert "price_fetch" in result.report


def test_limit_is_flagged_as_a_partial_run(universe: Path, tmp_path: Path):
    result = screen.snapshot_only(
        as_of=AS_OF, universe_dir=universe, snapshot_root=tmp_path / "s",
        download=downloader({"SAP.DE": frame()}), sleep=lambda _: None, limit=1,
    )
    assert "this is a partial run" in result.report
    assert read_manifest(result.path)["limit"] == "1"


def test_asof_truncation_is_visible_in_the_manifest(universe: Path, tmp_path: Path):
    result = screen.snapshot_only(
        as_of=AS_OF, universe_dir=universe, snapshot_root=tmp_path / "s",
        download=downloader({"SAP.DE": frame(last=date(2026, 8, 28))}),
        sleep=lambda _: None,
    )
    assert read_manifest(result.path)["max_price_date"] == "2026-08-21"
    assert verify(result.path, universe) == []


# --- --filter1 -------------------------------------------------------------


@pytest.fixture()
def exclusions(tmp_path: Path) -> Path:
    path = tmp_path / "exclusions.csv"
    path.write_text(
        "ticker_yahoo,skal,datum,kalla\n"
        "SAP.DE,HELD,2026-08-22,held position\n"
        "GONE.ST,DROPPED,2026-08-22,not in this universe\n",
        encoding="utf-8",
    )
    return path


def dislocated(days: int = 2000, high: float = 100.0, low: float = 75.0,
               tail: int = 200) -> pd.DataFrame:
    """Flat at ``high`` for its whole life, then ``tail`` rows at ``low``.

    ``tail`` must stay INSIDE the trailing 365 days or `high_52w` never sees
    the peak: with days=2000 (E52's five-year floor) a step at the midpoint
    is three years old and the drawdown reads zero.
    """
    closes = [high] * (days - tail) + [low] * tail
    return frame(days=days).assign(Close=closes, Open=closes, High=closes, Low=closes)


def prepare(universe: Path, tmp_path: Path, frames: dict) -> Path:
    screen.snapshot_only(
        as_of=AS_OF, universe_dir=universe, snapshot_root=tmp_path / "snaps",
        download=downloader(frames), sleep=lambda _: None,
    )
    return tmp_path / "snaps"


def test_filter1_runs_step_0_then_the_band(universe: Path, tmp_path: Path,
                                           exclusions: Path):
    root = prepare(universe, tmp_path, {"SAP.DE": dislocated(), "VOLV-B.ST": dislocated()})
    run = screen.filter1(
        as_of=AS_OF, universe_dir=universe, snapshot_root=root,
        exclusions_path=exclusions, runs_root=tmp_path / "runs",
    )
    assert [c.ticker for c in run.result.candidates] == ["VOLV-B.ST"]
    assert "STEP 0 -- THE EXCLUSION LIST" in run.report
    assert "SAP.DE" in run.report and "HELD since 2026-08-22" in run.report


def test_filter1_report_carries_the_yield_table_with_both_columns(
    universe: Path, tmp_path: Path, exclusions: Path
):
    root = prepare(universe, tmp_path, {"SAP.DE": dislocated(), "VOLV-B.ST": dislocated()})
    run = screen.filter1(
        as_of=AS_OF, universe_dir=universe, snapshot_root=root,
        exclusions_path=exclusions, runs_root=tmp_path / "runs",
    )
    assert "rej(value)" in run.report and "rej(missing)" in run.report
    steps = [t.step for t in run.tallies]
    # E51 adds a second step-0 limb, E52 a step at the head of filter 1.
    # E96's limb sits beside E51's, with its own tally name.
    # E127 adds the trailing-year step after the band.
    assert steps[-8:] == ["exclusion_list", "circle_of_competence",
                          "commodity_price", "price_coverage", "listing_age",
                          "series_sanity", "dislocation", "trailing_year"]


def test_filter1_names_an_inert_exclusion_entry(universe: Path, tmp_path: Path,
                                                exclusions: Path):
    root = prepare(universe, tmp_path, {"SAP.DE": dislocated(), "VOLV-B.ST": dislocated()})
    run = screen.filter1(
        as_of=AS_OF, universe_dir=universe, snapshot_root=root,
        exclusions_path=exclusions, runs_root=tmp_path / "runs",
    )
    assert "matched NOTHING" in run.report
    assert "GONE.ST" in run.report


def test_filter1_writes_the_candidate_table(universe: Path, tmp_path: Path,
                                            exclusions: Path):
    root = prepare(universe, tmp_path, {"SAP.DE": dislocated(), "VOLV-B.ST": dislocated()})
    run = screen.filter1(
        as_of=AS_OF, universe_dir=universe, snapshot_root=root,
        exclusions_path=exclusions, runs_root=tmp_path / "runs",
    )
    assert run.candidates_path is not None and run.candidates_path.exists()
    text = run.candidates_path.read_text(encoding="utf-8")
    assert text.splitlines()[0].startswith("ticker,marknad,namn,last_close")
    assert "VOLV-B.ST" in text


def test_filter1_says_the_order_is_not_a_ranking(universe: Path, tmp_path: Path,
                                                 exclusions: Path):
    root = prepare(universe, tmp_path, {"SAP.DE": dislocated(), "VOLV-B.ST": dislocated()})
    run = screen.filter1(
        as_of=AS_OF, universe_dir=universe, snapshot_root=root,
        exclusions_path=exclusions, runs_root=tmp_path / "runs",
    )
    assert "not a ranking" in run.report
    assert "phase 5" in run.report


def _live_print(high: float = 100.0, low: float = 75.0, print_: float = 90.0,
                days: int = 2000, tail: int = 200) -> pd.DataFrame:
    """A dislocated series whose LAST bar, dated AS_OF, is a live print that
    would put the name outside the band: 90 against a high of 100 is a 10%
    drawdown; the settled close of the day before, 75, is 25%."""
    closes = [high] * (days - tail) + [low] * (tail - 1) + [print_]
    return frame(days=days).assign(Close=closes, Open=closes, High=closes, Low=closes)


def test_a_snapshot_taken_during_the_session_demotes_todays_bar(
        universe: Path, tmp_path: Path, exclusions: Path):
    """Item 2 (SCREENER-REVIEW-3 Part 1.2). The 11:19 CEST snapshot of
    2026-08-26 stored a live print as the close of the run date for 864 of
    1,370 names and the 15% edge was decided on it. Filter 1 now applies the
    same settlement cutoff `vss run` applies, struck from the clock the
    SNAPSHOT was taken by: 11:23 Stockholm is 05:23 New York, before the
    last close of the day, so the bar of the run date is a live print and
    filter 1 reads the settled close of the day before."""
    screen.snapshot_only(
        as_of=AS_OF, universe_dir=universe, snapshot_root=tmp_path / "snaps",
        download=downloader({"VOLV-B.ST": _live_print()}), sleep=lambda _: None,
        now=datetime(2026, 8, 21, 11, 23).astimezone(),
    )
    run = screen.filter1(
        as_of=AS_OF, universe_dir=universe, snapshot_root=tmp_path / "snaps",
        exclusions_path=exclusions, runs_root=tmp_path / "runs",
    )
    assert run.settled == date(2026, 8, 20)
    (volvo,) = run.result.candidates
    assert volvo.last_close_date == date(2026, 8, 20)
    assert volvo.last_close == 75.0
    assert volvo.drawdown == pytest.approx(0.25)
    assert "settled through 2026-08-20" in run.report and "DEMOTED" in run.report


def test_a_snapshot_taken_after_the_close_reads_todays_bar(
        universe: Path, tmp_path: Path, exclusions: Path):
    """The complement: the 22:17 CEST snapshot (16:17 New York) has every
    close settled, and the same series is priced at the 90 print, which is a
    10% drawdown and OUTSIDE the band -- the name is rejected on value."""
    screen.snapshot_only(
        as_of=AS_OF, universe_dir=universe, snapshot_root=tmp_path / "snaps",
        download=downloader({"VOLV-B.ST": _live_print()}), sleep=lambda _: None,
        now=datetime(2026, 8, 21, 22, 17).astimezone(),
    )
    run = screen.filter1(
        as_of=AS_OF, universe_dir=universe, snapshot_root=tmp_path / "snaps",
        exclusions_path=exclusions, runs_root=tmp_path / "runs",
    )
    assert run.settled == AS_OF
    assert run.result.candidates == []
    rejected = [r for r in run.result.rejections if r.key == "VOLV-B.ST"]
    assert rejected and "10.0%" in rejected[0].reason
    assert "settled through 2026-08-21" in run.report


def test_the_settlement_cutoff_reaches_the_ranking_through_the_settled_close(
        universe: Path, tmp_path: Path, exclusions: Path):
    """Rule 8 divides by the close filter 1 carried, so a demoted print never
    reaches the yield either: the market cap is struck on the 75 of 08-20."""
    screen.snapshot_only(
        as_of=AS_OF, universe_dir=universe, snapshot_root=tmp_path / "snaps",
        download=downloader({"VOLV-B.ST": _live_print()}), sleep=lambda _: None,
        now=datetime(2026, 8, 21, 11, 23).astimezone(),
    )

    def reader(ticker):
        return _info(regularMarketPrice=90.0), _rankable_statements(), 2

    screen.fetch_fundamentals(
        as_of=AS_OF, universe_dir=universe, snapshot_root=tmp_path / "snaps",
        exclusions_path=exclusions, reader=reader, sleep=lambda _: None,
        now=datetime(2026, 8, 22, 16, 0),
    )
    run = screen.rank(
        as_of=AS_OF, universe_dir=universe, snapshot_root=tmp_path / "snaps",
        exclusions_path=exclusions, runs_root=None, fx_lookup=fx_lookup,
    )
    (volvo,) = run.result.main
    assert volvo.scored.inputs.settled_close_date == date(2026, 8, 20)
    assert volvo.scored.implied_shares == pytest.approx(4800.0 / 90.0)
    assert volvo.scored.market_cap_settled == pytest.approx(4800.0 / 90.0 * 75.0)


def test_a_replay_from_a_later_snapshot_declares_the_survivorship_caveat(
    universe: Path, tmp_path: Path, exclusions: Path
):
    root = prepare(universe, tmp_path, {"SAP.DE": dislocated(), "VOLV-B.ST": dislocated()})
    run = screen.filter1(
        as_of=date(2026, 6, 1), universe_dir=universe, snapshot_root=root,
        exclusions_path=exclusions, runs_root=tmp_path / "runs",
    )
    assert run.snapshot_date == AS_OF
    assert "REPLAY" in run.report and "survivorship" in run.report


def test_a_snapshot_older_than_the_run_date_is_refused(universe: Path, tmp_path: Path,
                                                       exclusions: Path):
    root = prepare(universe, tmp_path, {"SAP.DE": dislocated()})
    with pytest.raises(UniverseError, match="before asof"):
        screen.filter1(
            as_of=date(2026, 12, 1), universe_dir=universe, snapshot_root=root,
            exclusions_path=exclusions, runs_root=tmp_path / "runs",
        )


def test_no_snapshot_at_all_is_a_clear_error(universe: Path, tmp_path: Path,
                                             exclusions: Path):
    with pytest.raises(UniverseError, match="no snapshots"):
        screen.filter1(
            as_of=AS_OF, universe_dir=universe, snapshot_root=tmp_path / "empty",
            exclusions_path=exclusions, runs_root=tmp_path / "runs",
        )


def test_filter1_fetches_nothing():
    """Structural: the filter path must not reach the network."""
    import ast

    source = Path("vss/screen.py").read_text(encoding="utf-8")
    tree = ast.parse(source)
    (func,) = [n for n in ast.walk(tree)
               if isinstance(n, ast.FunctionDef) and n.name == "filter1"]
    called = {n.func.id for n in ast.walk(func)
              if isinstance(n, ast.Call) and isinstance(n.func, ast.Name)}
    called |= {n.func.attr for n in ast.walk(func)
               if isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute)}
    assert "fetch_universe" not in called and "default_download" not in called
    assert "read_all_prices" in called


# --- phase 3: fundamentals and filter 2 -------------------------------------


def _info(**over):
    base = {
        "sector": "Technology", "industry": "Software", "financialCurrency": "EUR",
        "currency": "EUR", "quoteType": "EQUITY", "freeCashflow": 100.0,
        "operatingCashflow": 120.0, "totalRevenue": 1000.0, "revenueGrowth": 0.05,
        "ebitda": 200.0, "totalDebt": 300.0, "totalCash": 100.0,
        "enterpriseValue": 5000.0, "marketCap": 4800.0,
        # The vendor's quote at the fetch, which its marketCap embeds. The
        # test frames close at 75.0 (`dislocated`), so the ranking re-prices
        # the implied count at that settled close (rule 8).
        "regularMarketPrice": 80.0,
    }
    base.update(over)
    return base


def _statement(years=(2025, 2024, 2023, 2022), revenue=(1000, 950, 900, 850)):
    columns = [pd.Timestamp(f"{y}-12-31") for y in years]
    return pd.DataFrame(
        {c: [r, 200.0] for c, r in zip(columns, revenue)},
        index=["Total Revenue", "EBITDA"],
    )


def reader_for(per_ticker: dict):
    def reader(ticker):
        info, statement = per_ticker.get(ticker, (_info(), _statement()))
        return info, statement, 2
    return reader


@pytest.fixture()
def chain(universe: Path, tmp_path: Path, exclusions: Path):
    """A snapshot plus a fundamentals store, both from fakes."""
    root = prepare(universe, tmp_path, {"SAP.DE": dislocated(), "VOLV-B.ST": dislocated()})
    screen.fetch_fundamentals(
        as_of=AS_OF, universe_dir=universe, snapshot_root=root,
        exclusions_path=exclusions, reader=reader_for({}), sleep=lambda _: None,
        now=datetime(2026, 8, 22, 16, 0),
    )
    return universe, root, exclusions


def test_fundamentals_are_fetched_only_for_filter1_survivors(chain, tmp_path: Path):
    universe, root, exclusions = chain
    run = screen.fetch_fundamentals(
        as_of=AS_OF, universe_dir=universe, snapshot_root=root,
        exclusions_path=exclusions, reader=reader_for({}), sleep=lambda _: None,
    )
    # SAP.DE is on the exclusion list, so it never reaches the fetch.
    assert [c.ticker for c in run.survivors] == ["VOLV-B.ST"]
    assert [r.ticker for r in run.outcome.records] == ["VOLV-B.ST"]


def test_the_fundamentals_report_carries_the_look_ahead_banner(chain):
    """The user made this a hard requirement: it must be in the output."""
    universe, root, exclusions = chain
    run = screen.fetch_fundamentals(
        as_of=AS_OF, universe_dir=universe, snapshot_root=root,
        exclusions_path=exclusions, reader=reader_for({}), sleep=lambda _: None,
        now=datetime(2026, 8, 22, 16, 0),
    )
    assert "LOOK-AHEAD WARNING" in run.report
    assert "2026-08-22" in run.report and "2026-08-21" in run.report
    assert "no retroactive reading" in run.report.lower()


def test_the_filter2_report_carries_the_look_ahead_banner_naming_both_dates(chain):
    universe, root, exclusions = chain
    run = screen.filter2(
        as_of=AS_OF, universe_dir=universe, snapshot_root=root,
        exclusions_path=exclusions, runs_root=None,
    )
    assert "LOOK-AHEAD WARNING" in run.report
    assert "THESE TWO DATES DIFFER" in run.report
    assert "accounts as published by 2026-08-22" in run.report
    assert "price they are paired with is that of 2026-08-21" in run.report
    assert "NOT evidence of what a screener would have found" in run.report


def test_the_banner_says_contemporaneous_when_the_dates_agree(universe: Path,
                                                             tmp_path: Path,
                                                             exclusions: Path):
    """Reachable: snapshot, fetch and run all on the same day."""
    root = prepare(universe, tmp_path, {"VOLV-B.ST": dislocated()})
    screen.fetch_fundamentals(
        as_of=AS_OF, universe_dir=universe, snapshot_root=root,
        exclusions_path=exclusions, reader=reader_for({}), sleep=lambda _: None,
        now=datetime(2026, 8, 21, 22, 30),
    )
    run = screen.filter2(
        as_of=AS_OF, universe_dir=universe, snapshot_root=root,
        exclusions_path=exclusions, runs_root=None,
    )
    assert "THESE TWO DATES DIFFER" not in run.report
    assert "contemporaneous" in run.report


def test_filter2_report_states_the_decided_thresholds_and_their_source(chain):
    universe, root, exclusions = chain
    run = screen.filter2(
        as_of=AS_OF, universe_dir=universe, snapshot_root=root,
        exclusions_path=exclusions, runs_root=None,
    )
    assert "[DECIDED]" in run.report
    assert "FRAMEWORK-EDITS E2, E3, E4" in run.report
    assert "3.5x" in run.report
    assert "It has failed" in run.report and "to fail it" in run.report


def test_filter2_report_reconciles_the_survivor_set_against_the_store(chain):
    universe, root, exclusions = chain
    run = screen.filter2(
        as_of=AS_OF, universe_dir=universe, snapshot_root=root,
        exclusions_path=exclusions, runs_root=None,
    )
    assert "SURVIVOR SET AGAINST THE STORE" in run.report
    assert "No drift" in run.report


def test_filter2_names_a_survivor_the_store_never_saw(chain, tmp_path: Path):
    """Drift is what this check exists for, so it is provoked."""
    universe, root, exclusions = chain
    empty = tmp_path / "empty-exclusions.csv"
    empty.write_text("ticker_yahoo,skal,datum,kalla\n", encoding="utf-8")
    run = screen.filter2(
        as_of=AS_OF, universe_dir=universe, snapshot_root=root,
        exclusions_path=empty, runs_root=None,
    )
    # SAP.DE is no longer excluded, so it reaches filter 2 -- but the store
    # was built when it was still on the list.
    assert "SAP.DE" in run.result.not_fetched
    assert "were never fetched" in run.report


def test_filter2_without_a_fundamentals_store_says_what_to_run(universe: Path,
                                                               tmp_path: Path,
                                                               exclusions: Path):
    root = prepare(universe, tmp_path, {"VOLV-B.ST": dislocated()})
    with pytest.raises(UniverseError, match="--fundamentals"):
        screen.filter2(
            as_of=AS_OF, universe_dir=universe, snapshot_root=root,
            exclusions_path=exclusions, runs_root=None,
        )


def test_filter2_writes_its_own_candidate_table(chain, tmp_path: Path):
    universe, root, exclusions = chain
    screen.filter2(
        as_of=AS_OF, universe_dir=universe, snapshot_root=root,
        exclusions_path=exclusions, runs_root=tmp_path / "runs",
    )
    path = tmp_path / "runs" / AS_OF.isoformat() / "filter2-candidates.csv"
    assert path.exists()
    header = path.read_text(encoding="utf-8").splitlines()[0]
    assert header.startswith("ticker,marknad,last_close,drawdown,rsi14,fcf")


def test_the_yield_report_gains_a_filter2_row(chain):
    universe, root, exclusions = chain
    run = screen.filter2(
        as_of=AS_OF, universe_dir=universe, snapshot_root=root,
        exclusions_path=exclusions, runs_root=None,
    )
    steps = [t.step for t in run.upstream.tallies] + [run.result.tally.step]
    # E96 sits beside E51 at step 0 with its OWN tally name: two limbs
    # sharing one would be indistinguishable in the funnel.
    assert steps[-9:] == ["exclusion_list", "circle_of_competence",
                          "commodity_price", "price_coverage", "listing_age",
                          "series_sanity", "dislocation", "trailing_year",
                          "filter2"]
    assert "filter2" in run.report


# --- phase 5: the ranking ---------------------------------------------------


def fx_lookup(base, quote):
    return 1.0, date(2026, 8, 21), f"{base}{quote}=X"


def test_rank_produces_two_sections_and_saves_the_full_list(chain, tmp_path: Path):
    universe, root, exclusions = chain
    run = screen.rank(
        as_of=AS_OF, universe_dir=universe, snapshot_root=root,
        exclusions_path=exclusions, runs_root=tmp_path / "runs",
        fx_lookup=fx_lookup,
    )
    assert run.ranking_path.exists() and run.manifest_path.exists()
    text = run.ranking_path.read_text(encoding="utf-8")
    header, *rows = text.splitlines()
    assert header.startswith("section,combined_rank,quality_rank,ey_rank,ticker")
    assert "TOP 20 -- RANKED ON BOTH COMPONENTS" in run.report
    assert "EARNINGS YIELD ONLY" in run.report

    # Every saved row carries its market. The full list is the deliverable;
    # a column that is always empty is a column that lies.
    import csv as _csv

    saved = list(_csv.DictReader(text.splitlines()))
    assert saved, "the saved list is empty"
    assert all(row["marknad"] for row in saved), \
        "ranking.csv has rows with no marknad"
    assert all(row["ticker"] for row in saved)


def test_the_rank_report_states_what_the_quality_leg_is_and_what_it_replaced(
        chain, tmp_path: Path):
    """E6 superseded E5's leg. A report that printed only the new definition
    would leave a reader of two runs unable to see why the names changed."""
    universe, root, exclusions = chain
    run = screen.rank(
        as_of=AS_OF, universe_dir=universe, snapshot_root=root,
        exclusions_path=exclusions, runs_root=None, fx_lookup=fx_lookup,
    )
    assert "EBIT / total assets" in run.report and "E43" in run.report
    assert "Gross Profit / Total Assets" in run.report, "what E43 replaced must stay legible"
    assert "E6" in run.report and "E5" in run.report
    assert "net working capital" in run.report.lower()


def test_the_rank_report_prints_every_exchange_rate_it_used(chain, tmp_path: Path):
    """E5(b)'s binding condition, carried into E6: saved per run AND reported."""
    universe, root, exclusions = chain
    run = screen.rank(
        as_of=AS_OF, universe_dir=universe, snapshot_root=root,
        exclusions_path=exclusions, runs_root=tmp_path / "runs",
        fx_lookup=fx_lookup,
    )
    assert "EXCHANGE RATES USED" in run.report
    assert "GBp" in run.report and "major unit" in run.report.lower()
    import json

    manifest = json.loads(run.manifest_path.read_text(encoding="utf-8"))
    assert "fx" in manifest and "fx_failed" in manifest
    assert manifest["key"].startswith("FRAMEWORK-EDITS E6")


def _rankable_statements(year: int = 2025):
    """Income and balance sheets carrying everything the E6 key needs.

    The plain ``chain`` fixture's statement has revenue and EBITDA only, so
    its ranked list is EMPTY and any assertion about ordering made against it
    is vacuous. Anything testing the ranking itself uses this instead.
    """
    column = pd.Timestamp(f"{year}-12-31")
    return {
        "income": pd.DataFrame({column: [1000.0, 350.0, 120.0]},
                               index=["Total Revenue", "Gross Profit", "EBIT"]),
        "balance": pd.DataFrame({column: [2000.0, 400.0]},
                                index=["Total Assets", "Net PPE"]),
    }


@pytest.fixture()
def fx_chain(universe: Path, tmp_path: Path, exclusions: Path):
    """A chain whose survivor RANKS, and whose EBIT and EV are in DIFFERENT
    currencies -- so the exchange rate actually moves the earnings yield."""
    root = prepare(universe, tmp_path, {"SAP.DE": dislocated(), "VOLV-B.ST": dislocated()})

    def reader(ticker):
        return _info(financialCurrency="EUR", currency="SEK"), _rankable_statements(), 2

    screen.fetch_fundamentals(
        as_of=AS_OF, universe_dir=universe, snapshot_root=root,
        exclusions_path=exclusions, reader=reader, sleep=lambda _: None,
        now=datetime(2026, 8, 22, 16, 0),
    )
    return universe, root, exclusions


def test_the_fx_chain_fixture_actually_ranks_something(fx_chain, tmp_path: Path):
    """Guards every assertion below from passing on an empty list."""
    universe, root, exclusions = fx_chain
    run = screen.rank(
        as_of=AS_OF, universe_dir=universe, snapshot_root=root,
        exclusions_path=exclusions, runs_root=None, fx_lookup=fx_lookup,
    )
    assert [r.ticker for r in run.result.main] == ["VOLV-B.ST"]
    assert run.result.main[0].scored.earnings_yield is not None


def test_a_rank_run_says_it_is_auditable_and_NOT_reproducible(chain, tmp_path: Path):
    """SCREENER.md claimed the stronger word until 2026-08-22.

    The report has to draw the distinction itself, because the person reading
    a stored run months later is reading the report, not the source.
    """
    universe, root, exclusions = chain
    run = screen.rank(
        as_of=AS_OF, universe_dir=universe, snapshot_root=root,
        exclusions_path=exclusions, runs_root=tmp_path / "runs",
        fx_lookup=fx_lookup,
    )
    assert "AUDITABLE, NOT REPRODUCIBLE" in run.report
    assert "--fx-from-manifest" in run.report

    import json
    manifest = json.loads(run.manifest_path.read_text(encoding="utf-8"))
    assert manifest["fx_source"].startswith("fetched at run time")


def test_a_replayed_run_reproduces_the_stored_run_rate_for_rate(fx_chain, tmp_path: Path):
    """K7's actual claim: run it, replay it, get the same numbers."""
    universe, root, exclusions = fx_chain
    runs = tmp_path / "runs"
    first = screen.rank(
        as_of=AS_OF, universe_dir=universe, snapshot_root=root,
        exclusions_path=exclusions, runs_root=runs, fx_lookup=fx_lookup,
    )

    def moved(base, quote):
        """The rates have moved since. A replay must not notice."""
        return 99.0, date(2026, 9, 30), f"{base}{quote}=X"

    replay = screen.rank(
        as_of=AS_OF, universe_dir=universe, snapshot_root=root,
        exclusions_path=exclusions, runs_root=None, fx_lookup=moved,
        fx_from_manifest=first.manifest_path,
    )
    assert [r.ticker for r in replay.result.main] == \
        [r.ticker for r in first.result.main]
    for a, b in zip(replay.result.main, first.result.main):
        assert a.scored.earnings_yield == b.scored.earnings_yield
    assert "REPRODUCIBLE" in replay.report
    assert "AUDITABLE, NOT REPRODUCIBLE" not in replay.report


def test_a_fresh_lookup_would_have_changed_the_answer(fx_chain, tmp_path: Path):
    """So the test above is measuring the replay and not a coincidence."""
    universe, root, exclusions = fx_chain
    first = screen.rank(
        as_of=AS_OF, universe_dir=universe, snapshot_root=root,
        exclusions_path=exclusions, runs_root=None, fx_lookup=fx_lookup,
    )
    other = screen.rank(
        as_of=AS_OF, universe_dir=universe, snapshot_root=root,
        exclusions_path=exclusions, runs_root=None,
        fx_lookup=lambda b, q: (99.0, date(2026, 9, 30), f"{b}{q}=X"),
    )
    a = {r.ticker: r.scored.earnings_yield for r in first.result.main}
    b = {r.ticker: r.scored.earnings_yield for r in other.result.main}
    assert a != b, "the fixture's names do not cross a currency, so nothing is proved"


def test_the_look_ahead_banner_says_the_enterprise_value_is_BUILT_from_one_date(
        chain, tmp_path: Path):
    """The vendor's enterpriseValue sits among the fundamentals and is a
    precomputed figure on the vendor's own cadence (SCREENER-REVIEW-3 Part
    12). The banner used to call it a price-dependent quantity carrying the
    fetch-day quote; the data contradicted that, so the banner now says
    what the ranking actually divides by."""
    universe, root, exclusions = chain
    run = screen.rank(
        as_of=AS_OF, universe_dir=universe, snapshot_root=root,
        exclusions_path=exclusions, runs_root=None, fx_lookup=fx_lookup,
    )
    assert "ENTERPRISE VALUE IS BUILT HERE, NOT READ" in run.report
    assert "ONE price date per row" in run.report
    assert "enterprise_value_vendor_memo" in run.report
    assert "TWO PRICES FROM DIFFERENT DAYS" not in run.report


def test_the_yield_is_struck_on_the_snapshots_settled_close(fx_chain, tmp_path: Path):
    """Rule 8 through the whole chain: the vendor's quote at the fetch is
    80.0 and the snapshot's settled close is 75.0. 4,800 / 80 = 60 shares,
    re-priced at 75.0 = 4,500 -- not the 4,800 the vendor's marketCap says
    and not the 5,000 its enterpriseValue says."""
    universe, root, exclusions = fx_chain
    run = screen.rank(
        as_of=AS_OF, universe_dir=universe, snapshot_root=root,
        exclusions_path=exclusions, runs_root=tmp_path / "runs", fx_lookup=fx_lookup,
    )
    (volvo,) = run.result.main
    assert volvo.scored.implied_shares == pytest.approx(60.0)
    assert volvo.scored.market_cap_settled == pytest.approx(4_500.0)
    rate = volvo.scored.fx_rate
    assert volvo.scored.enterprise_value == pytest.approx(4_500.0 * rate + 300.0 - 100.0)
    rows = list(csv.DictReader(run.ranking_path.open(encoding="utf-8")))
    row = next(r for r in rows if r["ticker"] == "VOLV-B.ST")
    assert row["settled_close_date"] == AS_OF.isoformat()
    assert float(row["settled_close"]) == 75.0
    assert float(row["fetch_day_price"]) == 80.0
    assert float(row["enterprise_value_vendor_memo"]) == 5000.0
    assert row["net_debt_date"] == "2026-08-22"


def test_the_rank_report_says_it_is_the_only_ordering_and_not_advice(chain, tmp_path: Path):
    universe, root, exclusions = chain
    run = screen.rank(
        as_of=AS_OF, universe_dir=universe, snapshot_root=root,
        exclusions_path=exclusions, runs_root=None, fx_lookup=fx_lookup,
    )
    assert "ONLY ORDERING" in run.report.upper()
    assert "not a" in run.report and "recommendation" in run.report
    assert "phase 6" in run.report


def test_the_rank_report_carries_the_look_ahead_banner(chain):
    universe, root, exclusions = chain
    run = screen.rank(
        as_of=AS_OF, universe_dir=universe, snapshot_root=root,
        exclusions_path=exclusions, runs_root=None, fx_lookup=fx_lookup,
    )
    assert "LOOK-AHEAD WARNING" in run.report


def test_rank_writes_nothing_to_the_watchlist(chain, tmp_path: Path):
    import ast as _ast

    source = Path("vss/screen.py").read_text(encoding="utf-8")
    tree = _ast.parse(source)
    (func,) = [n for n in _ast.walk(tree)
               if isinstance(n, _ast.FunctionDef) and n.name == "rank"]
    names = {n.id for n in _ast.walk(func) if isinstance(n, _ast.Name)}
    names |= {n.attr for n in _ast.walk(func) if isinstance(n, _ast.Attribute)}
    for forbidden in ("load_watchlist", "compute_mbp", "mbp", "fv_base"):
        assert forbidden not in names


def test_cli_parses_the_rank_flag():
    args = build_parser().parse_args(["screen", "--rank", "--asof", "2026-08-21"])
    assert args.rank and not args.filter2
    assert not args.write_pipeline and args.top == 5


def test_cli_parses_the_pipeline_flags():
    args = build_parser().parse_args(
        ["screen", "--rank", "--write-pipeline", "--top", "3", "--dry-run"])
    assert args.write_pipeline and args.top == 3 and args.dry_run


def test_rank_collapses_share_classes_before_ranking(chain, tmp_path: Path):
    universe, root, exclusions = chain
    run = screen.rank(
        as_of=AS_OF, universe_dir=universe, snapshot_root=root,
        exclusions_path=exclusions, runs_root=None, fx_lookup=fx_lookup,
    )
    assert "ONE COMPANY, TWO LISTINGS" in run.report
    assert "MEASURED, never guessed from the ticker string" in run.report


def test_the_rank_report_says_the_yield_only_names_are_not_written(chain):
    universe, root, exclusions = chain
    run = screen.rank(
        as_of=AS_OF, universe_dir=universe, snapshot_root=root,
        exclusions_path=exclusions, runs_root=None, fx_lookup=fx_lookup,
    )
    assert "NOT WRITTEN TO THE WATCHLIST" in run.report
    assert "meaningful construct" in run.report


def test_write_pipeline_is_off_unless_asked(chain, tmp_path: Path):
    universe, root, exclusions = chain
    run = screen.rank(
        as_of=AS_OF, universe_dir=universe, snapshot_root=root,
        exclusions_path=exclusions, runs_root=None, fx_lookup=fx_lookup,
    )
    assert run.write_result is None
    assert "nothing was written to config/watchlist.yaml" in run.report


# --- CLI -------------------------------------------------------------------


def test_cli_parses_the_screen_flags():
    args = build_parser().parse_args(
        ["screen", "--snapshot-only", "--asof", "2026-08-21", "--tier", "A",
         "--tier", "B", "--batch-size", "25", "--limit", "10"]
    )
    assert args.command == "screen"
    assert args.snapshot_only and args.asof == "2026-08-21"
    assert args.tier == ["A", "B"] and args.batch_size == 25 and args.limit == 10


def test_cli_parses_the_phase3_flags():
    args = build_parser().parse_args(
        ["screen", "--fundamentals", "--asof", "2026-08-21"]
    )
    assert args.fundamentals and not args.filter2
    args = build_parser().parse_args(["screen", "--filter2", "--asof", "2026-08-21"])
    assert args.filter2 and not args.fundamentals


def test_cli_parses_the_filter1_flags():
    args = build_parser().parse_args(
        ["screen", "--filter1", "--asof", "2026-07-27",
         "--from-snapshot", "2026-08-21", "--exclusions", "x.csv"]
    )
    assert args.filter1 and args.asof == "2026-07-27"
    assert args.from_snapshot == "2026-08-21" and args.exclusions == "x.csv"


def test_screen_without_a_mode_explains_itself_and_fails(capsys, tmp_path: Path):
    code = screen.run_screen(
        universe_report_only=False, snapshot_only_flag=False, filter1_flag=False, as_of=AS_OF,
        universe_dir=tmp_path, tiers=("A",), snapshot_root=tmp_path,
        batch_size=50, limit=None,
    )
    assert code == 2
    assert "--filter1" in capsys.readouterr().err


def test_a_broken_universe_exits_with_a_code_not_a_traceback(tmp_path: Path):
    directory = tmp_path / "u"
    directory.mkdir()
    (directory / "broken.csv").write_text("nope\n", encoding="utf-8")
    (directory / "instrument_types.yaml").write_text(
        "include: {}\nexclude: {}\n", encoding="utf-8")
    code = screen.run_screen(
        universe_report_only=True, snapshot_only_flag=False, filter1_flag=False, as_of=AS_OF,
        universe_dir=directory, tiers=("A",), snapshot_root=tmp_path,
        batch_size=50, limit=None,
    )
    assert code == 2


# --- standing rules --------------------------------------------------------


def test_framework_constants_are_imported_from_rules_never_redefined():
    assert screen.DISLOCATION_MIN is rules.DISLOCATION_MIN
    assert screen.DISLOCATION_MAX is rules.DISLOCATION_MAX
    assert screen.MAX_CLOSE_AGE_TRADING_DAYS is rules.MAX_CLOSE_AGE_TRADING_DAYS
    for name in SCREENER_MODULES:
        source = Path(name).read_text(encoding="utf-8")
        assert "DISLOCATION_MIN =" not in source, f"{name} redefines a FRAMEWORK constant"
        assert "MAX_CLOSE_AGE_TRADING_DAYS =" not in source, \
            f"{name} redefines the staleness gate"


def test_the_staleness_gate_is_the_one_rules_py_owns():
    from vss import prices

    assert prices.stale_close_blocker is rules.stale_close_blocker


def test_rsi_and_sma_are_never_filters_and_the_reason_stays_on_the_record():
    source = Path("vss/screen.py").read_text(encoding="utf-8")
    assert "RSI AND SMA50 ARE FIELDS. THEY ARE NEVER FILTERS." in source
    assert "2026-07-27" in source and "SAP" in source
    for name in SCREENER_MODULES:
        text = Path(name).read_text(encoding="utf-8")
        for forbidden in ("rsi14 >", "rsi14 <", "sma50 >", "sma50 <", "rsi >", "rsi <"):
            assert forbidden not in text, f"{name} appears to filter on {forbidden!r}"


def test_the_screener_never_touches_the_watchlist_or_prices_a_position():
    """No path to watchlist.yaml, no buy price, no fair value.

    Phase 1 writes files under data/ and prints to stdout. PIPELINE writing
    is phase 6, and even then it must carry neither mbp nor fv_base.
    """
    import ast as _ast

    for name in SCREENER_MODULES:
        source = Path(name).read_text(encoding="utf-8")
        tree = _ast.parse(source)
        # Identifiers only. A report string may SAY that nothing is written to
        # config/watchlist.yaml -- that sentence is the promise, not a breach
        # of it -- so the check is on what the code touches.
        names = {n.id for n in _ast.walk(tree) if isinstance(n, _ast.Name)}
        names |= {n.attr for n in _ast.walk(tree) if isinstance(n, _ast.Attribute)}
        imported = set()
        for node in _ast.walk(tree):
            if isinstance(node, _ast.ImportFrom):
                imported |= {a.name for a in node.names}
            elif isinstance(node, _ast.Import):
                imported |= {a.name for a in node.names}
        touched = names | imported
        if name == "vss/pipeline.py":
            # Phase 6 is the ONE module allowed to write the watchlist, and it
            # is held to a different rule: it may name the file and re-parse
            # it, and it may not produce a price. FORBIDDEN_KEYS is its own
            # guard list, enforced in tests/test_pipeline.py.
            assert "compute_mbp" not in touched
            assert "MBP_TIER_MULTIPLIER" not in touched
            continue

        forbidden = ["load_watchlist", "WatchlistEntry", "compute_mbp",
                     "MBP_TIER_MULTIPLIER", "mbp", "fv_base"]
        if name == "vss/screen.py":
            # The orchestrator may hand a path through to phase 6. What it may
            # not do is reach the watchlist itself -- so attribute access on
            # the pipeline module is allowed and a direct import is not.
            reached = {n.attr for n in _ast.walk(tree)
                       if isinstance(n, _ast.Attribute)
                       and isinstance(n.value, _ast.Name)
                       and n.value.id == "pipeline_step"}
            touched = touched - reached
        else:
            forbidden.append("WATCHLIST_PATH")
        for item in forbidden:
            assert item not in touched, f"{name} touches {item}"
        assert ".config" not in {
            node.module for node in _ast.walk(tree)
            if isinstance(node, _ast.ImportFrom) and node.module
        }, f"{name} imports the watchlist loader"
        # And no code path may open the watchlist, whatever it is called.
        opened = [n.value for n in _ast.walk(tree)
                  if isinstance(n, _ast.Constant) and isinstance(n.value, str)
                  and n.value.endswith("watchlist.yaml")]
        assert not opened, f"{name} names the watchlist as a path: {opened}"


def test_no_ai_in_the_screener():
    for name in SCREENER_MODULES:
        source = Path(name).read_text(encoding="utf-8").lower()
        for forbidden in ("deepseek", "openai", "anthropic", "llm"):
            assert forbidden not in source, f"{name} mentions {forbidden}"


def test_insider_data_is_not_a_ranking_input_yet():
    for name in SCREENER_MODULES:
        source = Path(name).read_text(encoding="utf-8").lower()
        assert "insider" not in source and "insyn" not in source


# --- L5: a cross-dated replay is named, not refused -------------------------


def test_a_replay_into_another_date_is_called_CROSS_DATED():
    """REPRODUCIBLE was true and misleading at once: the run repeats exactly
    AND pairs one day's rates with another day's prices. The manifest knew
    which day it was; until 2026-08-23 nothing asked it."""
    from datetime import date

    from vss.fx import FxTable, Rate
    from vss.screen import _fx_reproducibility

    table = FxTable()
    table.rates["SEK->USD"] = Rate("SEK->USD", 0.1055, date(2026, 8, 21), "x")
    said = _fx_reproducibility(date(2026, 7, 27), table, "m.json", date(2026, 8, 21))
    assert "REPRODUCIBLE, AND CROSS-DATED" in said
    assert "2026-08-21" in said and "2026-07-27" in said
    assert "Nothing is refused" in said, "the flag must name, not block"


def test_a_replay_on_its_own_date_is_just_REPRODUCIBLE():
    from datetime import date

    from vss.fx import FxTable, Rate
    from vss.screen import _fx_reproducibility

    table = FxTable()
    table.rates["SEK->USD"] = Rate("SEK->USD", 0.1055, date(2026, 8, 21), "x")
    said = _fx_reproducibility(date(2026, 8, 21), table, "m.json", date(2026, 8, 21))
    assert "CROSS-DATED" not in said
    assert "REPRODUCIBLE -- rates replayed" in said


def test_a_manifest_with_no_date_is_reported_as_uncheckable():
    """Absence of the field is a reason to say so, not to assume agreement."""
    from datetime import date

    from vss.fx import FxTable, Rate
    from vss.screen import _fx_reproducibility

    table = FxTable()
    table.rates["SEK->USD"] = Rate("SEK->USD", 0.1055, date(2026, 8, 21), "x")
    said = _fx_reproducibility(date(2026, 7, 27), table, "m.json", None)
    assert "could not be checked" in said
    assert "CROSS-DATED" not in said


# --- E12 through --write-pipeline (build item 5) -----------------------------


def test_write_pipeline_freezes_the_drawdown_and_the_peak_date(fx_chain, tmp_path: Path):
    """The written entry carries dd_at_entry and peak_date -- the drawdown
    filter 1 measured and the session the 52-week closing high was set on
    -- and the real loader reads them back as the pair E12 stores."""
    from vss.config import load_watchlist

    universe, root, exclusions = fx_chain
    watchlist = tmp_path / "watchlist.yaml"
    watchlist.write_text("tickers:\n  - ticker: SAP.DE\n    name: SAP SE\n"
                         "    currency: EUR\n    status: HELD\n    fv_base: 185\n    fv_bull: 259\n"
                         "    tier: 1\n    stop_price: 165\n", encoding="utf-8")
    run = screen.rank(
        as_of=AS_OF, universe_dir=universe, snapshot_root=root,
        exclusions_path=exclusions, runs_root=tmp_path / "runs", fx_lookup=fx_lookup,
        write_pipeline=True, top=5, watchlist_path=watchlist,
        now=datetime(2026, 8, 22, 18, 0),
    )
    (candidate,) = run.upstream.upstream.result.candidates
    assert candidate.high_52w_date is not None
    (written,) = run.write_result.written
    assert written.dd_at_entry == pytest.approx(candidate.drawdown)
    assert written.peak_date == candidate.high_52w_date
    loaded = {e.ticker: e for e in load_watchlist(watchlist)}
    assert loaded["VOLV-B.ST"].dd_at_entry == pytest.approx(candidate.drawdown)
    assert loaded["VOLV-B.ST"].peak_date == candidate.high_52w_date
    # And filter 1's own table carries the date beside the high (E11).
    table = screen.filter1(
        as_of=AS_OF, universe_dir=universe, snapshot_root=root,
        exclusions_path=exclusions, runs_root=tmp_path / "runs",
    ).candidates_path
    (row,) = csv.DictReader(table.open(encoding="utf-8"))
    assert row["high_52w_date"] == candidate.high_52w_date.isoformat()


# --- E49: the fundamentals fetch carries the earlier-dated store in ---------


def _quarterly_reader(quarters: dict):
    frame = pd.DataFrame({pd.Timestamp(d): [v, 20.0] for d, v in quarters.items()},
                         index=["Total Revenue", "EBIT"])

    def reader(ticker):
        return _info(), {**_rankable_statements(), "income_quarterly": frame}, 5
    return reader


def test_e49_the_fundamentals_fetch_carries_in_the_earlier_dated_store(
        universe: Path, tmp_path: Path, exclusions: Path):
    from vss import snapshot as store
    from vss.fundamentals import fetch_one

    root = prepare(universe, tmp_path, {"VOLV-B.ST": dislocated()})
    earlier = store.fundamentals_path(date(2026, 8, 14), root)
    old = fetch_one("VOLV-B.ST", as_of=date(2026, 8, 14), sleep=lambda _: None,
                    reader=_quarterly_reader({"2025-03-31": 100.0, "2025-06-30": 110.0}))
    store.write_fundamentals(earlier, as_of=date(2026, 8, 14),
                             fetched_at=datetime(2026, 8, 14, 16, 0),
                             records=[old], requests=5)

    run = screen.fetch_fundamentals(
        as_of=AS_OF, universe_dir=universe, snapshot_root=root,
        exclusions_path=exclusions, sleep=lambda _: None,
        reader=_quarterly_reader({"2025-06-30": 111.0, "2025-09-30": 120.0,
                                  "2025-12-31": 130.0, "2026-03-31": 140.0}),
        now=datetime(2026, 8, 22, 16, 0),
    )
    (stored,) = store.read_fundamentals(run.path)
    assert stored.quarterly_series("Total Revenue") == [
        (date(2025, 3, 31), 100.0), (date(2025, 6, 30), 111.0), (date(2025, 9, 30), 120.0),
        (date(2025, 12, 31), 130.0), (date(2026, 3, 31), 140.0),
    ], "five quarters from two fetches of four and two"
    assert "RETENTION (E49)" in run.report
    assert "carried in from  1 earlier store(s): 2026-08-14" in run.report
    assert "THE STORE AFTER RETENTION" in run.report


def test_e49_the_net_debt_date_is_each_records_own_fetch(
        universe: Path, tmp_path: Path, exclusions: Path):
    """One store, two fetches: the name fetched in the first carries the
    first's date on its net-debt legs, not the manifest's latest."""
    from vss import snapshot as store
    from vss.fundamentals import fetch_one

    root = prepare(universe, tmp_path, {"VOLV-B.ST": dislocated()})
    screen.fetch_fundamentals(
        as_of=AS_OF, universe_dir=universe, snapshot_root=root,
        exclusions_path=exclusions, sleep=lambda _: None,
        reader=lambda t: (_info(), _rankable_statements(), 5),
        now=datetime(2026, 8, 22, 16, 0),
    )
    other = fetch_one("OTHER.ST", as_of=AS_OF, sleep=lambda _: None,
                      reader=lambda t: (_info(), _rankable_statements(), 5))
    store.write_fundamentals(store.fundamentals_path(AS_OF, root), as_of=AS_OF,
                             fetched_at=datetime(2026, 8, 25, 9, 0),
                             records=[other], requests=5)
    assert store.read_fundamentals_manifest(store.fundamentals_path(AS_OF, root))["fetched_at"] \
        == "2026-08-25T09:00:00"
    run = screen.rank(
        as_of=AS_OF, universe_dir=universe, snapshot_root=root,
        exclusions_path=exclusions, runs_root=None, fx_lookup=fx_lookup,
    )
    (volvo,) = run.result.main
    assert volvo.scored.inputs.net_debt_date == date(2026, 8, 22)
    assert "more than one fetch (E49)" in run.report


# --- E51 and E52 through the chain -----------------------------------------


def _pharma_list(tmp_path: Path, **blocks) -> Path:
    import yaml
    path = tmp_path / "pharma.yaml"
    document = {"industries": [], "sectors": [], "tickers": [], "exempt": []}
    document.update(blocks)
    path.write_text(yaml.safe_dump(document), encoding="utf-8")
    return path


def test_e51_step_0_removes_the_name_and_the_report_records_why(
        universe: Path, tmp_path: Path, exclusions: Path):
    """E51 is a step-0 exclusion, so the name never reaches a price series
    and the reason is in the run report rather than in someone's head."""
    root = prepare(universe, tmp_path, {"SAP.DE": dislocated(),
                                        "VOLV-B.ST": dislocated()})
    listed = _pharma_list(
        tmp_path, tickers=[{"ticker": "VOLV-B.ST", "company": "Volvo AB"}])
    run = screen.filter1(
        as_of=AS_OF, universe_dir=universe, snapshot_root=root,
        exclusions_path=exclusions, pharma_biotech_path=listed,
        runs_root=tmp_path / "runs",
    )
    assert [c.ticker for c in run.result.candidates] == []
    assert [h.ticker for h in run.circle.hits] == ["VOLV-B.ST"]
    assert "THE CIRCLE OF COMPETENCE (E51)" in run.report
    assert "VOLV-B.ST" in run.report and "owner list" in run.report
    # And the report states what the STRING limb could not see.
    assert "WHAT THE STRING LIMB COULD NOT SEE" in run.report


def test_e51_without_a_match_the_chain_is_unchanged(
        universe: Path, tmp_path: Path, exclusions: Path):
    root = prepare(universe, tmp_path, {"SAP.DE": dislocated(),
                                        "VOLV-B.ST": dislocated()})
    run = screen.filter1(
        as_of=AS_OF, universe_dir=universe, snapshot_root=root,
        exclusions_path=exclusions, pharma_biotech_path=_pharma_list(tmp_path),
        runs_root=tmp_path / "runs",
    )
    assert [c.ticker for c in run.result.candidates] == ["VOLV-B.ST"]
    assert run.circle.hits == []


def test_e52_a_short_series_is_removed_at_filter_1_and_the_report_says_so(
        universe: Path, tmp_path: Path, exclusions: Path):
    root = prepare(universe, tmp_path, {"SAP.DE": dislocated(),
                                        "VOLV-B.ST": dislocated(days=800)})
    run = screen.filter1(
        as_of=AS_OF, universe_dir=universe, snapshot_root=root,
        exclusions_path=exclusions, runs_root=tmp_path / "runs",
    )
    assert [c.ticker for c in run.result.candidates] == []
    age = {t.step: t for t in run.tallies}["listing_age"]
    assert age.rejected_on_missing == 1 and age.rejected_on_value == 0
    assert "THE LISTING-AGE FLOOR (E52)" in run.report
    assert "52-week coverage bar" in run.report


# --- E63: the 52-week low is a FIELD, never a filter, never a ranking input --


def test_e63_the_52_week_low_is_never_a_filter_and_never_reaches_the_ranking_key():
    """The same guard the RSI/SMA rule gets, for the other end of the window.

    Reported on every row, read as a pass/fail input by nothing, and named
    by nothing in the ranking key or the PIPELINE writer. Whether a
    threshold is ever drawn on it is B41, open -- decided on a month of the
    record, not in code.
    """
    import ast as _ast

    source = Path("vss/screen.py").read_text(encoding="utf-8")
    assert "E63" in source and "B41" in source
    for name in SCREENER_MODULES:
        text = Path(name).read_text(encoding="utf-8")
        for forbidden in ("pct_above_52w_low >", "pct_above_52w_low <",
                          "pct_above_52w_low >=", "pct_above_52w_low <=",
                          "low_52w >", "low_52w <"):
            assert forbidden not in text, f"{name} appears to filter on {forbidden!r}"
    for name in ("vss/ranking.py", "vss/pipeline.py", "vss/rules.py"):
        tree = _ast.parse(Path(name).read_text(encoding="utf-8"))
        names = {n.id for n in _ast.walk(tree) if isinstance(n, _ast.Name)}
        names |= {n.attr for n in _ast.walk(tree) if isinstance(n, _ast.Attribute)}
        assert not {"low_52w", "low_52w_date", "pct_above_52w_low"} & names, \
            f"{name} names an E63 field"


def test_e63_the_low_travels_to_both_csvs_and_both_reports_beside_the_drawdown(
        chain, tmp_path: Path):
    universe, root, exclusions = chain
    first = screen.filter1(
        as_of=AS_OF, universe_dir=universe, snapshot_root=root,
        exclusions_path=exclusions, runs_root=tmp_path / "runs",
    )
    header = first.candidates_path.read_text(encoding="utf-8").splitlines()[0]
    assert ",drawdown,low_52w,low_52w_date,pct_above_52w_low," in header
    assert "vs52wL" in first.report and "E63" in first.report

    import csv as _csv

    run = screen.rank(
        as_of=AS_OF, universe_dir=universe, snapshot_root=root,
        exclusions_path=exclusions, runs_root=tmp_path / "runs",
        fx_lookup=fx_lookup,
    )
    text = run.ranking_path.read_text(encoding="utf-8")
    assert ",sector,drawdown,pct_above_52w_low,low_52w,low_52w_date," in text.splitlines()[0]
    saved = list(_csv.DictReader(text.splitlines()))
    assert saved
    for saved_row in saved:
        for column in ("drawdown", "pct_above_52w_low", "low_52w", "low_52w_date"):
            assert saved_row[column] != "", f"{saved_row['ticker']} has no {column}"
    assert "vs52wL" in run.report and "E63" in run.report


# --- E96: the commodity-price limb ------------------------------------------


def test_e96_config_carries_no_bare_sector_string():
    """E96 refuses `Energy` and `Basic Materials` for the same reason E51
    refuses `Healthcare`: they would take utilities, renewables, specialty
    chemicals and building materials with them."""
    config = filters.load_circle_of_competence(
        filters.COMMODITY_PRICE_PATH, ruling="E96", label="commodity price",
        step=filters.STEP_COMMODITY_PRICE)
    assert config.sectors == frozenset()
    assert "Oil & Gas E&P" in config.industries
    assert "Steel" in config.industries
    assert "Marine Shipping" in config.industries
    # and the two whole sectors are NOT in it, by string or otherwise
    assert "Energy" not in config.industries
    assert "Basic Materials" not in config.industries


def test_e96_does_not_reach_semiconductors_or_utilities_or_chemicals():
    """Semiconductors were CONSIDERED AND DECLINED by the owner 2026-08-31
    (E96.1 part 3) -- not overlooked. MU stays in the ranking.

    A future session finding `Semiconductors` absent here must read E96.1
    and not add it as a fix; the config file says so at the point of
    absence, and this test says so too."""
    config = filters.load_circle_of_competence(
        filters.COMMODITY_PRICE_PATH, ruling="E96", label="commodity price",
        step=filters.STEP_COMMODITY_PRICE)
    for string in ("Semiconductors", "Semiconductor Equipment & Materials",
                   "Utilities - Renewable", "Utilities - Regulated Electric",
                   "Specialty Chemicals", "Chemicals", "Building Materials",
                   "Oil & Gas Integrated", "Oil & Gas Midstream",
                   "Oil & Gas Refining & Marketing"):
        assert string not in config.industries, string
    assert "MU" not in config.tickers


def test_e96_carries_the_owners_two_exemptions_with_reasons():
    """E96.1: TPL and TGS.OL, written by the owner 2026-08-31. The owner
    ticker list stays empty -- both blocks are his, and a session writes
    neither."""
    config = filters.load_circle_of_competence(
        filters.COMMODITY_PRICE_PATH, ruling="E96", label="commodity price",
        step=filters.STEP_COMMODITY_PRICE)
    assert config.tickers == frozenset()
    assert config.exempt == frozenset({"TPL", "TGS.OL"})
    # A reason beside every exemption is what the block exists for.
    assert "royalt" in config.exempt_reasons["TPL"].lower()
    assert "seismic" in config.exempt_reasons["TGS.OL"].lower()


def test_an_exempt_name_is_kept_and_reported_not_removed():
    from vss.universe import Instrument

    config = filters.load_circle_of_competence(
        filters.COMMODITY_PRICE_PATH, ruling="E96", label="commodity price",
        step=filters.STEP_COMMODITY_PRICE)
    tpl = Instrument(ticker_yahoo="TPL", ticker_lokal="TPL", isin=None,
                     namn="Texas Pacific Land", marknad="US", tier="A",
                     listdatum=None, valuta="USD", instrumenttyp="share")
    out = filters.apply_circle_of_competence(
        [tpl], config, industry_of={"TPL": "Oil & Gas E&P"})
    assert [i.ticker_yahoo for i in out.kept] == ["TPL"]
    assert out.rejections == []
    assert [h.ticker for h in out.exempted] == ["TPL"]


def test_the_smelters_stay_in_the_limb():
    """E96.1: no partial exemption. Downstream or not, the revenue is the
    LME price, and sizing 'how much downstream is enough' is the guess E96
    exists to refuse."""
    config = filters.load_circle_of_competence(
        filters.COMMODITY_PRICE_PATH, ruling="E96", label="commodity price",
        step=filters.STEP_COMMODITY_PRICE)
    assert "BOL.ST" not in config.exempt
    assert "NHY.OL" not in config.exempt
    assert "Aluminum" in config.industries
    assert "Other Industrial Metals & Mining" in config.industries


def test_e96_rejection_names_its_own_ruling_not_e51s():
    """A name removed for a commodity price must never read as one removed
    for a clinical trial."""
    config = filters.CircleConfig(
        industries=frozenset({"Steel"}), ruling="E96",
        label="commodity price", step=filters.STEP_COMMODITY_PRICE)
    from vss.universe import Instrument

    instrument = Instrument(
        ticker_yahoo="STLD", ticker_lokal="STLD", isin=None,
        namn="Steel Dynamics", marknad="US", tier="A", listdatum=None,
        valuta="USD", instrumenttyp="share")
    out = filters.apply_circle_of_competence(
        [instrument], config, industry_of={"STLD": "Steel"})
    assert out.kept == []
    assert len(out.rejections) == 1
    reason = out.rejections[0].reason
    assert "E96" in reason and "E51" not in reason
    assert out.rejections[0].step == "commodity_price"
    assert out.tally.step == "commodity_price"


def test_e51_and_e96_lists_do_not_mix():
    """Two grounds, two files. A pharma string must not remove a miner."""
    pharma = filters.load_circle_of_competence(filters.PHARMA_BIOTECH_PATH)
    commodity = filters.load_circle_of_competence(
        filters.COMMODITY_PRICE_PATH, ruling="E96", label="commodity price",
        step=filters.STEP_COMMODITY_PRICE)
    assert not (pharma.industries & commodity.industries)
    assert pharma.ruling == "E51" and commodity.ruling == "E96"
