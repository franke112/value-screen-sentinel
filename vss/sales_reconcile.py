"""E165: the watchlist's `sales:` blocks are reconciled against an account
export before `vss sales` is read (a DATA rule under E164).

`vss sales --reconcile EXPORT.csv` matches every sell row of an Avanza
transaction export (date, shares, price, proceeds, account) against the
booked fills, writes the result to config/sales_reconciled.yaml, and exits
1 when anything differs. `vss sales` prints the date of the latest
reconciliation and warns about fills it did not cover.

Matching is on the fill, not the name: the export's description ("Central
Garden & Pet A") is not a ticker, while date + shares + price identify a
fill. The core funds (FRAMEWORK §7) are sold in the export but booked in
§7 and E157's base note, never in `sales:`; they are listed apart.
"""
from __future__ import annotations

import csv
from dataclasses import dataclass, field
from datetime import date
from pathlib import Path
from typing import Sequence

import yaml

from .config import SaleRecord
from .runner import PROJECT_ROOT

STAMP_PATH = PROJECT_ROOT / "config" / "sales_reconciled.yaml"
#: FRAMEWORK §7's core: sold in the export, never a `sales:` fill.
CORE_FUNDS: tuple[str, ...] = ("Avanza Zero", "Avanza USA")
SELL = "Sälj"
PRICE_TOLERANCE = 1e-6
SEK_TOLERANCE = 0.005


@dataclass(frozen=True)
class ExportFill:
    day: date
    account: str
    description: str
    shares: float
    price: float
    proceeds_sek: float

    def line(self) -> str:
        return (f"{self.day} {self.description} {self.shares:g} at {self.price:g}, "
                f"{self.proceeds_sek:,.2f} SEK, account {self.account}")


@dataclass
class Reconciliation:
    export: str
    export_from: date | None
    export_through: date | None
    since: date
    matched: int = 0
    differing: list[str] = field(default_factory=list)
    not_booked: list[str] = field(default_factory=list)
    not_on_export: list[str] = field(default_factory=list)
    core_funds: list[str] = field(default_factory=list)

    @property
    def clean(self) -> bool:
        return not (self.differing or self.not_booked or self.not_on_export)


def _num(text: str) -> float | None:
    text = (text or "").strip().replace(" ", "").replace(",", ".")
    return float(text) if text else None


def read_export(path: Path) -> tuple[list[ExportFill], date | None, date | None]:
    """Every sell row of an Avanza export, and the export's first and last date."""
    fills: list[ExportFill] = []
    days: list[date] = []
    with path.open(encoding="utf-8-sig", newline="") as handle:
        for row in csv.DictReader(handle, delimiter=";"):
            try:
                day = date.fromisoformat(row["Datum"].strip())
            except (KeyError, ValueError):
                continue
            days.append(day)
            if row.get("Typ av transaktion", "").strip() != SELL:
                continue
            shares, price, amount = (_num(row.get("Antal", "")), _num(row.get("Kurs", "")),
                                     _num(row.get("Belopp", "")))
            if shares is None or price is None or amount is None:
                continue
            fills.append(ExportFill(day, row.get("Konto", "").strip(),
                                    row.get("Värdepapper/beskrivning", "").strip(),
                                    abs(shares), price, amount))
    return fills, (min(days) if days else None), (max(days) if days else None)


def reconcile(booked: Sequence[tuple[str, SaleRecord]], export: Sequence[ExportFill], *,
              export_name: str, export_from: date | None, export_through: date | None,
              since: date) -> Reconciliation:
    """Match the export's sells from `since` to the booked fills, one to one."""
    out = Reconciliation(export_name, export_from, export_through, since)
    # A counterfactual fill never happened: it is not on any export.
    booked = [(t, s) for t, s in booked if not getattr(s, "counterfactual", False)]
    used: set[int] = set()
    for fill in sorted(export, key=lambda f: (f.day, f.description, f.shares)):
        if fill.day < since:
            continue
        if fill.description in CORE_FUNDS:
            out.core_funds.append(fill.line())
            continue
        hit = next((i for i, (_, s) in enumerate(booked)
                    if i not in used and s.date == fill.day and s.shares == fill.shares
                    and s.price is not None and abs(s.price - fill.price) < PRICE_TOLERANCE),
                   None)
        if hit is None:
            out.not_booked.append(fill.line())
            continue
        used.add(hit)
        ticker, sale = booked[hit]
        problems = []
        if sale.proceeds_sek is None or abs(sale.proceeds_sek - fill.proceeds_sek) > SEK_TOLERANCE:
            problems.append(f"proceeds {sale.proceeds_sek} against {fill.proceeds_sek:.2f}")
        if (sale.account or "") != fill.account:
            problems.append(f"account {sale.account or '(blank)'} against {fill.account}")
        if problems:
            out.differing.append(f"{ticker} {fill.line()}: " + "; ".join(problems))
        else:
            out.matched += 1
    for i, (ticker, sale) in enumerate(booked):
        if i in used or sale.date < since:
            continue
        if export_through is not None and sale.date > export_through:
            continue        # after the export: not covered, reported by `vss sales`
        out.not_on_export.append(f"{ticker} {sale.date} {sale.shares:g} at {sale.price}")
    return out


def write_stamp(result: Reconciliation, *, on: date, path: Path = STAMP_PATH) -> None:
    doc = {
        "ruling": "E165",
        "reconciled_on": on.isoformat(),
        "export": result.export,
        "export_from": result.export_from.isoformat() if result.export_from else None,
        "export_through": result.export_through.isoformat() if result.export_through else None,
        "since": result.since.isoformat(),
        "status": "CLEAN" if result.clean else "DIFF",
        "matched": result.matched,
        "differing": result.differing,
        "not_booked": result.not_booked,
        "not_on_export": result.not_on_export,
        "core_funds_not_in_sales": result.core_funds,
    }
    path.write_text("# Written by `vss sales --reconcile` (E165). Do not edit by hand.\n"
                    + yaml.safe_dump(doc, sort_keys=False, allow_unicode=True), encoding="utf-8")


def load_stamp(path: Path = STAMP_PATH) -> dict | None:
    if not path.exists():
        return None
    return yaml.safe_load(path.read_text(encoding="utf-8")) or None


def stamp_lines(stamp: dict | None, sales: Sequence[SaleRecord]) -> list[str]:
    """What `vss sales` prints at the top: the latest reconciliation, and
    every fill it does not cover."""
    if not stamp:
        return ["**SALES NOT RECONCILED (E165):** no `vss sales --reconcile` has been "
                "run against an account export; the fills below are as booked."]
    through = date.fromisoformat(stamp["export_through"]) if stamp.get("export_through") else None
    lines = [f"**Last reconciled (E165):** {stamp['reconciled_on']} against "
             f"`{stamp['export']}` (rows {stamp.get('export_from')} to {through}), "
             f"status **{stamp['status']}**, {stamp.get('matched', 0)} fills matched."]
    after = [s for s in sales if through is not None and s.date > through
             and not getattr(s, "counterfactual", False)]
    if after:
        lines.append(f"**NOT COVERED:** {len(after)} fill(s) dated after the export's last "
                     f"day {through} -- reconcile against a newer export.")
    if stamp.get("status") != "CLEAN":
        lines.append("**The last reconciliation found differences** -- see "
                     "config/sales_reconciled.yaml.")
    return lines
