"""`vss xbrl --annual`: the annual facts section 5 needs, written into a
manual file.

ONE TEST GROUP PER DESIGN RULE, and the rules are numbered as the owner
wrote them:

  1. It WRITES A MANUAL FILE in the existing schema, so section 5 reads it
     through `vss manual` -- same validation, same E21 gate, same basis
     machinery. Origin marks it; the tag and accession are its page.
  2. It DERIVES NOTHING. An absent tag is DATA MISSING and is named.
  3. It NEVER MIXES SOURCES within one ticker's history.
  4. ANNUAL, not quarterly.
  5. Backup with a purpose suffix and a TIME in the filename.
  6. No AI anywhere in it.

THE FIXTURE IS NIKE's FY2025 and FY2026 AS FILED, trimmed to the tags this
path maps. Real figures, because the point of the last test in the file is
that the fair value the owner struck by hand on 2026-08-25 -- 22.15 at base
3%, r 9.5%, on FCF basis 1 -- is REPRODUCED BY THIS PATH GIVEN THE EIGHT
CHOICES DECLARED ON THAT TEST. It is not a known-correct value and must not
be read as one (REVIEW-4 report C 9.3 #2). It
carries the traps that are real for this filer: no OperatingIncomeLoss, no
FinanceLeasePrincipalPayments, no PaymentsToAcquireIntangibleAssets, a year
that ends 31 May, and an OperatingLeasePayments that must NOT be written.
"""

import json
from datetime import date, datetime, timedelta
from pathlib import Path

import pytest
import yaml

from vss import manual as M
from vss import xbrl as X
from vss.config import ConfigError

USD = "USD"


def _fact(val, *, start=None, end=None, accn="0000320187-26-000088",
          form="10-K", filed="2026-07-15"):
    entry = {"val": val, "end": end, "accn": accn, "form": form, "filed": filed}
    if start:
        entry["start"] = start
    return entry


FY25 = ("2024-06-01", "2025-05-31")
FY26 = ("2025-06-01", "2026-05-31")


def facts(**drop_or_add):
    """NIKE's two most recent years as filed, as a companyfacts payload."""
    gaap = {
        "RevenueFromContractWithCustomerExcludingAssessedTax": {"units": {USD: [
            _fact(46_309_000_000, start=FY25[0], end=FY25[1]),
            _fact(46_398_000_000, start=FY26[0], end=FY26[1])]}},
        "NetIncomeLoss": {"units": {USD: [
            _fact(3_219_000_000, start=FY25[0], end=FY25[1]),
            _fact(3_108_000_000, start=FY26[0], end=FY26[1])]}},
        "EarningsPerShareDiluted": {"units": {"USD/shares": [
            _fact(2.16, start=FY25[0], end=FY25[1]),
            _fact(2.10, start=FY26[0], end=FY26[1])]}},
        "NetCashProvidedByUsedInOperatingActivities": {"units": {USD: [
            _fact(3_698_000_000, start=FY25[0], end=FY25[1]),
            _fact(2_868_000_000, start=FY26[0], end=FY26[1])]}},
        "PaymentsToAcquirePropertyPlantAndEquipment": {"units": {USD: [
            _fact(430_000_000, start=FY25[0], end=FY25[1]),
            _fact(684_000_000, start=FY26[0], end=FY26[1])]}},
        # Read, and DELIBERATELY NOT WRITTEN: under ASC 842 this is already
        # inside operating cash flow.
        "OperatingLeasePayments": {"units": {USD: [
            _fact(647_000_000, start=FY25[0], end=FY25[1]),
            _fact(668_000_000, start=FY26[0], end=FY26[1])]}},
        "CashAndCashEquivalentsAtCarryingValue": {"units": {USD: [
            _fact(7_464_000_000, end="2025-05-31"),
            _fact(7_563_000_000, end="2026-05-31")]}},
        "LongTermDebtCurrent": {"units": {USD: [
            _fact(0, end="2025-05-31"),
            _fact(2_000_000_000, end="2026-05-31")]}},
        "LongTermDebtNoncurrent": {"units": {USD: [
            _fact(7_961_000_000, end="2025-05-31"),
            _fact(5_942_000_000, end="2026-05-31")]}},
        "OperatingLeaseLiability": {"units": {USD: [
            _fact(3_052_000_000, end="2025-05-31"),
            _fact(3_091_000_000, end="2026-05-31")]}},
        "OperatingLeaseLiabilityCurrent": {"units": {USD: [
            _fact(478_000_000, end="2026-05-31")]}},
        "OperatingLeaseLiabilityNoncurrent": {"units": {USD: [
            _fact(2_613_000_000, end="2026-05-31")]}},
        "WeightedAverageNumberOfDilutedSharesOutstanding": {"units": {"shares": [
            _fact(1_487_600_000, start=FY25[0], end=FY25[1]),
            _fact(1_481_000_000, start=FY26[0], end=FY26[1])]}},
    }
    for tag, value in drop_or_add.items():
        if value is None:
            gaap.pop(tag, None)
        else:
            gaap[tag] = value
    return {"entityName": "NIKE, Inc.", "facts": {"us-gaap": gaap}}


WATCHLIST = """
tickers:
  - ticker: NKE
    name: Nike
    currency: USD
    status: WATCH-GATED
    cik: 320187
    exec_changes: []
    quarters: []
"""

RUN_TS = datetime(2026, 8, 25, 22, 14, 3)


@pytest.fixture
def project(tmp_path):
    (tmp_path / "watchlist.yaml").write_text(WATCHLIST)
    (tmp_path / "manual").mkdir()
    return tmp_path


def run(project, *, payload=None, **kw):
    params = dict(ticker="NKE", watchlist_path=project / "watchlist.yaml",
                  db_path=project / "vss.sqlite",
                  manual_dir=project / "manual", now=RUN_TS,
                  fetcher=lambda cik: payload if payload is not None else facts())
    params.update(kw)
    return X.run_xbrl_annual(**params)


def emitted(project, **kw):
    """The written file, parsed back through the MANUAL loader."""
    code, report = run(project, write=True, **kw)
    target = project / "manual" / "NKE.yaml"
    parsed = M.parse_manual(yaml.safe_load(target.read_text()), path=target)
    return code, report, parsed


# --- RULE 1: it writes a manual file, in the existing schema --------------


def test_every_field_this_path_writes_is_a_field_the_schema_already_has():
    """The tag map may not invent a field name. A field the loader does not
    know is a figure nothing ever reads."""
    for spec in X.ANNUAL_FIELDS:
        assert spec.field in M.FIGURE_KEYS, spec.field
    assert "capex_combined" in {s.field for s in X.ANNUAL_FIELDS}


def test_it_writes_a_file_the_manual_loader_accepts(project):
    code, report, parsed = emitted(project)
    assert code == 0
    assert parsed.origin == M.ORIGIN_XBRL
    assert parsed.ticker == "NKE"
    assert parsed.reporting_currency == "USD"
    # ANNUAL entries, not periods -- see rule 4.
    assert parsed.periods == ()
    assert [a.fiscal_year for a in parsed.annual] == [2025, 2026]


def test_section_5_reads_it_through_the_same_basis_machinery(project):
    """E19's `annual as filed` branch, and no new branch beside it."""
    _, _, parsed = emitted(project)
    basis = M.section5_basis(parsed)
    assert basis.kind == "as filed"
    assert basis.label == "annual FY2026"
    assert basis.end == date(2026, 5, 31)
    assert M.resolve_on_basis(parsed, basis, "operating_cash_flow").value \
        == 2_868_000_000


def test_the_tag_and_the_accession_are_the_page_reference(project):
    """Rule 1: an XBRL figure's page is its provenance, not a page number."""
    _, _, parsed = emitted(project)
    figure = parsed.annual[-1].figures["operating_cash_flow"]
    assert "us-gaap:NetCashProvidedByUsedInOperatingActivities" in figure.page
    assert "2025-06-01..2026-05-31" in figure.page
    assert "0000320187-26-000088" in figure.page
    assert "10-K" in figure.page


def test_E40_a_tagged_fact_is_VERIFIED_by_provenance(project):
    """RULED (E40, 2026-08-26). Until then every figure landed UNVERIFIED and
    E21 refused on each one the basis read -- the single gate in front of
    the only fetched path. A tagged fact is verified by tag + accession +
    filing date, its kind is `tagged`, and the gate refuses nothing on it."""
    _, report, parsed = emitted(project)
    present = [f for f in parsed.all_figures() if f.present]
    assert present and all(f.verified for f in present)
    assert {f.verified_kind for f in present} == {M.KIND_TAGGED}
    gate = M.section5_gate(parsed, as_of=date(2026, 8, 25))
    assert not any(r.kind == M.REFUSE_UNVERIFIED for r in gate.refusals)
    assert "VERIFIED / tagged (E40)" in report


def test_a_tagged_zero_carries_e25_evidence(project):
    """A zero the FILER tagged is the issuer listing the line and stating
    nil -- E25's `caption` form, and evidence the filer supplied."""
    _, _, parsed = emitted(project)
    zero = parsed.annual[0].figures["financial_liabilities_current"]
    assert zero.value == 0 and zero.zero_basis == M.ZERO_CAPTION


# --- RULE 2: it derives nothing -------------------------------------------


def test_an_absent_tag_is_data_missing_and_is_named(project):
    """NIKE tags no FinanceLeasePrincipalPayments. The field stays empty and
    the report says so -- it is not filled from anything else."""
    _, report, parsed = emitted(project)
    assert parsed.annual[-1].value("lease_payments_capital") is None
    assert "`lease_payments_capital`" in report
    assert "`FinanceLeasePrincipalPayments`" in report
    assert "DATA MISSING" in report


def test_E70_the_operating_lease_payment_is_written_as_the_add_back_and_the_file_declares_it(project):
    """Until E70 (2026-08-30) OperatingLeasePayments was READ AND REFUSED:
    under ASC 842 it is inside operating cash flow, and writing it looked
    like basis 2 deducting it twice (B33). E70 turned it round: the lease
    is charged once, in net debt, so the payment the flow bore is the
    ADD-BACK, and the file says the flow bore it."""
    _, report, parsed = emitted(project)
    written = {f.name for f in parsed.all_figures() if f.present}
    assert "lease_payments_capital" not in written             # NIKE tags no finance lease
    assert "operating_lease_payments" in written
    assert parsed.annual[-1].value("operating_lease_payments") == 668_000_000
    assert parsed.operating_leases_in_ocf is not None
    assert parsed.operating_leases_in_ocf.value is True
    assert "ASC 842-20-45-5(a)" in parsed.operating_leases_in_ocf.page
    tags = {t for spec in X.ANNUAL_FIELDS for t in spec.tags}
    assert "OperatingLeasePayments" in tags
    assert not any(tag == "OperatingLeasePayments" for tag, _, _ in X.NOT_WRITTEN)
    # the fixture carries no interest figure, so FCF0 waits on THAT leg, not
    # on the lease leg
    ratios = {r.name: r for r in M.ratio_states(parsed)}
    assert "operating_lease_payments" not in ratios["free cash flow, FCF0 (E34)"].detail


def test_E71_two_captions_and_no_stated_total_are_added_with_both_named(project):
    """The filer states the current and non-current lease liability and
    never their total. Until E71 (2026-08-30) that was E26's DATA MISSING;
    E71 adds two stated parts of one quantity, and the filer's own choice of
    the taxonomy's two portion elements is its statement that they are one.
    Both parts are named on the figure."""
    _, report, parsed = emitted(project, payload=facts(OperatingLeaseLiability=None))
    fig = parsed.annual[-1].figures["lease_liabilities"]
    assert fig.value == 3_091_000_000                       # 478 + 2,613
    assert "E71" in fig.page
    assert "OperatingLeaseLiabilityCurrent" in fig.page
    assert "OperatingLeaseLiabilityNoncurrent" in fig.page
    assert "E71" in report and "478" in report and "2,613" in report


def test_E26_a_lone_lease_part_is_still_not_the_total(project):
    """One portion tagged and no total: E71 has nothing to add, and the
    lone part is E26's DATA MISSING, named and never the field."""
    _, report, parsed = emitted(project, payload=facts(
        OperatingLeaseLiability=None, OperatingLeaseLiabilityCurrent=None))
    assert parsed.annual[-1].value("lease_liabilities") is None
    assert "E26" in report and "2,613" in report
    assert "3,091" not in report


def test_the_only_transformation_is_the_sign_of_a_payments_element(project):
    """us-gaap states an outflow POSITIVE; this schema states it negative,
    because section 5 SUMS the capex legs into operating cash flow. The
    magnitude is untouched.

    WHAT THE -684,000,000 IS, DECLARED (REVIEW-4 report C 9.3 #5, report B
    6.3). It sits in `capex_combined`, whose ruling (E23) defines the field
    as *the single line an issuer prints when it does not split property,
    plant and equipment from intangibles* -- Betsson's "Investments in
    intangibles/tangibles", a line that genuinely holds both. NIKE's holds
    PROPERTY, PLANT AND EQUIPMENT AND NOTHING ELSE, because NIKE tags no
    intangible capital spend at all.

    That is not a defect in the placement and it is not corrected here: the
    field records the ISSUER'S CAPEX PRESENTATION, which is why the page
    reference names the exact tag rather than the field name. What it means
    for the figure is stated so nobody has to rediscover it: **any
    capitalised spend NIKE books under a third element this path does not
    read is outside FCF0, and free cash flow is that much too high.** No
    such element is in NIKE's facts, so the size today is zero; for a filer
    that has one it is not."""
    _, _, parsed = emitted(project)
    assert parsed.annual[-1].value("capex_combined") == -684_000_000
    negated = {s.field for s in X.ANNUAL_FIELDS if s.negate}
    # E34.1 added one: `InterestIncomeExpenseNonoperatingNet` is POSITIVE for
    # a net INCOME and this schema holds a net COST positive, so the sign is
    # flipped there too -- the element's convention, not an outflow.
    # 2026-08-29 added `capex_combined`: the us-gaap map now reads one
    # Payments element of its own for E23's one line (AOS), an outflow.
    # 2026-09-04 added `nci_dividends_paid`: E105's leg. The three us-gaap
    # elements that answer it (`PaymentsOfDividendsMinorityInterest` and the
    # two a filer uses instead) all state a POSITIVE payment, and FCF0 sums
    # this leg in like capex.
    assert negated == {"capex_ppe", "capex_intangibles", "capex_combined",
                       "lease_payments_capital", "net_finance_costs",
                       "nci_dividends_paid"}
    for spec in X.ANNUAL_FIELDS:
        if not spec.negate:
            continue
        assert "sign" in spec.note.lower() or "outflow" in spec.note.lower() \
            or "FINANCING" in spec.note


def test_no_figure_is_summed_out_of_two_others(project):
    """Every written value equals a value that is IN THE FACTS, up to sign --
    except the three sums of STATED captions E65, E66 and E68 authorise
    (2026-08-29), each of which names every component on its page line and
    is tested on its own below. The NIKE fixture triggers none of them."""
    payload = facts()
    _, _, parsed = emitted(project, payload=payload)
    stated = {abs(float(e["val"]))
              for node in payload["facts"]["us-gaap"].values()
              for entries in node["units"].values() for e in entries}
    for figure in parsed.all_figures():
        if figure.present:
            assert not figure.page.startswith(("E65", "E66", "E68")), figure.name
            assert abs(figure.value) in stated, figure.name


def test_a_lone_intangibles_line_is_not_promoted_to_the_combined_field(project):
    """E23: an intangibles line alone is not an issuer's capital spending.
    It stays a lone split leg, which E23 refuses to use, so free cash flow
    is DATA MISSING rather than understated."""
    payload = facts(
        PaymentsToAcquirePropertyPlantAndEquipment=None,
        PaymentsToAcquireIntangibleAssets={"units": {USD: [
            _fact(9_000_000, start=FY26[0], end=FY26[1])]}})
    _, _, parsed = emitted(project, payload=payload)
    year = parsed.annual[-1]
    assert year.value("capex_intangibles") == -9_000_000
    assert year.value("capex_combined") is None
    ratios = {r.name: r for r in M.ratio_states(parsed)}
    assert ratios["free cash flow, basis 1"].state == M.RATIO_MISSING


def test_both_capex_lines_tagged_means_the_split_pair(project):
    """E23: the split wins where the issuer prints it."""
    payload = facts(PaymentsToAcquireIntangibleAssets={"units": {USD: [
        _fact(9_000_000, start=FY26[0], end=FY26[1])]}})
    _, report, parsed = emitted(project, payload=payload)
    year = parsed.annual[-1]
    assert year.value("capex_ppe") == -684_000_000
    assert year.value("capex_intangibles") == -9_000_000
    assert year.value("capex_combined") is None
    assert "split" in report


# --- RULE 3: it never mixes sources within one ticker's history -----------


def test_a_file_of_another_origin_is_not_overwritten(project):
    """XBRL states whole units; a press release states millions. A history
    holding both passes every check in the loader and means nothing."""
    target = project / "manual" / "NKE.yaml"
    target.write_text("ticker: NKE\nname: Nike\norigin: manual\n")
    with pytest.raises(X.XbrlError) as exc:
        X.write_manual_file("x", target, run_ts=RUN_TS)
    assert "origin `manual`" in str(exc.value)
    assert "WHOLE UNITS" in str(exc.value)
    assert target.read_text().startswith("ticker: NKE")


def test_force_does_not_open_the_mixed_origin_refusal(project):
    """Which source a name is kept on is the owner's decision, not a flag."""
    target = project / "manual" / "NKE.yaml"
    target.write_text("ticker: NKE\nname: Nike\norigin: nordic-xlsx\n")
    with pytest.raises(X.XbrlError, match="does NOT open"):
        X.write_manual_file("x", target, run_ts=RUN_TS, force=True)


def test_the_run_refuses_rather_than_writing_beside_another_origin(project):
    """End to end: the command exits non-zero and the file is untouched."""
    target = project / "manual" / "NKE.yaml"
    target.write_text("ticker: NKE\nname: Nike\norigin: manual\n")
    code, report = run(project, write=True)
    assert code == 1
    assert "NOT OVERWRITTEN" in report
    assert target.read_text() == "ticker: NKE\nname: Nike\norigin: manual\n"


def test_a_file_that_does_not_load_is_not_overwritten_either(project):
    """Nothing can say what it holds or where it came from."""
    target = project / "manual" / "NKE.yaml"
    target.write_text("ticker: NKE\nname: Nike\norigin: not-an-origin\n")
    with pytest.raises(X.XbrlError, match="does not load"):
        X.write_manual_file("x", target, run_ts=RUN_TS)


def test_a_READING_is_not_flattened_without_force_but_a_tagged_flag_is_regenerable(project):
    """The status flag records work only a person can do -- and E40 says
    which flags are that work. A `tagged` flag is provenance this same path
    writes again, so a file of tagged flags is rewritten freely; ONE
    `same_page` or `cross_document` flag stops the write."""
    emitted(project)
    target = project / "manual" / "NKE.yaml"
    X.write_manual_file(target.read_text(), target, run_ts=RUN_TS)   # all tagged
    target.write_text(target.read_text().replace(
        "verified_kind: tagged", "verified_kind: same_page", 1))
    with pytest.raises(X.XbrlError, match="by a READING"):
        X.write_manual_file("x", target, run_ts=RUN_TS)
    X.write_manual_file("ticker: NKE\nname: Nike\norigin: sec-xbrl\n", target,
                        run_ts=RUN_TS, force=True)
    assert target.read_text().endswith("origin: sec-xbrl\n")


# --- RULE 4: annual, not quarterly ---------------------------------------


def test_a_quarter_length_window_is_not_read(project):
    """The quarter shape is a different command. A three-month duration in
    the facts must not become a fiscal year here."""
    payload = facts()
    payload["facts"]["us-gaap"]["NetCashProvidedByUsedInOperatingActivities"] \
        ["units"][USD].append(_fact(1_000_000_000, start="2026-03-01",
                                    end="2026-05-31"))
    _, _, parsed = emitted(project, payload=payload)
    assert [a.fiscal_year for a in parsed.annual] == [2025, 2026]
    assert parsed.annual[-1].value("operating_cash_flow") == 2_868_000_000


def test_the_entries_go_in_the_annual_block_and_carry_no_period_label(project):
    """E15's block is keyed on the FISCAL YEAR. A year that ends in another
    calendar year is an ordinary entry there and a label problem in
    `periods:` -- which is why this path writes no period labels at all."""
    _, _, parsed = emitted(project)
    assert parsed.periods == ()
    assert all(a.period_end.month == 5 for a in parsed.annual)
    assert parsed.annual[-1].period_end == date(2026, 5, 31)


def test_the_report_names_every_year_and_where_it_ends(project):
    _, report, _ = emitted(project)
    assert "FISCAL YEARS RETURNED" in report
    assert "2026-05-31" in report and "2025-05-31" in report
    assert "annual FY2026" in report


def test_a_window_outside_the_fiscal_year_end_month_is_passed_over_and_named(
        project):
    """A trailing twelve months or a stub. Named rather than dropped.

    A 52/53-WEEK YEAR IS NO LONGER IN THAT LIST, and the docstring used to
    say it was (REVIEW-4 report C 9.3 #6). `xbrl.py`'s own comment called
    the drifting 52/53-week filer "exactly the case where this rule is
    wrong", and the case was live on the watchlist -- see the two tests
    below. The window added here is a calendar-year stub on a May filer,
    215 days from the anchor, which is a stub under any tolerance."""
    payload = facts()
    payload["facts"]["us-gaap"]["NetCashProvidedByUsedInOperatingActivities"] \
        ["units"][USD].append(_fact(9_000_000_000, start="2025-01-01",
                                    end="2025-12-31"))
    _, report, parsed = emitted(project, payload=payload)
    assert [a.fiscal_year for a in parsed.annual] == [2025, 2026]
    assert "PASSED OVER" in report and "2025-12-31" in report


def _drifting_year_facts():
    """A 52/53-week filer whose year end walks across a month boundary.

    LULU's shape, and its dates: FY2024 ends 2024-01-28, FY2025 2025-02-02,
    FY2026 2026-02-01. The modal month of the annual durations is JANUARY,
    so under a bare same-month rule the two NEWEST years are passed over and
    an 18-month-old one is chosen.
    """
    windows = (("2023-01-30", "2024-01-28", 2_296_164_000),
               ("2024-01-29", "2025-02-02", 2_272_713_000),
               ("2025-02-03", "2026-02-01", 1_602_477_000),
               ("2021-02-01", "2022-01-30", 1_389_108_000),
               ("2022-01-31", "2023-01-29", 966_463_000))
    return {"facts": {"us-gaap": {
        "RevenueFromContractWithCustomerExcludingAssessedTax": {"units": {USD: [
            _fact(v, start=a, end=b) for a, b, v in windows]}},
        "NetCashProvidedByUsedInOperatingActivities": {"units": {USD: [
            _fact(v, start=a, end=b) for a, b, v in windows]}},
    }}}


def test_a_52_53_week_year_that_drifts_a_few_days_is_STILL_the_year_as_filed():
    """The half the suite did not carry (report C 9.3 #6, report B 5.1).

    RUN on the live filer before the fix: LULU's FY2025 and FY2026 were
    passed over, FY2024 was chosen, and the basis read 940 days old ->
    STALE. A loud failure rather than a wrong number, and only because the
    modal month happened to match the OLDER year; nothing prevents the
    reverse.
    """
    facts_ = _drifting_year_facts()
    month = X.fiscal_year_end_month(facts_, X.US_GAAP, "USD")
    assert month == 1                                     # January, modal
    ends, passed_over = X.fiscal_year_ends(facts_, month, currency="USD")
    assert ends[-2:] == ["2025-02-02", "2026-02-01"]      # both kept
    assert passed_over == []
    years, _ = X.build_annual(facts_, currency="USD")
    assert years[-1].end == date(2026, 2, 1)
    assert years[-1].value("operating_cash_flow") == 1_602_477_000


def _moved_year_end_facts(new_ends=("2022-06-30", "2023-06-30", "2024-06-30",
                                    "2025-06-30", "2026-06-30")):
    """HRB's shape: April years 2014-2021, then the year end moved to June."""
    old = [(f"{y - 1}-05-01", f"{y}-04-30") for y in range(2014, 2022)]
    new = [(str(date.fromisoformat(e) - timedelta(days=364)), e) for e in new_ends]
    return {"facts": {"us-gaap": {
        "RevenueFromContractWithCustomerExcludingAssessedTax": {"units": {USD: [
            _fact(1_000_000, start=a, end=b) for a, b in old + new]}},
        "NetCashProvidedByUsedInOperatingActivities": {"units": {USD: [
            _fact(1_000_000, start=a, end=b) for a, b in old + new]}},
    }}}


def test_a_filer_that_MOVED_its_year_end_is_read_on_the_new_month():
    """HRB, 2026-09-17: eight April years outvoted five June ones, every
    year since the move was passed over and the basis read FY2021."""
    facts_ = _moved_year_end_facts()
    month = X.fiscal_year_end_month(facts_, X.US_GAAP, "USD")
    assert month == 6
    ends, passed_over = X.fiscal_year_ends(facts_, month, currency="USD")
    assert ends[-1] == "2026-06-30"
    assert "2021-04-30" in passed_over          # the old years are named


def test_one_window_on_a_new_month_is_not_a_move():
    facts_ = _moved_year_end_facts(new_ends=("2026-06-30",))
    assert X.fiscal_year_end_month(facts_, X.US_GAAP, "USD") == 4


def test_two_stubs_on_different_months_are_not_a_move():
    facts_ = _moved_year_end_facts(new_ends=("2025-09-30", "2026-06-30"))
    assert X.fiscal_year_end_month(facts_, X.US_GAAP, "USD") == 4


def test_the_tolerance_is_a_week_and_a_stub_is_still_a_stub():
    facts_ = _drifting_year_facts()
    gaap = facts_["facts"]["us-gaap"]
    gaap["NetCashProvidedByUsedInOperatingActivities"]["units"][USD].append(
        _fact(9_000_000_000, start="2025-03-01", end="2026-02-28"))
    ends, passed_over = X.fiscal_year_ends(facts_, 1, currency="USD")
    assert "2026-02-28" in passed_over          # 28 days from the anchor
    assert "2026-02-01" in ends
    assert X.FISCAL_YEAR_END_TOLERANCE_DAYS == 7


def test_two_windows_within_a_week_of_one_anchor_leave_only_the_closest():
    """With a tolerance, a TTM stub can sit beside the year it shadows.
    Both would become an `annual:` entry keyed on the same year."""
    facts_ = _drifting_year_facts()
    gaap = facts_["facts"]["us-gaap"]
    gaap["NetCashProvidedByUsedInOperatingActivities"]["units"][USD].append(
        _fact(1_000_000_000, start="2025-01-31", end="2026-01-30"))
    ends, passed_over = X.fiscal_year_ends(facts_, 1, currency="USD")
    assert "2026-01-30" in ends                 # 1 day from 2026-01-31
    assert "2026-02-01" in passed_over          # 1 day too, and earlier
    assert len([e for e in ends if e.startswith("2026")]) == 1


def test_a_filer_with_no_annual_facts_is_refused_not_guessed(project):
    payload = {"entityName": "X", "facts": {"us-gaap": {}}}
    code, report = run(project, payload=payload, write=True)
    assert code == 1
    assert not (project / "manual" / "NKE.yaml").exists()


# --- RULE 5: a backup carries a TIME, not only a date --------------------


def test_the_backup_name_carries_the_time_and_a_purpose(tmp_path):
    name = X.backup_name(tmp_path / "NKE.yaml", RUN_TS).name
    assert name == "NKE.yaml.bak-2026-08-25-221403-pre-xbrl"


def test_two_runs_in_one_day_do_not_overwrite_each_others_backup(project):
    """The known defect on three writers in this project: a date-only stamp
    loses the earlier of two runs made on one day."""
    target = project / "manual" / "NKE.yaml"
    target.write_text("ticker: NKE\nname: Nike\norigin: sec-xbrl\n")
    morning = datetime(2026, 8, 25, 9, 30, 0)
    evening = datetime(2026, 8, 25, 22, 14, 3)
    X.write_manual_file("ticker: NKE\nname: A\norigin: sec-xbrl\n", target,
                        run_ts=morning)
    X.write_manual_file("ticker: NKE\nname: B\norigin: sec-xbrl\n", target,
                        run_ts=evening)
    backups = sorted(p.name for p in target.parent.glob("*.bak-*"))
    assert backups == ["NKE.yaml.bak-2026-08-25-093000-pre-xbrl",
                       "NKE.yaml.bak-2026-08-25-221403-pre-xbrl"]
    assert "name: Nike" in (target.parent /
                            "NKE.yaml.bak-2026-08-25-093000-pre-xbrl").read_text()


def test_the_run_names_the_backup_it_made(project):
    target = project / "manual" / "NKE.yaml"
    target.write_text("ticker: NKE\nname: Nike\norigin: sec-xbrl\n")
    _, report = run(project, write=True)
    assert "bak-2026-08-25-221403-pre-xbrl" in report
    assert "carries the TIME" in report


# --- RULE 6: no AI anywhere in it ----------------------------------------


def test_nothing_in_this_path_reaches_a_model(project, monkeypatch):
    """Deterministic tag reads. The run's own record says `model: None`, and
    the module imports no client library to reach one with."""
    import sqlite3

    source = Path(X.__file__).read_text()
    for name in ("anthropic", "openai", "langchain", "google.generativeai",
                 "litellm", "transformers"):
        assert name not in source, name

    # THE ONLY ENDPOINT IS data.sec.gov, and it is asserted on the CALL
    # rather than on the source text: a URL that appears in an error message
    # is not a URL anybody fetches, and a scan of the source cannot tell the
    # two apart. `urlopen` is broken here, so any network reach at all --
    # to a model or to anything else -- fails the test rather than escaping
    # it.
    import urllib.request

    assert X.API_URL.startswith("https://data.sec.gov/")

    def forbidden(*a, **kw):
        raise AssertionError("this path reached the network")

    monkeypatch.setattr(urllib.request, "urlopen", forbidden)

    run(project, write=True)
    conn = sqlite3.connect(project / "vss.sqlite")
    rows = conn.execute("SELECT model, raw_response FROM earnings_runs").fetchall()
    conn.close()
    assert rows and all(model is None for model, _ in rows)


def test_the_same_facts_produce_the_same_bytes(project, tmp_path):
    """Deterministic: no ordering, no clock and no model in the output."""
    first = X.manual_yaml(ticker="NKE", name="Nike", cik=320187,
                          quote_currency="USD",
                          years=X.build_annual(facts())[0], run_ts=RUN_TS)
    second = X.manual_yaml(ticker="NKE", name="Nike", cik=320187,
                           quote_currency="USD",
                           years=X.build_annual(facts())[0], run_ts=RUN_TS)
    assert first == second


# --- the store-to-engine path, with its assumptions declared -------------
#
# THIS SECTION WAS HEADED "the verification the build was measured against"
# and the module docstring called 22.15 a figure that "comes back out of this
# path unchanged". Both readings are the "known-correct" label REVIEW-4
# report C 9.3 #2 warns of. 22.15 IS THE ARITHMETIC OF ONE DAY'S CHOICES,
# and the choices are declared on the test.


def test_nke_reproduces_the_fair_value_struck_by_hand(project):
    """PINS ARITHMETIC GIVEN THE EIGHT DECLARATIONS BELOW.

    22.15 at base 3%, r 9.5%, FCF basis 1 -- the figure in NKE's watchlist
    note, struck by hand out of the FY2026 10-K on 2026-08-25. Every input
    comes off the written file, through `vss manual`'s own basis.

      1 SHARE COUNT: 1,481,000,000, the FY2026 weighted-average DILUTED
        count. Not a period-end count; A6 unthrown.
      2 SBC: 715m (`us-gaap:ShareBasedCompensation`), ADDED BACK inside
        operating cash flow. Deducted it gives 14.81 -- a third less.
      3 INTEREST: ASC 230, so `InterestPaidNet` 323m is INSIDE the 2,868m of
        operating cash flow, AND the net debt of 379m is subtracted as well.
        THE SAME INTEREST IS CHARGED TWICE, declared as such: charged once,
        the value is 24.87 (FCFF, ETR 18% a HYPOTHESIS) or 22.41 (FCFE, no
        net-debt step). E34 rules it.
      4 BRIDGE: A1 = N -- NIKE's short-term investments are tagged
        `DebtSecuritiesAvailableForSaleExcludingAccruedInterestCurrent`
        1,464m, which this path does not read; with them in, 23.14. A2 = N,
        operating leases 3,091m out, consistent with ASC 842 rent inside
        operating cash flow. No NCI, no pension.
      5 DCF CONVENTIONS: ten years, terminal 2.5%, end-of-year, stream
        starts at FCF0*(1+g), Gordon on year ten. Mid-year gives 23.19.
      6 r AND g: r 9.5% (7.0% core + 2.5% premium); g 3%
        (`reference/growth-views/NKE.md`, 2026-08-25).
      7 AS-OF DATES: flows FY to 2026-05-31, net debt 2026-05-31, count the
        FY2026 average. No price -- this test compares nothing to a market.
      8 PROVENANCE: 10-K 0000320187-26-000088, through the fixture at the
        top of this file.

    THE NET-DEBT DEFINITION IS FORMED HERE, in the test, and not read from
    `manual.RATIOS` -- so the gate's own definition can change without this
    test noticing (report C 9.3 #2(b), flip F4a). Left as it is deliberately:
    the point of the test is the store-to-engine arithmetic, and E35 pins the
    gate's definition where it belongs.
    """
    from vss.valuation import fair_value

    _, _, parsed = emitted(project)
    basis = M.section5_basis(parsed)

    def leg(name):
        return M.resolve_on_basis(parsed, basis, name).value

    legs, why = M.capex_legs(parsed, basis)
    assert legs == M.COMBINED_CAPEX and "combined" in why
    fcf0 = leg("operating_cash_flow") + sum(leg(n) for n in legs)
    net_cash = -(leg("financial_liabilities_current")
                 + leg("financial_liabilities_noncurrent")
                 - leg("cash_and_equivalents"))
    shares = leg("diluted_weighted_average_shares")
    assert (fcf0, net_cash, shares) == (2_184_000_000, -379_000_000,
                                        1_481_000_000)
    value = fair_value(fcf0=fcf0, growth=0.03, net_cash=net_cash, shares=shares)
    assert round(value.mid, 2) == 22.15
    assert (round(value.high, 2), round(value.low, 2)) == (20.64, 23.89)


# =========================================================================
# A SPLIT IS NOT A RESTATEMENT (REVIEW-4 report B 7.1, report C golden G9)
# =========================================================================


def _split_facts(ratio=6, effective="2024-09-13", filed="2024-10-31"):
    """NIKE's shape with a split tagged after the older year was filed."""
    base = facts()
    base["facts"]["us-gaap"]["StockholdersEquityNoteStockSplitConversionRatio1"] = {
        "units": {"pure": [
            {"val": ratio, "end": effective, "accn": "0000320187-24-000001",
             "form": "10-Q", "filed": filed},
            # the same split, tagged again by the next two filings
            {"val": ratio, "end": effective, "accn": "0000320187-25-000001",
             "form": "10-K", "filed": "2025-07-15"}]}}
    return base


def test_one_split_tagged_by_three_filings_is_one_split():
    splits = X.stock_splits(_split_facts())
    assert len(splits) == 1
    assert splits[0].ratio == 6
    assert splits[0].effective == date(2024, 9, 13)
    # the EARLIEST filing, because the question is "was this filed before it"
    assert splits[0].first_filed == "2024-10-31"


def test_a_per_share_figure_filed_before_the_split_is_marked_and_not_rescaled():
    years, _ = X.build_annual(_split_facts())
    eps = years[-1].figures["diluted_eps"]
    shares = years[-1].figures["diluted_weighted_average_shares"]
    # NIKE's fixture is filed 2026-07-15, AFTER the split -- so unmarked.
    assert eps.split_note == "" and shares.split_note == ""

    early = X.stock_splits(_split_facts(effective="2027-01-01",
                                        filed="2027-02-01"))
    marked = X.split_note(eps, "diluted_eps", early)
    assert "PRE-SPLIT BASIS" in marked
    assert "NOT RESCALED HERE" in marked
    assert "6-for-1 split effective 2027-01-01" in marked


def test_only_split_sensitive_fields_carry_the_note():
    years, _ = X.build_annual(_split_facts())
    ocf = years[-1].figures["operating_cash_flow"]
    later = X.stock_splits(_split_facts(effective="2027-01-01",
                                        filed="2027-02-01"))
    assert X.split_note(ocf, "operating_cash_flow", later) == ""
    assert X.split_note(ocf, "diluted_weighted_average_shares", later) != ""


def test_an_ifrs_filer_carries_no_split_tags_and_that_is_stated():
    """IFRS has no widely used element for a split ratio, so a pre-split
    figure in an IFRS file cannot be marked from the tags."""
    assert X.IFRS_TAXONOMY.split_tags == ()
    assert X.US_GAAP_TAXONOMY.split_tags


def test_the_committed_DECK_file_marks_its_pre_split_year():
    """The file on disk, regenerated by this path. FY2022 was filed
    2024-05-24, before the 6-for-1 split of 2024-09-13, and no later filing
    carries the year -- so nothing restated it and the old basis stayed."""
    text = Path("config/manual/DECK.yaml").read_text(encoding="utf-8")
    # FOUR: FY2022's `diluted_eps` and weighted average, and the
    # `shares_point_in_time` memos of FY2022 AND FY2023 -- both of those
    # were filed before 2024-09-13 too (2023-05-26 and 2024-05-24).
    assert text.count("PRE-SPLIT BASIS") == 4
    assert "value: 16.26" in text and "value: 27789000" in text   # not rescaled
    assert "value: 3.23" in text and "value: 160111000" in text
    assert "value: 26982000" in text and "value: 26176000" in text


def test_no_note_in_the_repo_still_says_the_period_end_count_is_untagged():
    """B36's claim, corrected 2026-08-26 (report A 2.3, report C 9.2).

    Both `us-gaap:CommonStockSharesOutstanding` and
    `dei:EntityCommonStockSharesOutstanding` are tagged; the path could not
    reach them because it never asked.
    """
    for path in (Path("vss/xbrl.py"), Path("reference/FRAMEWORK-EDITS.md")):
        text = path.read_text(encoding="utf-8")
        assert "neither of those is a tagged fact" not in text, path
    edits = Path("reference/FRAMEWORK-EDITS.md").read_text(encoding="utf-8")
    assert "CORRECTION OF RECORD, 2026-08-26" in edits
    assert "dei:EntityCommonStockSharesOutstanding" in edits


def test_no_note_in_the_repo_still_says_www_sec_gov_refuses_us():
    """B40's correction, and REVIEW-4 report B 7.1 found the last holdout.

    `www.sec.gov` refuses a User-Agent with no contact address, which is a
    header this project does not send from `source.py` -- not a closed door.
    """
    survey = Path("reference/FETCHER-SURVEY.md").read_text(encoding="utf-8")
    assert "`www.sec.gov` refuses it outright" not in survey
    assert "There is no closed door at SEC" in survey


# --- E34.1: Nike's FCF0 moves by the income statement's net, not by 323m --


def _nike_fy26_interest_facts():
    """FY2026 as tagged on 2026-08-26: paid 323m, income 278m, net +50m."""
    return facts(**{
        "ShareBasedCompensation": {"units": {USD: [
            _fact(715_000_000, start=FY26[0], end=FY26[1])]}},
        "InterestPaidNet": {"units": {USD: [
            _fact(323_000_000, start=FY26[0], end=FY26[1])]}},
        "InvestmentIncomeInterest": {"units": {USD: [
            _fact(278_000_000, start=FY26[0], end=FY26[1])]}},
        "InterestIncomeExpenseNonoperatingNet": {"units": {USD: [
            _fact(50_000_000, start=FY26[0], end=FY26[1])]}},
    })


def test_E34_1_the_us_map_reads_the_income_statement_net_with_its_sign():
    years, _ = X.build_annual(_nike_fy26_interest_facts())
    fy26 = years[-1]
    # +50m in the element is a net INCOME; the schema holds a net COST, so -50m
    assert fy26.value("net_finance_costs") == -50_000_000
    assert fy26.value("finance_income_period") == 278_000_000
    assert fy26.value("finance_costs_paid") == 323_000_000
    assert "finance_costs_period" in fy26.missing       # Nike tags no expense


def test_E34_1_nke_fcf0_moves_by_the_net_50m_not_by_323m(tmp_path):
    from datetime import datetime
    from zoneinfo import ZoneInfo
    from vss import runrecord as R
    fx = _nike_fy26_interest_facts()
    text = X.manual_yaml(ticker="NKE", name="Nike", cik=320187,
                         quote_currency="USD", years=X.build_annual(fx)[0],
                         run_ts=datetime(2026, 8, 26, tzinfo=ZoneInfo("UTC")),
                         facts=fx)
    assert "interest_source: income_statement_net" in text
    # the declarations the run record divides on: XBRL states whole units
    assert "money_unit: whole" in text and "share_unit: whole" in text
    parsed = M.parse_manual(yaml.safe_load(text), path=tmp_path / "NKE.yaml")
    assert (parsed.money_unit, parsed.share_unit) == ("whole", "whole")
    assert parsed.interest_in_ocf.accrual_proxy
    basis = M.section5_basis(parsed)
    # E35.1: Nike tags no pension liability, so without a hand input the
    # record is INCOMPLETE on net debt and prints no fair value at all
    bare = R.from_store(
        parsed, basis, run_ts=datetime(2026, 8, 26, tzinfo=ZoneInfo("UTC")),
        growth=R.Growth(base=0.03, view_file="reference/growth-views/NKE.md"))
    assert any("net debt" in gap for gap in bare.missing())
    record = R.from_store(
        parsed, basis, run_ts=datetime(2026, 8, 26, tzinfo=ZoneInfo("UTC")),
        growth=R.Growth(base=0.03, view_file="reference/growth-views/NKE.md"),
        hand_inputs=(R.Input("pension_deficit", 0.0,
                             "TEST FIXTURE: a hand zero so the record completes; "
                             "Nike's own note is not read here", "hand"),
                     R.Input("asset_retirement_obligation", 0.0,
                             "TEST FIXTURE: E68's leg, a hand zero so the record "
                             "completes", "hand"),
                     R.Input("prepaid_delivery_obligation", 0.0, "TEST FIXTURE: E81's leg, a hand zero so the record completes", "hand"),
                     R.Input("nci_dividends_paid", 0.0, "TEST FIXTURE: E105's leg, a hand zero so the record completes", "hand")))
    assert record.interest.accrual_proxy
    assert record.interest.net_interest_paid == -50_000_000
    # OCF 2,868 - capex 684 - SBC 715 - net interest INCOME 50 = 1,419m.
    # E70 added back the 668 of operating lease payments (2,087m); E117
    # (2026-09-19) reverses it -- rent is an operating cost.
    assert record.lease.rule == "E117" and record.lease.principal_added_back is None
    assert record.fcf0() == pytest.approx(1_419_000_000)
    without = 2_868_000_000 - 684_000_000 - 715_000_000
    assert abs(record.fcf0() - without) == 50_000_000      # NOT 323m
    rendered = record.render()
    assert "accrual proxy (E34.1)" in rendered
    assert "net interest INCOME of 50,000,000 is REMOVED" in rendered


def test_E35_1_both_maps_read_a_recognised_pension_liability():
    assert any(f.field == "pension_deficit" and f.kind == "instant"
               for f in X.ANNUAL_FIELDS)
    assert any(f.field == "pension_deficit"
               and f.tags == ("RecognisedLiabilitiesDefinedBenefitPlan",)
               for f in X.IFRS_ANNUAL_FIELDS)
    # Nike tags none: absence is DATA MISSING, never zero
    years, _ = X.build_annual(facts())
    assert "pension_deficit" in years[-1].missing


# --- 2026-08-29: four alias gaps found on LII and AOS (tag-map fixes, not rulings)


def _lii_interest_facts(**more):
    """LII FY2025 as tagged: gross 46.4m under `InterestExpenseOther`, income
    5.5m, and the filer's own `InterestExpense` 40.9m -- exactly the
    difference. No Nonoperating element of either kind."""
    return facts(**{
        "ShareBasedCompensation": {"units": {USD: [
            _fact(29_100_000, start=FY26[0], end=FY26[1])]}},
        "InterestPaidNet": {"units": {USD: [
            _fact(46_500_000, start=FY26[0], end=FY26[1])]}},
        "InterestExpenseOther": {"units": {USD: [
            _fact(46_400_000, start=FY26[0], end=FY26[1])]}},
        "InvestmentIncomeInterest": {"units": {USD: [
            _fact(5_500_000, start=FY26[0], end=FY26[1])]}},
        "InterestExpense": {"units": {USD: [
            _fact(40_900_000, start=FY26[0], end=FY26[1])]}},
        **more})


def test_the_pair_under_InterestExpenseOther_forms_the_accrual_net_by_E18_not_by_reconstruction(tmp_path):
    """E18 subtracts two STATED figures; E22 forbids inferring one the
    accounts do not state. Both operands here are stated, so the net is
    E18's and not E22's -- and it equals the filer's own net line."""
    from datetime import datetime
    from zoneinfo import ZoneInfo
    from vss import runrecord as R
    fx = _lii_interest_facts()
    years, _ = X.build_annual(fx)
    fy = years[-1]
    assert fy.value("finance_costs_period") == 46_400_000
    assert fy.figures["finance_costs_period"].tag == "InterestExpenseOther"
    assert "CONCEPT: the residual 'other' interest-expense element" in \
        fy.figures["finance_costs_period"].provenance
    assert fy.value("finance_income_period") == 5_500_000
    assert "net_finance_costs" in fy.missing            # the net element is NOT tagged
    text = X.manual_yaml(ticker="NKE", name="Nike", cik=320187, quote_currency="USD",
                         years=years, run_ts=datetime(2026, 8, 29, tzinfo=ZoneInfo("UTC")),
                         facts=fx)
    assert "interest_source: income_statement_net" in text
    assert "E34.1 via E18" in text and "interest_expense_only" not in text
    parsed = M.parse_manual(yaml.safe_load(text), path=tmp_path / "NKE.yaml")
    basis = M.section5_basis(parsed)
    assert M.resolve_or_subtract(parsed, basis, "net_finance_costs") == 40_900_000
    ratios = {r.name: r for r in M.ratio_states(parsed)}
    assert ratios["free cash flow, FCF0 (E34)"].state != M.RATIO_MISSING
    record = R.from_store(
        parsed, basis, run_ts=datetime(2026, 8, 29, tzinfo=ZoneInfo("UTC")),
        growth=R.Growth(base=0.03, view_file="reference/growth-views/NKE.md"),
        hand_inputs=(R.Input("pension_deficit", 0.0, "TEST FIXTURE", "hand"),
                     R.Input("nci_dividends_paid", 0.0,
                             "TEST FIXTURE: E105's leg, a hand zero so FCF0 "
                             "forms; this test is about E18's net", "hand")))
    assert record.interest.net_interest_paid == 40_900_000
    # OCF 2,868 - capex 684 - SBC 29.1 + net 40.9 = 2,195.8m (E70's 668
    # lease add-back reversed by E117, 2026-09-19)
    assert record.fcf0() == pytest.approx(2_195_800_000)


def test_InterestExpense_itself_is_read_and_refused_for_both_fields():
    """LII tags it for the NET line, AOS for the GROSS line: blind, it would
    be netted twice for one and never for the other."""
    for spec in X.ANNUAL_FIELDS:
        assert "InterestExpense" not in spec.tags, spec.field
    assert any(tag == "InterestExpense" for tag, _, _ in X.NOT_WRITTEN)
    years, _ = X.build_annual(_lii_interest_facts())
    assert all(f.tag != "InterestExpense" for f in years[-1].figures.values())


def test_InterestExpenseOther_alone_is_not_an_E61_proxy(tmp_path):
    """E61 names `InterestExpenseNonoperating`. A gross expense reached through
    the residual element, with no income leg to pair it with, leaves FCF0
    DATA MISSING rather than adding back a gross on an element no ruling covers."""
    from datetime import datetime
    from zoneinfo import ZoneInfo
    fx = _lii_interest_facts(InvestmentIncomeInterest=None, InterestExpense=None)
    years, _ = X.build_annual(fx)
    text = X.manual_yaml(ticker="NKE", name="Nike", cik=320187, quote_currency="USD",
                         years=years, run_ts=datetime(2026, 8, 29, tzinfo=ZoneInfo("UTC")),
                         facts=fx)
    assert "interest_source:" not in text and "NO PROXY" in text
    parsed = M.parse_manual(yaml.safe_load(text), path=tmp_path / "NKE.yaml")
    ratios = {r.name: r for r in M.ratio_states(parsed)}
    assert ratios["free cash flow, FCF0 (E34)"].state == M.RATIO_MISSING
    # ...while E61's own element still fires the proxy, as before
    fx = _lii_interest_facts(InvestmentIncomeInterest=None, InterestExpense=None,
                             InterestExpenseOther=None,
                             InterestExpenseNonoperating={"units": {USD: [
                                 _fact(46_400_000, start=FY26[0], end=FY26[1])]}})
    years, _ = X.build_annual(fx)
    text = X.manual_yaml(ticker="NKE", name="Nike", cik=320187, quote_currency="USD",
                         years=years, run_ts=datetime(2026, 8, 29, tzinfo=ZoneInfo("UTC")),
                         facts=fx)
    assert "interest_source: interest_expense_only" in text
    assert X.E61_GROSS_INTEREST_TAG == "InterestExpenseNonoperating"


def test_commercial_paper_is_added_beside_current_maturities_and_read_alone_without_them(project):
    """Written 2026-08-29 under the one-tag rule; rewritten the same day under
    E66: LII tags both, 18.3m and 226.0m, and the two stated captions are
    ADDED with both named. A filer tagging paper alone gets the paper."""
    cp = {"units": {USD: [_fact(226_000_000, end="2026-05-31")]}}
    _, report, parsed = emitted(project, payload=facts(CommercialPaper=cp))
    figure = parsed.annual[-1].figures["financial_liabilities_current"]
    assert figure.value == 2_226_000_000
    assert figure.page.startswith("E66") and "us-gaap:CommercialPaper" in figure.page
    _, report, parsed = emitted(
        project, payload=facts(CommercialPaper=cp, LongTermDebtCurrent=None))
    figure = parsed.annual[-1].figures["financial_liabilities_current"]
    assert figure.value == 226_000_000
    assert "us-gaap:CommercialPaper" in figure.page
    assert "CONCEPT: commercial paper outstanding" in figure.page


def test_productive_assets_is_E23s_one_line_when_no_ppe_element_is_tagged(project):
    """AOS tags `PaymentsToAcquireProductiveAssets` 70.8m and no PP&E element
    at all. The PP&E element, where present, is the narrower concept and wins."""
    pa = {"units": {USD: [_fact(70_800_000, start=FY26[0], end=FY26[1])]}}
    _, report, parsed = emitted(
        project, payload=facts(PaymentsToAcquireProductiveAssets=pa,
                               PaymentsToAcquirePropertyPlantAndEquipment=None))
    year = parsed.annual[-1]
    assert year.value("capex_combined") == -70_800_000
    assert "us-gaap:PaymentsToAcquireProductiveAssets" in year.figures["capex_combined"].page
    assert "CONCEPT: the filer's ONE capital-expenditure line" in year.figures["capex_combined"].page
    assert year.value("capex_ppe") is None
    ratios = {r.name: r for r in M.ratio_states(parsed)}
    assert ratios["free cash flow, basis 1"].state != M.RATIO_MISSING
    # both tagged: the PP&E line, not the broader one, and never a sum
    _, report, parsed = emitted(project, payload=facts(PaymentsToAcquireProductiveAssets=pa))
    year = parsed.annual[-1]
    assert year.value("capex_combined") == -684_000_000
    assert "PropertyPlantAndEquipment" in year.figures["capex_combined"].page
    # a split filer does not list the combined field as missing
    years, _ = X.build_annual(facts(PaymentsToAcquireIntangibleAssets={"units": {USD: [
        _fact(9_000_000, start=FY26[0], end=FY26[1])]}}))
    assert "capex_combined" not in years[-1].missing
    assert "capex_ppe" in years[-1].figures and "capex_intangibles" in years[-1].figures


def test_the_income_statement_sbc_charge_is_read_where_the_add_back_is_absent_and_says_so(project):
    """AOS tags `AllocatedShareBasedCompensationExpense` 13.8m and never the
    cash-flow add-back. E36 subtracts the cost either way; the page line
    records WHICH concept was taken so a later reader does not have to guess."""
    charge = {"units": {USD: [_fact(13_800_000, start=FY26[0], end=FY26[1])]}}
    _, _, parsed = emitted(project, payload=facts(AllocatedShareBasedCompensationExpense=charge))
    figure = parsed.annual[-1].figures["sbc"]
    assert figure.value == 13_800_000
    assert "us-gaap:AllocatedShareBasedCompensationExpense" in figure.page
    assert "CONCEPT: the INCOME-STATEMENT share-based compensation CHARGE" in figure.page
    # the add-back, where tagged, wins and carries no concept note
    both = facts(AllocatedShareBasedCompensationExpense=charge,
                 ShareBasedCompensation={"units": {USD: [
                     _fact(715_000_000, start=FY26[0], end=FY26[1])]}})
    _, _, parsed = emitted(project, payload=both)
    figure = parsed.annual[-1].figures["sbc"]
    assert figure.value == 715_000_000 and "CONCEPT" not in figure.page



# --- E65-E68 (2026-08-29): what counts as debt ---------------------------


def _inst(val, end="2026-05-31"):
    return {"units": {USD: [_fact(val, end=end)]}}


def _lii_shaped_debt_facts(**more):
    """LII at 2025-12-31, transposed onto the fixture's FY2026 year end:
    current maturities 18.3m tagged EQUAL to the inclusive current caption
    and to the current finance lease; commercial paper 226.0m; no
    borrowings-only non-current element but the combined caption 1,144.1m
    with 50.6m of finance lease inside; finance lease total 68.9m;
    operating leases 382.3m; the filer's own debt total 1,388.4m; no ARO."""
    return facts(**{
        "LongTermDebtCurrent": _inst(18_300_000),
        "LongTermDebtAndCapitalLeaseObligationsCurrent": _inst(18_300_000),
        "FinanceLeaseLiabilityCurrent": _inst(18_300_000),
        "CommercialPaper": _inst(226_000_000),
        "LongTermDebtNoncurrent": None,
        "LongTermDebtAndCapitalLeaseObligations": _inst(1_144_100_000),
        "FinanceLeaseLiabilityNoncurrent": _inst(50_600_000),
        "FinanceLeaseLiability": _inst(68_900_000),
        "OperatingLeaseLiability": _inst(382_300_000),
        "DebtAndCapitalLeaseObligations": _inst(1_388_400_000),
        **more})


def test_E66_two_stated_current_captions_are_added_and_every_component_is_named():
    years, _ = X.build_annual(_lii_shaped_debt_facts())
    fig = years[-1].figures["financial_liabilities_current"]
    assert fig.value == 244_300_000
    assert fig.tag == "LongTermDebtCurrent + CommercialPaper"
    assert fig.provenance.startswith("E66")
    assert "us-gaap:LongTermDebtCurrent [as of 2026-05-31]" in fig.provenance
    assert "us-gaap:CommercialPaper [as of 2026-05-31]" in fig.provenance
    assert "= 244,300,000" in fig.provenance
    assert len(fig.components) == 2


def test_E66_a_stated_subtotal_wins_and_the_captions_beside_it_are_memo():
    years, _ = X.build_annual(_lii_shaped_debt_facts(DebtCurrent=_inst(250_000_000)))
    fig = years[-1].figures["financial_liabilities_current"]
    assert fig.value == 250_000_000 and fig.tag == "DebtCurrent"
    assert "SUBTOTAL" in fig.provenance and "memo" in fig.provenance
    assert "`CommercialPaper` 226,000,000" in fig.provenance
    assert "`LongTermDebtCurrent` 18,300,000" in fig.provenance


def test_E66_short_term_borrowings_is_a_subtotal_over_commercial_paper():
    years, _ = X.build_annual(facts(ShortTermBorrowings=_inst(300_000_000),
                                    CommercialPaper=_inst(200_000_000)))
    fig = years[-1].figures["financial_liabilities_current"]
    assert fig.value == 2_300_000_000                      # 2,000 + 300, never + 200
    assert fig.tag == "LongTermDebtCurrent + ShortTermBorrowings"
    assert "`CommercialPaper` 200,000,000 is tagged beside it and is memo" in fig.provenance


def test_E67_the_combined_noncurrent_caption_is_read_whole_with_the_lease_inside_named():
    years, _ = X.build_annual(_lii_shaped_debt_facts())
    fig = years[-1].figures["financial_liabilities_noncurrent"]
    assert fig.value == 1_144_100_000
    assert fig.tag == "LongTermDebtAndCapitalLeaseObligations"
    assert "E67" in fig.provenance and "50,600,000 of it is `FinanceLeaseLiabilityNoncurrent`" in fig.provenance
    assert "E65 does not add that again" in fig.provenance


def test_E67_refuses_the_combined_caption_when_the_lease_inside_it_is_not_stated():
    years, _ = X.build_annual(_lii_shaped_debt_facts(FinanceLeaseLiabilityNoncurrent=None))
    year = years[-1]
    assert "financial_liabilities_noncurrent" in year.missing
    assert any("E67 REFUSES" in n for n in year.debt_notes)


def test_E72_the_combined_caption_is_read_whole_where_no_finance_lease_element_is_tagged():
    """Accenture's shape: `LongTermDebtAndCapitalLeaseObligations` tagged,
    NO finance-lease element of any kind -- the lease inside is stated only
    in words ('primarily finance lease liabilities', 'no material finance
    leases'). E72 (2026-08-30): the caption is the leg, read whole, and the
    words are quoted on the figure by hand. E65 adds nothing."""
    years, _ = X.build_annual(_lii_shaped_debt_facts(
        FinanceLeaseLiabilityNoncurrent=None, FinanceLeaseLiabilityCurrent=None,
        FinanceLeaseLiability=None))
    year = years[-1]
    fig = year.figures["financial_liabilities_noncurrent"]
    assert fig.value == 1_144_100_000
    assert fig.tag == "LongTermDebtAndCapitalLeaseObligations"
    assert "E72" in fig.provenance and "quoted on this figure by hand" in fig.provenance
    assert "financial_liabilities_noncurrent" not in year.missing
    assert any("read whole (E72)" in n for n in year.debt_notes)
    assert year.value("lease_liabilities") == 382_300_000        # operating alone
    assert any("NAMED ZERO" in n and "E73" in n for n in year.debt_notes)


def test_E65_finance_leases_enter_lease_liabilities_only_where_no_borrowing_leg_holds_them():
    """LII: 68.9 = 18.3 (inside the current leg) + 50.6 (inside the
    non-current leg), so nothing is added -- and the two borrowing legs sum
    to the filer's own DebtAndCapitalLeaseObligations. No dollar twice."""
    years, _ = X.build_annual(_lii_shaped_debt_facts())
    year = years[-1]
    leases = year.figures["lease_liabilities"]
    assert leases.value == 382_300_000
    assert leases.provenance.startswith("E65")
    assert "68,900,000" in leases.provenance and "so 0 is added" in leases.provenance
    assert "18,300,000 already inside `financial_liabilities_current`" in leases.provenance
    assert "50,600,000 already inside `financial_liabilities_noncurrent`" in leases.provenance
    current = year.figures["financial_liabilities_current"]
    assert "tagged INCLUSIVE of its finance lease" in current.provenance
    assert (year.value("financial_liabilities_current")
            + year.value("financial_liabilities_noncurrent")) == 1_388_400_000
    assert any("`lease_liabilities` = 382,300,000 (E65)" in n for n in year.debt_notes)


def test_E65_a_finance_lease_outside_any_borrowing_leg_is_added_from_its_two_stated_parts():
    """CTSH: borrowings-only elements on both legs, a finance lease tagged as
    current 10m + non-current 12m and no total -- added in full."""
    years, _ = X.build_annual(facts(ShortTermBorrowings=_inst(33_000_000),
                                    LongTermDebtCurrent=None,
                                    LongTermDebtNoncurrent=_inst(543_000_000),
                                    FinanceLeaseLiabilityCurrent=_inst(10_000_000),
                                    FinanceLeaseLiabilityNoncurrent=_inst(12_000_000),
                                    OperatingLeaseLiability=_inst(576_000_000)))
    year = years[-1]
    leases = year.figures["lease_liabilities"]
    assert leases.value == 598_000_000
    assert "two stated parts" in leases.provenance and "added in full" in leases.provenance
    assert year.value("financial_liabilities_noncurrent") == 543_000_000
    assert "no lease inside it (E14)" in " ".join(year.debt_notes)


def test_E65_a_lone_finance_lease_part_refuses_the_field_rather_than_understating_it():
    years, _ = X.build_annual(facts(FinanceLeaseLiabilityNoncurrent=_inst(12_000_000)))
    year = years[-1]
    assert "lease_liabilities" in year.missing
    assert any("one part alone is not the liability" in n for n in year.debt_notes)


def test_E68_the_total_first_then_two_stated_parts_never_a_lone_part():
    # EXE: total 724 with both parts beside it
    years, _ = X.build_annual(facts(AssetRetirementObligation=_inst(724_000_000),
                                    AssetRetirementObligationsNoncurrent=_inst(688_000_000),
                                    AssetRetirementObligationCurrent=_inst(36_000_000)))
    fig = years[-1].figures["asset_retirement_obligation"]
    assert fig.value == 724_000_000 and fig.tag == "AssetRetirementObligation"
    assert "memo and never added: `AssetRetirementObligationsNoncurrent` 688,000,000" in fig.provenance
    # two parts, no total: added, both named
    years, _ = X.build_annual(facts(AssetRetirementObligationsNoncurrent=_inst(688_000_000),
                                    AssetRetirementObligationCurrent=_inst(36_000_000)))
    fig = years[-1].figures["asset_retirement_obligation"]
    assert fig.value == 724_000_000 and fig.provenance.startswith("E68")
    # DECK: a lone non-current part is not the obligation
    years, _ = X.build_annual(facts(AssetRetirementObligationsNoncurrent=_inst(36_790_000)))
    year = years[-1]
    assert "asset_retirement_obligation" in year.missing
    assert any("a lone part is not the obligation" in n for n in year.debt_notes)
    # NIKE: untagged is DATA MISSING, never zero; both maps carry the field
    years, _ = X.build_annual(facts())
    assert "asset_retirement_obligation" in years[-1].missing
    assert any(f.field == "asset_retirement_obligation" for f in X.ANNUAL_FIELDS)
    assert any(f.field == "asset_retirement_obligation" for f in X.IFRS_ANNUAL_FIELDS)


def test_E68_the_gate_refuses_net_debt_without_the_leg_and_a_hand_zero_completes_the_record(project):
    from datetime import datetime
    from zoneinfo import ZoneInfo
    from vss import runrecord as R
    _, report, parsed = emitted(project)
    states = {r.name: r for r in M.ratio_states(parsed)}
    assert states["net debt"].state == M.RATIO_MISSING
    assert "asset_retirement_obligation" in states["net debt"].detail
    assert "DEBT LEGS ON THE BASIS (E65-E68)" in report
    assert "DATA MISSING, never zero (E68)" in report
    basis = M.section5_basis(parsed)
    record = R.from_store(
        parsed, basis, run_ts=datetime(2026, 8, 29, tzinfo=ZoneInfo("UTC")),
        growth=R.Growth(base=0.03, view_file="reference/growth-views/NKE.md"),
        hand_inputs=(R.Input("pension_deficit", 0.0, "TEST FIXTURE", "hand"),
                     R.Input("asset_retirement_obligation", 0.0, "TEST FIXTURE", "hand"),
                     R.Input("prepaid_delivery_obligation", 0.0, "TEST FIXTURE: E81's leg, a hand zero so the record completes", "hand"),
                     R.Input("nci_dividends_paid", 0.0, "TEST FIXTURE: E105's leg, a hand zero so the record completes", "hand")))
    assert "asset_retirement_obligations" in R.BRIDGE_ITEMS
    assert record.bridge.items["asset_retirement_obligations"] == 0.0
    # 2,000 + 5,942 + 0 + 0 - 7,563: the 3,091 operating lease liability
    # LEAVES net debt (E117, 2026-09-19); with it, 3,470
    assert record.bridge.net_debt == pytest.approx(379_000_000)
    assert "E68" in record.bridge.note


# --- 2026-09-04: one figure in two units, REFUSED rather than chosen ------


def _two_scales(*rows):
    """A minimal filer: one share-count element plus a currency fact, so
    `reporting_currency` and `fiscal_year_end_month` can answer at all."""
    return {"facts": {"us-gaap": {
        "WeightedAverageNumberOfDilutedSharesOutstanding": {
            "units": {"shares": list(rows)}},
        "Revenues": {"units": {"USD": [
            {"start": "2014-01-01", "end": "2014-12-31", "val": 1_198_202_000,
             "form": "10-K", "accn": "0001047469-15-001519",
             "filed": "2015-02-24"}]}}}}}


def _row(val, form, accn, filed, start="2014-01-01", end="2014-12-31"):
    return {"start": start, "end": end, "val": val, "form": form,
            "accn": accn, "filed": filed}


def test_a_unit_slip_INSIDE_the_statement_forms_is_found():
    """Narrowing the pool to statements did NOT close this class, and the
    measurement says so: over fifteen filers' complete companyfacts on
    2026-09-04, 6,924 (element, period) groups held more than one value and
    43 were a round power of a thousand apart -- of which only FIVE were the
    DEF 14A case. The rest are 10-K against 10-K and 10-Q against 10-Q."""
    slip = X._slip_in([_row(85_140, "10-K", "a", "2015-02-01"),
                       _row(85_140_000, "10-K", "a", "2015-02-01")])
    assert slip and "85,140" in slip and "85,140,000" in slip
    assert not X._slip_in([_row(85_140_000, "10-K", "a", "2015-02-01"),
                           _row(85_139_000, "10-K", "b", "2016-02-01")])
    assert not X._slip_in([_row(85_140_000, "10-K", "a", "2015-02-01")])


def test_the_WHOLE_pool_is_asked_not_only_the_chosen_entry():
    """A filer that tagged three values, two of them a thousand apart, has
    a slip whether or not the LATEST filing is one of the two."""
    assert X._slip_in([_row(85_140, "10-K", "a", "2015-02-01"),
                       _row(85_140_000, "10-K", "b", "2015-03-01"),
                       _row(85_141_000, "10-K", "c", "2016-02-01")])


def test_a_slipped_field_is_DATA_MISSING_and_not_a_coin_toss():
    """CROX FY2014, real: `WeightedAverageNumberOfDilutedSharesOutstanding`
    -- the SECTION 5 DIVISOR -- is tagged 85,140 and 85,140,000 in the same
    10-K. Taking either by filing date is a coin toss on a factor of a
    thousand, and a wrong divisor makes every per-share figure wrong by it.
    """
    facts = _two_scales(_row(85_140, "10-K", "0001047469-15-001519", "2015-02-24"),
                        _row(85_140_000, "10-K", "0001047469-15-001519", "2015-02-24"))
    years, _ = X.build_annual(facts, limit=5)
    assert years, "the year should still be built"
    year = years[-1]
    assert year.value("diluted_weighted_average_shares") is None
    why = year.unit_slips["diluted_weighted_average_shares"]
    assert "TWO SCALES" in why and "85,140" in why and "85,140,000" in why
    assert "0001047469-15-001519" in why


def test_one_scale_is_written_normally():
    facts = _two_scales(_row(85_140_000, "10-K", "a", "2015-02-24"))
    years, _ = X.build_annual(facts, limit=5)
    assert years[-1].value("diluted_weighted_average_shares") == 85_140_000
    assert not years[-1].unit_slips
