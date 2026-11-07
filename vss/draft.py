"""`vss manual --merge-draft`: a pre-fill DRAFT into the live store.

Decision (a), HANDOFF 2026-11-07: a pre-fill (`esef-ixbrl`, later
`llm-pdf`) writes ``config/manual/drafts/<T>.<origin>.yaml`` and never the
live store, because the ranking key is not gated on status (SPEC §5b) and
`prepare` runs the filter limbs on `manual.as_record` -- a live UNVERIFIED
figure would leak into both. This merges a draft in, by hand, when the
owner (or the session under E141) chooses to.

WHAT IT DOES, and nothing else:

- a fiscal year the store lacks is added whole;
- a figure the store lacks, in a year it has, is added;
- a figure the store HAS is never touched: the same value is reported as
  agreeing, a different value is printed SIDE BY SIDE as a conflict and
  left as the store has it;
- a year whose period end differs from the store's is a conflict, whole.

It REFUSES (nothing written) where the draft and the store state a
different reporting currency, money unit or share unit: no silent scaling.

The live file is edited as TEXT, so every comment in it survives; the
result must load through `manual.parse_manual` before it is written, and
the old file is copied to ``arkiv/config-bak/config/manual/`` first.
"""

from __future__ import annotations

import re
import shutil
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path

import yaml

from .manual import MANUAL_DIR, ManualError, parse_manual

DRAFTS_DIR = MANUAL_DIR / "drafts"
BACKUP_DIR = Path("arkiv/config-bak/config/manual")
DRAFT_ORIGINS = ("esef-ixbrl", "llm-pdf")


@dataclass
class MergeResult:
    target: Path
    created: bool = False
    added_years: list = field(default_factory=list)
    added: list = field(default_factory=list)          # (year, field, value)
    agreed: list = field(default_factory=list)         # (year, field, value)
    conflicts: list = field(default_factory=list)      # one line each
    backup: Path | None = None
    written: bool = False


def _year_block(lines: list[str], year, key_name: str = "fiscal_year") -> tuple[int, int] | None:
    """(first, end) line indices of `  - <key_name>: <year>`'s entry."""
    key = f"  - {key_name}: {year}"
    start = next((i for i, l in enumerate(lines) if l.rstrip() == key), None)
    if start is None:
        return None
    end = len(lines)
    for i in range(start + 1, len(lines)):
        l = lines[i]
        if l.startswith("  - ") or (l and not l.startswith(" ") and not l.startswith("#")):
            end = i
            break
    # trailing blanks and comments belong to what follows
    while end > start + 1 and (not lines[end - 1].strip() or lines[end - 1].lstrip().startswith("#")):
        end -= 1
    return start, end


def _figure_block(lines: list[str], start: int, end: int, name: str) -> list[str]:
    head = f"      {name}:"
    i = next(k for k in range(start, end) if lines[k].rstrip() == head)
    out = [lines[i]]
    for k in range(i + 1, end):
        if lines[k].startswith("        ") or not lines[k].strip():
            out.append(lines[k])
        else:
            break
    while out and not out[-1].strip():
        out.pop()
    return out


def _annual_end(lines: list[str], block: str = "annual") -> int | None:
    """Where the `<block>:` list ends (insert point for a new entry)."""
    start = next((i for i, l in enumerate(lines) if re.match(rf"^{block}:\s*(#.*)?$", l)), None)
    if start is None:
        return None
    end = len(lines)
    for i in range(start + 1, len(lines)):
        l = lines[i]
        if l and not l.startswith(" ") and not l.startswith("#"):
            end = i
            break
    while end > start + 1 and (not lines[end - 1].strip() or lines[end - 1].lstrip().startswith("#")):
        end -= 1
    return end


def _same(a, b) -> bool:
    try:
        return abs(float(a) - float(b)) <= 1e-9 * max(1.0, abs(float(a)))
    except (TypeError, ValueError):
        return a == b


def merge_draft(ticker: str, *, origin: str = "esef-ixbrl",
                manual_dir: Path = MANUAL_DIR, drafts_dir: Path | None = None,
                backup_dir: Path = BACKUP_DIR, write: bool = True,
                now: datetime | None = None) -> MergeResult:
    ticker = ticker.strip().upper()
    if origin not in DRAFT_ORIGINS:
        raise ManualError(f"--origin must be one of {', '.join(DRAFT_ORIGINS)}")
    drafts_dir = Path(drafts_dir) if drafts_dir else Path(manual_dir) / "drafts"
    dpath = drafts_dir / f"{ticker}.{origin}.yaml"
    if not dpath.exists():
        raise ManualError(f"no draft at {dpath}")
    dtext = dpath.read_text(encoding="utf-8")
    ddoc = yaml.safe_load(dtext)
    parse_manual(ddoc, path=dpath)
    dlines = dtext.split("\n")
    target = Path(manual_dir) / f"{ticker}.yaml"
    res = MergeResult(target=target)
    stamp = (now or datetime.now().astimezone())

    if not target.exists():
        res.created = True
        for block, kn in (("annual", "fiscal_year"), ("periods", "period")):
            for y in ddoc.get(block) or []:
                res.added_years.append(y[kn])
                for f, raw in (y.get("figures") or {}).items():
                    res.added.append((y[kn], f, raw.get("value")))
        if write:
            target.write_text(dtext, encoding="utf-8")
            res.written = True
        return res

    ltext = target.read_text(encoding="utf-8")
    ldoc = yaml.safe_load(ltext)
    parse_manual(ldoc, path=target)
    for key, default in (("reporting_currency", None), ("money_unit", "whole"),
                         ("share_unit", "whole")):
        dv = str(ddoc.get(key) or default)
        lv = str(ldoc.get(key) or default)
        if ldoc.get(key) is None and key == "reporting_currency":
            continue
        if dv != lv:
            raise ManualError(
                f"{target}: {key} is {lv!r} and the draft's is {dv!r}. Nothing "
                f"is merged: a figure is never rescaled or converted on the "
                f"way in (no silent scaling).")

    lines = ltext.split("\n")
    for block, kn in (("annual", "fiscal_year"), ("periods", "period")):
        _merge_block(block, kn, ddoc, dlines, ldoc, lines, res)

    if not res.added:
        return res
    new = "\n".join(lines)
    parse_manual(yaml.safe_load(new), path=target)       # fail closed
    if write:
        backup_dir = Path(backup_dir)
        backup_dir.mkdir(parents=True, exist_ok=True)
        res.backup = backup_dir / f"{target.name}.bak-{stamp.strftime('%Y-%m-%d-%H%M%S')}-merge-draft"
        shutil.copy2(target, res.backup)
        target.write_text(new, encoding="utf-8")
        res.written = True
    return res


def render(res: MergeResult, *, origin: str) -> str:
    out = [f"vss manual --merge-draft -> {res.target} ({origin})"]
    if res.created:
        out.append("  NEW STORE: there was no live file; the draft became it")
    if res.backup:
        out.append(f"  backup: {res.backup}")
    if res.added_years:
        out.append(f"  entries added: {', '.join(f'FY{y}' if isinstance(y, int) else str(y) for y in res.added_years)}")
    out.append(f"  figures added: {len(res.added)} (all UNVERIFIED; E149: the owner verifies)")
    for y, f, v in res.added:
        out.append(f"    + {'FY' if isinstance(y, int) else ''}{y} {f} = {v}")
    if res.agreed:
        out.append(f"  already in the store, same value: {len(res.agreed)}")
    if res.conflicts:
        out.append(f"  CONFLICTS, left as the store has them: {len(res.conflicts)}")
        for c in res.conflicts:
            out.append(f"    ! {c}")
    if not res.written:
        out.append("  nothing written" + ("" if res.added else " (nothing to add)"))
    return "\n".join(out)


def _label(block: str, key) -> str:
    return f"FY{key}" if block == "annual" else str(key)


def _merge_block(block: str, kn: str, ddoc: dict, dlines: list[str], ldoc: dict,
                 lines: list[str], res: "MergeResult") -> None:
    """One block (`annual:` keyed on fiscal_year, `periods:` on period)."""
    live = {y.get(kn): y for y in (ldoc.get(block) or [])}
    for dy in ddoc.get(block) or []:
        fy = dy[kn]
        lab = _label(block, fy)
        db = _year_block(dlines, fy, kn)
        ly = live.get(fy)
        if ly is None:
            clash = [y for y in live.values()
                     if str(y.get("period_end")) == str(dy.get("period_end"))]
            if clash:
                res.conflicts.append(
                    f"{lab}: the store keys period end {dy.get('period_end')} as "
                    f"{_label(block, clash[0].get(kn))}; not added")
                continue
            block_lines = dlines[db[0]:db[1]]
            later = sorted(str(y) for y in live if str(y) > str(fy))
            if later:
                # before the next later entry, and before the comments over it
                key = next(y for y in live if str(y) == later[0])
                at = _year_block(lines, key, kn)[0]
                while at > 0 and lines[at - 1].lstrip().startswith("#") and lines[at - 1].startswith("  "):
                    at -= 1
            else:
                at = _annual_end(lines, block)
            if at is None:
                empty = next((i for i, l in enumerate(lines) if re.match(rf"^{block}:\s*\[\]\s*$", l)), None)
                if empty is not None:
                    lines[empty] = f"{block}:"
                    at = empty + 1
                else:
                    while lines and not lines[-1].strip():
                        lines.pop()
                    lines += ["", f"{block}:"]
                    at = len(lines)
            lines[at:at] = block_lines
            res.added_years.append(fy)
            for f, raw in (dy.get("figures") or {}).items():
                res.added.append((fy, f, raw.get("value")))
            continue
        if str(ly.get("period_end")) != str(dy.get("period_end")):
            res.conflicts.append(
                f"{lab}: period end {ly.get('period_end')} in the store, "
                f"{dy.get('period_end')} in the draft; left")
            continue
        lfigs = ly.get("figures") or {}
        for f, raw in (dy.get("figures") or {}).items():
            if f in lfigs:
                have = (lfigs[f] or {}).get("value") if isinstance(lfigs[f], dict) else lfigs[f]
                if _same(have, raw.get("value")):
                    res.agreed.append((fy, f, have))
                else:
                    res.conflicts.append(
                        f"{lab} {f}: store {have!r} | draft {raw.get('value')!r} "
                        f"({raw.get('page')}) -- left as the store has it")
                continue
            lb = _year_block(lines, fy, kn)
            fig = _figure_block(dlines, db[0], db[1], f)
            has_figures = any(lines[k].rstrip() == "    figures:" for k in range(lb[0], lb[1]))
            if not has_figures:
                fig = ["    figures:"] + fig
            lines[lb[1]:lb[1]] = fig
            res.added.append((fy, f, raw.get("value")))
