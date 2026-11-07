"""Foreign withholding tax on dividends in a Swedish ISK -- a pure cost under
the tax-free allowance.

Owner 2026-11-07 (from DonkeyInvestor's lessons): while the ISK's value is
under the year's allowance (300,000 kr in 2026) the ISK schablon tax is
zero, so foreign withholding tax cannot be credited against it and is a
plain cost. A Swedish listing withholds nothing in an ISK.

The drag is a yearly percentage of the holding: dividend yield x rate. It
is SHOWN beside a foreign name (the Nordic screen, the entry step); it does
not change fv, MBP or any rule -- that would be a ruling, the owner's.
"""
from __future__ import annotations

#: Statutory withholding on dividends to a Swedish ISK, as a fraction.
RATES: dict[str, float] = {"SE": 0.0, "FI": 0.35, "DK": 0.27, "NO": 0.25, "US": 0.15}

#: Ticker suffix -> country.
SUFFIX_COUNTRY: dict[str, str] = {"ST": "SE", "HE": "FI", "CO": "DK", "OL": "NO", "US": "US"}

ALLOWANCE_SEK_2026 = 300_000


def country_of(ticker: str) -> str:
    suffix = ticker.rsplit(".", 1)[-1].upper() if "." in ticker else "US"
    return SUFFIX_COUNTRY.get(suffix, "")


def drag(dividend_yield: float | None, country: str) -> float | None:
    """Yearly cost as a fraction of the holding, or None where unknown."""
    rate = RATES.get(country)
    if dividend_yield is None or rate is None:
        return None
    return dividend_yield * rate
