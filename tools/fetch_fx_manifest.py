"""BUILD tool. Fetches the exchange rates OF A NAMED DATE. Never called at runtime.

``vss/fx.py``'s ``default_lookup`` asks yfinance for ``period="5d"`` and takes
the LAST close, whatever ``--asof`` says. For most pairs that is the previous
trading close and it is right. For some it is not:

    SEKUSD=X, fetched on Sunday 2026-08-23, returns
        ... 2026-08-20  0.105924
            2026-08-21  0.105542
            2026-08-23  0.105789     <-- a weekend row
    EURUSD=X, the same minute, stops at 2026-08-21.

So a run dated 2026-08-21 recorded ten pairs at 08-21 and two -- NOK->USD and
SEK->USD -- at 08-22, and the report said only that it carried two rate dates.
Those two currencies are quoted through the weekend by whoever feeds Yahoo;
the euro is not. **Reproducing a defective record reproduces the defect**, so
this tool exists to build a clean one.

WHAT IT DOES DIFFERENTLY. It selects the row whose date IS the requested one.
A pair with no row on that date **FAILS and is named** -- it is never filled
from the nearest neighbouring session, because a rate silently taken from
another day is exactly the fault this tool is here to remove, in a smaller
size and harder to see.

    python tools/fetch_fx_manifest.py --asof 2026-08-21 \\
        --like data/screener_runs/2026-08-21/ranking-manifest-fetched-2026-08-22.json \\
        --out  data/screener_runs/2026-08-21/ranking-manifest-fx-asof-2026-08-21.json

The output is in the ranking manifest's own shape, so
``vss screen --rank --fx-from-manifest <out>`` replays it unchanged. This tool
does not rank anything and does not touch a run's own manifest.
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import date, timedelta
from pathlib import Path

#: How far back to ask, so the requested session is inside the window even
#: across a long weekend or a holiday. Rows outside it are irrelevant: only
#: the row ON the requested date is ever used.
LOOKBACK_DAYS = 10


def pairs_from_manifest(path: Path) -> list[tuple[str, str]]:
    """The pairs a stored run used, in the manifest's own ``BASE->QUOTE`` form."""
    document = json.loads(path.read_text(encoding="utf-8"))
    out = []
    for key in sorted((document.get("fx") or {})):
        base, _, quote = key.partition("->")
        if base and quote:
            out.append((base, quote))
    return out


def default_reader(symbol: str, start: date, end: date):
    """One pair's daily closes as ``[(date, close)]``. Replaced in tests."""
    import pandas as pd
    import yfinance as yf

    frame = yf.Ticker(symbol).history(
        start=start.isoformat(), end=end.isoformat(), interval="1d")
    if frame is None or len(frame) == 0 or "Close" not in frame.columns:
        return []
    return [(pd.Timestamp(stamp).date(), float(value))
            for stamp, value in frame["Close"].dropna().items()]


def fetch_on(base: str, quote: str, as_of: date, reader=None) -> tuple[float, str]:
    """The close dated exactly ``as_of``. Raises if there is none.

    The refusal is the point. Falling back to the nearest session would put a
    rate from another day into a record that says it is this day's -- the same
    fault this tool exists to remove, one size smaller and harder to see.

    ``reader`` defaults to ``default_reader`` at CALL time, not at definition
    time, so a test that replaces the module attribute is actually obeyed
    rather than quietly going to the network.
    """
    reader = reader or default_reader
    symbol = f"{base}{quote}=X"
    start = as_of - timedelta(days=LOOKBACK_DAYS)
    closes = reader(symbol, start, as_of + timedelta(days=1))
    if not closes:
        raise RuntimeError(f"{symbol}: no rows in {start}..{as_of}")
    for stamp, value in closes:
        if stamp == as_of:
            return float(value), symbol
    seen = ", ".join(stamp.isoformat() for stamp, _ in closes)
    raise RuntimeError(
        f"{symbol}: no close dated {as_of.isoformat()}; the window holds {seen}. "
        f"NOT filled from a neighbouring session."
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--asof", required=True, help="the close date every rate must carry")
    parser.add_argument("--like", required=True, type=Path,
                        help="a stored ranking manifest, read ONLY for its pair list")
    parser.add_argument("--out", required=True, type=Path)
    args = parser.parse_args(argv)

    as_of = date.fromisoformat(args.asof)
    pairs = pairs_from_manifest(args.like)
    if not pairs:
        print(f"{args.like}: no fx pairs to fetch", file=sys.stderr)
        return 1

    rates: dict[str, dict] = {}
    failed: dict[str, str] = {}
    for base, quote in pairs:
        key = f"{base}->{quote}"
        try:
            value, symbol = fetch_on(base, quote, as_of)
        except Exception as exc:  # noqa: BLE001 - reported by name, never guessed at
            failed[key] = f"{type(exc).__name__}: {exc}"
            print(f"  {key:<14}FAILED   {exc}")
            continue
        rates[key] = {"rate": value, "as_of": as_of.isoformat(),
                      "source": f"{symbol} close {as_of.isoformat()}"}
        print(f"  {key:<14}{value:>14.6f}   {symbol} close {as_of.isoformat()}")

    document = {
        "asof": as_of.isoformat(),
        "key": "exchange rates only -- built by tools/fetch_fx_manifest.py",
        "fx": dict(sorted(rates.items())),
        "fx_failed": failed,
        "fx_source": (f"fetched by tools/fetch_fx_manifest.py, every rate taken from "
                      f"the close dated {as_of.isoformat()} and from no other session"),
        "fx_rate_dates": sorted({r["as_of"] for r in rates.values()}),
    }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(document, indent=2) + "\n", encoding="utf-8")
    print(f"\n{len(rates)} of {len(pairs)} pairs at {as_of.isoformat()} -> {args.out}")
    if failed:
        print(f"{len(failed)} FAILED and are named in the file; a replay from it "
              f"will withhold the yields that needed them.")
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
