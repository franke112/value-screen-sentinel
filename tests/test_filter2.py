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
    LIMB_LEVERAGE,
    LIMB_REVENUE,
    NOT_APPLICABLE,
    PASS,
    STEP_FILTER2,
    Filter2Config,
    Filter2Error,
    fcf_limb,
    leverage_limb,
    limb_matrix,
    load_filter2_config,
    revenue_limb,
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
    # E44: Gate 3's own 2.5x. The screener feeds Gate 3, and a name at 3.3x
    # fails the hand chain regardless (SCREENER-REVIEW-3 Part 6: 72 names
    # passed E2's 3.5x and failed the framework's number).
    assert config.leverage_max == 2.5
    assert config.raw["limbs"]["net_debt_to_ebitda"]["decided"] == date(2026, 8, 26)
    assert "E44" in config.raw["limbs"]["net_debt_to_ebitda"]["amended_by"]
    # E3: Real Estate joins financials as NOT APPLICABLE.
    assert config.leverage_na_sectors == frozenset({"Financial Services", "Real Estate"})
    # E4: an untested limb passes the name through, never drops it.
    assert config.on_missing_action == "pass_through"
    assert config.fcf_min == 0.0
    # E45: the quarterly kill, with B9's annual FLAG as the fallback.
    assert config.revenue_kill_action == "KILL" and config.revenue_kill_after == 2
    assert config.revenue_quarters == 8
    assert config.revenue_year_ago_window == (350, 380)
    assert config.revenue_action == "FLAG" and config.revenue_flag_after == 2
    assert config.raw["limbs"]["revenue_trend"]["decided"] == date(2026, 8, 26)
    assert config.decided and config.raw.get("decided") == date(2026, 8, 22)


def test_the_hard_kill_is_recorded_as_the_road_not_taken(config):
    """E44 keeps E2's 3.5x visible in the file so the reversal stays legible."""
    leverage = config.raw["limbs"]["net_debt_to_ebitda"]
    assert leverage["not_chosen"]["max"] == 3.5
    assert "4.2.5" in leverage["not_chosen"]["framework"]
    assert "Gate 3" in leverage["framework"]


def test_no_threshold_is_hardcoded_in_the_module():
    """Change 2.5 to 3.5 in the config and nothing should recompile."""
    source = (ROOT / "vss" / "filters.py").read_text(encoding="utf-8")
    body = source[source.index("# --- filter 2"):]
    code = "\n".join(l for l in body.splitlines() if not l.strip().startswith("#"))
    for literal in ("2.5", "3.5", "Financial Services"):
        assert literal not in code, f"filters.py hardcodes {literal!r}"


def test_a_missing_limb_in_the_config_is_fatal(tmp_path: Path):
    path = tmp_path / "f2.yaml"
    path.write_text("status: PROPOSED\nlimbs:\n  free_cash_flow:\n    min: 0\n",
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


def test_leverage_inside_the_cap_passes(config):
    # net debt 150, EBITDA 100 -> 1.5x
    assert leverage_limb(record(debt=200, cash=50, ebitda=100), config).state == PASS


def test_leverage_above_the_cap_fails(config):
    # net debt 400, EBITDA 100 -> 4.0x, above the cap
    assert leverage_limb(record(debt=450, cash=50, ebitda=100), config).state == FAIL


def test_the_cap_boundary_passes(config):
    limb = leverage_limb(record(debt=300, cash=50, ebitda=100), config)
    assert limb.state == PASS and "2.50x" in limb.detail


def test_the_una_margin_still_passes_under_e44():
    """FRAMEWORK-EDITS E2's own case, re-read under E44.

    UNA.AS ran net debt/EBITDA 2.27-2.48x, just under Gate 3's 2.5x cap.
    E2 feared a 2.5x screen would settle that margin without the filing;
    E44 applies the gate's own cap, INCLUSIVE, and 2.48x is inside it.
    """
    config = load_filter2_config(ROOT / FILTER2_CONFIG_PATH)
    for ratio in (2.27, 2.48):
        # net debt = ratio * EBITDA, with EBITDA 100
        limb = leverage_limb(record(debt=ratio * 100 + 50, cash=50, ebitda=100), config)
        assert limb.state == PASS, ratio


def test_names_between_the_gate_and_the_hard_kill_now_fail_on_value_with_the_ratio():
    """E44 (SCREENER-REVIEW-3 Part 6): FGR.PA at 2.60x and AFRY.ST at 3.30x
    passed E2's 3.5x and would fail Gate 3 by hand regardless. They are
    rejected ON VALUE here, and the ratio is printed so the reason is a
    number, not a verdict."""
    config = load_filter2_config(ROOT / FILTER2_CONFIG_PATH)
    fgr = record("FGR.PA", debt=15_775.0, cash=5_870.0, ebitda=3_803.0)   # 2.60x
    afry = record("AFRY.ST", debt=7_296.0, cash=1_196.0, ebitda=1_849.0)   # 3.30x
    for rec, ratio in ((fgr, "2.60x"), (afry, "3.30x")):
        limb = leverage_limb(rec, config)
        assert limb.state == FAIL and ratio in limb.detail, rec.ticker
    result = run_filter2([Candidate("FGR.PA"), Candidate("AFRY.ST")],
                         {"FGR.PA": fgr, "AFRY.ST": afry}, config)
    assert result.survivors == []
    assert result.tally.rejected_on_value == 2 and result.tally.rejected_on_missing == 0
    assert all("net debt/EBITDA" in r.reason for r in result.rejections)


def test_e44_on_the_settled_2026_08_26_store_removes_the_seventy():
    """The measurement E44 was ruled on, re-run on the stored 22:30 fetch
    (gitignored; skipped where it is not on disk). Report B 6.3 counted 72
    RATIOS in (2.5x, 3.5x] over the 487 records; two of them -- CIBUS.ST
    (Real Estate) and IDUN-B.ST (Financial Services) -- are NOT APPLICABLE
    on the limb under either cap (E3), and LATO-B.ST and PRX.AS are NOT
    APPLICABLE by E46's list -- so 68 names moved from PASS at 3.5x to FAIL
    at 2.5x on the info field, FGR.PA and AFRY.ST among them; 56 on the
    statement EBITDA the limb reads since 2026-08-30."""
    from vss import snapshot as store

    path = ROOT / "data" / "screener_snapshots" / "2026-08-26" / "fundamentals.sqlite"
    if not path.exists():
        pytest.skip("the 2026-08-26 fundamentals store is not on this machine")
    config = load_filter2_config(ROOT / FILTER2_CONFIG_PATH)
    loose = Filter2Config(**{**config.__dict__, "leverage_max": 3.5})
    records = store.read_fundamentals(path)
    in_band = []
    for r in records:
        debt, cash, ebitda = r.value("totalDebt"), r.value("totalCash"), r.value("ebitda")
        if None in (debt, cash, ebitda) or ebitda <= 0:
            continue
        if 2.5 < (debt - cash) / ebitda <= 3.5:
            in_band.append(r.ticker)
    assert len(in_band) == 72, "the report's count of ratios in the band"
    exempt = sorted(r.ticker for r in records if r.ticker in in_band
                    and leverage_limb(r, config).state == NOT_APPLICABLE)
    # LATO-B.ST (2.96x, Industrials by string) and PRX.AS (Consumer Cyclical)
    # are investment companies by E46's list, so 68 names move once both
    # rulings apply.
    assert exempt == ["CIBUS.ST", "IDUN-B.ST", "LATO-B.ST", "PRX.AS"]
    moved = sorted(r.ticker for r in records
                   if leverage_limb(r, loose).state == PASS
                   and leverage_limb(r, config).state == FAIL)
    # 68 on the vendor's info-field EBITDA, which the limb read until the
    # 2026-08-30 fix. On the filer's statement EBITDA (lease-consistent with
    # the vendor's totalDebt) 28 of the 68 leave the band -- 20 at or below
    # 2.5x (FGR.PA 2.31x, AD.AS 2.20x), 8 above 3.5x or on a negative TTM
    # (LYB, MOS, TAP, NEXI.MI...) -- 16 others enter it, and 56 move.
    # AFRY.ST still does, at 2.79x.
    assert len(moved) == 56, len(moved)
    assert "FGR.PA" not in moved and "AD.AS" not in moved and "AFRY.ST" in moved
    left = set(in_band) - set(exempt) - set(moved)
    entered = set(moved) - set(in_band)
    assert len(left) == 28 and {"FGR.PA", "AD.AS", "LYB", "TAP"} <= left
    assert len(entered) == 16 and "COLO-B.CO" in entered


def test_net_cash_passes_without_computing_a_ratio(config):
    limb = leverage_limb(record(debt=10, cash=500, ebitda=100), config)
    assert limb.state == PASS and "net cash" in limb.detail


def test_a_financial_is_not_applicable_not_failed_and_not_missing(config):
    """FRAMEWORK Gate 3 excludes financials. Precedent: FRAMEWORK-EDITS B7."""
    limb = leverage_limb(record(sector="Financial Services", ebitda=None), config)
    assert limb.state == NOT_APPLICABLE
    assert limb.state not in (PASS, FAIL, DATA_MISSING)


def test_a_non_financial_without_ebitda_is_data_missing(config):
    limb = leverage_limb(record(sector="Utilities", ebitda=None), config)
    assert limb.state == DATA_MISSING


def test_absent_debt_or_cash_is_data_missing(config):
    assert leverage_limb(record(debt=None), config).state == DATA_MISSING
    assert leverage_limb(record(cash=None), config).state == DATA_MISSING


def test_non_positive_ebitda_with_net_debt_fails(config):
    limb = leverage_limb(record(debt=200, cash=50, ebitda=-10), config)
    assert limb.state == FAIL


def test_non_positive_ebitda_with_net_cash_passes(config):
    limb = leverage_limb(record(debt=10, cash=500, ebitda=-10), config)
    assert limb.state == PASS


# --- the revenue limb: the ANNUAL fallback (B9's reading, kept) --------------


def test_a_rising_revenue_series_passes(config):
    limb = revenue_limb(record(revenue=(100, 110, 120, 130)), config)
    assert limb.state == PASS
    assert limb.detail.startswith("annual fallback (no quarterly revenue from the vendor)")


def test_one_down_year_does_not_flag(config):
    assert revenue_limb(record(revenue=(100, 90, 120, 130)), config).state == PASS


def test_two_consecutive_declines_flag(config):
    limb = revenue_limb(record(revenue=(130, 120, 110, 115)), config)
    assert limb.state == FLAG
    assert "2 consecutive" in limb.detail


def test_the_annual_fallback_never_rejects(config):
    """Where the vendor has no quarters the limb reads the annual series and
    only FLAGS -- B9's reading, kept for that case. BUCN.SW on 2026-08-26:
    a half-yearly reporter, no quarterly statement, three annual declines,
    FLAG, passed through."""
    bucher_shaped = [Candidate("BUCN.SW")]
    fundamentals = {"BUCN.SW": record("BUCN.SW", revenue=(160, 155, 150, 145))}
    result = run_filter2(bucher_shaped, fundamentals, config)
    assert [c.ticker for c in result.survivors] == ["BUCN.SW"]
    assert result.assessed["BUCN.SW"].state(LIMB_REVENUE) == FLAG
    assert result.tally.rejected == 0


def test_too_few_revenue_points_is_data_missing(config):
    assert revenue_limb(record(revenue=(100.0,)), config).state == DATA_MISSING
    assert revenue_limb(record(revenue=()), config).state == DATA_MISSING


# --- the revenue limb: QUARTERS, and the kill (E45) --------------------------


def _q(year, month, day=None):
    import calendar

    return date(year, month, day or calendar.monthrange(year, month)[1])


def _eight(values, ends=None):
    """Eight quarters oldest first, ending 2026-06-30."""
    ends = ends or [_q(2024, 9), _q(2024, 12), _q(2025, 3), _q(2025, 6),
                    _q(2025, 9), _q(2025, 12), _q(2026, 3), _q(2026, 6)]
    return list(zip(ends, values))


def test_two_consecutive_quarterly_yoy_declines_from_the_newest_quarter_kill(config):
    """KEMIRA.HE as the vendor carried it on 2026-08-26 (report B 8.2): Q2
    2026 693.0 against 693.4, Q1 2026 677.3 against 708.8 -- two declines
    at the newest end. FAIL, on value, with the changes printed."""
    kemira = record("KEMIRA.HE", revenue=(800, 760, 700, 660),
                    quarterly=_eight([650.0, 640.0, 708.8, 693.4, 680.0, 663.7, 677.3, 693.0]))
    limb = revenue_limb(kemira, config)
    assert limb.state == FAIL
    assert "2 consecutive quarterly YoY declines" in limb.detail
    assert "2026-06-30 -0.1%" in limb.detail and "2026-03-31 -4.4%" in limb.detail
    result = run_filter2([Candidate("KEMIRA.HE")], {"KEMIRA.HE": kemira}, config)
    assert result.survivors == []
    assert result.tally.rejected_on_value == 1 and result.tally.rejected_on_missing == 0
    assert "revenue_trend" in result.rejections[0].reason


def test_quarterly_growth_with_one_weak_year_passes(config):
    """The annual series carries a down year; the quarters are up year on
    year. The quarters decide, and the name passes."""
    grower = record("G", revenue=(100, 90, 120, 130),
                    quarterly=_eight([25, 26, 27, 28, 30, 31, 32, 33]))
    limb = revenue_limb(grower, config)
    assert limb.state == PASS
    assert limb.detail.startswith("quarterly YoY, newest first")


def test_a_single_newest_decline_after_growth_does_not_kill(config):
    weak_quarter = record("W", quarterly=_eight([25, 26, 27, 28, 30, 31, 32, 27]))
    assert revenue_limb(weak_quarter, config).state == PASS


def test_a_kill_is_counted_from_the_newest_quarter_not_anywhere_in_the_window(config):
    """Two declines a year ago followed by growth are not a current fade."""
    recovered = record("R", quarterly=_eight([30, 31, 32, 33, 29, 30, 34, 35]))
    assert revenue_limb(recovered, config).state == PASS


def test_a_hole_at_the_newest_end_falls_back_to_the_annual_series(config):
    """ERIC-B.ST on 2026-08-26: the 2025-03-31 revenue is NaN, so Q1 2026 has
    no year-ago quarter and only ONE comparison is measurable at the newest
    end. A kill is never struck across a hole: the annual series is read,
    it FLAGS on its three declines, and the detail says why."""
    ericsson = record("ERIC-B.ST", revenue=(160, 155, 150, 145),
                      quarterly=_eight([60.0, 62.0, None, 56.1, 56.2, 69.3, 49.3, 52.7]))
    limb = revenue_limb(ericsson, config)
    assert limb.state == FLAG
    assert limb.detail.startswith("annual fallback (quarters unavailable")
    assert "1 year-on-year comparison(s) measurable" in limb.detail
    assert "3 consecutive annual declines" in limb.detail


def test_a_missing_quarter_is_matched_by_date_never_by_position(config):
    """KEMIRA's other shape: 2025-09-30 absent (#1345). Positions shift;
    dates do not. Q2 2026 still finds Q2 2025 a year back, and a quarter
    with no year-ago quarter is a hole, not a comparison with the wrong one."""
    ends = [_q(2025, 3), _q(2025, 6), _q(2025, 12), _q(2026, 3), _q(2026, 6)]
    holed = record("H", quarterly=list(zip(ends, [100, 100, 100, 90, 90])))
    limb = revenue_limb(holed, config)
    assert limb.state == FAIL
    assert "2026-06-30 -10.0%" in limb.detail and "2026-03-31 -10.0%" in limb.detail
    assert "2025-12-31 --" in limb.detail, "no 2024-12-31 quarter a year back"


def test_una_as_shape_is_now_removed_on_its_reported_quarters(config):
    """E45's stated cost. B9 was decided on UNA.AS: four consecutive
    reported declines while organic growth was positive in all eight
    quarters. The screener cannot read the organic series, so the name
    FAILS here; the organic carve-out governs the hand chain."""
    unilever = record("UNA.AS", quarterly=_eight([100, 100, 100, 100, 95.4, 96.5, 97.3, 96.7]))
    limb = revenue_limb(unilever, config)
    assert limb.state == FAIL
    assert "4 consecutive quarterly YoY declines" in limb.detail


def test_the_quarterly_config_is_validated(tmp_path: Path):
    text = (ROOT / FILTER2_CONFIG_PATH).read_text(encoding="utf-8")
    bad = tmp_path / "f2.yaml"
    bad.write_text(text.replace("year_ago_window_days: [350, 380]",
                                "year_ago_window_days: [380, 350]"), encoding="utf-8")
    with pytest.raises(Filter2Error, match="year_ago_window_days"):
        load_filter2_config(bad)
    bad.write_text(text.replace("      action: FLAG        # B9's reading",
                                "      action: MAYBE       # B9's reading"), encoding="utf-8")
    with pytest.raises(Filter2Error, match="annual_fallback.action"):
        load_filter2_config(bad)


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
    assert len(result.assessed["A"].untested) == 3


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
    assert result.assessed["HSBA.L"].state(LIMB_LEVERAGE) == NOT_APPLICABLE
    assert result.assessed["HSBA.L"].state(LIMB_FCF) == PASS


def test_the_limb_matrix_separates_all_five_states(config):
    candidates = [Candidate(t) for t in ("A", "B", "C")]
    fundamentals = {
        "A": record("A"),
        "B": record("B", sector="Financial Services", ebitda=None),
        "C": record("C", ebitda=None, sector="Utilities"),
    }
    result = run_filter2(candidates, fundamentals, config)
    matrix = limb_matrix(result.assessed)
    assert matrix[LIMB_LEVERAGE][PASS] == 1
    assert matrix[LIMB_LEVERAGE][NOT_APPLICABLE] == 1
    assert matrix[LIMB_LEVERAGE][DATA_MISSING] == 1


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


def test_a_listed_investment_company_is_not_applicable_whatever_its_string(config):
    """Latour comes back Industrials / Conglomerates and was ranked at 263
    on 2026-08-26 (report 7.3). The list decides, before the string."""
    latour = record("LATO-B.ST", sector="Industrials", debt=400, cash=50, ebitda=100)
    limb = leverage_limb(latour, config)
    assert limb.state == NOT_APPLICABLE and "E46" in limb.detail
    same_string = record("LIFCO-B.ST", sector="Industrials", debt=400, cash=50, ebitda=100)
    assert leverage_limb(same_string, config).state == FAIL


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


def test_the_limb_pairs_lease_inclusive_debt_with_the_statement_ebitda_not_the_info_field(config):
    """AD.AS as stored on 2026-08-26: totalDebt 19,261 (leases inside), cash
    3,211, the vendor's info field 5,388 (no ROU depreciation) and four
    consecutive statement quarters summing to 7,310. 2.98x -> 2.20x."""
    from vss.filters import statement_ebitda
    q = [(date(2025, 9, 30), 1839.0), (date(2025, 12, 31), 1896.0),
         (date(2026, 3, 31), 1795.0), (date(2026, 6, 30), 1780.0)]
    e = [(date(2025, 9, 30), 954.0), (date(2025, 12, 31), 936.0),
         (date(2026, 3, 31), 917.0), (date(2026, 6, 30), 891.0)]
    r = record(debt=19261.0, cash=3211.0, ebitda=5388.0, ebitda_annual=7304.0,
               ebitda_quarters=q, ebit_quarters=e)
    assert statement_ebitda(r) == (7310.0, "TTM to 2026-06-30")
    limb = leverage_limb(r, config)
    assert limb.state == PASS
    assert "2.20x" in limb.detail and "TTM to 2026-06-30" in limb.detail
    assert "5,388" in limb.detail and "not read" in limb.detail


def test_a_quarterly_line_that_equals_ebit_is_a_hole_and_the_annual_line_is_read(config):
    """The vendor's quarterly EBITDA equals EBIT for some filers (no D&A
    add-back): not a figure. The newest annual line stands in."""
    from vss.filters import statement_ebitda
    q = [(date(2025, 9, 30), 500.0), (date(2025, 12, 31), 500.0),
         (date(2026, 3, 31), 500.0), (date(2026, 6, 30), 500.0)]
    e = [(date(2025, 9, 30), 500.0), (date(2025, 12, 31), 500.0),
         (date(2026, 3, 31), 500.0), (date(2026, 6, 30), 500.0)]
    r = record(debt=450.0, cash=50.0, ebitda=100.0, ebitda_annual=400.0,
               ebitda_quarters=q, ebit_quarters=e)
    assert statement_ebitda(r) == (400.0, "annual to 2025-12-31")
    assert leverage_limb(r, config).state == PASS            # 400 / 400 = 1.0x


def test_four_quarters_with_a_hole_between_them_are_not_a_year(config):
    from vss.filters import statement_ebitda
    q = [(date(2025, 3, 31), 100.0), (date(2025, 6, 30), 100.0),
         (date(2025, 12, 31), 100.0), (date(2026, 3, 31), 100.0)]   # 2025-09 missing
    r = record(ebitda=100.0, ebitda_annual=350.0, ebitda_quarters=q)
    assert statement_ebitda(r) == (350.0, "annual to 2025-12-31")


def test_no_statement_ebitda_is_DATA_MISSING_even_when_the_info_field_exists(config):
    """E4: refused, with the reason, rather than a ratio on the wrong pair."""
    limb = leverage_limb(record(debt=450.0, cash=50.0, ebitda=100.0, ebitda_annual=None), config)
    assert limb.state == DATA_MISSING
    assert "no EBITDA on the filer's statements" in limb.detail and "100" in limb.detail


def test_net_cash_passes_without_any_ebitda(config):
    assert leverage_limb(record(debt=10.0, cash=500.0, ebitda=None, ebitda_annual=None),
                         config).state == PASS
