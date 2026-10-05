"""End-to-end verdict matrix against frozen price data.

Exercises every verdict path through the real pipeline -- config loading,
cache read, metric computation, rule evaluation -- with prices FROZEN at
2026-08-20 and no network access whatsoever.

The manual fields in the fixture watchlist are SYNTHETIC: fabricated to
place each close on a specific side of a threshold. They are not
valuations. See the fixture header.

Why frozen: the thresholds were reverse-engineered from that evening's
closes. Re-fetching would make a market move break these expectations
instead of a code change, which is the opposite of a regression test.
"""

from datetime import date, datetime
from pathlib import Path

import pytest

from vss import rules as R
from vss.config import load_watchlist
from vss.fetch import SOURCE_CACHE, get_history
from vss.runner import build_row

FIXTURE = Path(__file__).resolve().parent / "fixtures" / "verdict-matrix"
WATCHLIST = FIXTURE / "watchlist.yaml"
PRICES = FIXTURE / "prices"

#: Vendor price data, not redistributed (tests/fixtures/VENDOR-DATA.json).
pytestmark = pytest.mark.skipif(
    not (PRICES / "MSFT.csv").exists(),
    reason="needs the verdict-matrix prices: fetch your own copy with "
           "tools/fetch_test_fixtures.py")

#: The evening the prices were captured. Passed as as_of so the staleness
#: gate measures against the snapshot, not against the day the test runs.
FROZEN_AS_OF = date(2026, 8, 20)
FROZEN_NOW = datetime(2026, 8, 20, 22, 30)

#: ticker -> verdict codes that MUST be present.
#: E90 (2026-08-30) moved every threshold: base x 0.85/0.75/0.65 in place
#: of the fixture's original E28-era tuning. The closes are frozen, so the
#: sides some of them sit on flipped -- UNA.AS from APPROACHING to
#: AT_BELOW, SAP.DE and HNSA.ST gained APPROACHING -- and the expectations
#: below pin the NEW arithmetic on the same frozen prices.
EXPECTED: dict[str, set[str]] = {
    "MSFT": {R.AT_BELOW_MBP},
    "UNA.AS": {R.AT_BELOW_MBP},
    "SAP.DE": {R.STOP_BREACHED, R.APPROACHING_MBP},
    "HNSA.ST": {R.OUTSIDE_BAND, R.APPROACHING_MBP},
    "NKE": {R.NO_ACTION},
    "MC.PA": {R.STOP_BREACHED, R.AT_BELOW_MBP},
}

#: Drawdown is computed from price history, so no manual field can tune
#: it. MSFT (11.2%) and UNA.AS (13.7%) sit below the 0.15 floor and
#: therefore also carry OUTSIDE_BAND. Recorded rather than worked around.
ALSO_EXPECTED: dict[str, set[str]] = {
    "MSFT": {R.OUTSIDE_BAND},
    "UNA.AS": {R.OUTSIDE_BAND},
}


@pytest.fixture(scope="module")
def rows() -> dict:
    """Every fixture ticker assessed from frozen data. Never hits the network."""
    built = {}
    for entry in load_watchlist(WATCHLIST):
        fetched = get_history(
            entry.ticker, PRICES, now=FROZEN_NOW, allow_network=False, write=False
        )
        # allow_network=False cannot reach yfinance; if a CSV were missing
        # this would be SOURCE_NONE and the ticker would blank out.
        assert fetched.source == SOURCE_CACHE, f"{entry.ticker}: frozen CSV missing"
        assert fetched.ok, f"{entry.ticker}: frozen CSV unreadable"
        built[entry.ticker] = build_row(entry, fetched, FROZEN_AS_OF)
    return built


def codes(row) -> set[str]:
    return {v.code for v in row.assessment.verdicts}


def test_fixture_covers_every_ticker(rows):
    assert set(rows) == set(EXPECTED)


@pytest.mark.parametrize("ticker,expected", sorted((t, s) for t, s in EXPECTED.items()))
def test_expected_verdicts_fire(rows, ticker, expected):
    assert expected <= codes(rows[ticker]), (
        f"{ticker}: expected {sorted(expected)}, got {sorted(codes(rows[ticker]))}"
    )


@pytest.mark.parametrize("ticker,extra", sorted((t, s) for t, s in ALSO_EXPECTED.items()))
def test_drawdown_driven_extras_are_recorded(rows, ticker, extra):
    """These ride along because real drawdown is untunable, not by accident."""
    assert extra <= codes(rows[ticker])


def test_exact_verdict_sets(rows):
    """Nothing fires beyond what is documented -- no silent extra verdicts."""
    for ticker, row in rows.items():
        want = EXPECTED[ticker] | ALSO_EXPECTED.get(ticker, set())
        assert codes(row) == want, f"{ticker}: unexpected verdict set"


def test_every_verdict_path_is_exercised(rows):
    fired = {c for row in rows.values() for c in codes(row)}
    assert {
        R.AT_BELOW_MBP, R.APPROACHING_MBP, R.STOP_BREACHED,
        R.OUTSIDE_BAND, R.NO_ACTION,
    } <= fired


def test_no_ticker_is_blocked(rows):
    """A blocked ticker emits no verdict, which would void the whole matrix."""
    assert [t for t, r in rows.items() if r.assessment.blocked] == []


def test_collect_all_holds_on_real_prices(rows):
    """MC.PA carries a stop breach AND a buy signal simultaneously.

    Under first-match-wins only one would survive, and the buy signal
    would vanish silently.
    """
    assert codes(rows["MC.PA"]) == {R.STOP_BREACHED, R.AT_BELOW_MBP}
    assert len(rows["MC.PA"].assessment.verdicts) == 2


def test_prices_are_actually_frozen(rows):
    """Guards the snapshot itself: these closes must never drift."""
    frozen_closes = {
        "MSFT": 481.15, "UNA.AS": 54.30, "SAP.DE": 185.64,
        "HNSA.ST": 40.64, "NKE": 40.21, "MC.PA": 443.10,
    }
    for ticker, close in frozen_closes.items():
        assert rows[ticker].metrics.last_close == pytest.approx(close, abs=0.005)
        assert rows[ticker].metrics.last_close_date == FROZEN_AS_OF


def test_mbp_derivations_hold(rows):
    """mbp = fv_base x E90 cushion (0.85 / 0.75 / 0.65), on the fixture's
    fabricated fv_base and tier per name."""
    expected_mbp = {
        "MSFT": 511.70, "UNA.AS": 56.31, "SAP.DE": 180.00,
        "HNSA.ST": 39.00, "NKE": 37.50, "MC.PA": 510.00,
    }
    for ticker, mbp in expected_mbp.items():
        assert rows[ticker].assessment.mbp == pytest.approx(mbp)


def test_matrix_never_touches_the_network(monkeypatch):
    """Hard proof of determinism: sabotage the fetcher, matrix still holds.

    If any part of this path reached yfinance, this would raise.
    """
    def forbidden(*args, **kwargs):
        raise AssertionError("network access from a frozen fixture")

    monkeypatch.setattr("vss.fetch.fetch_live", forbidden)

    for entry in load_watchlist(WATCHLIST):
        fetched = get_history(
            entry.ticker, PRICES, now=FROZEN_NOW, allow_network=False, write=False
        )
        row = build_row(entry, fetched, FROZEN_AS_OF)
        want = EXPECTED[entry.ticker] | ALSO_EXPECTED.get(entry.ticker, set())
        assert {v.code for v in row.assessment.verdicts} == want


def test_fixture_is_immune_to_the_calendar(rows):
    """as_of is frozen, so the staleness gate cannot expire the snapshot.

    Re-evaluated against a date months later, the frozen closes would be
    stale and every ticker would block -- which is why the test pins
    as_of rather than using today.
    """
    from datetime import timedelta

    entry = load_watchlist(WATCHLIST)[0]
    fetched = get_history(
        entry.ticker, PRICES, now=FROZEN_NOW, allow_network=False, write=False
    )
    much_later = build_row(entry, fetched, FROZEN_AS_OF + timedelta(days=90))
    assert much_later.assessment.blocked          # would break an unpinned test
    assert not rows[entry.ticker].assessment.blocked   # pinned as_of is fine
