"""Filter 2: coarse quality. Mechanism here, values in the config."""

from __future__ import annotations

from datetime import date
from pathlib import Path

import pytest

from vss.filters import (
    DATA_MISSING,
    FAIL,
    FILTER2_CONFIG_PATH,
    FLAG,
    LIMB_FCF,
    NOT_APPLICABLE,
    PASS,
    STEP_FILTER2,
    Filter2Config,
    Filter2Error,
    fcf_limb,
    limb_matrix,
    load_filter2_config,
    run_filter2,
)
from vss.fundamentals import FieldValue, SeriesPoint, TickerFundamentals
from vss.prices import STATUS_OK
from vss.universe import ON_MISSING, ON_VALUE

ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture()
def config():
    return load_filter2_config(ROOT / FILTER2_CONFIG_PATH)


_SAME = object()


def record(ticker="X", *, sector="Technology", fcf=100.0, debt=200.0, cash=50.0,
           ebitda=100.0, revenue=(100.0, 110.0, 120.0, 130.0),
           quarterly=(), ebitda_annual=_SAME, ebitda_quarters=(),
           ebit_quarters=()) -> TickerFundamentals:
    """``revenue`` is the ANNUAL series (oldest first, year ends 2022..);
    ``quarterly`` is (period_end, value) pairs from the vendor's quarterly
    statement -- a value of None is a NaN quarter, a hole (E45)."""
    fields = [FieldValue(ticker, "sector", "OK", text=sector)]
    for name, value in (("freeCashflow", fcf), ("totalDebt", debt),
                        ("totalCash", cash), ("ebitda", ebitda)):
        fields.append(
            FieldValue(ticker, name, "OK" if value is not None else "NO_DATA",
                       number=value)
        )
    series = [
        SeriesPoint(ticker, "Total Revenue", date(2022 + i, 12, 31), value)
        for i, value in enumerate(revenue or ())
    ]
    series += [SeriesPoint(ticker, "Total Revenue", end, value, "income_quarterly", 3)
               for end, value in quarterly]
    # The leverage fix of 2026-08-30 reads the STATEMENT'S EBITDA line, not
    # the info field. Unless a test says otherwise, the statement's annual
    # line equals the `ebitda` kwarg, so every older test keeps its meaning.
    if ebitda_annual is _SAME:
        ebitda_annual = ebitda
    if ebitda_annual is not None:
        series.append(SeriesPoint(ticker, "EBITDA", date(2025, 12, 31), ebitda_annual,
                                  "income", 12))
    series += [SeriesPoint(ticker, "EBITDA", end, value, "income_quarterly", 3)
               for end, value in ebitda_quarters]
    series += [SeriesPoint(ticker, "EBIT", end, value, "income_quarterly", 3)
               for end, value in ebit_quarters]
    return TickerFundamentals(ticker, STATUS_OK, 1, 2, tuple(fields), tuple(series))


class Candidate:
    def __init__(self, ticker):
        self.ticker = ticker
        self.marknad = "Stockholm"
        self.last_close = 100.0
        self.drawdown = 0.25
        self.rsi14 = 45.0


# --- config ----------------------------------------------------------------


def test_the_committed_config_matches_what_the_owner_decided(config):
    """The three decisions of 2026-08-22, recorded as FRAMEWORK-EDITS E2-E4,
    with E2 amended by E44 on 2026-08-26."""
    # E168 (attempt #25): the leverage limb (E2/E44's net debt / EBITDA) is gone.
    assert "net_debt_to_ebitda" not in config.raw["limbs"]
    # E4: an untested limb passes the name through, never drops it.
    assert config.on_missing_action == "pass_through"
    assert config.fcf_min == 0.0
    # E163: the revenue-trend limb (4.2.1, E45) is gone.
    assert "revenue_trend" not in config.raw["limbs"]
    assert config.decided and config.raw.get("decided") == date(2026, 8, 22)


def test_no_threshold_is_hardcoded_in_the_module():
    """Change 2.5 to 3.5 in the config and nothing should recompile."""
    source = (ROOT / "vss" / "filters.py").read_text(encoding="utf-8")
    body = source[source.index("# --- filter 2"):]
    code = "\n".join(l for l in body.splitlines() if not l.strip().startswith("#"))
    for literal in ("2.5", "3.5", "Financial Services"):
        assert literal not in code, f"filters.py hardcodes {literal!r}"


def test_a_missing_limb_in_the_config_is_fatal(tmp_path: Path):
    path = tmp_path / "f2.yaml"
    path.write_text("status: PROPOSED\nlimbs:\n  something_else:\n    min: 0\n",
                    encoding="utf-8")
    with pytest.raises(Filter2Error, match="is missing"):
        load_filter2_config(path)


def test_a_bad_on_missing_action_is_fatal(tmp_path: Path):
    text = (ROOT / FILTER2_CONFIG_PATH).read_text(encoding="utf-8")
    path = tmp_path / "f2.yaml"
    path.write_text(text.replace("on_missing_action: pass_through",
                                 "on_missing_action: maybe"), encoding="utf-8")
    with pytest.raises(Filter2Error, match="on_missing_action"):
        load_filter2_config(path)


def test_a_missing_config_is_fatal(tmp_path: Path):
    with pytest.raises(Filter2Error, match="no filter 2 config"):
        load_filter2_config(tmp_path / "nope.yaml")


# --- the FCF limb ----------------------------------------------------------


def test_positive_free_cash_flow_passes(config):
    assert fcf_limb(record(fcf=1.0), config).state == PASS


def test_negative_free_cash_flow_fails(config):
    assert fcf_limb(record(fcf=-1.0), config).state == FAIL


def test_zero_free_cash_flow_fails_because_positive_means_positive(config):
    assert fcf_limb(record(fcf=0.0), config).state == FAIL


def test_absent_free_cash_flow_is_data_missing_not_a_failure(config):
    assert fcf_limb(record(fcf=None), config).state == DATA_MISSING
    assert fcf_limb(None, config).state == DATA_MISSING


# --- the leverage limb -----------------------------------------------------


























# --- the revenue limb: the ANNUAL fallback (B9's reading, kept) --------------












# --- the revenue limb: QUARTERS, and the kill (E45) --------------------------


def _q(year, month, day=None):
    import calendar

    return date(year, month, day or calendar.monthrange(year, month)[1])


def _eight(values, ends=None):
    """Eight quarters oldest first, ending 2026-06-30."""
    ends = ends or [_q(2024, 9), _q(2024, 12), _q(2025, 3), _q(2025, 6),
                    _q(2025, 9), _q(2025, 12), _q(2026, 3), _q(2026, 6)]
    return list(zip(ends, values))


















# --- the step --------------------------------------------------------------


def test_a_failing_name_is_rejected_on_a_value(config):
    result = run_filter2([Candidate("A")], {"A": record("A", fcf=-5.0)}, config)
    assert result.survivors == []
    assert result.tally.step == STEP_FILTER2
    assert result.tally.rejected_on_value == 1
    assert result.tally.rejected_on_missing == 0
    assert result.rejections[0].kind == ON_VALUE


def test_an_untested_name_passes_through_marked_by_default(config):
    """DATA MISSING is a third state: not tested is not failed."""
    result = run_filter2([Candidate("A")], {}, config)
    assert [c.ticker for c in result.survivors] == ["A"]
    assert result.tally.rejected == 0
    assert len(result.assessed["A"].untested) == 1      # fcf (E163, E168)


def test_rejecting_on_missing_data_is_counted_in_its_own_column(tmp_path: Path):
    text = (ROOT / FILTER2_CONFIG_PATH).read_text(encoding="utf-8")
    path = tmp_path / "f2.yaml"
    path.write_text(text.replace("on_missing_action: pass_through",
                                 "on_missing_action: reject"), encoding="utf-8")
    strict = load_filter2_config(path)
    result = run_filter2([Candidate("A")], {}, strict)
    assert result.survivors == []
    assert result.tally.rejected_on_missing == 1
    assert result.tally.rejected_on_value == 0
    assert result.rejections[0].kind == ON_MISSING


def test_a_value_failure_beats_a_missing_limb(config):
    """A name that failed one limb is rejected on the value, not on the gap."""
    thin = record("A", fcf=-5.0, ebitda=None, sector="Utilities")
    result = run_filter2([Candidate("A")], {"A": thin}, config)
    assert result.tally.rejected_on_value == 1
    assert result.tally.rejected_on_missing == 0


def test_a_financial_is_judged_on_its_other_limbs(config):
    bank = record("HSBA.L", sector="Financial Services", fcf=5.0, ebitda=None)
    result = run_filter2([Candidate("HSBA.L")], {"HSBA.L": bank}, config)
    assert [c.ticker for c in result.survivors] == ["HSBA.L"]
    assert result.assessed["HSBA.L"].state(LIMB_FCF) == PASS


def test_the_limb_matrix_counts_the_one_limb_left(config):
    candidates = [Candidate(t) for t in ("A", "B", "C")]
    fundamentals = {
        "A": record("A"),
        "B": record("B", sector="Financial Services", ebitda=None),
        "C": record("C", ebitda=None, sector="Utilities"),
    }
    result = run_filter2(candidates, fundamentals, config)
    matrix = limb_matrix(result.assessed)
    assert set(matrix) == {LIMB_FCF}
    assert sum(matrix[LIMB_FCF].values()) == 3


def test_filter2_sets_no_price_and_no_fair_value():
    import ast

    source = (ROOT / "vss" / "filters.py").read_text(encoding="utf-8")
    tree = ast.parse(source)
    (func,) = [n for n in ast.walk(tree)
               if isinstance(n, ast.FunctionDef) and n.name == "run_filter2"]
    names = {n.id for n in ast.walk(func) if isinstance(n, ast.Name)}
    names |= {n.attr for n in ast.walk(func) if isinstance(n, ast.Attribute)}
    for forbidden in ("mbp", "fv_base", "compute_mbp", "stop_price"):
        assert forbidden not in names


# --- the survivor set against the store ------------------------------------


def test_a_never_fetched_ticker_says_so_rather_than_blaming_the_company(config):
    """"We did not fetch this" is not "the company reported nothing"."""
    from vss.filters import NOT_FETCHED

    result = run_filter2([Candidate("GHOST.ST")], {}, config)
    assert result.not_fetched == ["GHOST.ST"]
    for limb in result.assessed["GHOST.ST"].limbs:
        assert limb.state == DATA_MISSING
        assert limb.detail == NOT_FETCHED


def test_a_reported_gap_is_worded_as_the_company_s(config):
    from vss.filters import NOT_FETCHED

    result = run_filter2([Candidate("A")], {"A": record("A", fcf=None)}, config)
    detail = next(l for l in result.assessed["A"].limbs if l.name == LIMB_FCF).detail
    assert detail != NOT_FETCHED
    assert "reported" in detail
    assert result.not_fetched == []


def test_the_store_size_is_reported_so_drift_is_visible(config):
    fundamentals = {"A": record("A"), "B": record("B"), "C": record("C")}
    result = run_filter2([Candidate("A"), Candidate("Z")], fundamentals, config)
    assert result.store_size == 3
    assert result.not_fetched == ["Z"]


# --- E46: investment companies, by the owner's list -------------------------




def test_the_committed_list_loads_and_names_every_share_class():
    from vss.filters import INVESTMENT_COMPANIES_PATH, load_investment_companies

    listed = load_investment_companies(ROOT / INVESTMENT_COMPANIES_PATH)
    for ticker in ("INVE-A.ST", "INVE-B.ST", "EQT.ST", "KINV-A.ST", "KINV-B.ST",
                   "INDU-A.ST", "INDU-C.ST", "LATO-B.ST", "LUND-B.ST", "SVOL-B.ST",
                   "BURE.ST", "CRED-A.ST", "ORES.ST", "TRAC-B.ST", "PRX.AS", "AKER.OL"):
        assert ticker in listed, ticker
    assert "INDT.ST" not in listed and "LIFCO-B.ST" not in listed, \
        "acquisitive operating groups are not investment companies (E46)"


def test_every_listed_ticker_is_in_the_committed_universe():
    """A listed name outside every universe file is inert; the report names
    it, but the committed list should not carry one to begin with."""
    from vss.filters import INVESTMENT_COMPANIES_PATH, load_investment_companies
    from vss.universe import load_type_rules, load_universe

    universe_dir = ROOT / "config" / "universe"
    load = load_universe(universe_dir, tiers=("A",),
                         type_rules=load_type_rules(universe_dir / "instrument_types.yaml"))
    tickers = {i.ticker_yahoo for i in load.instruments}
    listed = load_investment_companies(ROOT / INVESTMENT_COMPANIES_PATH)
    assert sorted(listed - tickers) == []


def test_a_malformed_or_missing_list_is_fatal(tmp_path: Path):
    from vss.filters import load_investment_companies

    with pytest.raises(Filter2Error, match="no investment-company list"):
        load_investment_companies(tmp_path / "nope.yaml")
    path = tmp_path / "ic.yaml"
    path.write_text("investment_companies:\n  - ticker: X.ST\n", encoding="utf-8")
    with pytest.raises(Filter2Error, match="names its company"):
        load_investment_companies(path)
    path.write_text("investment_companies:\n  - {ticker: X.ST, company: X}\n"
                    "  - {ticker: X.ST, company: X}\n", encoding="utf-8")
    with pytest.raises(Filter2Error, match="listed twice"):
        load_investment_companies(path)
    assert load_filter2_config(ROOT / FILTER2_CONFIG_PATH,
                               investment_companies_path=None).investment_companies == frozenset()



# --- the leverage limb reads the STATEMENT'S EBITDA (fix of 2026-08-30) -----










