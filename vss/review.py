"""`vss review` -- the review session's record, validated and recorded.

WHAT THIS IS. `/review TICKER` (`.claude/commands/review.md`) walks the
owner through the playbook's steps one at a time and writes what the owner
said into `reference/reviews/<TICKER>/<date>.yaml`. That file is the
session's whole output. This module is the guard on it:

  * `--validate PATH` refuses a file that is not a review: a step the
    playbook does not know, a step neither answered nor skipped with a
    reason, a section-5 step answered before the growth view was
    registered, a machine-struck valuation figure quoted into the owner's
    words before the strike, a verification figure the prepare report
    never listed.
  * `--record PATH` validates, then appends the owner's note VERBATIM to
    the watchlist entry (backup first), registers the growth view where
    the code keeps growth views (`reference/growth-views/<TICKER>.md` and
    the entry's `growth:` block, E109), and stores nothing else. Never
    status, fv_base, tier, mbp or stop_price: those are the owner's to
    write by hand, and the refusal is enforced by re-reading the file
    after the write and restoring the backup if anything else moved.
  * `--schema` prints `config/review/SCHEMA.md` from this module, so the
    document and the validator cannot drift apart (a test holds them
    equal).

WHAT IT IS NOT. It composes no verdict, no tier, no fair value and no
growth rate. Every enum here is the playbook's own (`tools/playbook/
steps.py`: a step's `exits`), every refusal is a fact about the file's
shape or ordering, and the words in the file are the owner's.
"""

from __future__ import annotations

import re
import shutil
import sys
from dataclasses import dataclass, field
from datetime import date, datetime
from pathlib import Path
from typing import Any, Sequence

import yaml

from .runner import PROJECT_ROOT, WATCHLIST_PATH
from .rules import VALID_STATUSES

SCHEMA_VERSION = "vss/review v1"
REVIEWS_DIR = PROJECT_ROOT / "reference" / "reviews"
GROWTH_VIEWS_DIR = PROJECT_ROOT / "reference" / "growth-views"


def _steps_module():
    """`tools/playbook/steps.py`, the one step list. `tools/` is a sibling
    of `vss/`, on the path when run from the repository root and put there
    here otherwise."""
    try:
        from tools.playbook import steps
    except ImportError:  # pragma: no cover - a checkout run from elsewhere
        sys.path.insert(0, str(PROJECT_ROOT))
        from tools.playbook import steps
    return steps


# --------------------------------------------------------------- the step table

#: The chain from Gate 1 to the verdict: what a PIPELINE name walks.
_FROM_GATE_1 = ("gate-1", "gate-2", "gate-3", "gate-4", "gate-5",
                "hard-kills", "conviction",
                "basis", "flow", "net-debt", "divisor",
                "growth-view", "strike", "tier-mbp", "verdict")

#: A name that has been through section 5 re-reads and re-strikes: the
#: reading, the basis, the view, the strike, the verdict.
_RESTRIKE = ("hard-kills", "conviction",
             "basis", "flow", "net-debt", "divisor",
             "growth-view", "strike", "tier-mbp", "verdict")

#: Which steps a review walks, by the status the name holds when it
#: starts. Every id is a `tools/playbook/steps.py` step; the order is the
#: chain's. INTAKE and DROPPED open with the intake question (is the
#: record complete enough to watch?) because neither is watched.
REVIEW_STEPS: dict[str, tuple[str, ...]] = {
    "INTAKE": ("intake",) + _FROM_GATE_1,
    "PIPELINE": _FROM_GATE_1,
    "WATCH-GATED": _FROM_GATE_1,
    "WATCH-PRICED": _RESTRIKE,
    "HELD": _RESTRIKE,
    "DROPPED": ("intake",) + _FROM_GATE_1,
}

#: The step whose answer IS the registration, and every step after it:
#: none may be answered before `growth_view.registered_at`.
VIEW_BOUND = ("growth-view", "strike", "tier-mbp", "verdict")

#: The section-5 basis steps walked BEFORE the view is registered: their
#: text may carry no machine-struck valuation figure (the anchoring
#: guard, the playbook's GUARDED tuple minus the view-bound steps).
PRE_VIEW_GUARDED = ("basis", "flow", "net-debt", "divisor")

#: The step that carries the verification list.
VERIFICATION_STEP = "basis"

#: A step's outcome vocabulary is the playbook's `exits` plus `next` (the
#: name walks on). The verdict has no `next`: it exits, and a HELD name
#: reviewed and kept exits to `held`.
NEXT = "next"

STEP_KEYS = ("step", "outcome", "text", "answered_at", "skipped", "skip_reason",
             "documents_opened", "rulings_cited", "verification")
STEP_REQUIRED = ("step", "outcome", "text", "skipped", "skip_reason",
                 "documents_opened", "rulings_cited")
TOP_KEYS = ("schema", "ticker", "date", "status_at_start", "prepare_report",
            "prepare_waived", "started_at", "resume_reason", "steps",
            "growth_view", "note")
TOP_REQUIRED = ("ticker", "date", "status_at_start", "prepare_report", "steps",
                "growth_view", "note")
GROWTH_KEYS = ("base", "bear", "bull", "reasons", "registered_at")
VERIFICATION_KEYS = ("field", "period", "value", "outcome", "corrected_value")
VERIFICATION_OUTCOMES = ("VERIFIED", "CORRECTED")
_RULING_KEY = re.compile(r"^[A-F]\d+(?:\.\d+)?$")


def outcomes_for(step_id: str) -> tuple[str, ...]:
    steps = _steps_module()
    step = steps.BY_ID[step_id]
    if step_id == "verdict":
        return tuple(step.exits) + ("held",)
    return (NEXT,) + tuple(e for e in step.exits)


def steps_for(status: str) -> tuple[str, ...]:
    return REVIEW_STEPS[status]


# ------------------------------------------------------------------ the record

class ReviewError(Exception):
    """A refusal. The message says what and why; nothing was written."""


@dataclass
class Validation:
    path: Path
    ticker: str
    date: date
    status: str
    steps: list[dict]
    growth_view: dict | None
    note: str
    prepare: dict | None
    refusals: list[str] = field(default_factory=list)
    notices: list[str] = field(default_factory=list)

    @property
    def ok(self) -> bool:
        return not self.refusals

    def report(self) -> str:
        head = f"vss review --validate {self.path}"
        answered = [s["step"] for s in self.steps if not s.get("skipped")]
        skipped = [s["step"] for s in self.steps if s.get("skipped")]
        lines = [head, "",
                 f"{self.ticker} {self.date.isoformat()} from {self.status}: "
                 f"{len(answered)} answered, {len(skipped)} skipped of {len(self.steps)} steps"]
        if self.refusals:
            lines += ["", f"REFUSED ({len(self.refusals)}):"] + [f"  - {r}" for r in self.refusals]
        else:
            lines += ["", "VALID. Nothing was written."]
        if self.notices:
            lines += ["", "noted:"] + [f"  - {n}" for n in self.notices]
        return "\n".join(lines)


def _as_datetime(value: Any) -> datetime | None:
    if value is None or value == "":
        return None
    if isinstance(value, datetime):
        dt = value
    elif isinstance(value, date):
        dt = datetime(value.year, value.month, value.day)
    elif isinstance(value, str):
        try:
            dt = datetime.fromisoformat(value.strip())
        except ValueError:
            return None
    else:
        return None
    if dt.tzinfo is None:
        dt = dt.astimezone()
    return dt


def _as_date(value: Any) -> date | None:
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, date):
        return value
    if isinstance(value, str):
        try:
            return date.fromisoformat(value.strip())
        except ValueError:
            return None
    return None


def _is_number(value: Any) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool)


# ----------------------------------------------------- machine figures, spelled

def figure_spellings(value: float, *, percent: bool = False) -> set[str]:
    """The ways a figure gets written down, so a quoted one is found."""
    out: set[str] = set()
    v = float(value)
    if percent:
        p = v * 100
        for fmt in ("{:.0f}%", "{:.1f}%", "{:.2f}%", "{:g}%"):
            out.add(fmt.format(p))
        out.add(f"{v:g}")
        return out
    for fmt in ("{:g}", "{:.0f}", "{:.1f}", "{:.2f}", "{:,.0f}", "{:,.1f}", "{:,.2f}"):
        out.add(fmt.format(v))
    return {s for s in out if s not in ("0", "0.0", "0.00")}


def mentions(text: str, spellings: set[str]) -> str | None:
    for s in sorted(spellings, key=len, reverse=True):
        if re.search(r"(?<![\w.,])" + re.escape(s) + r"(?![\d])", text):
            return s
    return None


def machine_figures(entry, prepare: dict | None) -> dict[str, set[str]]:
    """The valuation figures the MACHINE holds for this name: the entry's
    fv_base, tier, mbp and stop, and any the prepare report's stands
    section quotes. Not the price and not the store's own figures -- those
    are facts, not anchors."""
    out: dict[str, set[str]] = {}
    if entry is not None:
        if entry.fv_base is not None:
            out["fv_base"] = figure_spellings(entry.fv_base)
        if entry.tier is not None:
            out["tier"] = {f"tier {entry.tier}", f"tier-{entry.tier}", f"Tier {entry.tier}"}
        if entry.stop_price is not None:
            out["stop_price"] = figure_spellings(entry.stop_price)
        try:
            from .rules import compute_mbp
            mbp = compute_mbp(entry.fv_base, entry.tier)
        except Exception:  # noqa: BLE001 -- no MBP is no anchor
            mbp = None
        if _is_number(mbp):
            out["mbp"] = figure_spellings(mbp)
    if prepare:
        stands = (prepare.get("context") or {}).get("stands") or {}
        for key in ("fv_base", "tier"):
            m = re.search(r"(-?\d[\d,]*\.?\d*)", str(stands.get(key) or ""))
            if m and key not in out:
                try:
                    out[key] = figure_spellings(float(m.group(1).replace(",", "")))
                except ValueError:
                    pass
    return out


# ------------------------------------------------------------------- validate

def load_review(path: Path) -> dict:
    try:
        raw = yaml.safe_load(Path(path).read_text(encoding="utf-8"))
    except (OSError, yaml.YAMLError) as exc:
        raise ReviewError(f"{path}: not a readable YAML file ({exc})")
    if not isinstance(raw, dict):
        raise ReviewError(f"{path}: the top level must be a mapping")
    return raw


def _load_entry(ticker: str, watchlist_path: Path):
    from .config import load_watchlist
    try:
        entries = load_watchlist(watchlist_path)
    except Exception as exc:  # noqa: BLE001 -- the file's own error is the message
        raise ReviewError(f"{watchlist_path}: would not load ({exc})")
    return next((e for e in entries if e.ticker.upper() == ticker.upper()), None), entries


def validate(path: Path, *, root: Path = PROJECT_ROOT,
             watchlist_path: Path = WATCHLIST_PATH) -> Validation:
    """Every refusal, collected; the shape errors that make the rest
    unreadable raise ReviewError instead."""
    path = Path(path)
    raw = load_review(path)
    steps_mod = _steps_module()
    refusals: list[str] = []
    notices: list[str] = []

    unknown = sorted(set(raw) - set(TOP_KEYS))
    if unknown:
        refusals.append(f"unknown top-level key(s): {', '.join(unknown)}. A figure can only enter "
                        f"this file inside the fields the schema names")
    missing = [k for k in TOP_REQUIRED if k not in raw]
    if missing:
        raise ReviewError(f"{path}: missing {', '.join(missing)}")
    if raw.get("schema") not in (None, SCHEMA_VERSION):
        refusals.append(f"schema is {raw.get('schema')!r}; this validator reads {SCHEMA_VERSION}")

    ticker = str(raw["ticker"]).strip()
    when = _as_date(raw["date"])
    if when is None:
        raise ReviewError(f"{path}: date must be YYYY-MM-DD, got {raw['date']!r}")
    status = str(raw["status_at_start"]).strip()
    if status not in VALID_STATUSES:
        raise ReviewError(f"{path}: status_at_start must be one of {'|'.join(VALID_STATUSES)}, "
                          f"got {status!r}")
    if path.parent.name != ticker or path.stem != when.isoformat():
        refusals.append(f"the file sits at {path.parent.name}/{path.name}; a review of {ticker} on "
                        f"{when.isoformat()} is reference/reviews/{ticker}/{when.isoformat()}.yaml")

    # the prepare report
    prepare: dict | None = None
    rel = raw.get("prepare_report")
    if rel in (None, ""):
        if not str(raw.get("prepare_waived") or "").strip():
            refusals.append("prepare_report is empty and prepare_waived carries no words: a review "
                            "starts from reports/prepare/<TICKER>-<date>.json or from the owner "
                            "saying, in the file, to proceed without it")
        else:
            notices.append(f"no prepare report; waived: {str(raw['prepare_waived']).strip()}")
    else:
        p = Path(rel)
        p = p if p.is_absolute() else root / p
        if not p.exists():
            refusals.append(f"prepare_report {rel} is not on disk")
        else:
            try:
                import json
                prepare = json.loads(p.read_text(encoding="utf-8"))
            except (OSError, ValueError) as exc:
                refusals.append(f"prepare_report {rel} would not load: {exc}")
            else:
                if str(prepare.get("ticker", "")).upper() != ticker.upper():
                    refusals.append(f"prepare_report {rel} is for {prepare.get('ticker')}, not {ticker}")
                if prepare.get("as_of") != when.isoformat():
                    notices.append(f"prepare report is from {prepare.get('as_of')}, the review from "
                                   f"{when.isoformat()}")

    # the watchlist entry, for the machine figures and the status
    entry = None
    try:
        entry, _ = _load_entry(ticker, watchlist_path)
    except ReviewError as exc:
        notices.append(str(exc))
    if entry is None:
        notices.append(f"{ticker} has no watchlist entry (E109 keeps some viewed names off the "
                       f"list); --record will refuse, --validate does not")
    elif entry.status != status:
        notices.append(f"status_at_start {status}; the entry now reads {entry.status}")

    # the steps, in order
    expected = steps_for(status)
    steps = raw.get("steps")
    if not isinstance(steps, list):
        raise ReviewError(f"{path}: steps must be a list")
    seen = [str(s.get("step")) if isinstance(s, dict) else "?" for s in steps]
    for s in seen:
        if s not in steps_mod.BY_ID:
            refusals.append(f"unknown step {s!r}: not in tools/playbook/steps.py")
    if tuple(seen) != expected:
        refusals.append(f"a {status} review walks {', '.join(expected)} in that order; the file has "
                        f"{', '.join(seen) or 'nothing'}")

    growth = raw.get("growth_view")
    registered_at = None
    if growth is not None:
        if not isinstance(growth, dict):
            refusals.append("growth_view must be a mapping with base, bear, bull, reasons, registered_at")
            growth = None
        else:
            unknown = sorted(set(growth) - set(GROWTH_KEYS))
            if unknown:
                refusals.append(f"growth_view has unknown key(s) {', '.join(unknown)}")
            for k in ("base", "bear", "bull"):
                if not _is_number(growth.get(k)):
                    refusals.append(f"growth_view.{k} must be a number the owner typed, as a fraction "
                                    f"(0.025 for 2.5%); got {growth.get(k)!r}")
                elif not -0.5 <= float(growth[k]) <= 0.5:
                    refusals.append(f"growth_view.{k} is {growth[k]}, outside -50%..+50%: a fraction, not a percent")
            if all(_is_number(growth.get(k)) for k in ("base", "bear", "bull")):
                if not growth["bear"] <= growth["base"] <= growth["bull"]:
                    refusals.append("growth_view wants bear <= base <= bull")
            if not str(growth.get("reasons") or "").strip():
                refusals.append("growth_view.reasons is empty: three rates with no words are numbers, not a view")
            registered_at = _as_datetime(growth.get("registered_at"))
            if registered_at is None:
                refusals.append(f"growth_view.registered_at must be an ISO timestamp, got "
                                f"{growth.get('registered_at')!r}")

    anchors = machine_figures(entry, prepare)
    strike_index = expected.index("strike") if "strike" in expected else len(expected)
    listed = {}
    if prepare:
        for item in prepare.get("verification") or []:
            listed[(str(item.get("field")), str(item.get("period")))] = item

    for i, s in enumerate(steps):
        if not isinstance(s, dict):
            refusals.append(f"step {i + 1} is not a mapping")
            continue
        sid = str(s.get("step"))
        where = f"step {i + 1} ({sid})"
        unknown = sorted(set(s) - set(STEP_KEYS))
        if unknown:
            refusals.append(f"{where}: unknown key(s) {', '.join(unknown)}")
        missing = [k for k in STEP_REQUIRED if k not in s]
        if missing:
            refusals.append(f"{where}: missing {', '.join(missing)}")
        for k in ("documents_opened", "rulings_cited"):
            v = s.get(k)
            if v is None:
                continue
            if not isinstance(v, list) or not all(isinstance(x, str) for x in v):
                refusals.append(f"{where}: {k} must be a list of strings")
            elif k == "rulings_cited":
                bad = [x for x in v if not _RULING_KEY.match(x.strip())]
                if bad:
                    refusals.append(f"{where}: rulings_cited holds {', '.join(bad)}; a ruling is E27, B22, C1")
        text = s.get("text")
        if text is not None and not isinstance(text, str):
            refusals.append(f"{where}: text must be a string, the owner's words")
            text = str(text)
        text = text or ""
        skipped = bool(s.get("skipped"))
        if skipped:
            if not str(s.get("skip_reason") or "").strip():
                refusals.append(f"{where}: skipped without a skip_reason")
            if s.get("outcome") not in (None, ""):
                refusals.append(f"{where}: skipped and yet carries outcome {s.get('outcome')!r}")
            continue
        # answered
        if sid not in steps_mod.BY_ID:
            continue
        allowed = outcomes_for(sid)
        if s.get("outcome") not in allowed:
            refusals.append(f"{where}: not skipped and outcome is {s.get('outcome')!r}; one of "
                            f"{', '.join(allowed)}")
        if not text.strip():
            refusals.append(f"{where}: not skipped and text is empty -- a step without an answer")
        answered_at = _as_datetime(s.get("answered_at"))
        if answered_at is None:
            refusals.append(f"{where}: answered_at must be an ISO timestamp on an answered step")
        if sid == "verdict" and s.get("outcome") == "held" and status != "HELD":
            refusals.append(f"{where}: `held` is the verdict of a HELD name reviewed and kept; this one started {status}")
        if sid in VIEW_BOUND:
            if growth is None:
                refusals.append(f"{where}: a section-5 step answered with growth_view absent (E28)")
            elif registered_at is not None and answered_at is not None and registered_at > answered_at:
                refusals.append(f"{where}: answered {answered_at.isoformat()} but the view was registered "
                                f"{registered_at.isoformat()}, later (E28: the view comes first)")
        if i < strike_index:
            for name, spellings in anchors.items():
                hit = mentions(text, spellings)
                if hit:
                    refusals.append(f"{where}: text quotes {name} as {hit!r} before the strike -- a "
                                    f"machine figure, not owner-typed (anchoring guard)")
        if sid == VERIFICATION_STEP:
            ver = s.get("verification") or []
            if not isinstance(ver, list):
                refusals.append(f"{where}: verification must be a list")
                ver = []
            for j, item in enumerate(ver):
                if not isinstance(item, dict):
                    refusals.append(f"{where}: verification item {j + 1} is not a mapping")
                    continue
                unknown = sorted(set(item) - set(VERIFICATION_KEYS))
                if unknown:
                    refusals.append(f"{where}: verification item {j + 1} has unknown key(s) {', '.join(unknown)}")
                key = (str(item.get("field")), str(item.get("period")))
                outcome = item.get("outcome")
                if outcome not in VERIFICATION_OUTCOMES:
                    refusals.append(f"{where}: verification {key[0]} {key[1]} outcome {outcome!r}; "
                                    f"VERIFIED or CORRECTED, on the owner's word")
                if prepare is not None and key not in listed:
                    refusals.append(f"{where}: verification names {key[0]} {key[1]}, which the prepare "
                                    f"report did not list -- not a figure the machine put up")
                elif key in listed and outcome == "VERIFIED" and _is_number(item.get("value")) \
                        and _is_number(listed[key].get("value")) \
                        and float(item["value"]) != float(listed[key]["value"]):
                    refusals.append(f"{where}: {key[0]} {key[1]} VERIFIED at {item['value']} but the report "
                                    f"listed {listed[key]['value']}; a different value is CORRECTED, not VERIFIED")
                if outcome == "CORRECTED" and not _is_number(item.get("corrected_value")):
                    refusals.append(f"{where}: {key[0]} {key[1]} CORRECTED without a corrected_value the owner typed")
            if prepare is not None:
                unrecorded = [k for k in listed if k not in {(str(v.get('field')), str(v.get('period')))
                                                             for v in ver if isinstance(v, dict)}]
                if unrecorded:
                    notices.append(f"{len(unrecorded)} of {len(listed)} listed figure(s) not recorded on the "
                                   f"basis step: " + ", ".join(f"{f} {p}" for f, p in unrecorded[:6])
                                   + (" ..." if len(unrecorded) > 6 else ""))
        else:
            if s.get("verification"):
                refusals.append(f"{where}: verification belongs on the {VERIFICATION_STEP} step")

    # the view's own words are pre-strike text
    if growth is not None:
        reasons = str(growth.get("reasons") or "")
        for name, spellings in anchors.items():
            hit = mentions(reasons, spellings)
            if hit:
                refusals.append(f"growth_view.reasons quotes {name} as {hit!r} -- a machine figure "
                                f"in the owner's reasons (anchoring guard)")
    for s in steps:
        if not (isinstance(s, dict) and s.get("skipped")):
            continue
        sid = str(s.get("step"))
        if sid not in expected or expected.index(sid) >= strike_index:
            continue
        reason = str(s.get("skip_reason") or "")
        for name, spellings in anchors.items():
            hit = mentions(reason, spellings)
            if hit:
                refusals.append(f"step {sid}: skip_reason quotes {name} as {hit!r} before the strike")

    note = raw.get("note")
    if note is not None and not isinstance(note, str):
        refusals.append("note must be a string: the owner's words, verbatim")
        note = str(note)

    started = raw.get("started_at")
    if started not in (None, ""):
        if started not in expected:
            refusals.append(f"started_at {started!r} is not a step of a {status} review")
        elif not str(raw.get("resume_reason") or "").strip():
            refusals.append("started_at names a resume point but resume_reason says nothing about why the "
                            "earlier steps are not walked")
        else:
            before = expected[:expected.index(started)]
            walked = [s.get("step") for s in steps if isinstance(s, dict) and not s.get("skipped")
                      and s.get("step") in before]
            if walked:
                refusals.append(f"started_at {started} but {', '.join(walked)} carry answers")

    return Validation(path, ticker, when, status, [s for s in steps if isinstance(s, dict)],
                      growth, note or "", prepare, refusals, notices)


# --------------------------------------------------------------------- record

@dataclass
class Recorded:
    watchlist: Path
    backup: Path | None
    note_appended: bool
    view_written: Path | None
    view_block_written: bool
    view_kept: str | None

    def report(self) -> str:
        lines = [f"recorded on {self.watchlist}" + (f" (backup {self.backup.name})" if self.backup else "")]
        lines.append("note appended verbatim to the entry's notes" if self.note_appended else "note not appended")
        if self.view_written:
            lines.append(f"growth view written to {self.view_written}")
        if self.view_block_written:
            lines.append("growth: block set on the entry (E109)")
        if self.view_kept:
            lines.append(self.view_kept)
        lines.append("nothing else: no status, fv_base, tier, mbp or stop_price")
        return "\n".join(lines)


def _entry_block(lines: list[str], ticker: str) -> tuple[int, int]:
    """[start, end) of the entry's lines in the watchlist text."""
    start = None
    for i, line in enumerate(lines):
        m = re.match(r"^  - ticker:\s*['\"]?([^'\"\s#]+)", line)
        if m and m.group(1).upper() == ticker.upper():
            start = i
            break
    if start is None:
        raise ReviewError(f"{ticker}: no `  - ticker:` line in the watchlist text")
    end = len(lines)
    for j in range(start + 1, len(lines)):
        line = lines[j]
        if re.match(r"^  - ", line) or (line.strip() and not line.startswith(" ") and not line.startswith("#")):
            end = j
            break
    return start, end


def _scalar_extent(lines: list[str], key_line: int, indent: int) -> int:
    """The line after the last continuation line of the scalar at key_line."""
    end = key_line + 1
    while end < len(lines):
        line = lines[end]
        if line.strip() == "" or (len(line) - len(line.lstrip(" ")) > indent and not line.lstrip().startswith("#")):
            end += 1
            continue
        break
    while end > key_line + 1 and lines[end - 1].strip() == "":
        end -= 1
    return end


def _literal(key: str, value: str, indent: int) -> list[str]:
    pad = " " * (indent + 2)
    out = [" " * indent + f"{key}: |2-"]
    for line in value.split("\n"):
        out.append((pad + line) if line != "" else "")
    return out


def _growth_lines(view: dict, view_path: str, registered: date, indent: int = 4) -> list[str]:
    pad = " " * indent
    return [f"{pad}growth:",
            f"{pad}  base: {view['base']}",
            f"{pad}  bear: {view['bear']}",
            f"{pad}  bull: {view['bull']}",
            f"{pad}  view: {view_path}",
            f"{pad}  registered: {registered.isoformat()}"]


def _view_file_text(ticker: str, view: dict, registered: datetime, review_rel: str,
                    old: str | None) -> str:
    def pct(x: float) -> str:
        return f"{x * 100:g}%"
    head = [f"# {ticker} — growth view", "",
            f"Set by the owner, {registered.date().isoformat()}, pre-registered under FRAMEWORK-EDITS E28 "
            f"BEFORE any fair value was computed and BEFORE g* was solved for. Recorded by "
            f"`vss review --record` from {review_rel} at {registered.isoformat()}.", "",
            f"Base case FCF growth, 10 years: {pct(view['base'])}",
            f"Bear: {pct(view['bear'])}",
            f"Bull: {pct(view['bull'])}", "",
            f"## The three rates, in the owner's words as recorded on {registered.date().isoformat()}", "",
            str(view["reasons"]).rstrip(), "",
            "*Recorded, not assessed. A changed view is a new dated entry above a SUPERSEDED block; "
            "the rates of a registered view are never edited (E76, E95).*", ""]
    if old:
        demoted = []
        for line in old.rstrip().split("\n"):
            demoted.append(re.sub(r"^\s{0,3}#{1,2}(?!#)\s*", "### ", line) if re.match(r"^\s{0,3}#{1,2}(?!#)\s", line) else line)
        head += ["", f"## SUPERSEDED — the earlier file, kept in the record and never edited "
                     f"(superseded {registered.date().isoformat()})", ""] + demoted + [""]
    return "\n".join(head)


def record(path: Path, *, root: Path = PROJECT_ROOT, watchlist_path: Path = WATCHLIST_PATH,
           views_dir: Path = GROWTH_VIEWS_DIR, now: datetime | None = None,
           dry_run: bool = False) -> Recorded:
    """Validate, then append the note and register the view. Nothing else."""
    from .config import load_watchlist

    v = validate(path, root=root, watchlist_path=watchlist_path)
    if not v.ok:
        raise ReviewError("refusing to record; " + v.report())
    now = now or datetime.now().astimezone()
    entry, entries = _load_entry(v.ticker, watchlist_path)
    if entry is None:
        raise ReviewError(f"{v.ticker} has no watchlist entry: nothing to append to. E109 keeps a viewed "
                          f"name off the list until the owner enters it by hand")
    if entry.status != v.status:
        raise ReviewError(f"the review started from {v.status} and the entry now reads {entry.status}; "
                          f"the entry moved since, and this record would say otherwise")
    note = v.note.rstrip("\n")
    if not note.strip():
        raise ReviewError("the note is empty; there is nothing of the owner's to record")
    old_notes = (entry.notes or "")
    if note in old_notes:
        raise ReviewError("already recorded: the entry's notes carry this note verbatim")

    original = Path(watchlist_path).read_text(encoding="utf-8")
    lines = original.split("\n")
    start, end = _entry_block(lines, v.ticker)

    # the growth view: written only where it is new or changed
    view = v.growth_view
    view_written: Path | None = None
    view_block = False
    kept = None
    new_growth_lines: list[str] | None = None
    registered = _as_datetime(view["registered_at"]) if view else None
    if view is not None:
        g = entry.growth
        same = (g is not None and g.bear is not None
                and float(g.base) == float(view["base"]) and float(g.bear) == float(view["bear"])
                and float(g.bull) == float(view["bull"]))
        if same:
            kept = (f"growth view unchanged: the registration of {g.registered.isoformat()} "
                    f"({g.view}) stands")
        else:
            view_rel = f"reference/growth-views/{v.ticker}.md"
            view_path = Path(views_dir) / f"{v.ticker}.md"
            old = view_path.read_text(encoding="utf-8") if view_path.exists() else None
            try:
                review_rel = Path(path).resolve().relative_to(Path(root).resolve()).as_posix()
            except ValueError:
                review_rel = str(path)
            text = _view_file_text(v.ticker, view, registered, review_rel, old)
            if not dry_run:
                view_path.parent.mkdir(parents=True, exist_ok=True)
                if old is not None:
                    shutil.copy2(view_path, view_path.with_name(
                        f"{view_path.name}.bak-{now.date().isoformat()}-{now.strftime('%H%M%S')}-pre-review"))
                view_path.write_text(text, encoding="utf-8")
            view_written = view_path
            new_growth_lines = _growth_lines(view, view_rel, registered.date())
            view_block = True

    # the notes scalar
    block = lines[start:end]
    key_line = next((i for i, l in enumerate(block) if re.match(r"^    notes:", l)), None)
    new_notes = old_notes + ("\n\n" if old_notes else "") + note
    if key_line is None:
        block = block + _literal("notes", new_notes, 4)
    else:
        scalar_end = _scalar_extent(block, key_line, 4)
        block = block[:key_line] + _literal("notes", new_notes, 4) + block[scalar_end:]
    if new_growth_lines is not None:
        g_line = next((i for i, l in enumerate(block) if re.match(r"^    growth:", l)), None)
        if g_line is None:
            block = block[:1] + new_growth_lines + block[1:]
        else:
            g_end = _scalar_extent(block, g_line, 4)
            block = block[:g_line] + new_growth_lines + block[g_end:]
    new_text = "\n".join(lines[:start] + block + lines[end:])

    backup = None
    if not dry_run:
        backup = Path(watchlist_path).with_name(
            f"{Path(watchlist_path).name}.bak-{now.date().isoformat()}-{now.strftime('%H%M%S')}"
            f"-pre-review-{v.ticker.lower()}")
        shutil.copy2(watchlist_path, backup)
        Path(watchlist_path).write_text(new_text, encoding="utf-8")
        try:
            after = load_watchlist(Path(watchlist_path))
            _assert_only_note_and_view_moved(entries, after, v.ticker, new_notes, view if view_block else None)
        except Exception as exc:
            shutil.copy2(backup, watchlist_path)
            raise ReviewError(f"{watchlist_path}: the write did not read back as intended ({exc}); "
                              f"restored from {backup.name}") from exc
    return Recorded(Path(watchlist_path), backup, True, view_written, view_block, kept)


def _assert_only_note_and_view_moved(before, after, ticker: str, new_notes: str, view: dict | None) -> None:
    from dataclasses import asdict
    if len(before) != len(after):
        raise ReviewError("the entry count changed")
    for b, a in zip(before, after):
        db, da = asdict(b), asdict(a)
        if b.ticker.upper() == ticker.upper():
            if da["notes"] != new_notes:
                raise ReviewError("the notes did not read back verbatim")
            db.pop("notes"); da.pop("notes")
            gb, ga = db.pop("growth"), da.pop("growth")
            if view is not None:
                if ga is None or (float(ga["base"]), float(ga["bear"]), float(ga["bull"])) != \
                        (float(view["base"]), float(view["bear"]), float(view["bull"])):
                    raise ReviewError("the growth block did not read back as the review's view")
            elif gb != ga:
                raise ReviewError("the growth block moved and the review did not ask it to")
            for key in ("status", "fv_base", "tier", "stop_price"):
                if db.get(key) != da.get(key):
                    raise ReviewError(f"{key} moved: {db.get(key)!r} -> {da.get(key)!r}")
        if db != da:
            raise ReviewError(f"{b.ticker}: a field other than notes/growth changed")


# ---------------------------------------------------------------------- schema

def schema_markdown() -> str:
    steps_mod = _steps_module()
    L = ["# The review file -- `reference/reviews/<TICKER>/<date>.yaml`", "",
         f"Generated by `vss review --schema` from `vss/review.py` (schema `{SCHEMA_VERSION}`); "
         "a test holds this file equal to that output, so edit the module, not this page. "
         "The file is the whole output of a `/review TICKER` session: what the owner said, "
         "step by step, in the playbook's order. `vss review --validate PATH` refuses what "
         "the rules below refuse; `vss review --record PATH` validates, appends the note "
         "verbatim to the watchlist entry, registers the growth view, and stores nothing else.",
         "", "## Shape", "",
         "```yaml",
         f"schema: {SCHEMA_VERSION}",
         "ticker: NVR                      # the directory name",
         "date: 2026-09-13                 # the file name",
         "status_at_start: PIPELINE        # a VALID_STATUSES value; picks the step list",
         "prepare_report: reports/prepare/NVR-2026-09-13.json   # or null with prepare_waived",
         "prepare_waived: null             # the owner's words, when proceeding without a report",
         "started_at: tier-mbp             # optional: the step the walk resumed on",
         "resume_reason: \"...\"             # required with started_at: why earlier steps are not walked",
         "steps:                           # one entry per step, in order (see the table)",
         "  - step: gate-1",
         "    outcome: next                # the step's enum, or null when skipped",
         "    text: \"...\"                  # the owner's words, verbatim",
         "    answered_at: 2026-09-13T10:12:00+02:00",
         "    skipped: false",
         "    skip_reason: null            # required when skipped",
         "    documents_opened: []         # strings",
         "    rulings_cited: []            # E27, B22, C1 ...",
         "    verification: []             # basis step only: see below",
         "growth_view:                     # null until the growth-view step",
         "  base: 0.025                    # fractions the owner typed",
         "  bear: -0.03",
         "  bull: 0.065",
         "  reasons: \"...\"",
         "  registered_at: 2026-09-13T10:40:00+02:00",
         "note: |                          # the owner's note, verbatim; --record appends it",
         "  ...",
         "```", "",
         "A verification item, on the `basis` step, one per figure the prepare report listed:", "",
         "```yaml",
         "    verification:",
         "      - {field: lease_liabilities, period: 2026-Q2, value: 62219.0, outcome: VERIFIED}",
         "      - {field: diluted_weighted_average_shares, period: 2026-Q1, value: 38665512.0,",
         "         outcome: CORRECTED, corrected_value: 38665212.0}",
         "```", "",
         "## The steps a review walks, by the status it starts from", ""]
    for status in VALID_STATUSES:
        L.append(f"- **{status}**: " + ", ".join(f"`{s}`" for s in steps_for(status)))
    L += ["", "Every id is a step of `tools/playbook/steps.py`; the order is the chain's. "
          "A resumed review keeps every earlier step as an entry with `skipped: true` and the "
          "resume reason.", "",
          "## Each step's outcome vocabulary", "",
          "`next` is the playbook's own word for walking on; the rest are the step's `exits`. "
          "The verdict has no `next`.", "",
          "| step | outcomes | question |", "|---|---|---|"]
    seen: list[str] = []
    for status in VALID_STATUSES:
        for sid in steps_for(status):
            if sid in seen:
                continue
            seen.append(sid)
    order = [s.id for s in steps_mod.STEPS if s.id in seen]
    for sid in order:
        st = steps_mod.BY_ID[sid]
        q = st.question.replace("{section}", st.sections[0] if st.sections else "")
        L.append(f"| `{sid}` | {', '.join(f'`{o}`' for o in outcomes_for(sid))} | {q} |")
    L += ["", "## What `--validate` refuses", "",
          "- a top-level or step key the schema does not name (a figure can enter the file only "
          "through the fields above);",
          "- a step name not in `tools/playbook/steps.py`, a step missing, extra or out of order "
          "for the status;",
          "- a step neither skipped with a `skip_reason` nor answered: an answered step needs an "
          "`outcome` from its vocabulary, non-empty `text` and an `answered_at`;",
          f"- a section-5 step ({', '.join(f'`{s}`' for s in VIEW_BOUND)}) answered with "
          "`growth_view` absent, or with `registered_at` later than that step's `answered_at` (E28);",
          "- a `growth_view` whose rates are not numbers in -50%..+50% as fractions, out of "
          "bear <= base <= bull, or with empty `reasons`;",
          "- a machine-struck valuation figure -- the entry's `fv_base`, `tier`, `mbp`, "
          "`stop_price`, or those the prepare report's stands section quotes -- appearing in the "
          "`text` of any step before `strike`, in a pre-strike `skip_reason`, or in "
          "`growth_view.reasons` (the anchoring guard: those are not owner-typed);",
          "- a `verification` item off the `basis` step, naming a field and period the prepare "
          "report did not list, VERIFIED at a value other than the listed one, or CORRECTED "
          "without a `corrected_value`;",
          "- `prepare_report` empty without `prepare_waived` carrying the owner's words, or a "
          "path not on disk or for another ticker;",
          "- `started_at` with no `resume_reason`, or with an earlier step carrying an answer;",
          "- `held` as a verdict on a review that did not start from HELD.", "",
          "What it cannot check, and the session is trusted with: that `text` is the owner's words "
          "and not the session's paraphrase; that the figures the owner typed are the owner's; "
          "that nothing was shown before the view was registered. `answered_at` and "
          "`registered_at` are what the session wrote.", "",
          "## What `--record` writes", "",
          "1. `config/watchlist.yaml`, backed up first as "
          "`watchlist.yaml.bak-<date>-<time>-pre-review-<ticker>`: the note appended verbatim to "
          "the entry's `notes` (the scalar is rewritten as a literal block so every character "
          "reads back), and -- only when the review's view is new or differs from the entry's -- "
          "the `growth:` block set to the review's rates with `view` and `registered` (E109).",
          "2. `reference/growth-views/<TICKER>.md`, only in that same case: the new view on top, "
          "the earlier file beneath a `## SUPERSEDED` heading with its headings demoted, so "
          "`readiness.read_growth_view` reads the new rates alone (E76, E95).",
          "3. Nothing else. The file is re-read after the write and compared entry by entry; if "
          "status, fv_base, tier, stop_price or any other field moved, the backup is restored "
          "and the command fails. A note already on the entry is refused, so a second run writes "
          "nothing.", ""]
    return "\n".join(L)


# ------------------------------------------------------------------------ CLI

def run_review(*, validate_path: str | None, record_path: str | None, schema: bool,
               dry_run: bool = False, watchlist_path: Path = WATCHLIST_PATH,
               root: Path = PROJECT_ROOT, views_dir: Path = GROWTH_VIEWS_DIR) -> tuple[int, str]:
    if schema:
        return 0, schema_markdown()
    if validate_path:
        try:
            v = validate(Path(validate_path), root=root, watchlist_path=watchlist_path)
        except ReviewError as exc:
            return 2, f"REFUSED: {exc}"
        return (0 if v.ok else 2), v.report()
    if record_path:
        try:
            r = record(Path(record_path), root=root, watchlist_path=watchlist_path,
                       views_dir=views_dir, dry_run=dry_run)
        except ReviewError as exc:
            return 2, f"REFUSED: {exc}"
        return 0, ("DRY RUN -- nothing written\n" if dry_run else "") + r.report()
    return 2, "nothing to do: --validate PATH, --record PATH or --schema"
