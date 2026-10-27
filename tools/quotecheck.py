"""Run the mechanical read-back (vss/quotecheck.py) over every store and
print one line per figure that did NOT pass, plus the counts. SHADOW: it
writes nothing -- unless --apply names a store.

    .venv/bin/python tools/quotecheck.py            # UNVERIFIED figures
    .venv/bin/python tools/quotecheck.py --all      # verified hand reads too
    .venv/bin/python tools/quotecheck.py --apply X  # E131: mark X's PASSes

--apply X sets `status: VERIFIED` and `verified_kind: machine_read_back` on
every UNVERIFIED figure of config/manual/X.yaml whose verdict is PASS or
PASS (near), and on nothing else (E131). Every other line is kept.
"""
import collections
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from vss import quotecheck as Q  # noqa: E402


def _entry_start(lines, where):
    """The line index where `where`'s entry opens, or None."""
    block, _, label = where.partition(" ")
    if block == "annual":
        key = f"  - fiscal_year: {label}"
    elif block == "periods":
        key = f"  - period: {label}"
    else:
        key = "roll_forward:"
    return next((i for i, line in enumerate(lines) if line == key), None)


def apply(ticker):
    """E131: mark the store's passing UNVERIFIED figures, nothing else."""
    path = Path("config/manual") / f"{ticker}.yaml"
    checks = [r for r in Q.check_store(path)
              if r.verdict.startswith("PASS") and r.status == "UNVERIFIED"]
    lines = path.read_text().split("\n")
    marked = []
    for r in checks:
        start = _entry_start(lines, r.where)
        if start is None:
            continue
        indent = "    " if r.where.startswith("roll_forward") else "      "
        name_at = next((i for i in range(start + 1, len(lines))
                        if lines[i] == f"{indent}{r.name}:"), None)
        if name_at is None:
            continue
        for i in range(name_at + 1, len(lines)):
            if not lines[i].startswith(indent + "  "):
                break
            if lines[i].strip() == "status: UNVERIFIED":
                lines[i] = f"{indent}  status: VERIFIED"
                lines.insert(i + 1, f"{indent}  verified_kind: machine_read_back")
                marked.append(f"{r.where} {r.name}")
                break
    path.write_text("\n".join(lines))
    for m in marked:
        print("VERIFIED (machine_read_back)", ticker, m)
    print(f"{ticker}: {len(marked)} figure(s) marked")


def main(argv):
    if "--apply" in argv:
        apply(argv[argv.index("--apply") + 1])
        return
    rows = []
    for p in sorted(Path("config/manual").glob("*.yaml")):
        if p.stem != "TEMPLATE":
            rows += Q.check_store(p, include_verified="--all" in argv)
    for r in rows:
        if not r.verdict.startswith("PASS"):
            missing = [q for q, v in r.quotes.items() if v == Q.MISSING]
            print(f"{r.verdict:20} {r.ticker:10} {r.where:22} {r.name}={r.value}"
                  + (f"  missing: {missing[0][:90]!r}" if missing else "")
                  + (f"  {r.searches[0]}" if r.searches else ""))
    print(len(rows), dict(collections.Counter(r.verdict for r in rows)))


if __name__ == "__main__":
    main(sys.argv[1:])
