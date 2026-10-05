"""GDDY: re-strike on the growth view the owner RE-REGISTERED 2026-08-30
after the E76 reading -- base 3% (was 5%), bear 1%, bull 8%.

Reuses the strike machinery of `tools/strike_acn_gddy_nvr_ulta_2026_08_30.py`
unchanged; only the view, the stamp and the printout's header differ. It
WRITES TWO THINGS ONLY: `reference/GDDY-STRIKE-2026-08-30-restrike.md` and
`reference/run-records/GDDY-2026-08-30-restrike.json`. It NEVER writes
fv_base, tier or mbp to config/watchlist.yaml, and it does not score a tier.

    python tools/restrike_gddy_2026_08_30.py
"""

from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

spec = importlib.util.spec_from_file_location(
    "first_strike", ROOT / "tools" / "strike_acn_gddy_nvr_ulta_2026_08_30.py")
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)

STAMP = "2026-08-30-restrike"
m.VIEWS = {"GDDY": dict(base=0.03, bear=0.01, bull=0.08)}     # the re-registered view
m.STAMP = STAMP


def report(s: dict) -> str:
    t = s["ticker"]
    return "\n".join([
        f"# {t} -- section 5 RE-STRIKE on the re-registered growth view, {STAMP}",
        "",
        f"**{m.RUN_TS.strftime('%Y-%m-%d %H:%M %Z')}. `config/watchlist.yaml` IS NOT "
        "WRITTEN -- no fv_base, tier or mbp is written; this is a printout and a "
        "stop.** The run record is written to "
        f"`reference/run-records/{t}-{STAMP}.json`; linking it to a watchlist entry "
        "remains the owner's write.",
        "",
        "**E76, applied:** the E76 reading (`reports/GDDY-reading-2026-08-30.md`, "
        "2026-08-30) changed what the owner believes about growth, so the view was "
        "RE-REGISTERED with the reason and the name re-struck. **Growth view: "
        "`reference/growth-views/GDDY.md` -- base 3% (was 5%), bear 1% (unchanged), "
        "bull 8% (unchanged), re-registered by the owner 2026-08-30 after the "
        "reading and BEFORE this re-strike; the superseded first view (5% / 1% / 8%, "
        "struck at fv_base 156.45 in `reference/GDDY-STRIKE-2026-08-30.md`) stays in "
        "the record.** The owner's reason, as recorded: *the customer count has "
        "fallen three years running while revenue per customer rose 19%, bookings "
        "growth has decelerated 9.5% to 7.2% to 4.2%, hosting is shrinking, and the "
        "CEO's pay is tied to cash flow and relative share price rather than growth. "
        "Five per cent assumed price increases could continue indefinitely against "
        "cheaper registrars; three assumes they mostly can.*",
        "",
        f"Tool: `tools/restrike_gddy_2026_08_30.py` over the first strike's machinery "
        f"at `{m.tool_commit()}`. r 9.5% (7.0% core + 2.5% premium, E29); terminal "
        f"2.5%; 10 explicit years; end-of-year discounting. The store file "
        f"`config/manual/GDDY.yaml` is unchanged since the first strike; only the "
        f"growth rate moved.",
        "",
        m.render(s),
        m.framework_output(s) if "band" in s else "",
        "",
        "---",
        "",
        "## What this run does NOT do",
        "",
        "- **It writes nothing to `config/watchlist.yaml`.**",
        f"- **It does not score tier.** Section 4.4 has not been scored for {t}; the "
        "§4.4 evidence is assembled in the reading, and MBP is printed as DATA MISSING "
        "with the per-tier range against the NEW bear case.",
        "- **It does not authorise a purchase.** S0 rule 4 stands.",
        "",
    ])


def main() -> int:
    m.RECORDS.mkdir(parents=True, exist_ok=True)
    s = m.strike("GDDY")
    if "record" in s:
        (m.RECORDS / f"GDDY-{STAMP}.json").write_text(
            json.dumps(s["record"].to_dict(), indent=1) + "\n", encoding="utf-8")
    text = report(s)
    (ROOT / "reference" / f"GDDY-STRIKE-{STAMP}.md").write_text(text, encoding="utf-8")
    print(text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
