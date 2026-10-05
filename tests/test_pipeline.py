"""Phase 6: writing PIPELINE entries into the live watchlist."""

from __future__ import annotations

from datetime import date, datetime
from pathlib import Path

import pytest

from vss.config import load_watchlist
from vss.pipeline import (
    FORBIDDEN_KEYS,
    Entry,
    PipelineError,
    backup_path,
    entries_from_ranking,
    existing_tickers,
    summary,
    write,
)

NOW = datetime(2026, 8, 22, 18, 0)

WATCHLIST = """# config/watchlist.yaml
#
# A hand-maintained file. These comments must survive a write.
tickers:
  - ticker: SAP.DE
    name: SAP SE
    currency: EUR
    status: HELD
    fv_bull: 259.0    # the exit test C4/E42 runs on (owner, 2026-09-20)
    fv_base: 185
    tier: 1
    stop_price: 165
    notes: "Held."
"""


def watchlist(tmp_path: Path) -> Path:
    path = tmp_path / "watchlist.yaml"
    path.write_text(WATCHLIST, encoding="utf-8")
    return path


def entry(ticker="TE.PA", name="Technip Energies", currency="EUR") -> Entry:
    return Entry(ticker, name, currency, "Screener 2026-08-21: rank 1 of 314.")


# --- the summary line ------------------------------------------------------


def test_the_summary_is_measured_and_carries_no_assessment():
    text = summary(
        ticker="BATS.L", rank=2, of=314, asof=date(2026, 8, 21),
        sector="Consumer Defensive", marknad="London", drawdown=0.274,
        operating_profitability=0.856, earnings_yield=0.0965, quote_currency="GBp",
    )
    for figure in ("rank 2 of 314", "Consumer Defensive", "London", "27.4%",
                   "85.6%", "9.7%"):
        assert figure in text
    for judgement in ("attractive", "cheap", "quality", "strong", "opportunity",
                      "undervalued", "buy at", "recommend"):
        assert judgement not in text.lower()
    assert "not a buy" in text


def test_the_summary_names_the_minor_unit_when_there_is_one():
    text = summary(ticker="BATS.L", rank=1, of=10, asof=date(2026, 8, 21),
                   sector="X", marknad="London", drawdown=0.2, operating_profitability=0.5,
                   earnings_yield=0.1, quote_currency="GBp")
    assert "GBp" in text and "MINOR unit" in text
    assert "must be in GBX, not GBP" in text


def test_a_pence_quoted_entry_stores_gbx_so_the_report_cannot_say_gbp(tmp_path: Path):
    """A pence figure labelled GBP invites a hundredfold error on a stop."""
    from vss.pipeline import entries_from_ranking

    class I:
        sector, quote_currency = "Consumer Defensive", "GBp"

    class S:
        ticker, operating_profitability, earnings_yield = "BATS.L", 0.856, 0.0965
        inputs = I()

    class R:
        scored = S()

    (built,) = entries_from_ranking([R()], asof=date(2026, 8, 21), top=1,
                                    names={"BATS.L": "BAT"}, markets={},
                                    drawdowns={}, total=314)
    assert built.currency == "GBX"
    assert built.currency.upper() == "GBX"

    path = watchlist(tmp_path)
    write([built], path=path, now=NOW, validate=load_watchlist)
    stored = next(e for e in load_watchlist(path) if e.ticker == "BATS.L")
    assert stored.currency == "GBX", "the loader turned it into pounds"


def test_an_ordinary_currency_adds_no_unit_note():
    text = summary(ticker="TE.PA", rank=1, of=10, asof=date(2026, 8, 21),
                   sector="Energy", marknad="Paris", drawdown=0.2, operating_profitability=0.5,
                   earnings_yield=0.1, quote_currency="EUR")
    assert "minor unit" not in text


def test_a_missing_figure_says_data_missing_rather_than_nothing():
    text = summary(ticker="X", rank=1, of=10, asof=date(2026, 8, 21),
                   sector=None, marknad=None, drawdown=None, operating_profitability=None,
                   earnings_yield=None, quote_currency=None)
    assert text.count("DATA MISSING") == 5


def test_the_summary_states_that_section_5_has_not_been_run():
    text = summary(ticker="X", rank=1, of=10, asof=date(2026, 8, 21), sector="X",
                   marknad="X", drawdown=0.2, operating_profitability=0.5, earnings_yield=0.1,
                   quote_currency="EUR")
    assert "No fv_base, no tier and no mbp" in text


def test_no_width_of_figures_can_fold_the_note_into_a_pseudo_key():
    """The note is a FOLDED scalar, so the wrap points move with the numbers.

    On 2026-08-22 a longer quality-leg sentence pushed the fold until a line
    began "mbp: section 5 has not been run". That is note CONTENT and YAML
    reads it correctly -- but the write guard scans the rendered text, refused
    the write, and was right to: a guard that reasoned about intent rather
    than text would be worth nothing.

    So the note must never take that shape at any figure width. This sweeps
    the widths instead of trusting one example.
    """
    import re
    from vss.pipeline import FORBIDDEN_KEYS

    for rank in (1, 12, 300):
        for sector in ("Healthcare", "Consumer Cyclical", "Communication Services"):
            for market in ("New York", "Stockholm", "London", "Paris", "Xetra"):
                for currency in ("USD", "GBp", "SEK"):
                    for value in (0.0, 0.07, 0.7431, 1.0115, 12.5):
                        entry = Entry("X.ST", "A Company", currency, summary(
                            ticker="X", rank=rank, of=325, asof=date(2026, 8, 21),
                            sector=sector, marknad=market, drawdown=value,
                            operating_profitability=value, earnings_yield=value,
                            quote_currency=currency,
                        ))
                        text = entry.to_yaml()
                        for forbidden in FORBIDDEN_KEYS:
                            hit = re.search(rf"^\s*{forbidden}\s*:", text, re.MULTILINE)
                            assert hit is None, (
                                f"{forbidden!r} folded to a line start at "
                                f"rank={rank} {sector}/{market}/{currency} "
                                f"value={value}: {text}"
                            )


# --- the entry -------------------------------------------------------------


def test_an_entry_is_pipeline_and_nothing_else():
    text = entry().to_yaml()
    assert "status: PIPELINE" in text
    for forbidden in FORBIDDEN_KEYS:
        assert f"{forbidden}:" not in text


def test_a_name_with_yaml_punctuation_is_quoted():
    text = Entry("X.ST", "Ericsson: B shares", "SEK", "note").to_yaml()
    assert 'name: "Ericsson: B shares"' in text


# --- writing ---------------------------------------------------------------


def test_a_write_appends_and_preserves_every_earlier_byte(tmp_path: Path):
    path = watchlist(tmp_path)
    before = path.read_text(encoding="utf-8")
    result = write([entry()], path=path, now=NOW)
    after = path.read_text(encoding="utf-8")
    assert after.startswith(before)
    assert "These comments must survive a write." in after
    assert "- ticker: TE.PA" in after
    assert len(result.written) == 1


def test_the_file_is_backed_up_before_a_byte_is_written(tmp_path: Path):
    path = watchlist(tmp_path)
    result = write([entry()], path=path, now=NOW)
    assert result.backup is not None and result.backup.exists()
    assert result.backup.read_text(encoding="utf-8") == WATCHLIST
    assert result.backup.name.endswith("bak-2026-08-22-pre-pipeline")


def test_an_existing_ticker_is_never_touched(tmp_path: Path):
    path = watchlist(tmp_path)
    result = write([entry("SAP.DE", "SAP SE", "EUR")], path=path, now=NOW)
    assert result.written == []
    assert result.skipped == [("SAP.DE", "already in the watchlist")]
    assert path.read_text(encoding="utf-8") == WATCHLIST


def test_a_duplicate_inside_one_batch_is_written_once(tmp_path: Path):
    path = watchlist(tmp_path)
    result = write([entry(), entry()], path=path, now=NOW)
    assert len(result.written) == 1
    assert path.read_text(encoding="utf-8").count("- ticker: TE.PA") == 1


def test_the_written_file_still_loads(tmp_path: Path):
    path = watchlist(tmp_path)
    write([entry(), entry("RKT.L", "Reckitt Benckiser Group PLC", "GBP")],
          path=path, now=NOW, validate=load_watchlist)
    entries = {e.ticker: e for e in load_watchlist(path)}
    assert entries["TE.PA"].status == "PIPELINE"
    assert entries["TE.PA"].fv_base is None
    assert entries["TE.PA"].tier is None
    assert entries["TE.PA"].stop_price is None


def test_the_written_entry_has_no_computed_buy_price(tmp_path: Path):
    from vss.rules import compute_mbp

    path = watchlist(tmp_path)
    write([entry()], path=path, now=NOW, validate=load_watchlist)
    written = next(e for e in load_watchlist(path) if e.ticker == "TE.PA")
    assert compute_mbp(written.fv_base, written.tier) is None


def test_a_write_that_breaks_the_file_is_rolled_back(tmp_path: Path):
    path = watchlist(tmp_path)

    def refuse(_):
        raise ValueError("bad entry")

    with pytest.raises(PipelineError, match="restored from"):
        write([entry()], path=path, now=NOW, validate=refuse)
    assert path.read_text(encoding="utf-8") == WATCHLIST


def test_a_dry_run_writes_nothing_and_makes_no_backup(tmp_path: Path):
    path = watchlist(tmp_path)
    result = write([entry()], path=path, now=NOW, dry_run=True)
    assert result.dry_run and len(result.written) == 1
    assert result.backup is None
    assert path.read_text(encoding="utf-8") == WATCHLIST


def test_writing_nothing_makes_no_backup(tmp_path: Path):
    path = watchlist(tmp_path)
    result = write([], path=path, now=NOW)
    assert result.backup is None
    assert path.read_text(encoding="utf-8") == WATCHLIST


def test_a_missing_watchlist_is_an_error(tmp_path: Path):
    with pytest.raises(PipelineError, match="no watchlist"):
        write([entry()], path=tmp_path / "nope.yaml", now=NOW)


def test_existing_tickers_are_read_without_parsing_yaml():
    assert existing_tickers(WATCHLIST) == {"SAP.DE"}


def test_the_backup_name_carries_the_date():
    assert backup_path(Path("config/watchlist.yaml"), NOW).name == \
        "watchlist.yaml.bak-2026-08-22-pre-pipeline"


# --- selection -------------------------------------------------------------


class FakeInputs:
    def __init__(self, sector, quote):
        self.sector = sector
        self.quote_currency = quote


class FakeScored:
    def __init__(self, ticker, operating_profitability, ey, sector="Technology",
                 quote="SEK"):
        self.ticker = ticker
        self.operating_profitability = operating_profitability
        self.earnings_yield = ey
        self.inputs = FakeInputs(sector, quote)


class FakeRanked:
    def __init__(self, scored):
        self.scored = scored


def test_only_the_top_n_of_the_both_legs_list_are_taken():
    ranked = [FakeRanked(FakeScored(t, 0.5, 0.1)) for t in ("A", "B", "C", "D", "E", "F")]
    out = entries_from_ranking(
        ranked, asof=date(2026, 8, 21), top=5, names={}, markets={},
        drawdowns={}, total=len(ranked),
    )
    assert [e.ticker for e in out] == ["A", "B", "C", "D", "E"]


def test_the_rank_in_the_note_is_the_position_in_that_list():
    ranked = [FakeRanked(FakeScored(t, 0.5, 0.1)) for t in ("A", "B")]
    out = entries_from_ranking(ranked, asof=date(2026, 8, 21), top=2,
                               names={"A": "Alpha"}, markets={"A": "Stockholm"},
                               drawdowns={"A": 0.3}, total=314)
    assert "rank 1 of 314" in out[0].notes
    assert "rank 2 of 314" in out[1].notes
    assert "not the universe" in out[0].notes
    assert out[0].name == "Alpha"
    assert out[1].name == "B"          # no name known: the ticker, never blank


# --- E12: the frozen Gate 1 reading is WRITTEN, as a pair (build item 5) ----


def test_a_written_entry_carries_dd_at_entry_and_peak_date_as_a_pair():
    text = Entry("X.ST", "X AB", "SEK", "note", dd_at_entry=0.1564,
                 peak_date=date(2025, 8, 22)).to_yaml()
    assert "    dd_at_entry: 0.1564\n" in text
    assert "    peak_date: 2025-08-22\n" in text
    assert text.index("status: PIPELINE") < text.index("dd_at_entry") < text.index("notes:")
    # One without the other is not written at all: config.py refuses the pair
    # half-recorded, and a frozen drawdown whose peak is unnamed is E11.
    half = Entry("X.ST", "X AB", "SEK", "note", dd_at_entry=0.1564).to_yaml()
    assert "dd_at_entry" not in half and "peak_date" not in half


def test_the_written_pair_loads_back_through_the_real_loader(tmp_path: Path):
    path = watchlist(tmp_path)
    frozen = Entry("PNDORA.CO", "Pandora A/S", "DKK", "Screener 2026-08-21: rank 4.",
                   dd_at_entry=0.1564, peak_date=date(2025, 8, 22))
    write([frozen], path=path, now=NOW, validate=load_watchlist)
    entries = {e.ticker: e for e in load_watchlist(path)}
    assert entries["PNDORA.CO"].dd_at_entry == pytest.approx(0.1564)
    assert entries["PNDORA.CO"].peak_date == date(2025, 8, 22)


def test_entries_from_ranking_freezes_the_pair_only_when_both_are_known():
    ranked = [FakeRanked(FakeScored(t, 0.5, 0.1)) for t in ("A", "B")]
    out = entries_from_ranking(
        ranked, asof=date(2026, 8, 21), top=2, names={}, markets={},
        drawdowns={"A": 0.1564, "B": 0.30}, total=2,
        peak_dates={"A": date(2025, 8, 22)},
    )
    a, b = out
    assert (a.dd_at_entry, a.peak_date) == (pytest.approx(0.1564), date(2025, 8, 22))
    assert "FROZEN at this reading per FRAMEWORK-EDITS E12" in a.notes
    assert "2025-08-22" in a.notes
    assert b.dd_at_entry is None and b.peak_date is None
    assert "NOT frozen" in b.notes and "date was not recorded" in b.notes


def test_a_later_price_move_does_not_change_the_recorded_drawdown(tmp_path: Path):
    """The entry is text in a file the screener never rewrites: what was
    frozen at entry is what the loader reads back, whatever the price did."""
    path = watchlist(tmp_path)
    write([Entry("X.ST", "X AB", "SEK", "n", dd_at_entry=0.20, peak_date=date(2026, 3, 1))],
          path=path, now=NOW, validate=load_watchlist)
    before = path.read_text(encoding="utf-8")
    # A second run, days later, with the same name now at another drawdown.
    later = Entry("X.ST", "X AB", "SEK", "n", dd_at_entry=0.05, peak_date=date(2026, 3, 1))
    result = write([later], path=path, now=NOW, validate=load_watchlist)
    assert result.skipped == [("X.ST", "already in the watchlist")]
    assert path.read_text(encoding="utf-8") == before
    assert load_watchlist(path)[-1].dd_at_entry == pytest.approx(0.20)
