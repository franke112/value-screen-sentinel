"""FRAMEWORK-EDITS E114: the shadow book, and the two things it never does.

E114 forbids exactly two substitutions, and both are easy to make by
accident: reading the baseline off the nearest bar when the verdict date
has none, and filling a window that has not elapsed with the figure so
far. Everything else here is the book's own validation.
"""

from __future__ import annotations

import ast
import re

from datetime import date, datetime, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo

import pandas as pd
import pytest

from vss.config import ConfigError
from vss.fetch import FetchResult
from vss.sales import pct
from vss.sales import DATA_MISSING
from vss.shadowbook import (BENCHMARKS, COLUMNS, INCOMPLETE, PRICE_RETURN,
                            SAMPLE_FLOOR, TOTAL_RETURN, WINDOW_MONTHS,
                            add_months, load_shadow_book, parse_book,
                            run_shadow)

#: After the New York close, so `settled_through` is the day itself.
NOW = datetime(2026, 9, 8, 23, 0, tzinfo=ZoneInfo("UTC"))
SETTLED = date(2026, 9, 8)

HEADER = ",".join(COLUMNS)


def frame(start: date, days: int, close: float, step: float = 0.0,
          weekdays_only: bool = True, dividend: tuple[date, float] | None = None,
          adj_close: bool = True, dividends_col: bool = True) -> pd.DataFrame:
    """A vendor frame in the shape `get_history` returns.

    `dividend` is one ex-dividend event, BACK-ADJUSTED the way the vendor
    does it: bars before the ex-date are scaled by (1 - amount / the
    close before it), bars on and after it are not. That is what makes
    the adjusted series a total return, and a test that leaves it out is
    testing a price return with a different name.

    `adj_close` and `dividends_col` drop a column, which is how a name
    whose dividends cannot be established is spelled.
    """
    dates, closes, day = [], [], start
    while len(dates) < days:
        if not weekdays_only or day.weekday() < 5:
            dates.append(day)
            closes.append(close + step * len(dates))
        day += timedelta(days=1)
    divs = [0.0] * len(dates)
    factors = [1.0] * len(dates)
    if dividend is not None:
        ex, amount = dividend
        at = next(i for i, d in enumerate(dates) if d >= ex)
        divs[at] = amount
        factor = 1.0 - amount / closes[at - 1]
        for i in range(at):
            factors[i] = factor
    data = {"Close": closes}
    if adj_close:
        data["Adj Close"] = [c * f for c, f in zip(closes, factors)]
    if dividends_col:
        data["Dividends"] = divs
    return pd.DataFrame(data, index=pd.to_datetime(dates))


def book_file(tmp_path: Path, *rows: str) -> Path:
    path = tmp_path / "shadow_book.csv"
    path.write_text("\n".join([HEADER, *rows]) + "\n", encoding="utf-8")
    return path


def row(ticker="ZZZ", when="2026-03-02", verdict="DROPPED",
        standing="STANDING", close="100", currency="USD", fv="",
        decided="Gate 3.", source="watchlist note") -> str:
    return (f"{ticker},{when},{verdict},{standing},{close},{currency},{fv},"
            f"\"{decided}\",\"{source}\"")


def fetcher(frames: dict[str, pd.DataFrame | None]):
    def fetch(ticker: str) -> FetchResult:
        got = frames.get(ticker)
        if got is None:
            return FetchResult(ticker, None, "none", None, "no data")
        return FetchResult(ticker, got, "cache", NOW)
    return fetch


def report(tmp_path: Path, path: Path, frames) -> str:
    _, markdown = run_shadow(book_path=path, reports_dir=tmp_path / "reports",
                             now=NOW, dry_run=True, fetch=fetcher(frames))
    return markdown


# --- E114's two prohibitions -------------------------------------------------


def test_a_verdict_date_with_no_close_is_DATA_MISSING_not_the_nearest_bar(tmp_path):
    """2026-03-07 is a Saturday. The Friday close is not that day's close."""
    path = book_file(tmp_path, row(ticker="ZZZ", when="2026-03-07", close=""))
    frames = {"ZZZ": frame(date(2026, 3, 2), 120, 100.0, step=1.0)}
    markdown = report(tmp_path, path, frames)

    assert "Verdicts with no baseline close" in markdown
    assert "Saturday is not a trading day" in markdown
    # The Friday bar exists and is NOT quietly promoted to a baseline.
    zzz = next(line for line in markdown.splitlines()
               if line.startswith("| `ZZZ`"))
    assert zzz.count("DATA MISSING") >= 2, zzz


def test_an_unelapsed_window_is_INCOMPLETE_and_carries_no_figure(tmp_path):
    """One month has elapsed, three have not. None of the three prints a
    number, and the one that has prints a real one."""
    path = book_file(tmp_path, row(when="2026-08-03", close="100"))
    frames = {"ZZZ": frame(date(2026, 8, 3), 60, 100.0, step=1.0)}
    markdown = report(tmp_path, path, frames)

    zzz = next(line for line in markdown.splitlines()
               if line.startswith("| `ZZZ`"))
    # "| a | b |".split("|") leaves an empty cell at each end, and the
    # last real cell is `decided_by`; the four windows sit before it.
    cells = [c.strip() for c in zzz.split("|")]
    windows = cells[-6:-2]
    assert INCOMPLETE not in windows[0], windows          # 1m: 2026-09-03
    assert all(INCOMPLETE in c for c in windows[1:]), windows
    assert not any("%" in c for c in windows[1:]), windows


def test_a_window_ending_on_the_settled_day_itself_has_elapsed(tmp_path):
    path = book_file(tmp_path, row(when="2026-08-08", close="100"))
    frames = {"ZZZ": frame(date(2026, 8, 3), 60, 100.0, step=1.0)}
    markdown = report(tmp_path, path, frames)
    assert f"{INCOMPLETE} (2026-09-08)" not in markdown


# --- the arithmetic ----------------------------------------------------------


def test_add_months_clamps_the_day_to_the_month():
    assert add_months(date(2026, 8, 31), 6) == date(2027, 2, 28)
    assert add_months(date(2026, 8, 30), 6) == date(2027, 2, 28)
    assert add_months(date(2026, 12, 15), 1) == date(2027, 1, 15)
    assert add_months(date(2026, 1, 31), 1) == date(2026, 2, 28)


def test_the_windows_are_the_four_E114_names():
    assert WINDOW_MONTHS == (1, 3, 6, 12)


def test_the_benchmarks_declare_which_basis_they_are():
    bases = {b.label: b.basis for b in BENCHMARKS}
    assert bases == {"OMXS30": PRICE_RETURN, "S&P 500": TOTAL_RETURN}


def test_the_benchmark_is_converted_into_the_name_s_quote_currency(tmp_path):
    """The index is flat in SEK and the krona halves against the euro, so
    a EUR-quoted name must see the OMXS30 leg fall by half -- not read a
    flat index and call the comparison done."""
    path = book_file(tmp_path, row(when="2026-08-03", close="100",
                                   currency="EUR"))
    flat = frame(date(2026, 8, 1), 60, 1000.0)
    halving = frame(date(2026, 8, 1), 60, 1.0)
    # The krona halves on 2026-08-20, INSIDE the settled window -- a move
    # after the last settled close would be invisible and prove nothing.
    halving.loc[halving.index >= pd.Timestamp(2026, 8, 20), "Close"] = 0.5
    frames = {"ZZZ": frame(date(2026, 8, 3), 60, 100.0),
              "^OMX": flat, "^SP500TR": flat,
              "SEKEUR=X": halving, "USDEUR=X": frame(date(2026, 8, 1), 60, 1.0)}
    markdown = report(tmp_path, path, frames)

    zzz = next(line for line in markdown.splitlines()
               if line.startswith("| `ZZZ`"))
    assert "-50.0%" in zzz, zzz


def test_a_return_is_scale_invariant_so_GBX_and_GBP_agree(tmp_path):
    """`major_unit` is what makes the pair fetchable at all; the figure it
    produces must not depend on which unit the row was written in."""
    frames = {"ZZZ": frame(date(2026, 8, 3), 60, 100.0),
              "^OMX": frame(date(2026, 8, 1), 60, 1000.0, step=1.0),
              "^SP500TR": frame(date(2026, 8, 1), 60, 1000.0, step=1.0),
              "SEKGBP=X": frame(date(2026, 8, 1), 60, 0.07),
              "USDGBP=X": frame(date(2026, 8, 1), 60, 0.74)}
    lines = []
    for currency in ("GBX", "GBp", "GBP"):
        path = book_file(tmp_path / currency if False else tmp_path,
                         row(when="2026-08-03", close="100",
                             currency=currency))
        markdown = report(tmp_path, path, frames)
        line = next(l for l in markdown.splitlines() if l.startswith("| `ZZZ`"))
        lines.append(line.replace(currency, ""))
    assert lines[0] == lines[1] == lines[2]


def test_pct_never_puts_a_sign_on_a_rounded_zero():
    """A baseline stored to two decimals against a fifteen-decimal vendor
    close reads -2.6e-8, and `-0.0%` would print as a fall."""
    assert pct(-2.6e-8) == "0.0%"
    assert pct(0.0) == "0.0%"
    assert pct(0.0004) == "0.0%"
    assert pct(0.006) == "+0.6%"
    assert pct(-0.006) == "-0.6%"


# --- the book's own validation -----------------------------------------------


def test_the_header_must_be_exactly_the_nine_columns(tmp_path):
    path = tmp_path / "shadow_book.csv"
    path.write_text("ticker,verdict_date\nZZZ,2026-03-02\n", encoding="utf-8")
    with pytest.raises(ConfigError, match="header must be exactly"):
        load_shadow_book(path)


def test_a_missing_book_is_refused_rather_than_created(tmp_path):
    with pytest.raises(ConfigError, match="no shadow book"):
        load_shadow_book(tmp_path / "nowhere.csv")


@pytest.mark.parametrize("bad, message", [
    (row(verdict="WATCH-PRICED"), "verdict must be one of"),
    (row(standing="MAYBE"), "standing must be one of"),
    (row(when="02/03/2026"), "verdict_date must be YYYY-MM-DD"),
    (row(close="nought"), "close must be a number"),
    (row(close="0"), "close must be positive"),
    (row(fv="-3"), "fv_base must be positive"),
    (row(decided=""), "missing decided_by"),
    (row(source=""), "missing source"),
])
def test_the_book_refuses_a_row_it_cannot_read(tmp_path, bad, message):
    with pytest.raises(ConfigError, match=message):
        load_shadow_book(book_file(tmp_path, bad))


def test_one_verdict_one_row(tmp_path):
    with pytest.raises(ConfigError, match="appears twice"):
        load_shadow_book(book_file(tmp_path, row(), row(close="90")))


def test_the_same_name_may_be_judged_twice_on_different_days(tmp_path):
    """NKE's 2026-08-25 re-read superseded its 2026-08-22 verdict in the
    exclusion CSV, because a ticker listed twice THERE is a hard error.
    The shadow book is a history and has no such rule."""
    book = load_shadow_book(book_file(tmp_path, row(when="2026-03-02"),
                                      row(when="2026-04-02", close="90")))
    assert [v.verdict_date for v in book] == [date(2026, 3, 2),
                                              date(2026, 4, 2)]


def test_blank_close_and_blank_fv_are_DATA_MISSING_not_zero(tmp_path):
    book = parse_book([dict(zip(COLUMNS, ["ZZZ", "2026-03-02", "INTAKE",
                                          "OPEN", "", "USD", "", "x", "y"]))])
    assert book[0].close is None and book[0].fv_base is None
    assert book[0].baseline_missing


def test_the_book_is_sorted_by_date_then_ticker(tmp_path):
    book = load_shadow_book(book_file(
        tmp_path, row(ticker="BBB", when="2026-04-02"),
        row(ticker="AAA", when="2026-04-02"),
        row(ticker="CCC", when="2026-03-02")))
    assert [v.ticker for v in book] == ["CCC", "AAA", "BBB"]


# --- E114: it is not a signal ------------------------------------------------


#: The modules allowed to read the shadow book, and why each one is.
#:
#: `__main__` dispatches the command. `overview` MEASURES the book for the
#: read-only page and `render` PRINTS what it measured; neither does
#: anything else with it, and the next test is what holds them to that.
#: Any other name appearing here is a module that could act on a refusal's
#: subsequent price, which is the thing E114 forbids.
SHADOW_BOOK_READERS = {"shadowbook.py", "__main__.py", "overview.py",
                       "render.py"}

#: What the page may take from the module: the book, the measurement, the
#: benchmark labels, the INCOMPLETE marker and the path. Every one of them
#: READS or NAMES. Nothing that decides is on this list, and the list is
#: the guarantee -- an import of anything else fails the test below.
OVERVIEW_MAY_IMPORT = {"BENCHMARKS", "INCOMPLETE", "SHADOW_BOOK_PATH",
                       "load_shadow_book", "shadow_rows"}
#: The two halves of the page, checked against that list together.
PAGE_MODULES = ("overview.py", "render.py")


def test_only_the_command_and_the_read_only_page_read_the_shadow_book():
    """E114: nothing here may arm an alert, enter a name or reach a
    valuation. The cheapest guarantee of that was that NO module read the
    book at all; it now has exactly one reader that is not the command, and
    that reader is the page which by construction cannot act.

    THE GUARANTEE IS UNCHANGED AND THE PROXY IS NARROWER. `overview` writes
    one HTML file under `reports/` and nothing else, anywhere -- there is no
    form, no script and no second write on it -- so a shadow-book row
    reaching it can be looked at and can do nothing. The list is closed:
    a new name here is a new module that could act on a refusal's price.
    """
    root = Path(__file__).resolve().parent.parent / "vss"
    readers = [p.name for p in root.glob("*.py")
               if p.name not in SHADOW_BOOK_READERS
               and "shadowbook" in p.read_text(encoding="utf-8")]
    assert readers == [], readers


def test_the_page_takes_only_reading_names_from_the_shadow_book():
    """The other half of the guarantee: WHAT the readers may import.

    PARSED, NOT MATCHED. A regex over the source read a bare
    `from .shadowbook import BENCHMARKS, INCOMPLETE` and swallowed the
    next thirty lines with it; `ast` sees the statement and nothing else.
    """
    root = Path(__file__).resolve().parent.parent / "vss"
    seen: set[str] = set()
    for module in PAGE_MODULES:
        tree = ast.parse((root / module).read_text(encoding="utf-8"))
        names = {alias.name for node in ast.walk(tree)
                 if isinstance(node, ast.ImportFrom)
                 and (node.module or "").split(".")[-1] == "shadowbook"
                 for alias in node.names}
        assert names, f"{module} is listed as a reader and imports nothing"
        assert names <= OVERVIEW_MAY_IMPORT, names - OVERVIEW_MAY_IMPORT
        seen |= names
    assert seen


def test_the_report_writes_one_file_and_says_where(tmp_path):
    path = book_file(tmp_path, row(when="2026-08-03", close="100"))
    reports = tmp_path / "reports"
    code, markdown = run_shadow(book_path=path, reports_dir=reports, now=NOW,
                                fetch=fetcher({"ZZZ": frame(date(2026, 8, 3),
                                                            60, 100.0)}))
    assert code == 0
    written = list(reports.glob("*.md"))
    assert [p.name for p in written] == ["SHADOW-BOOK-2026-09-08.md"]
    assert "THIS IS NOT A SIGNAL" in markdown
    assert written[0].read_text(encoding="utf-8").startswith("# vss shadow")


def test_a_dry_run_writes_nothing(tmp_path):
    path = book_file(tmp_path, row(when="2026-08-03", close="100"))
    reports = tmp_path / "reports"
    _, markdown = run_shadow(book_path=path, reports_dir=reports, now=NOW,
                             dry_run=True,
                             fetch=fetcher({"ZZZ": frame(date(2026, 8, 3),
                                                         60, 100.0)}))
    assert not reports.exists()
    assert "DRY RUN" in markdown


def test_a_name_the_fetch_cannot_serve_prints_its_error_not_a_zero(tmp_path):
    path = book_file(tmp_path, row(when="2026-08-03", close="100"))
    markdown = report(tmp_path, path, {"ZZZ": None})
    zzz = next(l for l in markdown.splitlines() if l.startswith("| `ZZZ`"))
    assert "no data" in zzz and "0.0%" not in zzz


# --- the committed book ------------------------------------------------------


def test_the_committed_book_loads_and_every_row_names_its_source():
    book = load_shadow_book()
    assert len(book) >= 23
    assert all(v.source and v.decided_by for v in book)
    assert all(v.verdict_date <= date(2026, 10, 5) for v in book)   # CPRT, 2026-10-05


# --- E114 limit three: both legs are the same kind of return -----------------


def test_the_name_is_measured_on_TOTAL_return_not_price_return(tmp_path):
    """Close is flat at 100 throughout and a 5.00 dividend goes ex in the
    middle. The price return is nil; the total return is not, and it is
    the total return the report prints."""
    path = book_file(tmp_path, row(when="2026-08-03", close="100"))
    frames = {"ZZZ": frame(date(2026, 8, 3), 60, 100.0,
                           dividend=(date(2026, 8, 17), 5.0))}
    markdown = report(tmp_path, path, frames)

    zzz = next(l for l in markdown.splitlines() if l.startswith("| `ZZZ`"))
    # 100 / 95 - 1 = +5.26%. A price return would read 0.0%.
    assert "+5.3%" in zzz, zzz
    assert "What reinvesting the dividends was worth" in markdown
    assert "+5.26pp" in markdown


def test_a_name_with_no_Dividends_column_is_DATA_MISSING_not_a_price_return(tmp_path):
    """The whole of the amendment: an absent dividend record cannot be
    told from a name that paid nothing, so nothing is compared."""
    path = book_file(tmp_path, row(when="2026-08-03", close="100"))
    frames = {"ZZZ": frame(date(2026, 8, 3), 60, 100.0, step=1.0,
                           dividends_col=False)}
    markdown = report(tmp_path, path, frames)

    assert "could not be derived" in markdown
    assert "cannot be told from one whose dividends are not recorded" in markdown
    zzz = next(l for l in markdown.splitlines() if l.startswith("| `ZZZ`"))
    cells = [c.strip() for c in zzz.split("|")]
    assert cells[8] == f"**{DATA_MISSING}**", cells      # Since verdict (TR)
    # The RECORDED close survives -- the row keeps its fact.
    assert cells[5].startswith("100.00"), cells


def test_a_name_with_no_Adj_Close_column_is_DATA_MISSING(tmp_path):
    path = book_file(tmp_path, row(when="2026-08-03", close="100"))
    frames = {"ZZZ": frame(date(2026, 8, 3), 60, 100.0, adj_close=False)}
    markdown = report(tmp_path, path, frames)
    assert "no Adj Close column" in markdown


def test_a_dividends_column_of_zeros_is_evidence_not_an_absence(tmp_path):
    """E110's posture: a stated zero is evidence. A tracked series that
    paid nothing IS a total return -- it just equals its price return."""
    path = book_file(tmp_path, row(when="2026-08-03", close="100"))
    frames = {"ZZZ": frame(date(2026, 8, 3), 60, 100.0)}
    markdown = report(tmp_path, path, frames)

    assert "could not be derived" not in markdown
    zzz = next(l for l in markdown.splitlines() if l.startswith("| `ZZZ`"))
    assert DATA_MISSING not in zzz, zzz
    assert "No name has gone ex-dividend since its verdict" in markdown


def test_the_windows_are_total_return_too_not_only_the_since_column(tmp_path):
    path = book_file(tmp_path, row(when="2026-08-03", close="100"))
    frames = {"ZZZ": frame(date(2026, 8, 3), 60, 100.0,
                           dividend=(date(2026, 8, 17), 5.0))}
    markdown = report(tmp_path, path, frames)
    zzz = next(l for l in markdown.splitlines() if l.startswith("| `ZZZ`"))
    cells = [c.strip() for c in zzz.split("|")]
    one_month = cells[-6]                       # the 1m window, 2026-09-03
    assert one_month.startswith("+5.3%"), one_month


def test_the_benchmarks_are_never_both_price_returns():
    """The S&P leg was the silent mismatch and is a total return. OMXS30
    stays a price index and must SAY so -- a stated substitution."""
    spx = next(b for b in BENCHMARKS if b.label == "S&P 500")
    omx = next(b for b in BENCHMARKS if b.label == "OMXS30")
    assert spx.basis == TOTAL_RETURN and spx.symbol == "^SP500TR"
    assert omx.basis == PRICE_RETURN and omx.symbol == "^OMX"
    assert "^OMXS30GI" in omx.note


# --- the stored fact, re-read ------------------------------------------------


def test_a_restated_baseline_is_flagged_and_the_book_is_not_rewritten(tmp_path):
    """A split restates an unadjusted series. The book keeps what it
    recorded and the report says the two disagree."""
    path = book_file(tmp_path, row(when="2026-08-03", close="200"))
    frames = {"ZZZ": frame(date(2026, 8, 3), 60, 100.0)}
    markdown = report(tmp_path, path, frames)

    assert "no longer match what the vendor serves" in markdown
    assert "book says 200.00, vendor now serves 100.00" in markdown
    assert load_shadow_book(path)[0].close == 200.0


def test_a_matching_baseline_says_so_rather_than_staying_silent(tmp_path):
    path = book_file(tmp_path, row(when="2026-08-03", close="100"))
    frames = {"ZZZ": frame(date(2026, 8, 3), 60, 100.0)}
    markdown = report(tmp_path, path, frames)
    assert "still match the vendor's unadjusted close" in markdown


def test_rounding_the_stored_close_is_not_a_restatement(tmp_path):
    """The book stores four decimals against a vendor carrying fifteen.
    That gap is arithmetic, not a restatement."""
    path = book_file(tmp_path, row(when="2026-08-03", close="511.33"))
    frames = {"ZZZ": frame(date(2026, 8, 3), 60, 511.3299865722656)}
    markdown = report(tmp_path, path, frames)
    assert "still match the vendor's unadjusted close" in markdown


# --- E114 limit four: a weekend verdict is re-dated, not priced off a bar ----


def test_every_committed_verdict_date_is_a_settled_session_or_unpriced():
    """Limit four: a recorded verdict date that carries a close must be a
    date the name actually traded on. A row with no close is exempt --
    it is waiting for its own session to settle."""
    import pandas as pd_

    from vss.metrics import index_dates
    from vss.runner import CACHE_DIR

    for verdict in load_shadow_book():
        if verdict.close is None:
            continue
        cache = CACHE_DIR / f"{verdict.ticker}.csv"
        if not cache.exists():          # nothing to check against offline
            continue
        served = pd_.read_csv(cache, index_col=0, parse_dates=True)
        days = set(index_dates(served.index))
        assert verdict.verdict_date in days, (
            f"{verdict.ticker} is dated {verdict.verdict_date}, which is "
            f"not a session it traded on")


def test_every_re_dated_row_says_where_it_moved_from():
    moved = [v for v in load_shadow_book() if "RE-DATED" in v.source]
    assert len(moved) == 6, [v.ticker for v in moved]   # MUSA and NHY.OL re-dated 2026-09-19 -> 09-18
    for verdict in moved:
        assert "RE-DATED from" in verdict.source, verdict.source
        # Both ends of the move are on the row: the date it now carries,
        # and the administrative date it moved off.
        assert f"to {verdict.verdict_date.isoformat()}" in verdict.source
        assert verdict.close is not None


def test_the_sample_sentence_names_the_reason_that_actually_fired(tmp_path):
    """It said "below 20 measurable rows" on a book of 22 measurable rows,
    because the OTHER condition was the one that fired. And `INCOMPLETE`
    must survive the sentence being assembled -- str.capitalize() lowers
    everything after the first character."""
    frames = {"ZZZ": frame(date(2026, 8, 3), 60, 100.0)}

    # Nothing has elapsed: that is the reason, and it must be the one given.
    fresh = book_file(tmp_path, row(when="2026-09-01", close="100"))
    markdown = report(tmp_path, fresh, frames)
    assert "Not one fixed window has elapsed" in markdown
    assert INCOMPLETE in markdown.split("Not one fixed window")[1]
    assert "reads incomplete" not in markdown

    # A window HAS elapsed, so the sample floor is the only reason left --
    # and the old sentence claimed both regardless of which was true.
    old = book_file(tmp_path, row(when="2026-08-03", close="100"))
    markdown = report(tmp_path, old, frames)
    assert "Not one fixed window has elapsed" not in markdown
    assert f"fewer than {SAMPLE_FLOOR} measurable rows" in markdown
