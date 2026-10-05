"""A SYNTHETIC section 5 run record for a SYNTHETIC fixture (Build 2 item 9).

`vss run` prints an `fv_base` only from a complete run record that replays
to it. The verdict-matrix fixture's fair values are fabricated thresholds
(see its header), so the records that let them print are fabricated the
same way and say so on every line: FCF0 is zero, net cash IS the fair
value, the share count is one (whole), money is in whole units, and every
provenance string reads SYNTHETIC. Nothing here is a valuation of anything.
"""

from __future__ import annotations

from datetime import date, datetime
from zoneinfo import ZoneInfo

from vss import runrecord as R

SYNTHETIC = "SYNTHETIC FIXTURE (tests/_records.py) -- not a filing, not a figure"
WHEN = date(2026, 8, 20)


def synthetic_record(ticker: str, currency: str, fv_base: float) -> R.RunRecord:
    """Complete in all eight declarations, and replays to ``fv_base`` exactly."""
    inputs = tuple(R.Input(name, value, SYNTHETIC, "hand", "hand") for name, value in (
        ("operating_cash_flow", 0.0), ("capex_combined", 0.0), ("sbc", 0.0),
        ("net_interest_paid", 0.0), ("diluted_weighted_average_shares", 1.0),
        ("financial_liabilities_current", 0.0),
        ("financial_liabilities_noncurrent", 0.0), ("lease_liabilities", 0.0),
        ("pension_deficit", 0.0), ("cash_and_equivalents", float(fv_base)),
        ("other_current_financial_assets", 0.0),
        ("nci_dividends_paid", 0.0)))
    return R.RunRecord(
        ticker=ticker, currency=currency,
        run_ts=datetime(2026, 8, 20, 22, 30, tzinfo=ZoneInfo("Europe/Stockholm")),
        basis=f"{SYNTHETIC}: no window",
        shares=R.ShareBasis(count=1.0, basis=SYNTHETIC, as_of=WHEN, unit="whole"),
        sbc=R.SbcTreatment(R.SBC_DEDUCTED, 0.0),
        interest=R.InterestTreatment(True, SYNTHETIC, 0.0),
        bridge=R.Bridge(net_debt=-float(fv_base),
                        items={item: 0.0 for item in R.BRIDGE_ITEMS},
                        note=SYNTHETIC),
        dates=R.AsOfDates(WHEN, WHEN, WHEN, WHEN),
        growth=R.Growth(base=0.0, view_file=SYNTHETIC),
        operating_cash_flow=0.0, capex=0.0,
        # E105: a synthetic record has no minorities, and says so rather
        # than being coerced -- an absent leg is DATA MISSING by the ruling.
        nci_dividends_paid=0.0,
        inputs=inputs, tool_commit="synthetic", notes=SYNTHETIC,
        money_unit="whole")
