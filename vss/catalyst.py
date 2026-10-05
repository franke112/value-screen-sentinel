"""Gate 1's catalyst limb: the DATED FACTS a reader needs, and nothing more.

B1 passes Gate 1 only on a decline "attributable to an identifiable,
dateable catalyst (headline + date)". Finding one meant opening a chart and
a news site by hand. This module lays out, for the window from the
reference peak to today, two things that need no model:

1. **the price** -- every session in the window that fell by
   `DOWN_DAY_THRESHOLD` or more, off the settled closes this project
   already holds, plus the move on the day the peak itself was set;
2. **the issuer's own filings** -- every periodic report and 8-K SEC lists
   in the window, with the 8-K item codes decoded (2.02 is results, 5.02 is
   an officer leaving).

IT NEVER NAMES THE CATALYST. The two lists are placed side by side on one
timeline, by date, and nothing here says that a filing CAUSED a fall. Which
event, if any, carries the decline is the owner's reading at the review's
`gate-1` step. A headline search is deliberately absent: a web search
returned last year's article and the wrong daily move on its first use
(HRB, 2026-09-17), and a fact list that can be wrong is worse than a short
one.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, timedelta
from typing import Iterable, Sequence

#: A session that fell this much or more is listed. CROX's hand
#: measurement (2026-09-04) counted sessions at -3%, and so does this.
DOWN_DAY_THRESHOLD = -0.03

#: The forms that carry the issuer's own news. Insider and ownership forms
#: (3, 4, 5, 144, SC 13G) are about holders, not the business.
NEWS_FORMS = ("8-K", "8-K/A", "10-Q", "10-Q/A", "10-K", "10-K/A", "10-KT",
              "6-K", "20-F", "40-F")

#: SEC's Form 8-K item numbers, as the form names them.
ITEMS = {
    "1.01": "Entry into a Material Definitive Agreement",
    "1.02": "Termination of a Material Definitive Agreement",
    "1.05": "Material Cybersecurity Incidents",
    "2.01": "Completion of Acquisition or Disposition of Assets",
    "2.02": "Results of Operations and Financial Condition",
    "2.03": "Creation of a Direct Financial Obligation",
    "2.04": "Triggering Events That Accelerate a Financial Obligation",
    "2.05": "Costs Associated with Exit or Disposal Activities",
    "2.06": "Material Impairments",
    "3.01": "Notice of Delisting or Failure to Satisfy a Listing Rule",
    "4.01": "Changes in Registrant's Certifying Accountant",
    "4.02": "Non-Reliance on Previously Issued Financial Statements",
    "5.02": "Departure or Appointment of Directors or Certain Officers",
    "5.03": "Amendments to Articles of Incorporation or Bylaws",
    "5.07": "Submission of Matters to a Vote of Security Holders",
    "7.01": "Regulation FD Disclosure",
    "8.01": "Other Events",
    "9.01": "Financial Statements and Exhibits",
}


@dataclass(frozen=True)
class Move:
    day: date
    close_before: float
    close: float

    @property
    def change(self) -> float:
        return self.close / self.close_before - 1.0


def moves(closes: Sequence[tuple[date, float]]) -> list[Move]:
    """Each session's move against the session before it, oldest first."""
    ordered = sorted(closes)
    return [Move(day, before, close)
            for (_, before), (day, close) in zip(ordered, ordered[1:])
            if before]


def price_facts(closes: Sequence[tuple[date, float]], peak: date, to: date,
                threshold: float = DOWN_DAY_THRESHOLD) -> dict:
    """The window's down days, the peak day's own move, and the counts."""
    every = moves(closes)
    window = [m for m in every if peak < m.day <= to]
    peak_day = next((m for m in every if m.day == peak), None)
    down = [m for m in window if m.change <= threshold]
    return {
        "threshold": threshold,
        "sessions": len(window),
        "down_days": [_move(m) for m in down],
        "largest": _move(min(window, key=lambda m: m.change)) if window else None,
        "peak_day": _move(peak_day) if peak_day else None,
    }


def _move(m: Move) -> dict:
    return {"date": m.day.isoformat(), "close_before": round(m.close_before, 4),
            "close": round(m.close, 4), "change": round(m.change, 6)}


def decode_items(items: str) -> list[str]:
    """`"2.02,9.01"` -> `["2.02 Results of Operations ...", ...]`; 9.01 dropped.

    9.01 only says exhibits are attached, which every 8-K with a press
    release carries. An unknown code is kept as the bare number rather than
    guessed at.
    """
    out = []
    for code in (c.strip() for c in (items or "").split(",")):
        if not code or code == "9.01":
            continue
        out.append(f"{code} {ITEMS[code]}" if code in ITEMS else code)
    return out


#: Filings this many calendar days BEFORE the peak are listed too. HRB's
#: results 8-K was filed the evening of 2026-08-11 and the peak was set by
#: the +16% session after it; a window opening on the peak day hid it.
#: Four days reaches the session before a peak set on a Monday.
PEAK_LEAD_DAYS = 4


def filings_in_window(filings: Iterable, peak: date, to: date,
                      lead_days: int = PEAK_LEAD_DAYS) -> list[dict]:
    """The issuer's news-bearing filings from shortly before the peak through `to`."""
    start = peak - timedelta(days=lead_days)
    out = []
    for f in filings:
        if f.form not in NEWS_FORMS or not f.filed:
            continue
        filed = date.fromisoformat(f.filed)
        if start <= filed <= to:
            out.append({"date": f.filed, "form": f.form,
                        "items": decode_items(getattr(f, "items", "")),
                        "accession": f.accession, "url": f.url})
    return sorted(out, key=lambda d: (d["date"], d["form"]))


def timeline(price: dict | None, filings: Sequence[dict]) -> list[str]:
    """One list, by date: down days and filings side by side, never linked."""
    rows: list[tuple[str, int, str]] = []
    if price and price.get("peak_day"):
        p = price["peak_day"]
        rows.append((p["date"], 0, f"PEAK SET: close {p['close_before']:.2f} → "
                                   f"{p['close']:.2f} ({p['change']:+.2%})"))
    for m in (price or {}).get("down_days", []):
        rows.append((m["date"], 0, f"DOWN DAY: close {m['close_before']:.2f} → "
                                   f"{m['close']:.2f} ({m['change']:+.2%})"))
    for f in filings:
        what = "; ".join(f["items"]) if f["items"] else ""
        rows.append((f["date"], 1, f"FILED {f['form']}" + (f" — {what}" if what else "")
                     + f" — {f['url']}"))
    return [f"{day} {text}" for day, _, text in sorted(rows)]
