"""Backfill FRAMEWORK-EDITS E114's shadow book from the record, 2026-09-08.

A dated one-off, of the same kind as the other scripts in this directory.
It writes `config/shadow_book.csv` from what the record already says:
every DROPPED, WATCH-GATED and INTAKE name in `config/watchlist.yaml` and
`config/screener_exclusions.csv`.

THE VERDICT DATES AND THE ONE-LINE REASONS ARE TRANSCRIBED BY HAND, and
the `source` column on every row says from WHERE -- the watchlist note
where the note carries a dated verdict, the exclusion CSV's `datum` where
it does not, and the reference document where that is the only record.
Nothing here infers a date.

THE CLOSE IS AN EXACT MATCH OR IT IS DATA MISSING. E114 forbids the
nearest bar, so a verdict written before its own session has settled gets
a blank close and keeps it until that session settles. Re-running this
script fills such a blank and changes nothing else.

AMENDED 2026-09-09 (E114 limit four). The dates below are the dates the
verdicts were WRITTEN. A verdict written on a SATURDAY or a SUNDAY is
re-dated to the last weekday on or before it, and the `source` column
says which date the row moved from and to. The prohibition on the nearest
bar is untouched: the DATE moves and the price is then an exact match on
it, which is a different act from reading Friday's close as Saturday's.

THE WALK-BACK CROSSES WEEKENDS AND NOTHING ELSE. A weekday with no bar
stays where it is and is DATA MISSING: this script cannot tell an
exchange holiday from a vendor that has lost a day, and the first cut,
which walked back until it found a price, moved MEKKO.HE from Tuesday
2026-09-08 to Friday 2026-09-04 for a vendor gap on a market that was
open. A verdict written on a session that has not settled yet is not
moved either -- it waits.
"""

from __future__ import annotations

import argparse
import csv
import logging
import sys
from datetime import date, datetime, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from vss import metrics as M                                   # noqa: E402
from vss.fetch import get_history                              # noqa: E402
from vss.runner import CACHE_DIR                               # noqa: E402
from vss.sales import settled_closes                           # noqa: E402
from vss.shadowbook import (COLUMNS, SHADOW_BOOK_PATH,         # noqa: E402
                            load_shadow_book)

WL = "config/watchlist.yaml note"
CSV = "config/screener_exclusions.csv datum"

#: ticker, THE DATE THE VERDICT WAS WRITTEN, verdict, standing, currency,
#: fv, one line, source. The date recorded in the book is resolved from
#: this one by `settled_session_on_or_before` -- see E114 limit four.
#: fv is the entry's `fv_base` where the entry carries one; where it is a
#: figure that lives only in the prose of a verdict note, the source
#: column says so and says that it carries NO run record.
RECORD: tuple[tuple[str, str, str, str, str, float | None, str, str], ...] = (
    ("MSFT", "2026-08-22", "DROPPED", "STANDING", "USD", 323.0,
     "Exited 2026-08-21 under C4; the exclusion row was written 2026-08-22. "
     "EXIT -- B45 measures this position from its FILL.",
     f"{CSV}; the watchlist note carries no DROPPED date. fv_base from the "
     f"watchlist entry."),
    ("HNSA.ST", "2026-08-22", "DROPPED", "STANDING", "SEK", None,
     "Sold 2026-08-22 in full; never analysed, outside framework scope. "
     "EXIT -- B45 territory, and never a refusal.",
     f"{CSV}; the watchlist note gives the same date."),
    ("LULU", "2026-08-23", "DROPPED", "STANDING", "USD", None,
     "Gate 3's gross-margin limb: four of eight quarters outside B4's band "
     "with no Class C event, margin down five quarters running, and Method "
     "A resting on a multiple from a growth rate the company has abandoned.",
     f"{WL} (DROPPED 2026-08-23); {CSV} agrees."),
    ("JD.L", "2026-08-24", "DROPPED", "STANDING", "GBX", None,
     "Section 1.2 hard stop: the newest income statement is seven months "
     "old and the publication that moved the price contains none, so the "
     "company cannot be valued on fresh earnings data.",
     f"{WL} (DROPPED 2026-08-24); {CSV} agrees."),
    ("DECK", "2026-08-24", "WATCH-GATED", "EXPIRY", "USD", None,
     "Gate 1's level limb passes and its catalyst limb does not: the one "
     "dated catalyst (-15.21% on 2025-10-24) was fully recovered by "
     "2026-01-30 and what remains is unattributable drift. Re-entry is on "
     "an event, never on a price level.",
     f"{WL} (WATCH 2026-08-24); {CSV} agrees."),
    ("NKE", "2026-08-25", "DROPPED", "STANDING", "USD", 22.15,
     "Method C on fiscal 2026 gives 22.15 at the pre-registered 3% base "
     "against a close of 39.41, and the 5% bull case 25.73 is still below "
     "the price, so C4 is met on the optimistic view.",
     f"{WL} (DROPPED confirmed 2026-08-25); the fair value is from the same "
     f"note and carries NO run record -- it is not the entry's fv_base."),
    ("BETS-B.ST", "2026-08-25", "DROPPED", "STANDING", "SEK", None,
     "Gate 3's gross-margin band fails, 65.3% to 57.2% over eight quarters "
     "against a 200bp limit; the B2B licence loss has no floor the owner "
     "can judge better than the market.",
     f"{WL} (DROPPED 2026-08-25); {CSV} agrees."),
    ("SYNSAM.ST", "2026-08-25", "DROPPED", "STANDING", "SEK", 36.29,
     "Fair value 36.29 on FCF basis two at the pre-registered 2.5% growth "
     "against a close of 59.50, and the 5% bull 48.22 is still below it; "
     "C4 met, and the owner does not believe the ten-year story.",
     f"{WL} (DROPPED 2026-08-25); the fair value is from the same note and "
     f"carries NO run record -- it is not the entry's fv_base."),
    ("PNDORA.CO", "2026-08-25", "WATCH-GATED", "EXPIRY", "DKK", None,
     "Gate 1's catalyst leg fails: the 2026-01-09 decline is fully "
     "recovered and B1 reads -1.5568, a window holding a recovery rather "
     "than a fall. Re-entry is on a named information event.",
     f"{WL} (WATCH 2026-08-25); {CSV} agrees."),
    ("ADBE", "2026-08-25", "DROPPED", "STANDING", "USD", None,
     "Dropped on the owner's own judgement, before any section 5 run and "
     "expressly NOT VERIFIED: the moat is lock-in rather than product, and "
     "AI is the alternative that did not exist before.",
     f"{CSV} -- ADBE has no watchlist entry; reasoning in "
     f"reference/growth-views/ADBE.md."),
    ("NOVO-B.CO", "2026-08-27", "DROPPED", "STANDING", "DKK", None,
     "E51: pharmaceuticals and biotech are outside the circle of "
     "competence, because the pre-registered growth rate E28 requires "
     "would be a guess about drug approvals.",
     f"{WL} (DROPPED 2026-08-27 under E51); no exclusion row."),
    ("NREST.ST", "2026-08-27", "DROPPED", "EXPIRY", "SEK", None,
     "E52: the price history reaches only to 2024-05-24, short of the "
     "five-year floor. Rejected at filter 1 on MISSING data -- it did not "
     "fail a limb, the limbs could not be evaluated.",
     f"{WL} (DROPPED 2026-08-27 under E52); no exclusion row."),
    ("UNA.AS", "2026-08-30", "DROPPED", "STANDING", "EUR", 43.5,
     "Sold in full 2026-08-24 at 54.81 EUR under C4's second application; "
     "the status became DROPPED on the 2026-08-30 booking. EXIT -- B45 "
     "measures this position from its FILL.",
     f"{WL} (status DROPPED from the 2026-08-30 booking); the exclusion CSV "
     f"carries the London line ULVR.L, not this one. fv_base from the entry."),
    ("ACN", "2026-09-04", "INTAKE", "OPEN", "USD", None,
     "E111 INTAKE: read, not watched. Store COMPLETE, struck 2026-08-30. "
     "Nothing has been decided.",
     f"{WL} (E111 INTAKE, 2026-09-04)."),
    ("AOS", "2026-09-04", "INTAKE", "OPEN", "USD", None,
     "E111 INTAKE: read, not watched. Store REFUSED on SIZE -- E70's "
     "operating-lease leg is DATA MISSING and bounded at 23,200,000, which "
     "moves fv_base 4.27% against E106's 3.5%.",
     f"{WL} (E111 INTAKE, 2026-09-04)."),
    ("LII", "2026-09-04", "INTAKE", "OPEN", "USD", None,
     "E111 INTAKE: read, not watched. Store COMPLETE, struck 2026-08-30 "
     "under E70. Nothing has been decided.",
     f"{WL} (E111 INTAKE, 2026-09-04)."),
    ("LOPE", "2026-09-04", "INTAKE", "OPEN", "USD", None,
     "E111 INTAKE: read, not watched. Store COMPLETE, and NO GROWTH VIEW "
     "IS REGISTERED, so nothing has been struck.",
     f"{WL} (E111 INTAKE, 2026-09-04)."),
    ("MUSA", "2026-09-04", "INTAKE", "OPEN", "USD", None,
     "E111 INTAKE: read, not watched. Store COMPLETE, and NO GROWTH VIEW "
     "IS REGISTERED, so nothing has been struck.",
     f"{WL} (E111 INTAKE, 2026-09-04)."),
    ("RKT.L", "2026-09-04", "INTAKE", "OPEN", "GBX", None,
     "E111 INTAKE: read, not watched. Store COMPLETE, struck 2026-08-30, "
     "E105's leg read back by the owner 2026-09-04.",
     f"{WL} (E111 INTAKE, 2026-09-04)."),
    ("ULTA", "2026-09-04", "INTAKE", "OPEN", "USD", None,
     "E111 INTAKE: read, not watched. Store COMPLETE, struck 2026-08-30. "
     "Nothing has been decided.",
     f"{WL} (E111 INTAKE, 2026-09-04)."),
    ("CROX", "2026-09-08", "DROPPED", "STANDING", "USD", None,
     "Gate 2 classification D, which is a hard kill: HEYDUDE revenue "
     "-24.7% over two years and guided down again is structural "
     "deterioration, and a brand the company bought and cannot fix is not "
     "a disconnect between price and value.",
     f"{WL} (DROPPED, 2026-09-08); no exclusion row."),
    ("MEKKO.HE", "2026-09-08", "WATCH-GATED", "EXPIRY", "EUR", None,
     "Gate 2 class D on the section 4.2 hard kill: comparable Finnish "
     "store sales fell four quarters running and revenue fell on 7% MORE "
     "stores, which is the opposite of what the expansion argument "
     "predicts. Otherwise sound -- gated, not dropped.",
     f"{WL} (WATCH-GATED, 2026-09-08); full record in "
     f"reference/MEKKO.HE-GATED-2026-09-08.md; no exclusion row."),
    ("CRUS", "2026-09-08", "DROPPED", "STANDING", "USD", None,
     "Dropped on the owner's judgement about his own information set, "
     "before any section 5 run: Apple is ~91% of net sales by the filer's "
     "own statement and that decision is unobservable from outside. The "
     "same ground as BETS-B.ST.",
     f"{CSV} -- CRUS has no watchlist entry; record in "
     f"reference/CRUS-DROP-2026-09-08.md."),
)


def off_the_weekend(day: date) -> date:
    """E114 limit four: back over Saturday and Sunday, and no further.

    A weekday is returned unchanged even when the vendor has no bar for
    it -- that case is DATA MISSING, not a re-dating, because a holiday
    and a vendor outage look identical from here.
    """
    while day.weekday() >= 5:
        day -= timedelta(days=1)
    return day


def main() -> int:
    logging.basicConfig(level=logging.WARNING,
                        format="%(levelname)s %(name)s: %(message)s")
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--out", default=str(SHADOW_BOOK_PATH))
    ap.add_argument("--cache", default=str(CACHE_DIR))
    ap.add_argument("--offline", action="store_true",
                    help="read the price cache only")
    ap.add_argument("--dry-run", action="store_true")
    a = ap.parse_args()

    now = datetime.now().astimezone()
    settled = M.settled_through(now)
    cache = Path(a.cache)
    print(f"settled through {settled.isoformat()}; {len(RECORD)} verdicts")

    rows: list[dict[str, str]] = []
    unpriced: list[tuple[str, str, str]] = []
    moved: list[tuple[str, str, str]] = []
    for ticker, when, verdict, standing, currency, fv, line, source in RECORD:
        written = date.fromisoformat(when)
        fetched = get_history(ticker, cache, now=now,
                              allow_network=not a.offline,
                              write=not a.dry_run)
        day = off_the_weekend(written)
        close = None
        why = "no data for the ticker at all"
        if fetched.frame is not None:
            closes = settled_closes(fetched.frame, settled)
            hit = closes[closes.index == day] if len(closes) else closes
            if len(hit):
                close = float(hit.iloc[0])
            elif day > settled:
                why = f"{day.isoformat()} is not yet settled"
            else:
                why = (f"{day.strftime('%A')} {day.isoformat()} is a weekday "
                       f"and the vendor serves no settled bar for {ticker} "
                       f"on it -- a holiday and a vendor gap look the same "
                       f"from here, so the date is NOT walked back further")
        if close is not None and day != written:
            source += (f" VERDICT RE-DATED from {when} "
                       f"({written.strftime('%A')}) to {day.isoformat()} "
                       f"({day.strftime('%A')}), the last weekday on or "
                       f"before the day the decision was written -- E114 "
                       f"limit four.")
            moved.append((ticker, when, day.isoformat()))
        elif close is None:
            day = written          # an unpriced row keeps the date as written
        if close is None:
            unpriced.append((ticker, when, why))
        rows.append({
            "ticker": ticker, "verdict_date": day.isoformat(),
            "verdict": verdict, "standing": standing,
            "close": "" if close is None else f"{close:.4f}".rstrip("0").rstrip("."),
            "currency": currency,
            "fv_base": "" if fv is None else f"{fv:g}",
            "decided_by": line, "source": source,
        })
        note = "" if day == written else f"  <- written {when}"
        print(f"  {ticker:11} {day.isoformat()} {verdict:12} {standing:9} "
              f"{'DATA MISSING' if close is None else f'{close:>10.2f} {currency}'}"
              f"{note}")

    rows.sort(key=lambda r: (r["verdict_date"], r["ticker"]))
    out = Path(a.out)
    if a.dry_run:
        print("\nDRY RUN -- nothing written.")
    else:
        with out.open("w", encoding="utf-8", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=list(COLUMNS),
                                    lineterminator="\n")
            writer.writeheader()
            writer.writerows(rows)
        print(f"\nwrote {out} ({len(rows)} rows)")
        book = load_shadow_book(out)
        print(f"read back {len(book)} rows; earliest "
              f"{min(v.verdict_date for v in book).isoformat()}")

    if moved:
        print(f"\n{len(moved)} verdict(s) RE-DATED to the session the "
              f"decision was struck against (E114 limit four):")
        for ticker, was, now_ in moved:
            print(f"  {ticker:11} {was} -> {now_}")

    if unpriced:
        print(f"\n{len(unpriced)} verdict(s) with NO baseline close "
              f"(E114: never the nearest bar):")
        for ticker, when, why in unpriced:
            print(f"  {ticker:11} {when}  {why}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
