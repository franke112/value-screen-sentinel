"""The anchoring guard's redactor: case figures become [figure].

A THRESHOLD IS THE RULE, A CASE FIGURE IS THE ANCHOR. On a section-5 or
pre-registration step opened without a registered growth view, the rule
text stays readable and every figure that is a price, fair value, MBP,
tier, growth rate, multiple or stop is replaced with `[figure]`. Ruling
numbers, dates and the thresholds the rules themselves state stay.

What counts as a threshold is READ FROM FRAMEWORK.md, not listed here:
every percentage, basis-point figure, multiple and multiplier the
framework's own text states (15–50%, ±200bps, 2.5×, 0.85, 9.5% ...). A
figure of that shape that the framework never states is a case figure.
A figure the rule cannot tell apart is REDACTED AND LOGGED, never kept.
"""

from __future__ import annotations

import re
from typing import Iterable

FIGURE = "[figure]"

_SIGN = r"[+\-−±]?"
_NUM = r"(?:\d{1,3}(?:,\d{3})+|\d+)(?:[.,]\d+)?"
_UNIT = r"(?:%|bps|bp|×|x\b|USD|EUR|SEK|NOK|DKK|GBX|GBP|CHF|US\$m|m\b|bn\b|million|billion)"

_RANGE = rf"{_SIGN}{_NUM}\s*{_UNIT}?\s*(?:[-–]|to|/)\s*{_SIGN}{_NUM}"

#: One numeric token: a range or a single number, with an optional unit.
#: The lookbehind keeps it off dates (2026-08-30), keys (E70, 10-K),
#: section numbers (§5.3, 4.2.1) and words (FY2025, RSI(14) is fine).
TOKEN = re.compile(
    rf"(?<![A-Za-z0-9§./\-])(?P<body>(?:{_RANGE})|(?:{_SIGN}{_NUM}))\s*(?P<unit>{_UNIT})?"
    rf"(?![\d.]*[A-Za-z0-9]|-\d)")

_PROTECT = re.compile(r"\d{4}-\d{2}-\d{2}|§\s*\d+(?:\.\d+)*|\b\d+\.\d+\.\d+\b|\b(?:19|20)\d{2}\b(?!\.\d)|\bline \d+")

#: Words that make the figure after them a case figure whatever its shape.
_CASE_BEFORE = re.compile(
    r"(fv_base|fair value|\bfv\b|\bmbp\b|maximum buy price|stop_price|\bstop\b|\bprice\b|\bclose[sd]?\b|"
    r"\bbear\b|\bbull\b|\bbase\b|g_base|g_bear|g_bull|\bg\\?\*|\bg\b|implied|organic|reported|\bmargin\b|"
    r"coverage|\byield\b|drawdown|\bdd\b|returns?\b|\bfell\b|\brose\b|\bgrowth\b|\bscores?\b|\bread[s]?\b|"
    r"\bprinted\b|\bat\b|=|->|→|\bfrom\b|\bnet (?:debt|cash)\b|FCF0|\bFCF\b|\bcapex\b|\brevenue\b|\bsales\b|"
    r"\bdivisor\b|\bcount\b|\bshares\b|\bleg\b|\btier\b|\bP/E\b|EV/EBIT|\bmultiple\b)\s*[:\-–—]?\s*\**$",
    re.I)
#: The words that override a threshold-shaped figure (one the framework
#: states, like 9.5% or 2.5×): a measurement word. "flat at 9.5%" is the
#: rule's own rate; "margin 9.5%" is a case figure.
_STRONG_CASE_BEFORE = re.compile(
    r"(g_base|g_bear|g_bull|\bg\\?\*|implied|organic|reported|\bmargin\b|coverage|\byield\b|drawdown|\bdd\b|"
    r"returns?\b|\bfell\b|\brose\b|\bgrowth\b|\bread[s]?\b|\bprinted\b|\bP/E\b|EV/EBIT|\bmultiple\b|"
    r"\bmbp\b|fv_base|fair value|\bstop\b|\bprice\b|\bclose[sd]?\b|\bbear\b|\bbull\b|\bbase\b)\s*[:\-–—]?\s*\**$", re.I)
_NOT_CASE_BEFORE = re.compile(r"\bat (?:least|most)\s*$|\bwithin\s*$", re.I)
_TIER_KEEP_AFTER = re.compile(r"^\s*(?:[×x]|\*\*?\s*[×x]|0\.\d|cushion|multiplier|\||keeps)")
_CURRENCY = re.compile(r"USD|EUR|SEK|NOK|DKK|GBX|GBP|CHF|US\$m|^m$|^bn$|million|billion")


def normalise(body: str, unit: str | None) -> str:
    """A token as the threshold set spells it: no sign, no spaces, x→×."""
    body = re.sub(r"^[+\-−±]", "", body.strip())
    body = re.sub(r"\s*(?:%|bps|bp|×|x)?\s*(?:[-–]|to|/)\s*[+\-−±]?", "–", body)
    body = body.replace(",", "")
    unit = (unit or "").strip().replace("x", "×").replace("bp", "bps").replace("bpss", "bps")
    return body + unit


def thresholds_from(text: str) -> set[str]:
    """Every rule-shaped figure the framework's own text states.

    A signed figure (+10.5%, −3.2%) is an example the framework quotes, not
    a rule; a percentage with a decimal above ten (46.9%) likewise. Bare
    multipliers of the form 0.xx are read too, for the §5.3 table."""
    out: set[str] = set()
    for m in TOKEN.finditer(text):
        body, unit = m.group("body"), m.group("unit")
        if not unit or _CURRENCY.search(unit):
            continue
        if re.match(r"[+\-−]", body.strip()) and not re.search(r"[-–]|\bto\b|/", body[1:]):
            continue  # a signed single figure is an example the framework quotes; a signed range is a cap
        if unit == "%" and re.fullmatch(r"\d+\.\d+", body.strip()) and float(body) > 10:
            continue
        out.add(normalise(body, unit))
    out |= {m.group(0) for m in re.finditer(r"\b0\.\d{2}\b", text)}
    return out


class Redactor:
    def __init__(self, thresholds: Iterable[str]):
        self.thresholds = set(thresholds)
        self.unsure: list[str] = []
        self.count = 0

    def _decide(self, text: str, m: re.Match) -> bool:
        """True when the token is a case figure and must go."""
        body, unit = m.group("body"), (m.group("unit") or "").strip()
        before = text[max(0, m.start() - 28): m.start()]
        after = text[m.end(): m.end() + 14]
        key = normalise(body, unit)
        signed = bool(re.match(r"[+\-−]", body.strip()))
        case_word = bool(_CASE_BEFORE.search(before)) and not _NOT_CASE_BEFORE.search(before)
        strong = bool(_STRONG_CASE_BEFORE.search(before))
        is_range = bool(re.search(r"[-–]|\bto\b|/", body))
        digits = re.sub(r"[^\d]", "", body.split("–")[0].split("-")[0])
        # a tier stated for a name is a case figure; "tier 1 × 0.85" is the rule
        if re.search(r"\btier\s*\**$", before, re.I):
            return not _TIER_KEEP_AFTER.match(after)
        if unit and _CURRENCY.search(unit):
            return True
        if unit in ("%", "bps", "bp"):
            if is_range and key in self.thresholds and not strong:
                return False
            if signed:
                return True
            if key in self.thresholds and not strong:
                return False
            if not case_word and not is_range and re.fullmatch(r"\d+", body.strip()):
                self.unsure.append(f"{m.group(0).strip()!r} after {before[-24:]!r}")
            return True
        if unit in ("×", "x"):
            if key in self.thresholds and not strong:
                return False
            if not case_word:
                self.unsure.append(f"{m.group(0).strip()!r} after {before[-24:]!r}")
            return True
        # no unit: a multiplier is a threshold only in a multiplier's place --
        # beside a ×, a cushion or a multiplier word. "0.51 above the limit"
        # is a distance, and a case figure.
        multiplier_place = bool(re.search(r"[×x]\s*\**$|(?:cushion|multiplier|weight)\s*(?:of|is|:)?\s*$", before, re.I)
                                or re.match(r"\s*\**\s*[×x]|\s*\)?\s*(?:cushion|multiplier)", after))
        if (key in self.thresholds or re.fullmatch(r"0\.\d+", body.strip())) and multiplier_place:
            return False
        if re.fullmatch(r"0\.\d{2,}", body.strip()):
            return True
        if "," in body or len(digits) >= 4:
            return True
        if re.search(r"\.\d{2,}", body):
            return True
        if case_word and (float(digits or 0) >= 10 or "." in body or is_range):
            return True
        if is_range and "." in body:
            return True
        return False

    def __call__(self, text: str) -> str:
        if not text:
            return text
        keep: list[str] = []

        def stash(m: re.Match) -> str:
            keep.append(m.group(0))
            return f"\x00{len(keep) - 1}\x00"
        work = _PROTECT.sub(stash, text)

        def sub(m: re.Match) -> str:
            if self._decide(work, m):
                self.count += 1
                return FIGURE
            return m.group(0)
        work = TOKEN.sub(sub, work)
        return re.sub(r"\x00(\d+)\x00", lambda m: keep[int(m.group(1))], work)
