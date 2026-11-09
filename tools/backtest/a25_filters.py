"""ATTEMPTS #25 (pre-registered 2026-11-09, before any run): every mechanical
filter still in the method and never tested, as IN against OUT, in one run.

    DEVOUR_LB=clean .venv/bin/python -m tools.backtest.a25_filters > reports/attempts/A25-RESULT.md

Reads the cleaned rows (nordic-m7, US *-clean) and the signals of
data/backtest/devour-fundsig-r2/ (a3_kills.attach). The population is the
VALUED names of each date (measure.usable: status ok, a price, a return at
the horizon). Per date, the mean 3-year excess return of the names the
filter lets through minus the mean of the names it stops; a date counts
only with >= 3 names on each side.

THE DECISION RULE (registered with this script, before it ran): a filter
HOLDS if its spread (through minus stopped) at 3 years is

  (a) > 0 in BOTH markets AND in BOTH halves of each market, and
  (b) above the 95th percentile of 1,000 within-date permutations of the
      same labels, in each market (the pooled mean over dates).

A filter that holds STAYS. One that does not is REMOVED from the code and
the documents (E164: a decision rule leaves on a registered test). A filter
whose legs the rows do not carry is NOT TESTABLE and stays as a hand part;
it is listed, not decided. 1 and 5 years are printed beside, never decide.
"""
from __future__ import annotations

import random
import statistics
from datetime import timedelta

from . import a3_kills as A3
from . import devour as D
from . import eodhd_reprice as EP
from . import measure as MS

H = 3
MIN_SIDE = 3


def s(r, k):
    return (r.get("_s") or {}).get(k)


def ebitda(r):
    e, da = s(r, "ebit"), s(r, "da")
    return None if e is None or da is None else e + da


def nd_ebitda(r):
    nd, eb = r.get("net_debt"), ebitda(r)
    if nd is None or eb is None:
        return None
    if eb <= 0:
        return float("inf") if nd > 0 else None
    return nd / eb


def _yr_ago(r):
    """E127's leg: the close a year before the entry, from the price file."""
    if "_e127" in r:
        return r["_e127"]
    out = None
    sym = D.symbol(r) or (f"{r['ticker']}.US" if r.get("ticker") else None)
    if sym:
        f = EP.frame(sym)
        if f is not None:
            day = D.start_day(r)
            a, b = EP.on(f, day - timedelta(days=365), "adjusted_close"), EP.on(f, day, "adjusted_close")
            if a and b and a[1] > 0:
                out = b[1] < a[1]
    r["_e127"] = out
    return out


def q(r, k):
    v = (r.get("quality") or {}).get(k)
    return v if isinstance(v, bool) else None


def kill43(r):
    st = (s(r, "kills") or {}).get("4.3.soft")
    return None if st not in ("TRIP", "NO_TRIP") else st == "NO_TRIP"


def fcf_pos(r):
    v = r.get("fcf_mean")
    return None if v is None else v > 0


def lev(limit):
    def f(r):
        x = nd_ebitda(r)
        return None if x is None else x <= limit
    return f


def mbp(r):
    x = MS.fv_ratio(r)
    return None if x is None else x >= 1 / 0.85


def ocf_conv(r):
    o, n = s(r, "ocf"), s(r, "ni")
    return None if o is None or n is None or n <= 0 else o / n >= 1.0


def margin_up(r):
    m = s(r, "margin_chg_bps")
    return None if m is None else m > 0


#: (name, where it is in the method, through(r) -> True / False / None)
FILTERS = (
    ("E127: close below a year ago", "filter 1 (vss/screen.py)", _yr_ago),
    ("Filter 2 FCF limb: FCF > 0 (3-y mean)", "filter 2 (vss/filters.py)", fcf_pos),
    ("Filter 2 leverage limb: net debt / EBITDA <= 2.5", "filter 2 (vss/filters.py)", lev(2.5)),
    ("4.2.5: net debt / EBITDA <= 3.5 (kill when above)", "hard kill (vss/rules.py)", lev(3.5)),
    ("4.3 soft flag: no 3 sequential revenue declines", "soft flag (vss/rules.py)", kill43),
    ("Q1-Q3 all pass (E145 drop rule)", "E145 (vss/strike.py)",
     lambda r: None if None in (q(r, "Q1"), q(r, "Q2"), q(r, "Q3")) else all((q(r, "Q1"), q(r, "Q2"), q(r, "Q3")))),
    ("Q4: ROIIC >= r for a repeat buyer (tier step)", "E145 (vss/strike.py)", lambda r: q(r, "Q4")),
    ("MBP cushion: price <= 0.85 x fv", "§5 MBP (vss/queue.py)", mbp),
    ("Green flag: OCF / net income >= 1", "§4.4 (struck D12; vss review)", ocf_conv),
    ("Green flag: operating margin up YoY", "§4.4 (struck D12; vss review)", margin_up),
)

NOT_TESTABLE = (
    ("Gate 3 (quality floor over 8 quarters)", "the rows carry no quarterly margins or returns"),
    ("4.2.3 guidance cuts / 4.2.6 CEO+CFO", "no guidance or officer data"),
    ("Q5 (the issuer's sentence)", "text, a hand part"),
)


def spreads(data, market, h, through, labels=None):
    out = []
    for d, rows in sorted(data.items()):
        u = MS.usable(rows, h)
        lab = labels[d] if labels else {id(r): through(r) for r in u}
        a = [MS.excess(r, h) for r in u if lab.get(id(r)) is True]
        b = [MS.excess(r, h) for r in u if lab.get(id(r)) is False]
        if len(a) >= MIN_SIDE and len(b) >= MIN_SIDE:
            out.append((d, statistics.mean(a) - statistics.mean(b), len(a), len(b)))
    return out


def permuted_p95(data, market, h, through, n=1000, seed=20261109):
    rng = random.Random(seed)
    base = {}
    for d, rows in data.items():
        u = MS.usable(rows, h)
        base[d] = [(id(r), through(r)) for r in u]
    means = []
    for _ in range(n):
        labels = {}
        for d, pairs in base.items():
            ids = [i for i, v in pairs if v is not None]
            vals = [v for _, v in pairs if v is not None]
            rng.shuffle(vals)
            labels[d] = dict(zip(ids, vals))
        sp = spreads(data, market, h, through, labels)
        if sp:
            means.append(statistics.mean(x for _, x, _, _ in sp))
    means.sort()
    return means[int(0.95 * len(means))] if means else None


def main() -> int:
    if D.LB != "clean":
        raise SystemExit("run with DEVOUR_LB=clean (the registered data)")
    print("# #25 -- the untested filters, through against stopped\n")
    print("Pre-registered 2026-11-09 (ATTEMPTS #25), decision rule in the script's docstring.\n")
    markets = ("nordic", "us-bust")
    data = {}
    for m in markets:
        data[m] = D.load(m)
        A3.attach(m, data[m])
    decisions = []
    print("| Filter | Market | h | dates | mean through/stopped | spread (pp) | half 1 / half 2 | perm. p95 |")
    print("|---|---|---|---:|---|---:|---|---:|")
    for name, where, f in FILTERS:
        ok = True
        for m in markets:
            for h in (1, 3, 5):
                sp = spreads(data[m], m, h, f)
                if not sp:
                    print(f"| {name} | {m} | {h} y | 0 | -- | -- | -- | -- |")
                    if h == H:
                        ok = False
                    continue
                mean = statistics.mean(x for _, x, _, _ in sp)
                hl = [D.mean([x for d, x, _, _ in sp if D.half_of(m, d) == hf]) for hf in (0, 1)]
                na = round(statistics.mean(a for *_, a, _ in sp))
                nb = round(statistics.mean(b for *_, b in sp))
                p95 = permuted_p95(data[m], m, h, f) if h == H else None
                print(f"| {name} | {m} | {h} y | {len(sp)} | {na}/{nb} | {D.pp(mean)} | "
                      f"{' / '.join('--' if x is None else D.pp(x) for x in hl)} | "
                      f"{'' if p95 is None else D.pp(p95)} |")
                if h == H and (None in hl or any(x <= 0 for x in hl) or mean <= 0
                               or p95 is None or mean <= p95):
                    ok = False
        decisions.append((name, where, ok))
    print("\n## Not testable on these rows (stay as hand parts, not decided)\n")
    for name, why in NOT_TESTABLE:
        print(f"- **{name}**: {why}")
    print("\n## Decisions (3 years, both markets, both halves, above the permutation p95)\n")
    for name, where, ok in decisions:
        print(f"- **{name}** ({where}): {'HOLDS -> stays (IN)' if ok else 'does not hold -> removed (OUT)'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
