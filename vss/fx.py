"""Exchange rates for the ranking key (FRAMEWORK-EDITS E5(b), kept by E6).

The screener avoided FX for three phases because every ratio it computed came
from a single statement and the currency cancelled. The earnings yield is the
first that does not: EBIT is in the reporting currency while enterprise value
is in the quoting one, and they differ for roughly one candidate in seven.

Two things this module exists to get right.

**Rates are fetched once per RUN, per PAIR.** Ten-odd pairs, not one lookup
per ticker. Every rate is returned with the date of the close it came from.

**AND THEY CAN BE READ BACK -- WHICH IS NOT THE SAME THING.** Writing the rates
into a manifest makes a run AUDITABLE: you can see afterwards which rate was
used. It does not make it REPRODUCIBLE, and until 2026-08-22 nothing said so.
``default_lookup`` always asks for ``period="5d"`` and takes the LAST close, so
re-running ``--rank --asof 2026-08-21`` tomorrow silently uses tomorrow's
rates. The proof was already sitting inside the 2026-08-21 manifest, which
carries ten pairs dated 08-21 and two dated 08-22: ONE RUN, TWO CURRENCY
DATES, and no line of output mentioned it.

``lookup_from_manifest`` is the read-back path, reached by
``--fx-from-manifest``. A pair the manifest does not carry is NOT quietly
fetched -- that would produce a "reproduction" that is partly a new run. It
FAILS, is named as a failure, and withholds the yields that needed it.

**A quote currency's minor unit is not its currency.** London quotes in GBp --
pence -- but market capitalisation and enterprise value come back in GBP, the
major unit; this was verified by ``marketCap / sharesOutstanding`` reproducing
price divided by a hundred. Reading an EV in GBP as if it were pence would
divide it by a hundred and multiply the earnings yield by the same, putting
every British name at the top of the list. It is the error that does the most
damage and shows the least, so the mapping is explicit, tested, and applied
before any rate is looked up.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import date
from typing import Callable, Iterable, Mapping

log = logging.getLogger(__name__)

#: Quote codes that name a MINOR unit, mapped to the major unit the quote
#: summary's monetary fields actually use. Not a guess: verified against
#: marketCap / sharesOutstanding for a pence-quoted London name.
MINOR_UNITS: dict[str, str] = {
    "GBp": "GBP",   # London, pence
    "GBX": "GBP",   # the same thing under its other code
    "ZAc": "ZAR",   # Johannesburg, cents
    "ILA": "ILS",   # Tel Aviv, agorot
}


#: How many minor units make one major unit. Used ONLY on figures that are
#: quoted in the minor unit -- which means the PRICE SERIES, and nothing that
#: comes out of the quote summary.
#:
#: The distinction is easy to get backwards and expensive both ways. Market
#: capitalisation and enterprise value arrive in GBP for a GBp-quoted name, so
#: they need no division; the daily close arrives in pence, so turnover
#: computed from it does. Dividing the first would shrink an enterprise value
#: by a hundred; not dividing the second would make one London listing look a
#: hundred times more traded than a Stockholm one.
MINOR_UNITS_PER_MAJOR: dict[str, float] = {
    "GBp": 100.0, "GBX": 100.0, "ZAc": 100.0, "ILA": 100.0,
}


def minor_unit_divisor(code: str | None) -> float:
    """Divide a PRICE-DERIVED amount by this to reach the major unit."""
    if not code:
        return 1.0
    return MINOR_UNITS_PER_MAJOR.get(code.strip(), 1.0)


#: Minor-unit codes that survive being upper-cased without changing meaning.
#: The watchlist loader upper-cases whatever currency it is given, so "GBp"
#: cannot be stored: it would come back "GBP" and a price of 4161 pence would
#: read as 4161 pounds. GBX is the standard upper-case code for pence and
#: means exactly what GBp does, so it survives the round trip intact.
UPPER_SAFE_MINOR: dict[str, str] = {
    "GBp": "GBX", "GBX": "GBX", "ZAc": "ZAC", "ILA": "ILA",
}


def upper_safe_code(code: str | None) -> str | None:
    """A currency code that still means the same thing after ``.upper()``.

    Anywhere a code is written into a file that will upper-case it, this is
    the form to write. Getting it wrong turns a pence quote into a pound one
    and every hand-entered stop for that name into a hundredfold error.
    """
    if not code:
        return None
    code = code.strip()
    return UPPER_SAFE_MINOR.get(code, code.upper())


def major_unit(code: str | None) -> str | None:
    """The currency a quote-summary monetary field is denominated in.

    ``major_unit("GBp") == "GBP"``. Case is preserved for the lookup because
    "GBp" and "GBP" are different codes meaning different units, and folding
    them together is the bug.
    """
    if not code:
        return None
    return MINOR_UNITS.get(code.strip(), code.strip())


@dataclass(frozen=True)
class Rate:
    pair: str
    value: float
    as_of: date | None
    source: str

    def convert(self, amount: float) -> float:
        return amount * self.value


@dataclass
class FxTable:
    """Every rate a run used, and how it got them."""

    rates: dict[str, Rate] = field(default_factory=dict)
    failures: dict[str, str] = field(default_factory=dict)

    def key(self, base: str, quote: str) -> str:
        return f"{base}->{quote}"

    def get(self, base: str | None, quote: str | None) -> Rate | None:
        """Rate that turns an amount in ``base`` into ``quote``.

        Returns None -- DATA MISSING -- when the pair could not be fetched.
        Never falls back to 1.0: a missing rate silently treated as parity is
        an error of exactly the size of the exchange rate.
        """
        base, quote = major_unit(base), major_unit(quote)
        if not base or not quote:
            return None
        if base == quote:
            return Rate(self.key(base, quote), 1.0, None, "identity")
        return self.rates.get(self.key(base, quote))

    def as_manifest(self) -> dict[str, str]:
        out = {
            f"fx:{rate.pair}": f"{rate.value:.6f} ({rate.source})"
            for rate in self.rates.values()
        }
        out.update({f"fx_failed:{pair}": reason for pair, reason in self.failures.items()})
        return out


def default_lookup(base: str, quote: str) -> tuple[float, date | None, str]:
    """One pair from yfinance's FX series. Replaced wholesale in tests."""
    import yfinance as yf

    symbol = f"{base}{quote}=X"
    frame = yf.Ticker(symbol).history(period="5d", interval="1d")
    if frame is None or len(frame) == 0 or "Close" not in frame.columns:
        raise RuntimeError(f"{symbol}: no rows")
    closes = frame["Close"].dropna()
    if closes.empty:
        raise RuntimeError(f"{symbol}: no usable close")
    import pandas as pd

    return float(closes.iloc[-1]), pd.Timestamp(closes.index[-1]).date(), symbol


def read_manifest_rates(path) -> dict[str, Rate]:
    """Every rate a stored run recorded, keyed ``BASE->QUOTE``.

    Accepts the ranking manifest as written by ``screen._write_ranking``. The
    rate's own ``as_of`` is preserved rather than replaced by the replay date,
    because it is the date of the close the number came from and pretending
    otherwise would hide exactly what this flag exists to expose.
    """
    import json
    from pathlib import Path as _Path

    document = json.loads(_Path(path).read_text(encoding="utf-8"))
    stored = document.get("fx") or {}
    out: dict[str, Rate] = {}
    for pair, entry in stored.items():
        as_of = entry.get("as_of")
        out[pair] = Rate(
            pair=pair,
            value=float(entry["rate"]),
            as_of=date.fromisoformat(as_of) if as_of else None,
            source=f"{entry.get('source', '?')} (replayed from manifest)",
        )
    return out


def manifest_asof(path) -> date | None:
    """The date a stored manifest says its rates belong to (L5).

    The field was written from the first run and read by nothing, so replaying
    2026-08-21's rates into a run dated 2026-07-27 was accepted in silence.
    Returns None when the file does not carry the field -- which is a reason
    to say so, not a reason to assume the dates agree.
    """
    import json
    from pathlib import Path as _Path

    document = json.loads(_Path(path).read_text(encoding="utf-8"))
    stamp = document.get("asof")
    return date.fromisoformat(stamp) if stamp else None


def lookup_from_manifest(path) -> Callable[[str, str], tuple[float, date | None, str]]:
    """A lookup that reads a stored run instead of the network.

    Raises for a pair the manifest does not carry. ``build_table`` turns that
    into a recorded FAILURE, which withholds the yields that needed the pair
    and prints the missing pair by name -- rather than a silent half-fetch
    that would make the answer neither the old one nor a new one.
    """
    rates = read_manifest_rates(path)

    def lookup(base: str, quote: str) -> tuple[float, date | None, str]:
        rate = rates.get(f"{base}->{quote}")
        if rate is None:
            raise KeyError(
                f"{base}->{quote} is not in {path}; this run needs a pair the "
                f"stored run did not use, so it cannot be reproduced from it"
            )
        return rate.value, rate.as_of, rate.source

    return lookup


def pairs_needed(currency_pairs: Iterable[tuple[str | None, str | None]]) -> list[tuple[str, str]]:
    """Distinct (base, quote) pairs, after minor units are resolved.

    Identity pairs are dropped: nothing needs fetching to convert EUR to EUR.
    """
    out: set[tuple[str, str]] = set()
    for base, quote in currency_pairs:
        base, quote = major_unit(base), major_unit(quote)
        if base and quote and base != quote:
            out.add((base, quote))
    return sorted(out)


def build_table(
    currency_pairs: Iterable[tuple[str | None, str | None]],
    *,
    lookup: Callable[[str, str], tuple[float, date | None, str]] = default_lookup,
) -> FxTable:
    table = FxTable()
    for base, quote in pairs_needed(currency_pairs):
        key = table.key(base, quote)
        try:
            value, as_of, source = lookup(base, quote)
        except Exception as exc:  # noqa: BLE001 - a missing pair is reported, not fatal
            table.failures[key] = f"{type(exc).__name__}: {exc}"
            log.warning("fx %s failed: %s", key, exc)
            continue
        if not value or value <= 0:
            table.failures[key] = f"non-positive rate {value!r}"
            continue
        table.rates[key] = Rate(key, float(value), as_of, source)
    return table


def describe(table: FxTable) -> str:
    lines = []
    for key in sorted(table.rates):
        rate = table.rates[key]
        stamp = rate.as_of.isoformat() if rate.as_of else "-"
        lines.append(f"  {key:<14}{rate.value:>14.6f}   {rate.source} close {stamp}")
    for key in sorted(table.failures):
        lines.append(f"  {key:<14}{'FAILED':>14}   {table.failures[key]}")
    return "\n".join(lines) if lines else "  (no conversion needed)"


def to_quote_units(value: float | None, value_currency: str | None,
                   quote_code: str | None) -> float | None:
    """A record's per-share VALUE in the unit the PRICE is quoted in.

    The GBX/GBP seam (golden case G17, closed 2026-09-19 on the owner's
    AUTO.L-S): a London record values the share in POUNDS -- its accounts'
    currency -- while the close arrives in PENCE. Where the quote code is a
    minor unit of exactly the record's currency, the value is multiplied by
    that minor unit's divisor; where the codes are the same, it passes
    unchanged. A value in any OTHER currency is returned unchanged too:
    that is E24's cross-currency question, not this seam, and is not
    settled here.
    """
    if value is None or not quote_code:
        return value
    divisor = minor_unit_divisor(quote_code)
    if divisor != 1.0 and value_currency and major_unit(quote_code) == value_currency.upper():
        return value * divisor
    return value

