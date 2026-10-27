"""Facts out of ONE filing's inline XBRL, in the companyfacts API's shape.

WHY THIS EXISTS. E140.1(3) rolls the bridge to the LATEST filed balance
sheet. SEC's companyfacts API is a compilation and it LAGS: on 2026-10-27 it
held Cognizant's and Lennox's Q1 10-Qs (filed 2026-04-29) and not their Q2
10-Qs (filed 2026-07-29). A roll-forward built on it alone would have
stood on March for both and said nothing. The filing itself carries the same
tagged facts -- every 10-Q since 2021 is inline XBRL -- so they are read
from the document the filer filed, and merged into the facts under the
filing's own accession, form and date.

WHAT IT READS. `ix:nonFraction` elements whose context has NO SEGMENT (a
dimensional fact is a part of a line, never the line), in `us-gaap` or
`ifrs-full`, scaled by the element's own `scale` and signed by its `sign`.
A fact displayed as a dash (`ixt:fixed-zero` / `ixt-sec:numdash`) is zero.
Nothing is inferred: a fact the document does not tag is not here.
"""

from __future__ import annotations

import re
from typing import Any

from lxml import etree

NS_IX = "http://www.xbrl.org/2013/inlineXBRL"
NS_XBRLI = "http://www.xbrl.org/2003/instance"
TAXONOMIES = {"us-gaap", "ifrs-full"}


class IxbrlError(Exception):
    """The document is not inline XBRL, or holds no reachable fact."""


def _text(element) -> str:
    return "".join(element.itertext()).strip()


#: The display formats a filer may tag a number in. A dash IS a zero.
_ZERO_FORMATS = {"fixed-zero", "fixedzero", "numdash", "zerodash"}
_COMMA_DECIMAL = {"num-comma-decimal", "numcommadecimal", "numdotcomma"}


def _number(element) -> float | None:
    fmt = (element.get("format") or "").split(":")[-1].lower()
    raw = _text(element)
    if fmt in _ZERO_FORMATS or raw in ("-", "\u2014", "\u2013"):
        return 0.0
    digits = re.sub(r"[^0-9.,]", "", raw)
    if not digits:
        return None
    if fmt in _COMMA_DECIMAL:
        digits = digits.replace(".", "").replace(",", ".")
    else:
        digits = digits.replace(",", "")
    try:
        value = float(digits)
    except ValueError:
        return None
    scale = element.get("scale")
    if scale:
        value *= 10 ** int(scale)
    if element.get("sign") == "-":
        value = -value
    return value


def facts_from_inline(html: bytes, *, accession: str, form: str,
                      filed: str) -> dict[str, Any]:
    """The filing's non-dimensional numeric facts, companyfacts-shaped:
    ``{"facts": {taxonomy: {tag: {"units": {unit: [entry, ...]}}}}}``."""
    try:
        root = etree.fromstring(html, parser=etree.XMLParser(recover=True,
                                                             huge_tree=True))
    except etree.XMLSyntaxError as exc:
        raise IxbrlError(f"not parseable as XHTML: {exc}") from exc
    if root is None:
        raise IxbrlError("empty document")
    contexts: dict[str, tuple[str | None, str]] = {}
    for ctx in root.iter(f"{{{NS_XBRLI}}}context"):
        if ctx.find(f".//{{{NS_XBRLI}}}segment") is not None:
            continue
        period = ctx.find(f"{{{NS_XBRLI}}}period")
        if period is None:
            continue
        instant = period.find(f"{{{NS_XBRLI}}}instant")
        if instant is not None:
            contexts[ctx.get("id")] = (None, instant.text.strip())
            continue
        start = period.find(f"{{{NS_XBRLI}}}startDate")
        end = period.find(f"{{{NS_XBRLI}}}endDate")
        if start is not None and end is not None:
            contexts[ctx.get("id")] = (start.text.strip(), end.text.strip())
    units: dict[str, str] = {}
    for unit in root.iter(f"{{{NS_XBRLI}}}unit"):
        measures = [m.text.split(":")[-1] for m in unit.iter(f"{{{NS_XBRLI}}}measure")]
        units[unit.get("id")] = "/".join(measures) if measures else unit.get("id")
    out: dict[str, Any] = {"facts": {}}
    seen: set[tuple] = set()
    for fact in root.iter(f"{{{NS_IX}}}nonFraction"):
        name = fact.get("name") or ""
        if ":" not in name:
            continue
        prefix, tag = name.split(":", 1)
        if prefix not in TAXONOMIES:
            continue
        period = contexts.get(fact.get("contextRef"))
        if period is None:
            continue
        value = _number(fact)
        if value is None:
            continue
        unit = units.get(fact.get("unitRef"), "")
        start, end = period
        key = (prefix, tag, unit, start, end)
        if key in seen:
            continue
        seen.add(key)
        entry = {"end": end, "val": value, "accn": accession, "form": form,
                 "filed": filed}
        if start:
            entry["start"] = start
        node = out["facts"].setdefault(prefix, {}).setdefault(tag, {"units": {}})
        node["units"].setdefault(unit, []).append(entry)
    if not out["facts"]:
        raise IxbrlError("no us-gaap or ifrs-full fact in the document")
    return out


def merge_facts(facts: dict[str, Any], extra: dict[str, Any]) -> dict[str, Any]:
    """`facts` with `extra`'s entries added. An entry already present for the
    same accession, tag, unit and window is not added twice."""
    merged = {"facts": {t: {k: {"units": {u: list(es) for u, es in v["units"].items()}}
                            for k, v in tags.items()}
                        for t, tags in (facts.get("facts") or {}).items()}}
    for key, value in facts.items():
        if key != "facts":
            merged[key] = value
    for taxonomy, tags in extra.get("facts", {}).items():
        for tag, node in tags.items():
            target = merged["facts"].setdefault(taxonomy, {}).setdefault(
                tag, {"units": {}})
            for unit, entries in node["units"].items():
                have = target["units"].setdefault(unit, [])
                known = {(e.get("accn"), e.get("start"), e["end"]) for e in have}
                for e in entries:
                    if (e["accn"], e.get("start"), e["end"]) not in known:
                        have.append(e)
    return merged
