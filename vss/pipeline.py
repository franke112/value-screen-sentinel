"""Phase 6: entering ranked names in the watchlist as PIPELINE.

This is the only module in the screener that writes to the file holding the
owner's live positions, so the rules are narrow and enforced here rather than
trusted to the caller.

    * PIPELINE only. No mbp, no fv_base, no tier, no stop_price. The whole
      FRAMEWORK section 5 chain -- fair value, margin of safety, maximum buy
      price -- is run by hand afterwards, and a screener that pre-filled any
      of it would be handing the owner a number nobody computed.
    * A ticker already in the file is NEVER touched. Not updated, not
      reordered, not re-noted. It is reported as already present and skipped.
    * The file is BACKED UP before a byte is written, and re-parsed after. If
      it no longer loads, the backup is restored and the run fails loudly.
    * Entries are APPENDED as text. The watchlist is hand-maintained and full
      of comments; rewriting it through a YAML dumper would silently discard
      them, which is a worse loss than any entry is a gain.

The one-line summary is assembled from figures the run already has -- sector,
drawdown, the two ranking components. It contains no assessment. "Rank 3 of
329, drawdown 27.4%, operating profitability 8.6%" is a record of what the
screener measured; "attractive entry point" would be the tool doing the
owner's job badly.
"""

from __future__ import annotations

import logging
import re
import shutil
from dataclasses import dataclass, field
from datetime import date, datetime
from pathlib import Path
from typing import Mapping, Sequence

from .fx import upper_safe_code

log = logging.getLogger(__name__)

WATCHLIST_PATH = Path("config/watchlist.yaml")
PIPELINE_STATUS = "PIPELINE"

#: Keys this module is allowed to write. Anything outside it is a value the
#: screener has no business supplying. `dd_at_entry` and `peak_date` are
#: FRAMEWORK-EDITS E12's frozen Gate 1 reading -- MEASURED figures the run
#: already reported, written as the pair the schema validates them as.
WRITABLE_KEYS = ("ticker", "name", "currency", "status", "dd_at_entry",
                 "peak_date", "notes")

#: Keys that must never appear on a row written here, whatever the caller asks.
FORBIDDEN_KEYS = ("mbp", "fv_base", "tier", "stop_price")


class PipelineError(Exception):
    """The watchlist could not be written safely. Always fatal."""


@dataclass(frozen=True)
class Entry:
    ticker: str
    name: str
    currency: str
    notes: str
    #: E12: Gate 1 is evaluated ONCE, at entry, and frozen. The drawdown as
    #: a FRACTION and the date of the 52-week closing high it was struck
    #: against. Written together or not at all: `config.py` refuses one
    #: without the other, and a frozen drawdown whose peak is not named
    #: cannot be told from one whose peak has aged out (E11).
    dd_at_entry: float | None = None
    peak_date: date | None = None

    def to_yaml(self) -> str:
        lines = [
            f"  - ticker: {self.ticker}",
            f"    name: {_scalar(self.name)}",
            f"    currency: {self.currency}",
            f"    status: {PIPELINE_STATUS}",
        ]
        if self.dd_at_entry is not None and self.peak_date is not None:
            lines.append(f"    dd_at_entry: {self.dd_at_entry:.4f}")
            lines.append(f"    peak_date: {self.peak_date.isoformat()}")
        lines.append("    notes: >-")
        for line in _wrap(self.notes, 68):
            lines.append(f"      {line}")
        return "\n".join(lines) + "\n"


@dataclass
class WriteResult:
    written: list[Entry] = field(default_factory=list)
    skipped: list[tuple[str, str]] = field(default_factory=list)
    backup: Path | None = None
    path: Path | None = None
    dry_run: bool = False


def _scalar(value: str) -> str:
    """Quote a YAML scalar only when it needs it."""
    if value == "" or re.search(r"[:#\[\]{}&*!|>'\"%@`,]", value) or value != value.strip():
        return '"' + value.replace("\\", "\\\\").replace('"', '\\"') + '"'
    return value


def _wrap(text: str, width: int) -> list[str]:
    words, lines, current = text.split(), [], ""
    for word in words:
        if current and len(current) + 1 + len(word) > width:
            lines.append(current)
            current = word
        else:
            current = f"{current} {word}".strip()
    if current:
        lines.append(current)
    return lines or [""]


def summary(
    *,
    ticker: str,
    rank: int,
    of: int,
    asof: date,
    sector: str | None,
    marknad: str | None,
    drawdown: float | None,
    operating_profitability: float | None,
    earnings_yield: float | None,
    quote_currency: str | None,
    peak_date: date | None = None,
) -> str:
    """One line, entirely measured. No assessment, ever.

    Every figure here was computed by a step that has already reported it;
    nothing is inferred, and no word in it says whether the name is good.
    """
    if drawdown is None:
        gate = "Drawdown DATA MISSING from the 52-week closing high."
    elif peak_date is None:
        gate = (f"Drawdown {drawdown:.1%} from the 52-week closing high, whose date "
                f"was not recorded, so Gate 1 is NOT frozen on this entry (E12 "
                f"needs the pair).")
    else:
        gate = (f"Drawdown {drawdown:.1%} from the 52-week closing high set "
                f"{peak_date.isoformat()}. Gate 1 is FROZEN at this reading per "
                f"FRAMEWORK-EDITS E12 and is not re-read; leaving PIPELINE takes "
                f"an information event.")
    parts = [
        f"Screener {asof.isoformat()}: rank {rank} of {of} names ranked on BOTH "
        f"components of the two-component key (FRAMEWORK-EDITS E6); "
        f"{of} is that list, not the universe.",
        f"Sector {sector or 'DATA MISSING'}.",
        f"Market {marknad or 'DATA MISSING'}.",
        gate,
        f"Operating profitability (EBIT / total assets, FRAMEWORK-EDITS E43) "
        f"{'DATA MISSING' if operating_profitability is None else f'{operating_profitability:.1%}'}.",
        f"Earnings yield "
        f"{'DATA MISSING' if earnings_yield is None else f'{earnings_yield:.1%}'}.",
    ]
    from .fx import major_unit, upper_safe_code

    if quote_currency and upper_safe_code(quote_currency) != major_unit(quote_currency):
        # Pence, not pounds. The currency FIELD carries GBX so the report
        # cannot print a pence figure labelled GBP, and the note says it in
        # words as well: any fv_base or stop entered by hand must use the
        # same unit as the quoted price.
        parts.append(
            f"Quoted in {quote_currency} -- the price series is in the MINOR unit, "
            f"and the currency field says {upper_safe_code(quote_currency)} for that "
            f"reason. Any fv_base or stop_price entered by hand must be in "
            f"{upper_safe_code(quote_currency)}, not "
            f"{major_unit(quote_currency)}."
        )
    parts.append(
        # NO COLON AFTER A FORBIDDEN WORD. The note is emitted as a FOLDED
        # block scalar, so where the text wraps is a function of how long the
        # figures happen to be. On 2026-08-22 a longer quality-leg sentence
        # moved the fold until a line began "mbp: section 5 has not been run"
        # -- content, not a key, and YAML parses it correctly, but the guard
        # below scans the RENDERED TEXT and refused the write. The guard was
        # right to: a check that reasoned about intent instead of text would
        # be worth nothing. So the note keeps clear of the shape instead.
        "No fv_base, no tier and no mbp -- section 5 has not been run. "
        "This entry is review work, not a buy."
    )
    return " ".join(parts)


def validate_watchlist(path: Path) -> None:
    """Re-parse the file with the real loader.

    Lives here, not in the caller: this module is the only one permitted to
    know the watchlist exists, and the check that a write left the file
    loadable belongs beside the write that could break it.
    """
    from .config import load_watchlist

    load_watchlist(path)


def existing_tickers(text: str) -> set[str]:
    """Tickers already in the file, read without reformatting it."""
    return {
        match.group(1).strip()
        for match in re.finditer(r"^\s*-\s*ticker:\s*(\S+)", text, re.MULTILINE)
    }


def backup_path(path: Path, now: datetime) -> Path:
    return path.with_name(
        f"{path.name}.bak-{now.date().isoformat()}-pre-pipeline"
    )


def write(
    entries: Sequence[Entry],
    *,
    path: Path = WATCHLIST_PATH,
    now: datetime,
    dry_run: bool = False,
    validate=None,
) -> WriteResult:
    """Append PIPELINE entries. Backup first, re-parse after, restore on failure."""
    if not path.exists():
        raise PipelineError(f"{path}: no watchlist to write to")
    original = path.read_text(encoding="utf-8")
    present = existing_tickers(original)

    result = WriteResult(path=path, dry_run=dry_run)
    to_write: list[Entry] = []
    for entry in entries:
        if entry.ticker in present:
            result.skipped.append((entry.ticker, "already in the watchlist"))
            continue
        for forbidden in FORBIDDEN_KEYS:
            if re.search(rf"^\s*{forbidden}\s*:", entry.to_yaml(), re.MULTILINE):
                raise PipelineError(
                    f"{entry.ticker}: refusing to write {forbidden} -- "
                    "the screener does not compute it"
                )
        to_write.append(entry)
        present.add(entry.ticker)

    result.written = to_write
    if dry_run or not to_write:
        return result

    backup = backup_path(path, now)
    shutil.copy2(path, backup)
    result.backup = backup

    block = "".join(entry.to_yaml() for entry in to_write)
    header = (
        f"\n  # --- added by `vss screen --write-pipeline` on "
        f"{now.date().isoformat()} ---\n"
        f"  # PIPELINE only: no mbp, no fv_base, no tier. Section 5 is run by hand.\n"
    )
    body = original if original.endswith("\n") else original + "\n"
    path.write_text(body + header + block, encoding="utf-8")

    if validate is not None:
        try:
            validate(path)
        except Exception as exc:
            shutil.copy2(backup, path)
            raise PipelineError(
                f"{path}: no longer loads after the write ({exc}); "
                f"restored from {backup.name}"
            ) from exc
    return result


def entries_from_ranking(
    ranked: Sequence,
    *,
    asof: date,
    top: int,
    names: Mapping[str, str],
    markets: Mapping[str, str],
    drawdowns: Mapping[str, float],
    total: int,
    peak_dates: Mapping[str, date] | None = None,
) -> list[Entry]:
    """The top ``top`` of the BOTH-legs list, as watchlist entries.

    Only that list. The earnings-yield-only section is not written: its names
    are ranked on one leg, and for the sector-exempt majority enterprise value
    is not a meaningful construct either, so they are in practice not ranked.

    ``peak_dates`` is the date of each name's 52-week closing high (E12).
    An entry gets `dd_at_entry` and `peak_date` written ONLY when both are
    known; otherwise neither, and the note says why.
    """
    peak_dates = peak_dates or {}
    out = []
    for position, item in enumerate(ranked[:top], start=1):
        scored = item.scored
        inputs = scored.inputs
        ticker = scored.ticker
        drawdown = drawdowns.get(ticker)
        peak = peak_dates.get(ticker)
        frozen = drawdown is not None and peak is not None
        out.append(
            Entry(
                ticker=ticker,
                name=names.get(ticker) or ticker,
                currency=upper_safe_code(inputs.quote_currency) or "DATA MISSING",
                notes=summary(
                    ticker=ticker, rank=position, of=total, asof=asof,
                    sector=inputs.sector, marknad=markets.get(ticker),
                    drawdown=drawdown,
                    operating_profitability=scored.operating_profitability,
                    earnings_yield=scored.earnings_yield,
                    quote_currency=inputs.quote_currency,
                    peak_date=peak,
                ),
                dd_at_entry=drawdown if frozen else None,
                peak_date=peak if frozen else None,
            )
        )
    return out
