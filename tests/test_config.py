"""Watchlist validation: every malformed entry must fail the whole run loudly."""

from datetime import date

import pytest

from vss.config import ConfigError, parse_entry, parse_watchlist


def entry(**overrides):
    raw = {"ticker": "TEST.ST", "name": "Test AB", "currency": "SEK", "status": "WATCH-GATED"}
    raw.update(overrides)
    return raw


def doc(*entries):
    return {"tickers": list(entries)}


# --- mbp provenance -------------------------------------------------------


def test_hand_entered_mbp_fails_the_run():
    with pytest.raises(ConfigError, match="mbp is COMPUTED"):
        parse_watchlist(doc(entry(mbp=140.0)))


def test_mbp_conflict_message_names_the_ticker_and_the_fix():
    with pytest.raises(ConfigError) as exc:
        parse_watchlist(doc(entry(mbp=1.0)))
    assert "TEST.ST" in str(exc.value)
    assert "fv_base" in str(exc.value) and "tier" in str(exc.value)


def test_mbp_is_not_an_allowed_key():
    e = parse_entry(entry(fv_base=200.0, tier=2), 0)
    assert not hasattr(e, "mbp")


# --- required fields ------------------------------------------------------


@pytest.mark.parametrize("missing", ["ticker", "name", "currency", "status"])
def test_missing_required_field_fails(missing):
    raw = entry()
    del raw[missing]
    with pytest.raises(ConfigError, match="missing required key"):
        parse_watchlist(doc(raw))


@pytest.mark.parametrize("blank", ["", "   "])
def test_blank_required_field_fails(blank):
    with pytest.raises(ConfigError, match="must not be empty"):
        parse_watchlist(doc(entry(name=blank)))


# --- enums ----------------------------------------------------------------


@pytest.mark.parametrize("status", ["HELD", "WATCH-GATED", "WATCH-PRICED",
                                    "PIPELINE", "held", "Watch-Priced"])
def test_valid_statuses_are_normalised_to_upper(status):
    # a HELD entry carries the bull its exit test runs on (owner, 2026-09-20)
    bull = {"fv_bull": 140.0} if status.upper() == "HELD" else {}
    assert parse_entry(entry(status=status, **bull), 0).status == status.upper()


def test_invalid_status_fails():
    with pytest.raises(ConfigError, match="status must be one of"):
        parse_watchlist(doc(entry(status="MAYBE")))


@pytest.mark.parametrize("tier", [1, 2, 3, "2"])
def test_valid_tiers(tier):
    assert parse_entry(entry(tier=tier), 0).tier == int(tier)


@pytest.mark.parametrize("tier", [0, 4, "high", 2.5])
def test_invalid_tier_fails(tier):
    with pytest.raises(ConfigError, match="tier must be 1, 2 or 3"):
        parse_watchlist(doc(entry(tier=tier)))


def test_absent_tier_is_allowed_and_yields_no_mbp():
    assert parse_entry(entry(fv_base=200.0), 0).tier is None


# --- typos must not be silently ignored -----------------------------------


def test_unknown_key_fails_rather_than_being_ignored():
    """A typo like 'stop' instead of 'stop_price' must not silently vanish."""
    with pytest.raises(ConfigError, match="unknown key"):
        parse_watchlist(doc(entry(stop=80.0)))


def test_unknown_key_message_lists_the_allowed_keys():
    with pytest.raises(ConfigError) as exc:
        parse_watchlist(doc(entry(notez="oops")))
    assert "stop_price" in str(exc.value)


# --- types ----------------------------------------------------------------


def test_non_numeric_fv_base_fails():
    with pytest.raises(ConfigError, match="fv_base must be a number"):
        parse_watchlist(doc(entry(fv_base="cheap")))


def test_non_numeric_stop_price_fails():
    with pytest.raises(ConfigError, match="stop_price must be a number"):
        parse_watchlist(doc(entry(stop_price="low")))


def test_catalyst_date_accepts_date_and_iso_string():
    assert parse_entry(entry(catalyst_date=date(2026, 10, 24)), 0).catalyst_date == date(2026, 10, 24)
    assert parse_entry(entry(catalyst_date="2026-10-24"), 0).catalyst_date == date(2026, 10, 24)


def test_malformed_catalyst_date_fails():
    with pytest.raises(ConfigError, match="must be a YYYY-MM-DD date"):
        parse_watchlist(doc(entry(catalyst_date="next Tuesday")))


# --- document level -------------------------------------------------------


def test_duplicate_ticker_fails():
    with pytest.raises(ConfigError, match="duplicate ticker"):
        parse_watchlist(doc(entry(), entry()))


def test_missing_tickers_key_fails():
    with pytest.raises(ConfigError, match="top-level 'tickers:' list"):
        parse_watchlist({"names": []})


def test_empty_watchlist_fails():
    with pytest.raises(ConfigError, match="non-empty list"):
        parse_watchlist({"tickers": []})
    with pytest.raises(ConfigError, match="empty"):
        parse_watchlist(None)


def test_one_bad_entry_fails_the_whole_run_not_just_that_entry():
    with pytest.raises(ConfigError):
        parse_watchlist(doc(entry(ticker="GOOD"), entry(ticker="BAD", status="NOPE")))


def test_shipped_example_watchlist_is_valid():
    from pathlib import Path

    import yaml

    path = Path(__file__).resolve().parent.parent / "config" / "watchlist.example.yaml"
    entries = parse_watchlist(yaml.safe_load(path.read_text(encoding="utf-8")))
    assert len(entries) == 2


# --- E27: WATCH was split, and the bare word must not survive -------------


def test_e27_bare_watch_is_not_in_the_vocabulary():
    """FRAMEWORK-EDITS E27: WATCH gained two successors and lost itself.

    The bare word carried two states whose re-entry rules are opposite --
    WATCH-PRICED waits on a price it may be bought at, WATCH-GATED waits
    on an information event and may never be bought on price. A status
    that means both is a status that answers neither question.
    """
    from vss.rules import VALID_STATUSES, WATCH_STATUSES

    assert "WATCH" not in VALID_STATUSES
    assert "WATCH-PRICED" in VALID_STATUSES
    assert "WATCH-GATED" in VALID_STATUSES
    assert WATCH_STATUSES == ("WATCH-PRICED", "WATCH-GATED")


def test_e27_bare_watch_is_refused_with_the_migration_named():
    """Refused, not auto-migrated.

    Which successor a name belongs in is a judgement about WHY it is
    waiting, and nothing in the file records that. So the loader stops and
    says what the choice is, rather than guessing one.
    """
    with pytest.raises(ConfigError) as excinfo:
        parse_watchlist(doc(entry(status="WATCH")))
    message = str(excinfo.value)
    assert "retired" in message
    assert "E27" in message
    assert "WATCH-PRICED" in message and "WATCH-GATED" in message
    # and it must NOT be mistaken for an ordinary typo
    assert "status must be one of" not in message


def test_e27_no_bare_watch_survives_in_any_shipped_watchlist():
    """The live file and the example, pinned together.

    E27 requires every existing WATCH row to be migrated with its reason
    stated. This is what stops one being reintroduced by hand later: the
    loader would refuse it, and this says so before anyone runs vss.
    """
    from pathlib import Path

    import yaml

    root = Path(__file__).resolve().parent.parent
    for name in ("watchlist.yaml", "watchlist.example.yaml"):
        path = root / "config" / name
        raw = yaml.safe_load(path.read_text(encoding="utf-8"))
        statuses = [str(e.get("status", "")).strip().upper()
                    for e in raw["tickers"]]
        assert "WATCH" not in statuses, f"bare WATCH survives in {name}"
        # and the file still loads, so the migration did not break it
        parse_watchlist(raw)


def test_e27_the_live_watchlist_migrated_the_three_names_it_had():
    """The instances E27 names, as migrated on 2026-08-25.

    MC.PA is WATCH-PRICED: it waits on a price and has never been through
    section 3, so nothing about it was disqualified. DECK and PNDORA.CO
    are WATCH-GATED: both failed Gate 1's CATALYST limb, so the failure
    was not about price and no price level may wake them.
    """
    from pathlib import Path

    import yaml

    root = Path(__file__).resolve().parent.parent
    raw = yaml.safe_load((root / "config" / "watchlist.yaml").read_text(encoding="utf-8"))
    status = {e["ticker"]: str(e["status"]).strip().upper() for e in raw["tickers"]}
    assert status["MC.PA"] == "WATCH-PRICED"
    assert status["DECK"] == "WATCH-GATED"
    assert status["PNDORA.CO"] == "WATCH-GATED"


def test_e27_mc_pa_alert_is_labelled_not_an_mbp():
    """440 EUR is an alert, not a maximum buy price, and the row says so.

    E27 carries forward the owner's own distinction from the NKE row of
    2026-08-21 -- "an alert level is NOT an MBP - compute properly". MC.PA
    has no fv_base and no tier, so no MBP has ever been computed for it,
    and a reader must not take 440 for one.
    """
    from pathlib import Path

    import yaml

    root = Path(__file__).resolve().parent.parent
    raw = yaml.safe_load((root / "config" / "watchlist.yaml").read_text(encoding="utf-8"))
    row = next(e for e in raw["tickers"] if e["ticker"] == "MC.PA")
    # 2026-09-19 (owner, A4): MC.PA was struck -- fv_base 321.94 off its own
    # store -- but it still has NO TIER, so still no MBP; the 440 alert
    # remains no buy price
    assert row.get("fv_base") == 321.94 and row.get("tier") is None
    notes = row["notes"].upper()
    assert "NOT AN MBP" in notes
    assert "NOT BUYABLE" in notes


# --- catalyst_resolved: structured replacement for the notes prefix gate ---


def test_catalyst_resolved_accepts_date_and_iso_string():
    e = parse_entry(entry(catalyst_date="2026-07-23", catalyst_resolved="2026-08-20"), 0)
    assert e.catalyst_resolved == date(2026, 8, 20)
    e = parse_entry(entry(catalyst_date=date(2026, 7, 23), catalyst_resolved=date(2026, 8, 20)), 0)
    assert e.catalyst_resolved == date(2026, 8, 20)


def test_catalyst_resolved_earlier_than_catalyst_date_fails_the_run():
    with pytest.raises(ConfigError, match="earlier than catalyst_date"):
        parse_watchlist(doc(entry(catalyst_date="2026-07-23", catalyst_resolved="2026-07-22")))


def test_catalyst_resolved_on_the_same_day_is_valid():
    e = parse_entry(entry(catalyst_date="2026-07-23", catalyst_resolved="2026-07-23"), 0)
    assert e.catalyst_resolved == date(2026, 7, 23)


def test_malformed_catalyst_resolved_fails():
    with pytest.raises(ConfigError, match="catalyst_resolved must be a YYYY-MM-DD date"):
        parse_watchlist(doc(entry(catalyst_resolved="last week")))


def test_catalyst_resolved_is_an_allowed_key():
    assert "catalyst_resolved" in __import__("vss.config", fromlist=["x"]).ALLOWED_KEYS


def test_notes_no_longer_carry_machine_meaning():
    """An 'outcome:' line in notes is prose; it must not resolve anything."""
    e = parse_entry(entry(catalyst_date="2026-07-23", notes="outcome: reported, fine"), 0)
    assert e.catalyst_resolved is None


# --- the unit contract: ratios are fractions (SPEC.md section 2) ----------
#
# This is the check that would have caught the live bug: `vss earnings`
# proposed op_margin 6.6 for a 6.6% margin, the watchlist accepted it, and
# 4.2.2 -- which multiplies by 10,000 for basis points -- read it as 660%.


def quarter(**overrides):
    q = {"period": "2026-Q2"}
    q.update(overrides)
    return q



@pytest.mark.parametrize("field,value", [
    ("op_margin", 6.6),        # the live bug: 6.6% written as a percentage
    ("op_margin", 15.1),
    ("revenue_yoy", 2.0),
    ("revenue_yoy", -7.0),
    ("covenant_headroom", 12.0),
])
def test_a_percentage_in_a_fraction_field_fails_the_load(field, value):
    with pytest.raises(ConfigError, match="FRACTIONS, not percentages"):
        parse_watchlist(doc(entry(quarters=[quarter(**{field: value})])))


def test_the_unit_error_shows_the_fraction_it_should_have_been():
    with pytest.raises(ConfigError) as exc:
        parse_watchlist(doc(entry(quarters=[quarter(op_margin=6.6)])))
    message = str(exc.value)
    assert "0.066" in message
    assert "do not scale it by hand" in message
    assert "SPEC.md" in message


@pytest.mark.parametrize("field,value", [
    ("op_margin", 0.066),
    ("op_margin", 1.0),          # exactly 100%: allowed, the band is inclusive
    ("op_margin", -9.5),         # a pre-revenue name losing many times revenue
    ("revenue_yoy", -1.0),
    ("revenue_yoy", 1.0),
    ("covenant_headroom", 0.12),
])
def test_a_fraction_inside_its_band_loads(field, value):
    e = parse_entry(entry(quarters=[quarter(**{field: value})]), 0)
    assert getattr(e.quarters[0], field) == value


def test_an_absent_ratio_is_not_a_unit_error():
    """A blank is DATA MISSING, which is a legitimate state, not a 0.0."""
    e = parse_entry(entry(quarters=[quarter(op_margin=None, revenue_yoy=None)]), 0)
    assert e.quarters[0].op_margin is None


def test_a_negative_percentage_margin_is_not_caught_by_the_band():
    """A documented limit, not an oversight.

    Lindab's 2024-Q4 margin of -3.1% written as -3.1 sits inside the band,
    because -310% is a real margin for a pre-revenue name and the band
    cannot tell the two apart. The reconciliation check below is what
    catches it -- which is why both checks exist.
    """
    e = parse_entry(entry(quarters=[quarter(op_margin=-3.1)]), 0)
    assert e.quarters[0].op_margin == -3.1


def test_that_same_negative_percentage_fails_once_revenue_is_stated():
    with pytest.raises(ConfigError, match="do not describe one measure"):
        parse_watchlist(doc(entry(quarters=[
            quarter(revenue=3308.0, op_income=-101.0, op_margin=-3.1),
        ])))


def test_the_band_is_asymmetric_on_purpose():
    """A margin over 100% is arithmetically impossible; a deep loss is not."""
    from vss.rules import FRACTION_BANDS
    low, high = FRACTION_BANDS["op_margin"]
    assert high == 1.0 and low < -1.0


# --- margin reconciliation: one measure, one period ----------------------


def test_a_margin_that_does_not_match_op_income_over_revenue_fails():
    """Lindab Q4 2025: adjusted margin 6.5% beside reported op income 97."""
    with pytest.raises(ConfigError, match="do not describe one measure"):
        parse_watchlist(doc(entry(quarters=[
            quarter(revenue=3134.0, op_income=97.0, op_margin=0.065),
        ])))


def test_the_reconciliation_error_shows_both_margins():
    with pytest.raises(ConfigError) as exc:
        parse_watchlist(doc(entry(quarters=[
            quarter(revenue=3134.0, op_income=97.0, op_margin=0.065),
        ])))
    message = str(exc.value)
    assert "0.0310" in message and "0.0650" in message
    assert "pp" in message


def test_a_margin_matching_its_own_income_and_revenue_loads():
    e = parse_entry(entry(quarters=[
        quarter(revenue=3134.0, op_income=97.0, op_margin=0.031),
    ]), 0)
    assert e.quarters[0].op_margin == 0.031


@pytest.mark.parametrize("op_margin", [0.0659, 0.0669])
def test_rounding_within_a_tenth_of_a_point_is_accepted(op_margin):
    """3306 and 218 imply 0.06594; a report rounding to 6.6% must load."""
    e = parse_entry(entry(quarters=[
        quarter(revenue=3306.0, op_income=218.0, op_margin=op_margin),
    ]), 0)
    assert e.quarters[0].revenue == 3306.0


def test_a_gap_just_over_the_tolerance_fails():
    with pytest.raises(ConfigError, match="do not describe one measure"):
        parse_watchlist(doc(entry(quarters=[
            quarter(revenue=1000.0, op_income=100.0, op_margin=0.1011),
        ])))


@pytest.mark.parametrize("missing", ["revenue", "op_income"])
def test_reconciliation_is_skipped_when_a_figure_is_absent(missing):
    """Two of three cannot contradict each other, and a blank stays blank.

    op_margin IS effectively in this list since E79: a missing margin
    leaves nothing to compare, and the check does not fire -- see below.
    """
    fields = {"revenue": 3134.0, "op_income": 97.0, "op_margin": 0.031}
    fields[missing] = None
    e = parse_entry(entry(quarters=[quarter(**fields)]), 0)
    assert getattr(e.quarters[0], missing) is None


def test_zero_revenue_does_not_divide():
    e = parse_entry(entry(quarters=[
        quarter(revenue=0.0, op_income=-50.0, op_margin=-9.0),
    ]), 0)
    assert e.quarters[0].revenue == 0.0


# --- the gap that let a wrong op_income through, and E79 -----------------
#
# NIKE has no Operating income line: EBIT sits in a non-GAAP table at the
# foot of the release. The extractor took "Income before income taxes"
# (1,416) instead of EBIT (1,392) and reported no margin at all -- and
# the reconciliation check skipped the quarter entirely. For a while an
# op_income with no margin was refused as UNRECONCILED for that reason.
# E79 (2026-08-30) withdrew the refusal: where the issuer states no margin
# the check has nothing to compare and does not fire; what guards the
# line is the page reference. The comparison that remains is made at the
# PRECISION THE ISSUER PRINTED.


def test_E79_an_op_income_without_a_margin_loads():
    e = parse_entry(entry(quarters=[
        quarter(revenue=12354.0, op_income=1416.0, op_margin=None),
    ]), 0)
    assert e.quarters[0].op_income == 1416.0 and e.quarters[0].op_margin is None


def test_E79_a_whole_percent_margin_agrees_at_a_whole_percent():
    """Rightmove: 287,874 / 425,129 = 67.71%, printed as 68%."""
    e = parse_entry(entry(quarters=[
        quarter(revenue=425129.0, op_income=287874.0, op_margin=0.68),
    ]), 0)
    assert e.quarters[0].op_margin == 0.68


def test_E79_a_tenth_of_a_percent_margin_is_compared_at_a_tenth():
    """RVRC Q3: 105 / 487 = 21.56%, printed 21.4% -- a 0.16pp gap, over
    the 0.1pp band a tenth-of-a-percent margin gets."""
    with pytest.raises(ConfigError, match="stated to a tenth of a percent"):
        parse_watchlist(doc(entry(quarters=[
            quarter(revenue=487.0, op_income=105.0, op_margin=0.214),
        ])))


def test_E79_a_trailing_zero_is_not_representable_and_reads_as_a_whole_percent():
    """RVRC Q1: 75 / 392 = 19.13% against a printed 19.0%. The entry
    `0.190` IS the float 0.19, so the check reads a whole percent and a
    0.13pp gap passes. The seam is documented in E79; the reader, who can
    see the printed tenth, does not enter such a figure knowing it
    disagrees at the printed precision."""
    from vss.config import margin_precision
    assert margin_precision(0.190) == 2
    e = parse_entry(entry(quarters=[
        quarter(revenue=392.0, op_income=75.0, op_margin=0.190),
    ]), 0)
    assert e.quarters[0].op_margin == 0.19
    e = parse_entry(entry(quarters=[
        quarter(revenue=14205.0, op_income=4217.0, op_margin=0.297),
    ]), 0)
    assert e.quarters[0].op_margin == 0.297


def test_E79_the_precision_is_read_from_the_entry_and_bounded():
    from vss.config import margin_precision
    assert margin_precision(0.68) == 2
    assert margin_precision(0.7) == 2          # floored: a printed 70%
    assert margin_precision(0.297) == 3
    assert margin_precision(0.2971) == 3       # capped: compared at a tenth
    assert margin_precision(-0.05) == 2
    from vss.config import margin_band
    assert margin_band(0.68) == pytest.approx(0.005)      # half a whole percent
    assert margin_band(0.297) == pytest.approx(0.001)     # the floor, one tenth


def test_the_disagreement_error_shows_both_figures_as_rounded():
    with pytest.raises(ConfigError) as exc:
        parse_watchlist(doc(entry(quarters=[
            quarter(revenue=12354.0, op_income=1416.0, op_margin=0.10),
        ])))
    message = str(exc.value)
    assert "0.1146" in message                      # 1416 / 12354
    assert "0.11" in message and "0.10" in message  # both, as rounded (E79)
    assert "do not describe one measure" in message


def test_a_margin_without_op_income_is_not_unreconciled():
    """op_margin is what the rules read; op_income is the corroborator."""
    e = parse_entry(entry(quarters=[
        quarter(revenue=12354.0, op_income=None, op_margin=0.1127),
    ]), 0)
    assert e.quarters[0].op_margin == 0.1127


def test_a_quarter_with_neither_figure_still_loads():
    """A blank that reports DATA MISSING stays legitimate."""
    e = parse_entry(entry(quarters=[quarter(revenue=12354.0)]), 0)
    assert e.quarters[0].op_income is None and e.quarters[0].op_margin is None


def test_op_income_without_revenue_cannot_be_reconciled_either_way():
    e = parse_entry(entry(quarters=[quarter(op_income=1416.0)]), 0)
    assert e.quarters[0].op_income == 1416.0


def test_the_nike_figures_reconcile_once_ebit_is_taken():
    """EBIT 1,392 on revenue 12,354 is the 11.3% the release states."""
    e = parse_entry(entry(quarters=[
        quarter(revenue=12354.0, op_income=1392.0, op_margin=0.1127),
    ]), 0)
    assert e.quarters[0].op_income == 1392.0


# --- one ticker, one unit ------------------------------------------------
#
# `vss xbrl` reports whole units (11,279,000,000); a press release reports
# millions (11,279). Each row is internally consistent, so the band check,
# the reconciliation check and every rule pass while the history is out by
# a factor of a million. Only a comparison ACROSS rows can see it.


def test_a_million_fold_jump_in_revenue_fails_the_load():
    with pytest.raises(ConfigError, match="UNIT MIX"):
        parse_watchlist(doc(entry(quarters=[
            quarter(period="2026-Q2", revenue=11279.0),
            quarter(period="2026-Q3", revenue=11_279_000_000.0),
        ])))


def test_the_unit_mix_error_names_both_quarters_and_the_factor():
    with pytest.raises(ConfigError) as exc:
        parse_watchlist(doc(entry(quarters=[
            quarter(period="2026-Q2", revenue=11279.0),
            quarter(period="2026-Q3", revenue=11_279_000_000.0),
        ])))
    message = str(exc.value)
    assert "2026-Q2" in message and "2026-Q3" in message
    assert "1,000,000x" in message
    assert "do not rescale a figure by hand" in message


@pytest.mark.parametrize("field", ["receivables", "inventory"])
def test_the_guard_covers_the_other_stable_money_fields(field):
    with pytest.raises(ConfigError, match="UNIT MIX"):
        parse_watchlist(doc(entry(quarters=[
            quarter(period="2026-Q2", **{field: 2317.0}),
            quarter(period="2026-Q3", **{field: 2_317_000_000.0}),
        ])))


def test_a_real_business_swing_still_loads():
    """Revenue tripling is a business event; the guard fires at 1000x."""
    e = parse_entry(entry(quarters=[
        quarter(period="2026-Q2", revenue=1000.0),
        quarter(period="2026-Q3", revenue=3000.0),
    ]), 0)
    assert [q.revenue for q in e.quarters] == [1000.0, 3000.0]


def test_op_income_is_excluded_from_the_guard():
    """It crosses zero and can genuinely swing orders of magnitude.

    Lindab went from -101 to 491 in four quarters; a near-breakeven
    quarter beside a good one is not evidence of a unit mix.
    """
    e = parse_entry(entry(quarters=[
        quarter(period="2026-Q2", revenue=3000.0, op_income=1.0, op_margin=0.0003),
        quarter(period="2026-Q3", revenue=3000.0, op_income=3000.0, op_margin=1.0),
    ]), 0)
    assert e.quarters[1].op_income == 3000.0


def test_one_quarter_alone_cannot_be_a_unit_mix():
    e = parse_entry(entry(quarters=[quarter(revenue=11_279_000_000.0)]), 0)
    assert e.quarters[0].revenue == 11_279_000_000.0


def test_a_whole_history_in_whole_units_loads():
    """XBRL-sourced rows are fine -- as long as they are ALL XBRL-sourced."""
    e = parse_entry(entry(quarters=[
        quarter(period="2026-Q2", revenue=81_273_000_000.0),
        quarter(period="2026-Q3", revenue=82_886_000_000.0),
    ]), 0)
    assert len(e.quarters) == 2


def test_a_zero_does_not_divide():
    e = parse_entry(entry(quarters=[
        quarter(period="2026-Q2", revenue=0.0),
        quarter(period="2026-Q3", revenue=3000.0),
    ]), 0)
    assert e.quarters[0].revenue == 0.0


# --- source: xbrl, and what it exempts -----------------------------------
#
# The reconciliation existed to establish WHICH LINE op_income came from.
# us-gaap:OperatingIncomeLoss answers that outright, so a margin adds
# nothing to it -- and computing one to satisfy the check would be
# inventing a figure to reassure a checker.


def test_an_xbrl_entry_needs_no_margin_to_load():
    """MSFT: eight quarters of tagged facts, and no margin tag exists."""
    e = parse_entry(entry(quarters=[
        quarter(revenue=82_886_000_000.0, op_income=38_398_000_000.0,
                op_margin=None, source="xbrl"),
    ]), 0)
    assert e.quarters[0].op_income == 38_398_000_000.0
    assert e.quarters[0].op_margin is None
    assert e.quarters[0].source == "xbrl"


@pytest.mark.parametrize("source", [None, "release"])
def test_E79_a_release_entry_no_longer_requires_its_margin(source):
    fields = {"revenue": 12354.0, "op_income": 1416.0, "op_margin": None}
    if source:
        fields["source"] = source
    e = parse_entry(entry(quarters=[quarter(**fields)]), 0)
    assert e.quarters[0].op_income == 1416.0


def test_an_xbrl_entry_that_states_a_margin_is_still_reconciled():
    """The exemption covers an ABSENT margin, not a contradictory one."""
    with pytest.raises(ConfigError, match="do not describe one measure"):
        parse_watchlist(doc(entry(quarters=[
            quarter(revenue=82_886_000_000.0, op_income=38_398_000_000.0,
                    op_margin=0.20, source="xbrl"),
        ])))


def test_an_xbrl_entry_obeys_the_band_check():
    """Exempt from one check, subject to every other."""
    with pytest.raises(ConfigError, match="FRACTIONS, not percentages"):
        parse_watchlist(doc(entry(quarters=[
            quarter(revenue=82_886_000_000.0, op_margin=46.3, source="xbrl"),
        ])))


def test_an_xbrl_entry_obeys_the_scale_guard():
    """source: xbrl records the origin; it does not license mixing units."""
    with pytest.raises(ConfigError, match="UNIT MIX"):
        parse_watchlist(doc(entry(quarters=[
            quarter(period="2026-Q2", revenue=3306.0, source="release"),
            quarter(period="2026-Q3", revenue=82_886_000_000.0, source="xbrl"),
        ])))


def test_an_unknown_source_fails_the_run():
    with pytest.raises(ConfigError, match="source must be one of"):
        parse_watchlist(doc(entry(quarters=[quarter(source="scraped")])))


def test_source_is_an_allowed_quarter_key():
    from vss.config import ALLOWED_QUARTER_KEYS
    assert "source" in ALLOWED_QUARTER_KEYS


def test_a_history_may_record_where_each_quarter_came_from():
    e = parse_entry(entry(quarters=[
        quarter(period="2026-Q2", revenue=81_273_000_000.0, source="xbrl"),
        quarter(period="2026-Q3", revenue=82_886_000_000.0, source="xbrl"),
    ]), 0)
    assert [q.source for q in e.quarters] == ["xbrl", "xbrl"]


# --- E12: Gate 1 frozen at entry -------------------------------------------


def test_a_pipeline_entry_may_carry_its_frozen_gate_1_reading():
    e = parse_entry(entry(status="PIPELINE", dd_at_entry=0.1564,
                          peak_date="2025-08-22"), 0)
    assert e.dd_at_entry == 0.1564
    assert e.peak_date == date(2025, 8, 22)


def test_neither_key_is_required():
    e = parse_entry(entry(), 0)
    assert e.dd_at_entry is None and e.peak_date is None


def test_a_frozen_drawdown_without_its_peak_date_fails_the_run():
    """E12 stores them as a PAIR.

    A frozen Gate 1 reading whose reference peak is not named cannot be
    told from one whose peak has since aged out of the rolling window --
    which is the whole of E11, where half of PNDORA.CO's move out of the
    band was the 2025-08-22 peak leaving the 365-day window.
    """
    with pytest.raises(ConfigError, match="peak_date is not"):
        parse_entry(entry(dd_at_entry=0.1564), 0)


def test_a_peak_date_without_its_drawdown_fails_the_run():
    with pytest.raises(ConfigError, match="dd_at_entry is not"):
        parse_entry(entry(peak_date="2025-08-22"), 0)


def test_a_drawdown_entered_as_a_percentage_is_a_unit_error():
    """15.64 is not a drawdown to evaluate; it is 1,564%."""
    with pytest.raises(ConfigError, match="FRACTION, not a percentage"):
        parse_entry(entry(dd_at_entry=15.64, peak_date="2025-08-22"), 0)


def test_a_negative_drawdown_is_refused():
    """The trailing high includes today's close, so it cannot be negative."""
    with pytest.raises(ConfigError, match=r"outside \[0, 1\]"):
        parse_entry(entry(dd_at_entry=-0.01, peak_date="2025-08-22"), 0)


def test_the_band_edges_are_accepted():
    assert parse_entry(entry(dd_at_entry=0.0, peak_date="2025-08-22"), 0).dd_at_entry == 0.0
    assert parse_entry(entry(dd_at_entry=1.0, peak_date="2025-08-22"), 0).dd_at_entry == 1.0


def test_a_malformed_peak_date_fails_the_run():
    with pytest.raises(ConfigError, match="peak_date must be a YYYY-MM-DD date"):
        parse_entry(entry(dd_at_entry=0.1564, peak_date="22 Aug 2025"), 0)


def test_dd_at_entry_is_not_computed_and_so_is_not_a_forbidden_key():
    """It is MANUAL, like fv_base -- a reading taken once and written down,
    not something the tool recomputes. Only `mbp` is COMPUTED."""
    from vss.config import ALLOWED_KEYS, COMPUTED_KEYS

    assert {"dd_at_entry", "peak_date"} <= ALLOWED_KEYS
    assert {"dd_at_entry", "peak_date"} & COMPUTED_KEYS == set()


# --- E24: the rate a converted verdict was struck at -------------------------


FX_OK = {
    "pair": "EUR->SEK",
    "rate": 11.08,
    "rate_as_of": "2026-08-21",
    "source": "EURSEK=X close 2026-08-21",
    "converted": "accounts",
    "price_date": "2026-08-21",
}


def _entry_with_fx(fx):
    return {"tickers": [{"ticker": "BETS-B.ST", "name": "Betsson",
                         "currency": "SEK", "status": "WATCH-GATED", "fx": fx}]}


def test_the_six_facts_round_trip():
    """E24: pair with its direction, rate, the rate's own as-of date, source,
    which side was converted, and the price date it is compared against."""
    from datetime import date

    (entry,) = parse_watchlist(_entry_with_fx(dict(FX_OK)))
    fx = entry.fx
    assert (fx.pair, fx.base, fx.quote) == ("EUR->SEK", "EUR", "SEK")
    assert fx.rate == 11.08
    assert fx.rate_as_of == date(2026, 8, 21)
    assert fx.price_date == date(2026, 8, 21)
    assert fx.converted == "accounts"
    assert "EURSEK" in fx.source
    assert fx.age_days(date(2026, 9, 1)) == 11


def test_no_fx_block_is_the_normal_case():
    (entry,) = parse_watchlist(
        {"tickers": [{"ticker": "SAP.DE", "name": "SAP", "currency": "EUR",
                      "status": "HELD", "fv_bull": 259.0}]})
    assert entry.fx is None


@pytest.mark.parametrize("missing", list(FX_OK))
def test_five_of_six_is_not_a_record(missing):
    """A rate without its own as-of date cannot be re-struck, and a rate
    without a direction is as likely to be its reciprocal."""
    fx = {k: v for k, v in FX_OK.items() if k != missing}
    with pytest.raises(ConfigError, match="fx is missing"):
        parse_watchlist(_entry_with_fx(fx))


def test_the_pair_must_carry_its_direction():
    fx = dict(FX_OK, pair="EURSEK")
    with pytest.raises(ConfigError, match="BASE->QUOTE"):
        parse_watchlist(_entry_with_fx(fx))


def test_the_converted_side_must_say_which_side():
    fx = dict(FX_OK, converted="yes")
    with pytest.raises(ConfigError, match="fx converted must be one of"):
        parse_watchlist(_entry_with_fx(fx))


def test_a_negative_rate_is_refused():
    fx = dict(FX_OK, rate=-11.08)
    with pytest.raises(ConfigError, match="fx rate must be positive"):
        parse_watchlist(_entry_with_fx(fx))


def test_an_unknown_fx_key_is_refused():
    fx = dict(FX_OK, note="looks harmless")
    with pytest.raises(ConfigError, match="unknown key"):
        parse_watchlist(_entry_with_fx(fx))


# --- E29: the frozen hurdle rate ------------------------------------------


def test_e29_hurdle_is_four_facts_or_none():
    """FRAMEWORK-EDITS E29, on E24's reasoning.

    A rate without its anchor cannot be audited later, and a rate without its
    own as-of date cannot be told from today's. So a partial block is an
    error rather than a best effort.
    """
    good = {"rate": 0.095, "core_expected_return": 0.07, "premium": 0.025,
            "rate_as_of": "2026-08-25"}
    e = parse_entry(entry(hurdle=good), 0)
    assert e.hurdle.rate == 0.095
    assert e.hurdle.core_expected_return == 0.07
    assert e.hurdle.premium == 0.025
    assert e.hurdle.rate_as_of == date(2026, 8, 25)

    # absent is fine -- most rows have no purchase verdict to freeze
    assert parse_entry(entry(), 0).hurdle is None

    for dropped in good:
        partial = {k: v for k, v in good.items() if k != dropped}
        with pytest.raises(ConfigError, match="hurdle is missing"):
            parse_entry(entry(hurdle=partial), 0)


def test_e29_hurdle_must_reconcile_to_its_own_anchor():
    """r = core expected return + premium, or it is not anchored."""
    with pytest.raises(ConfigError, match="does not equal"):
        parse_entry(entry(hurdle={"rate": 0.10, "core_expected_return": 0.07,
                                  "premium": 0.025,
                                  "rate_as_of": "2026-08-25"}), 0)


def test_e29_premium_outside_the_ruled_band_is_refused():
    """2-3 points is the ruling; moving it is a change to E29, not an input."""
    with pytest.raises(ConfigError, match="premium"):
        parse_entry(entry(hurdle={"rate": 0.12, "core_expected_return": 0.07,
                                  "premium": 0.05,
                                  "rate_as_of": "2026-08-25"}), 0)


def test_e29_hurdle_rejects_unknown_keys():
    with pytest.raises(ConfigError, match="unknown key"):
        parse_entry(entry(hurdle={"rate": 0.095, "core_expected_return": 0.07,
                                  "premium": 0.025, "rate_as_of": "2026-08-25",
                                  "currency": "SEK"}), 0)


# --- E32: mbp_basis, and the guard that still refuses a hand-written mbp ---


def test_e32_a_hand_written_mbp_is_still_refused():
    """E32 changes what the message ASSERTS, not what the guard DOES."""
    with pytest.raises(ConfigError, match="mbp is COMPUTED"):
        parse_watchlist(doc(entry(mbp=140.0)))


def test_e32_the_guard_message_no_longer_asserts_the_struck_definition():
    with pytest.raises(ConfigError) as exc:
        parse_watchlist(doc(entry(mbp=1.0)))
    message = str(exc.value)
    assert "mbp = fv_base * tier multiplier" not in message, (
        "the message must not state a definition the framework has struck")
    assert "SUPERSEDED" in message and "pre-registered bear case" in message.lower()
    assert "fv_base" in message and "tier" in message


def test_e32_mbp_basis_records_the_definition_and_the_date():
    e = parse_entry(entry(fv_base=185.0, tier=1, mbp_basis={
        "definition": "fv_base_x_tier", "struck": "2026-08-22"}), 0)
    assert e.mbp_basis.definition == "fv_base_x_tier"
    assert e.mbp_basis.struck == "2026-08-22"
    assert e.mbp_basis.superseded is True


def test_e32_the_e28_definition_is_not_superseded():
    e = parse_entry(entry(fv_base=185.0, tier=1, mbp_basis={
        "definition": "e28_bear_case", "struck": "2026-10-22"}), 0)
    assert e.mbp_basis.superseded is False


def test_e32_an_unrecoverable_date_may_be_bounded():
    """LIAB.ST's shape: the day is not recoverable and is not invented."""
    e = parse_entry(entry(fv_base=102.66, tier=2, mbp_basis={
        "definition": "fv_base_x_tier", "struck": "on or before 2026-08-21"}), 0)
    assert e.mbp_basis.struck == "on or before 2026-08-21"


@pytest.mark.parametrize("struck", [
    "2026", "August 2026", "before 2026-08-21", "circa 2026-08-21", "sometime",
])
def test_e32_there_is_no_third_date_form(struck):
    with pytest.raises(ConfigError, match="on or before"):
        parse_entry(entry(fv_base=1.0, tier=1, mbp_basis={
            "definition": "fv_base_x_tier", "struck": struck}), 0)


def test_e32_mbp_basis_is_both_keys_or_neither():
    with pytest.raises(ConfigError, match="mbp_basis is missing"):
        parse_entry(entry(mbp_basis={"definition": "fv_base_x_tier"}), 0)
    with pytest.raises(ConfigError, match="mbp_basis is missing"):
        parse_entry(entry(mbp_basis={"struck": "2026-08-22"}), 0)


def test_e32_an_unknown_definition_fails_the_run():
    with pytest.raises(ConfigError, match="mbp_basis.definition must be one of"):
        parse_entry(entry(mbp_basis={"definition": "e28", "struck": "2026-08-22"}), 0)


def test_e32_the_shipped_watchlist_records_all_three_held_names():
    """The three E32 retains, each carrying its definition and its date.

    SAP.DE was SOLD 2026-08-26 under C4 (FRAMEWORK-EDITS E42) and moved to
    WATCH-PRICED with a re-entry line struck under E28 on the re-strike of
    the same day (bear case pre-registered first, item 6), so its basis is
    E28's and not superseded; re-struck 2026-08-30 from the store, end to
    end, and again the same evening under E90/E91 (basis e90_base_cushion).
    UNA.AS and LIAB.ST still carry the retained
    fv_base_x_tier figures E32 kept.
    """
    import yaml
    from pathlib import Path
    path = Path(__file__).resolve().parents[1] / "config" / "watchlist.yaml"
    entries = {e.ticker: e for e in parse_watchlist(
        yaml.safe_load(path.read_text(encoding="utf-8")))}
    expected = (
        ("SAP.DE", "e90_base_cushion", "2026-08-30", False),
        ("UNA.AS", "fv_base_x_tier", "2026-08-22", True),
        ("LIAB.ST", "fv_base_x_tier", "on or before 2026-08-21", True),
    )
    for ticker, definition, struck, superseded in expected:
        basis = entries[ticker].mbp_basis
        assert basis is not None, f"{ticker} has an mbp and no record of its basis"
        assert basis.definition == definition
        assert basis.struck == struck
        assert basis.superseded is superseded
    # WATCH-PRICED -> WATCH-GATED 2026-09-20 (owner): a bound, pre-E117
    # value on a superseded basis was carrying a live buy line.
    assert entries["SAP.DE"].status == "WATCH-GATED"
    assert entries["SAP.DE"].stop_price is None


# --- F3: a YAML boolean is not a number -----------------------------------
#
# YAML 1.1 resolves an unquoted no/yes/on/off to a bool before the loader
# sees it, and float(False) is 0.0. `manual._as_float` has always refused a
# bool; this loader did not, so a word written where a number belongs became
# a figure nobody entered.


@pytest.mark.parametrize("token", ["no", "yes", "on", "off"])
@pytest.mark.parametrize(
    "key", ["fv_base", "stop_price", "dd_at_entry"])
def test_a_yaml_boolean_is_refused_on_every_entry_number(key, token):
    import yaml
    value = yaml.safe_load(token)
    assert isinstance(value, bool), f"{token!r} no longer resolves to a bool"
    raw = entry(**{key: value})
    if key == "dd_at_entry":
        raw["peak_date"] = "2026-01-01"
    with pytest.raises(ConfigError, match="must be a number"):
        parse_entry(raw, 0)


@pytest.mark.parametrize(
    "key",
    ["revenue", "revenue_yoy", "revenue_yoy_organic", "op_income", "op_margin",
     "eps", "eps_consensus", "net_debt_ebitda", "receivables", "inventory",
     "class_c_impact", "covenant_headroom"],
)
def test_a_yaml_boolean_is_refused_on_every_quarter_number(key):
    """`covenant_headroom: no` read as 0.0 TRIPS 4.2.5 as covenant
    proximity, and `revenue_yoy_organic: no` read as 0.0 SUPPRESSES the
    4.2.1 decline kill. Neither figure was entered by anyone."""
    with pytest.raises(ConfigError, match="must be a number"):
        parse_entry(entry(quarters=[{"period": "2026-Q2", key: False}]), 0)


def test_the_boolean_message_names_yaml_as_the_cause():
    with pytest.raises(ConfigError) as exc:
        parse_entry(entry(stop_price=False), 0)
    text = str(exc.value)
    assert "BOOLEAN" in text and "yes/no/on/off" in text
    assert "DATA MISSING" in text


def test_a_quoted_number_is_still_a_number():
    """Refusing bools must not refuse the string forms that already worked."""
    e = parse_entry(entry(fv_base="200.0", stop_price=140), 0)
    assert e.fv_base == 200.0 and e.stop_price == 140.0


# --- F3: a price leg is a price -------------------------------------------


@pytest.mark.parametrize("bad", [0, 0.0, -1, -140.0])
@pytest.mark.parametrize("key", ["fv_base", "stop_price"])
def test_a_price_leg_of_zero_or_less_fails_the_run(key, bad):
    with pytest.raises(ConfigError, match="must be strictly positive"):
        parse_entry(entry(**{key: bad}), 0)


def test_a_zero_stop_would_otherwise_be_a_stop_that_can_never_breach():
    """The mechanism, stated in the test so the reason survives a refactor.

    `missing_stop_blocker` tests `stop_price is None`, so 0.0 raises no
    blocker; `stop_verdict` tests `last_close <= stop_price`, so no real
    close ever breaches. The HELD row would report AT/BELOW MBP -- a buy --
    on a position whose exit is unreachable.
    """
    from vss.rules import missing_stop_blocker, stop_verdict
    assert missing_stop_blocker("HELD", 0.0) is None
    assert stop_verdict("HELD", 41.0, 0.0) is None
    with pytest.raises(ConfigError, match="a stop of 0 can never breach"):
        parse_entry(entry(status="HELD", stop_price=0), 0)


def test_a_zero_fv_base_would_otherwise_replace_data_missing_with_no_verdict():
    """`compute_mbp(0.0, 2)` is 0.0, not None, and `mbp_verdict` then
    returns nothing at all rather than the DATA MISSING it is written to
    report."""
    from vss.rules import compute_mbp, mbp_verdict
    assert compute_mbp(0.0, 2) == 0.0
    assert mbp_verdict(41.0, 0.0) is None
    assert mbp_verdict(41.0, None).code == "DATA_MISSING"
    with pytest.raises(ConfigError, match="must be strictly positive"):
        parse_entry(entry(fv_base=0, tier=2), 0)


def test_a_blank_price_leg_is_still_data_missing_and_still_loads():
    """The check does not make either field required."""
    e = parse_entry(entry(fv_base=None, stop_price=None), 0)
    assert e.fv_base is None and e.stop_price is None


@pytest.mark.parametrize(
    "key,zero_is_a_reading",
    [("revenue_yoy", "flat revenue"),
     ("revenue_yoy_organic", "flat organic revenue"),
     ("op_income", "breakeven"),
     ("op_margin", "breakeven"),
     ("eps", "breakeven"),
     ("eps_consensus", "consensus of nil"),
     ("net_debt_ebitda", "a debt-free balance sheet"),
     ("covenant_headroom", "no headroom, which SHOULD trip 4.2.5"),
     ("class_c_impact", "a one-off of nil")],
)
def test_zero_is_kept_on_every_field_where_it_is_a_real_reading(
        key, zero_is_a_reading):
    """The price-leg rule is narrow ON PURPOSE. Refusing zero on these
    would convert a reading into an error."""
    e = parse_entry(entry(quarters=[{"period": "2026-Q2", key: 0}]), 0)
    assert getattr(e.quarters[0], key) == 0.0, zero_is_a_reading


def test_zero_is_kept_on_dd_at_entry_for_a_name_at_its_own_high():
    e = parse_entry(entry(dd_at_entry=0.0, peak_date="2026-01-01"), 0)
    assert e.dd_at_entry == 0.0


# --- F4: a currency code must survive being upper-cased -------------------


def test_gbp_minor_unit_is_stored_as_gbx_not_gbp():
    """`GBp` is PENCE. `.upper()` turns it into `GBP`, which is pounds --
    a different unit, a factor of a hundred, and `fv_base`, `stop_price`
    and the mbp are compared against `last_close` with no conversion
    anywhere (E24)."""
    e = parse_entry(entry(ticker="JD.L", currency="GBp"), 0)
    assert e.currency == "GBX"


@pytest.mark.parametrize(
    "given,stored",
    [("GBp", "GBX"), ("GBX", "GBX"), ("gbx", "GBX"),
     ("ZAc", "ZAC"), ("ILA", "ILA"),
     ("SEK", "SEK"), ("usd", "USD"), ("eur", "EUR"), (" dkk ", "DKK")],
)
def test_currency_round_trip(given, stored):
    assert parse_entry(entry(currency=given), 0).currency == stored


def test_the_loader_uses_fx_upper_safe_code_and_does_not_restate_it():
    """One mapping, one place. A second copy is how the two drift apart."""
    import inspect
    from vss import config as config_module
    from vss.fx import UPPER_SAFE_MINOR, upper_safe_code
    source = inspect.getsource(config_module.parse_entry)
    assert "upper_safe_code" in source
    assert '"currency"' in source and ".upper()" not in source.split(
        'currency = ')[1].split("\n")[0]
    for given, expected in UPPER_SAFE_MINOR.items():
        assert parse_entry(entry(currency=given), 0).currency == \
            upper_safe_code(given) == expected


def test_the_shipped_watchlist_still_stores_jd_l_as_gbx():
    import yaml
    from pathlib import Path
    path = Path(__file__).resolve().parents[1] / "config" / "watchlist.yaml"
    entries = {e.ticker: e for e in parse_watchlist(
        yaml.safe_load(path.read_text(encoding="utf-8")))}
    assert entries["JD.L"].currency == "GBX"


# --- B45: the sales block, one item per fill ---------------------------------


def _fill(**overrides):
    raw = {"date": "2026-08-21", "price": 482.43, "shares": 4, "rule": "C4",
           "account": "ACCOUNT-B", "proceeds_sek": 18185.66}
    raw.update(overrides)
    return raw


def test_b45_a_fill_parses_with_every_field():
    e = parse_entry(entry(currency="USD", status="DROPPED", sales=[_fill(
        run_record="reference/run-records/X.json", note="booked")]), 0)
    assert len(e.sales) == 1
    s = e.sales[0]
    assert s.date == date(2026, 8, 21)
    assert s.price == 482.43 and s.shares == 4 and s.rule == "C4"
    assert s.account == "ACCOUNT-B" and s.proceeds_sek == 18185.66
    assert s.run_record == "reference/run-records/X.json"
    assert s.currency == "USD" and not s.price_missing


def test_b45_a_fill_with_no_price_is_data_missing_not_an_error():
    e = parse_entry(entry(sales=[_fill(price=None)]), 0)
    assert e.sales[0].price is None and e.sales[0].price_missing


def test_b45_fills_are_sorted_oldest_first():
    e = parse_entry(entry(sales=[_fill(date="2026-08-26"), _fill(date="2026-08-21")]), 0)
    assert [s.date for s in e.sales] == [date(2026, 8, 21), date(2026, 8, 26)]


def test_b45_the_fill_currency_defaults_to_the_entry_currency_and_may_be_stated():
    e = parse_entry(entry(currency="SEK", sales=[_fill(), _fill(currency="EUR")]), 0)
    assert [s.currency for s in e.sales] == ["SEK", "EUR"]


@pytest.mark.parametrize("missing", ["date", "shares", "rule"])
def test_b45_date_shares_and_rule_are_required(missing):
    raw = _fill()
    del raw[missing]
    with pytest.raises(ConfigError, match=f"missing {missing}"):
        parse_entry(entry(sales=[raw]), 0)


def test_b45_rule_vocabulary_is_closed_and_owner_is_a_rule():
    assert parse_entry(entry(sales=[_fill(rule="owner")]), 0).sales[0].rule == "owner"
    assert parse_entry(entry(sales=[_fill(rule="c1")]), 0).sales[0].rule == "C1"
    with pytest.raises(ConfigError, match="rule must be one of"):
        parse_entry(entry(sales=[_fill(rule="C9")]), 0)


@pytest.mark.parametrize("bad", [{"price": -1.0}, {"price": 0}, {"shares": 0},
                                 {"shares": -3}, {"proceeds_sek": -5.0}])
def test_b45_a_fill_that_cannot_be_a_fill_fails(bad):
    with pytest.raises(ConfigError):
        parse_entry(entry(sales=[_fill(**bad)]), 0)


def test_b45_unknown_fill_keys_fail_loudly():
    with pytest.raises(ConfigError, match="unknown key"):
        parse_entry(entry(sales=[_fill(fill_price=1.0)]), 0)


def test_b45_sales_must_be_a_list():
    with pytest.raises(ConfigError, match="sales must be a list"):
        parse_entry(entry(sales=_fill()), 0)


def test_b45_no_sales_block_means_no_fills():
    assert parse_entry(entry(), 0).sales == ()


# --- duplicate keys: YAML takes the LAST and says nothing -----------------

def _duplicate_keys(path):
    """Every key stated twice in one mapping, with the two line numbers.

    `yaml.safe_load` takes the LAST of a repeated key and reports nothing,
    so a duplicate is a line that is IN THE FILE and INVISIBLE TO THE TOOL.
    Nothing in this repo could see one until 2026-09-08.
    """
    import yaml

    found = []

    class Loader(yaml.SafeLoader):
        pass

    def mapping(loader, node, deep=False):
        seen = {}
        for key_node, _ in node.value:
            key = loader.construct_object(key_node, deep=deep)
            if key in seen:
                found.append((key, seen[key], key_node.start_mark.line + 1))
            seen[key] = key_node.start_mark.line + 1
        return yaml.SafeLoader.construct_mapping(loader, node, deep=deep)

    Loader.add_constructor(yaml.resolver.BaseResolver.DEFAULT_MAPPING_TAG,
                           mapping)
    with open(path, encoding="utf-8") as handle:
        yaml.load(handle, Loader=Loader)
    return found


def test_no_watchlist_row_states_a_key_twice():
    """CROX carried two `notes:` and the OWNER'S RULING was the losing one.

    2026-09-08: the row said DROPPED, the note the tool loaded said
    "E111 INTAKE ... NO GROWTH VIEW IS REGISTERED", and the DROPPED
    reasoning -- the verbatim ruling, the HEYDUDE figures, the buyback
    measurement -- sat above it in the file where nothing would ever read
    it. The stale line was also FALSE on its own terms: the row carries a
    growth block registered 2026-09-04.

    THE ONLY DUPLICATES LEFT ARE SAP.DE's `source:` PLACEHOLDERS, and they
    are here by name rather than by a blanket exemption: each is an empty
    template `source:` shadowed by the `source: release` written under it,
    so the surviving value is the one that was meant and the shadowed one
    carries no information. That is the whole difference from CROX, where
    what was shadowed was the record.
    """
    dups = _duplicate_keys("config/watchlist.yaml")
    assert all(key == "source" for key, _, _ in dups), \
        f"a watchlist row states a key twice: {dups}"
    assert len(dups) == 10, \
        f"the SAP.DE `source:` placeholders were 10; now {len(dups)}"


def test_a_shadowed_store_figure_would_be_a_figure_nobody_chose():
    """The same mechanism in the manual store, where it reaches a FIGURE.

    RKT.L states `shares_issued_period_end` and `treasury_shares_period_end`
    twice, and RMV.L states `op_margin` twice in two periods. In all four
    the two entries carry the SAME `value` and differ only in the `page`
    prose, so no figure is chosen by line order today. This test is what
    keeps that true: an edit that moved one of the values and not the other
    would change a store figure with nothing printed and nothing refused.
    """
    import yaml

    for path in ("config/manual/RKT.L.yaml", "config/manual/RMV.L.yaml"):
        lines = open(path, encoding="utf-8").read().split("\n")
        for key, first, second in _duplicate_keys(path):
            def value_under(line):
                # `value:` is the first line of the block the key opens
                assert lines[line].strip().startswith("value:"), \
                    f"{path}:{line + 1} does not open with `value:`"
                return yaml.safe_load(lines[line].split(":", 1)[1])
            assert value_under(first) == value_under(second), \
                (f"{path}: `{key}:` at line {first} is SHADOWED by line "
                 f"{second} and the two state different values -- the store "
                 f"figure is whichever was written last")
