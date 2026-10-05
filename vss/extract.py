"""LLM figure extraction from a primary source (OpenRouter).

The model's job is narrow and total: pull stated figures and the verbatim
sentence each came from. It does not decide materiality, does not write
prose, does not judge, and does not recommend. Everything downstream of
this module is deterministic Python.

Three invariants, each enforced by a test:

1. ``eps_consensus`` is MANUAL ONLY. It is not in the extraction schema
   and must never be proposed -- consensus is not in the primary source
   and is the same class of number as fv_base.
2. Nothing here writes to ``quarters:``. Figures are PROPOSED in the
   alert; the owner enters them by hand.
3. A null figure, a parse failure or any ambiguity marks the whole
   extraction UNCERTAIN. It never silently degrades.
"""

from __future__ import annotations

import json
import logging
import math
import os
import re
import urllib.error
import urllib.request
from dataclasses import dataclass, field

from . import env
from .rules import (
    FRACTION_BANDS,
    VALID_ACCOUNTING,
    VALID_BASIS,
    VALID_GUIDANCE_ACTIONS,
    VALID_PERIOD_BASIS,
)

log = logging.getLogger(__name__)

API_URL = "https://openrouter.ai/api/v1/chat/completions"
KEY_ENV = "VSS_OPENROUTER_KEY"
MODEL_ENV = "VSS_OPENROUTER_MODEL"
#: OpenRouter model ids are vendor-prefixed. Overridable via MODEL_ENV;
#: any rejection is reported with the id echoed so a wrong id is obvious.
#: NOT deepseek/deepseek-chat -- that is V3 (Dec 2024), a different model.
DEFAULT_MODEL = "deepseek/deepseek-v4-flash"
TIMEOUT_SECONDS = 120

#: Figures the model may extract. eps_consensus is DELIBERATELY ABSENT.
EXTRACTABLE_FIELDS = (
    "revenue", "revenue_yoy", "revenue_yoy_organic", "op_income", "op_margin",
    "eps", "net_debt_ebitda", "receivables", "inventory", "class_c_impact",
    "covenant_headroom",
)
#: Never extractable, at any prompt. Guarded by a test.
FORBIDDEN_FIELDS = ("eps_consensus",)

#: Stored as fractions, but quoted in the source as percentages. A quote
#: saying "12.0 per cent" does support an op_margin of 0.120. THE UNIT
#: CONTRACT lives in rules.FRACTION_BANDS and SPEC.md section 2; these are
#: the fields it governs.
PERCENT_FIELDS = tuple(FRACTION_BANDS)

#: Any run of digits with optional thousand separators and decimals,
#: plus any scale word immediately following it.
_NUMBER_RE = re.compile(
    r"(\d[\d.,\u00a0 ]*\d|\d)\s*"
    r"(billion|bn|billions|million|mn|millions|thousand|k)?",
    re.IGNORECASE,
)
_SCALES = {
    "billion": 1e9, "bn": 1e9, "billions": 1e9,
    "million": 1e6, "mn": 1e6, "millions": 1e6,
    "thousand": 1e3, "k": 1e3,
}
#: Reporting units a figure might be expressed in, relative to base units.
_UNITS = (1.0, 1e3, 1e6, 1e9)

PROVENANCE_UNVERIFIABLE = "PROVENANCE UNVERIFIABLE"
UNIT_ERROR = "UNIT ERROR -- RATIO OUT OF BAND"
EXTRACTION_DISAGREEMENT = "EXTRACTION DISAGREEMENT"

#: Claims about the source that are not figures, compared field by field
#: when two runs are reconciled by ``agreement``.
SCALAR_CLAIMS = ("period", "period_basis", "basis", "accounting", "guidance_action")

#: Words that mark a figure as an adjusted measure rather than the
#: reported one. Used only to describe the policy in the prompt; the
#: model reports which measure it took and this module never guesses.
ADJUSTED_WORDS = ("adjusted", "underlying", "like-for-like", "before items",
                  "excluding one-offs", "organic")


def _parsings(token: str) -> list[float]:
    """A token read under both separator conventions.

    Both are tried because "4,120" is 4120 to a US filer and 4.120 to a
    Swedish one, and guessing wrong would reject a perfectly good quote.
    """
    thousands = token.replace(",", "").replace(" ", "").replace("\u00a0", "")
    european = (token.replace(".", "").replace(" ", "")
                .replace("\u00a0", "").replace(",", "."))
    numbers = []
    for variant in (thousands, european):
        try:
            numbers.append(float(variant))
        except ValueError:
            continue
    return numbers


def _whitespace_readings(token: str) -> list[str]:
    """Every way the whitespace inside one number token can be read.

    Whitespace means two different things here and the text does not say
    which. In a Swedish report "4 120" is ONE number -- space is that
    convention's thousands separator. In a statement table flattened to a
    line, "24,371 24,008" is TWO numbers: adjacent period columns with the
    gap between them collapsed. Committing to either reading would reject
    quotes that plainly contain their figure.

    So every reading is offered: each part alone, and any run of parts a
    thousands separator could be joining. A space joins only where the
    part after it is exactly three digits, because three digits is all a
    thousands separator can precede. "4 120 4 265" therefore reads as
    4120 and 4265 -- two columns, Swedish grouping -- or as 4, 120, 4 and
    265, four columns; never as 41204, which is neither.
    """
    parts = [p for p in re.split(r"[\s\u00a0]+", token) if p]
    if len(parts) < 2:
        return []
    readings = []
    for start in range(len(parts)):
        readings.append(parts[start])
        for end in range(start + 2, len(parts) + 1):
            if not re.fullmatch(r"\d{3}", parts[end - 1]):
                break
            readings.append("".join(parts[start:end]))
    return readings


def candidate_numbers(text: str) -> set[float]:
    """Every number a sentence could be stating.

    Every reading is offered -- both separator conventions, and both the
    joined and split readings of whitespace -- because the check this
    feeds asks whether the quote CONTAINS the figure. Which column that
    figure sits in is a separate question, answered by period_column and
    enforced separately.
    """
    found: set[float] = set()
    for raw, scale_word in _NUMBER_RE.findall(text or ""):
        token = raw.strip()
        scale = _SCALES.get((scale_word or "").lower())
        for number in _parsings(token):
            found.add(number)
            # "$90.0 billion" states the same quantity as 90000 millions.
            # Expressing it in every standard unit is a unit conversion,
            # not a reconciliation: a DIFFERENT quantity still fails, so
            # "80.9 billion" never supports 80876.
            if scale:
                base = number * scale
                for unit in _UNITS:
                    found.add(base / unit)
        # The scale word qualifies the whole token -- "1 397 million" is
        # 1397 million, never 397 million -- so it is not applied to the
        # pieces a column gap would leave behind.
        for reading in _whitespace_readings(token):
            found.update(_parsings(reading))
    return found


def figure_supported(value, sentence: str | None, field: str) -> bool:
    """True when the quote actually contains the extracted figure.

    A quote is provenance only if the number is in it. "Inventories" does
    not evidence 1397, and "allowance for doubtful accounts of $1,040 and
    $944" does not evidence 80876 -- a balance-sheet label is not a fact.

    Containment is all this asks. A quoted statement row carries every
    period's column, so any of them satisfies it; WHICH column was read is
    a different question, and parse_response answers it by requiring a
    period_column for a tabular figure. Widening this check to guess at
    columns would put the same claim behind two half-tests instead of one
    whole one.

    An explicit scale word is honoured as a unit conversion: a quote
    saying "$90.0 billion" does support 90000 stated in millions. That is
    not reconciliation -- a DIFFERENT quantity still fails, so "80.9
    billion" never supports 80876. Signs are compared absolutely, since
    "a decrease of 3.4 per cent" states -0.034 without a minus sign.
    """
    if value is None or not sentence:
        return False
    targets = {abs(float(value))}
    if field in PERCENT_FIELDS:
        targets.add(abs(float(value)) * 100.0)
    for candidate in candidate_numbers(sentence):
        for target in targets:
            if math.isclose(abs(candidate), target, rel_tol=1e-6, abs_tol=1e-9):
                return True
    return False

SYSTEM_PROMPT = """You extract figures from company financial releases.

You are a transcriber, not an analyst. Obey exactly:

1. Return ONLY a JSON object. No prose, no markdown, no commentary.

2. SOURCE FIDELITY -- the most important rule. The quote must come from
   WHEREVER YOU READ THE NUMBER. A release states the same figure twice,
   once in a summary sentence and once in a statement table, at different
   precisions. Reporting the table's number while quoting the prose (or
   the reverse) cites two different sources, and the quote then cannot
   evidence the number. Never mix them.

   Read a TABLE ROW:
     - "source_type": "table"
     - quote the ROW ITSELF, INCLUDING THE NUMBER you took
     - "period_column": the exact column heading, verbatim. A statement
       carries two or more period columns and the reader cannot tell
       which you used unless you say.

   Read PROSE:
     - "source_type": "prose"
     - quote the sentence
     - report the number AT THE PROSE'S OWN PRECISION. If the sentence
       says "$90.0 billion", report 90000. Do NOT substitute 90007 from
       the table -- that is a different source.
     - "period_column": null

3. If a figure is NOT EXPLICITLY STATED, return null. Never derive it,
   never estimate it, never reconcile it against another figure, never
   compute it from other numbers. A null is a correct answer.

4. UNITS. A ratio is reported as a FRACTION, never as a percentage.
   "an operating margin of 6.6 per cent" is 0.066. "sales grew 2 per
   cent" is 0.02. "a decrease of 8 per cent" is -0.08. That is a
   transcription of the same quantity into the units this schema uses,
   not a calculation: quote the sentence or the row exactly as written,
   per cent sign and all, and put the fraction in "value".

   FRACTIONS: revenue_yoy, revenue_yoy_organic, op_margin,
   covenant_headroom.
   NOT a fraction: net_debt_ebitda is a multiple, so "2.7x" is 2.7.
   Everything else is in the report's own currency and scale -- if the
   table says "SEK m", then 3,306 is 3306.

4b. THE ORGANIC REVENUE FIGURE, AND IT IS THE ONE EXCEPTION TO RULE 5.

   "revenue_yoy" is the REPORTED year-on-year change in revenue.
   "revenue_yoy_organic" is the company's own ORGANIC / UNDERLYING /
   LIKE-FOR-LIKE year-on-year sales growth, where the report states one.
   Both are wanted, from the same report, side by side.

   WHY BOTH. A company that sells or demerges a business reports lower
   revenue by construction, and so does one whose trading currencies
   weaken. Neither is a loss of demand. The reported figure and the
   organic figure are DIFFERENT FACTS and this schema keeps them apart.

   TAKE IT ONLY WHERE THE REPORT STATES IT, under whatever name the
   company uses -- "underlying sales growth", "organic growth",
   "like-for-like", "comparable growth", "organic net revenue growth".
   Quote that line.

   WHERE THE REPORT STATES NO SUCH FIGURE, THE VALUE IS null. Do not
   derive it, do not strip currency out of the reported figure yourself,
   and never put 0 -- an absent organic figure means the company did not
   disclose one, and 0 would mean it disclosed flat organic growth.
   Those are opposite facts and only one of them is ever true.

5. ADJUSTED versus REPORTED. A report often states the same line twice:
   once adjusted ("adjusted", "underlying", "like-for-like", "before
   items", "excluding one-offs") and once as reported. When both are
   present, TAKE THE UNADJUSTED FIGURE and set "measure": "reported".

   If the report states ONLY an adjusted figure, take it and set
   "measure": "adjusted". Never pass an adjusted number off as a
   reported one -- which of the two you took is itself a fact about the
   source.

   THIS RULE DOES NOT APPLY TO "revenue_yoy_organic", which is by
   definition the underlying figure and has its own field (rule 4b). It
   does apply to "revenue_yoy", which is always the reported one.

   Never mix the two within a quarter. An adjusted margin beside a
   reported operating income describes no single measure of anything,
   and the two will not reconcile.

6. NO OPERATING INCOME LINE? USE EBIT. Some issuers never report
   "Operating income" at all. NIKE is one: its income statement runs
   from Gross profit and overhead straight to "Income before income
   taxes", and its operating profit appears only in a separate
   non-GAAP table at the foot of the release, headed EARNINGS BEFORE
   INTEREST AND TAXES ("EBIT").

   When a release has NO Operating income line but DOES have such a
   table, take the issuer's TOTAL EBIT row as op_income and "EBIT
   margin" as op_margin. The row is labelled either way and both are
   the same line:

       TOTAL NIKE, INC. EARNINGS BEFORE INTEREST AND TAXES
       TOTAL NIKE, INC. EBIT

   Take the TOTAL row, never a segment's EBIT ("TOTAL NIKE BRAND EBIT",
   "Converse", "Corporate") -- those are parts, not the company. Set
   "measure": "adjusted" for both figures: an EBIT presented this way is
   a non-GAAP measure and the release says so in its own footnote.

   NEVER take "Income before income taxes" as op_income. It is struck
   after interest, so it is a different quantity: in NIKE's Q3 FY26 it
   is 650 where EBIT is 635.

   NEVER take "Gross margin" as op_margin. It is a different line
   entirely: 40.2% in that same quarter, where EBIT margin is 5.6%.

   In these tables the row LABEL and its NUMBERS frequently come out on
   two separate lines:

       TOTAL NIKE, INC. EBIT1
       635    826    -23 %    2,529    3,482    -27 %

   Quote BOTH LINES TOGETHER as the sentence. The label alone contains
   no number and evidences nothing; the numbers alone do not say which
   row they came from.

7. EVERY CLAIM NEEDS PROVENANCE, INCLUDING A NEGATIVE ONE. "No guidance
   action was taken" is a claim about the source like any other. If you
   report guidance_action "none", quote the sentence establishing it. If
   you cannot quote one, return null -- not "none".

8. PERIOD. Report "period" as "YYYY-Qn" for a three-month quarter,
   "YYYY-H1" or "YYYY-H2" for a six-month half-year, and "YYYY-FY" for a
   twelve-month full year -- the label must match the span the figures
   cover: a half-year report's "first half" column is "2026-H1", a
   full-year results release's "full year" column is "2025-FY", and a
   quarterly trading statement is "2026-Q1". Set "period_basis" to
   "fiscal" or "calendar", quoting the text that establishes which.
   These are not interchangeable: Microsoft's FISCAL Q4 2026 ended
   30 June 2026, whereas CALENDAR Q4 2026 is October-December 2026.
   Label a fiscal fourth quarter "2026-Q4" with period_basis "fiscal".
   Never invent a label the source does not support.

   A company whose financial year ENDS 31 DECEMBER reports calendar
   quarters, so period_basis is "calendar". Quote the text that shows
   the year end -- "the financial year ended 31 December 2025", a
   full-year report covering January-December, or a Q4 described as
   October-December.

9. State whether figures are "reported" or "constant_currency", and
   "gaap" or "non_gaap". If the release does not say, return null.
   This is a different question from rule 5: "reported" here is about
   currency translation, "measure" there is about adjustments.

10. Never judge materiality. Never say whether anything is good or bad.

11. Never recommend an action.

FIELD NOTE -- class_c_impact

A QUANTIFIED ONE-OFF: a restructuring charge, an impairment, a provision
or the release of one, a settlement, a disposal gain. An item the report
itself separates out as not part of ordinary trading, stated as an
amount, on its own line.

SIGN: record its effect on REPORTED operating profit, with the sign the
statement prints. A charge is NEGATIVE -- SAP's Q1 2024 restructuring
line reads "Restructuring 0 -2,242" and the 2024 figure is -2242. A
release or credit is POSITIVE -- the same line for Q3 2024 reads
"Restructuring 18 52" and the 2024 figure is +52.

Only when the report STATES the amount on a line of its own. Never infer
one from the gap between a reported and an adjusted figure: that gap is a
computation, and it bundles other adjustments in with the one-off.

JSON shape:
{
  "period": {"value": "2026-Q4" or null, "sentence": str or null},
  "period_basis": "fiscal" | "calendar" | null,
  "basis": "reported" | "constant_currency" | null,
  "accounting": "gaap" | "non_gaap" | null,
  "guidance_action": {"value": "raised"|"maintained"|"cut"|"none"|null,
                      "sentence": str or null},
  "figures": {
     "<field>": {"value": number or null,
                 "sentence": str or null,
                 "source_type": "prose" | "table" | null,
                 "period_column": str or null,
                 "measure": "reported" | "adjusted" | null},
     ...
  },
  "exec_changes": [{"role": "CEO"|"CFO"|"other", "departed": "YYYY-MM-DD",
                    "sentence": str}],
  "ambiguities": [str]
}

VALIDATION EXAMPLES

Given this source:

    Revenue was $90.0 billion and increased 18%.

    Three Months Ended June 30,
                                  2026        2025
    Revenue                    $90,007     $76,441
    Inventories                 $1,397      $1,246

CORRECT -- table citation (row quoted, number present, column named):
  "revenue": {"value": 90007,
              "source_type": "table",
              "period_column": "Three Months Ended June 30, 2026",
              "sentence": "Revenue $90,007 $76,441"}

CORRECT -- prose citation (prose precision, prose quoted):
  "revenue": {"value": 90000,
              "source_type": "prose",
              "period_column": null,
              "sentence": "Revenue was $90.0 billion and increased 18%."}

WRONG -- mixes sources. The number is the table's, the quote is the
prose's, so the quote does not contain 90007 and cannot evidence it:
  "revenue": {"value": 90007,
              "source_type": "prose",
              "sentence": "Revenue was $90.0 billion and increased 18%."}

WRONG -- a label is not provenance. The quote contains no number, and
the reader cannot tell which of the two columns was read:
  "inventory": {"value": 1397,
                "source_type": "table",
                "sentence": "Inventories"}

CORRECT -- the same figure, cited properly:
  "inventory": {"value": 1397,
                "source_type": "table",
                "period_column": "Three Months Ended June 30, 2026",
                "sentence": "Inventories $1,397 $1,246"}

CORRECT -- a negative claim, with provenance:
  "guidance_action": {"value": "none",
                      "sentence": "The company did not update its
                                   full-year outlook."}

WRONG -- a negative claim asserted with nothing behind it. Return
{"value": null, "sentence": null} instead:
  "guidance_action": {"value": "none", "sentence": null}

Given this second source:

    Operating profit amounted to SEK 97 m and the operating margin was
    3.1 percent. Adjusted operating profit was SEK 204 m, giving an
    adjusted operating margin of 6.5 percent. Net sales decreased by
    5 percent.

    Net sales, SEK m            3,134   3,301
    Operating margin, %           3.1     8.2

CORRECT -- the unadjusted figure, as a fraction, quoting the prose that
states it:
  "op_margin": {"value": 0.031,
                "source_type": "prose",
                "period_column": null,
                "measure": "reported",
                "sentence": "Operating profit amounted to SEK 97 m and the
                             operating margin was 3.1 percent."}

WRONG -- the adjusted figure taken while the reported one was right
there. 6.5 per cent is a real number in this source, but it is not the
one to take, and nothing in the output would say which was taken:
  "op_margin": {"value": 0.065, "measure": "adjusted",
                "sentence": "adjusted operating margin of 6.5 percent"}

WRONG -- the right figure in the wrong units. A "value" of 3.1 means
three hundred and ten per cent:
  "op_margin": {"value": 3.1, "measure": "reported",
                "sentence": "the operating margin was 3.1 percent"}

CORRECT -- the same figure read from the table instead, still a
fraction, with its column named:
  "op_margin": {"value": 0.031,
                "source_type": "table",
                "period_column": "Q4 2025",
                "measure": "reported",
                "sentence": "Operating margin, % 3.1 8.2"}

CORRECT -- a decline, as a negative fraction:
  "revenue_yoy": {"value": -0.05,
                  "source_type": "prose",
                  "period_column": null,
                  "measure": "reported",
                  "sentence": "Net sales decreased by 5 percent."}

CORRECT -- the two revenue figures side by side, from one report. The
reported line fell and the underlying line rose; both are true and they
are different facts:
  "revenue_yoy": {"value": -0.033,
                  "source_type": "prose",
                  "period_column": "Q1 2026",
                  "measure": "reported",
                  "sentence": "Turnover decreased 3.3%, with currency
                  (4.9)% and disposals (1.2)%."}
  "revenue_yoy_organic": {"value": 0.041,
                  "source_type": "prose",
                  "period_column": "Q1 2026",
                  "measure": "adjusted",
                  "sentence": "Underlying sales growth was 4.1%."}

CORRECT -- the report states no organic figure. ABSENT, NOT ZERO:
  "revenue_yoy_organic": {"value": null,
                  "source_type": null,
                  "period_column": null,
                  "measure": null,
                  "sentence": null}

Fields to attempt: __FIELDS__

Put anything you were unsure about in "ambiguities" -- an unclear unit, a
restated prior period, a figure that could be either basis, a period you
could not confirm as fiscal or calendar. Listing an ambiguity is always
better than resolving it yourself.
""".replace("__FIELDS__", ", ".join(EXTRACTABLE_FIELDS))


class ExtractionError(Exception):
    """Raised when the model cannot be reached or its output is unusable."""


@dataclass(frozen=True)
class Figure:
    value: float | None
    sentence: str | None

    @property
    def stated(self) -> bool:
        return self.value is not None


@dataclass
class Extraction:
    url: str
    model: str
    period: str | None = None
    period_basis: str | None = None
    basis: str | None = None
    accounting: str | None = None
    guidance_action: str | None = None
    figures: dict = field(default_factory=dict)
    sentences: dict = field(default_factory=dict)
    #: Which table column each figure was read from, when tabular.
    period_columns: dict = field(default_factory=dict)
    source_types: dict = field(default_factory=dict)
    #: Figures dropped because the quote did not contain them.
    unverifiable: dict = field(default_factory=dict)
    #: Figures dropped because the value is not in the units the schema
    #: uses -- a percentage where a fraction was asked for.
    out_of_band: dict = field(default_factory=dict)
    #: Which measure each figure was taken from: reported or adjusted.
    measures: dict = field(default_factory=dict)
    #: Fields where two runs of the same source did not agree.
    disagreements: dict = field(default_factory=dict)
    #: Figures both runs agreed on but read from a different place.
    attribution_differences: list = field(default_factory=list)
    #: True when this extraction is the agreement of two runs (--compare).
    compared: bool = False
    proposed_exec_changes: list = field(default_factory=list)
    ambiguities: list = field(default_factory=list)
    issues: list = field(default_factory=list)
    raw_response: str | None = None

    @property
    def uncertain(self) -> bool:
        """Any gap, ambiguity or problem makes the whole extraction uncertain."""
        return bool(self.issues or self.ambiguities) or any(
            v is None for v in self.figures.values()
        ) or self.basis is None or self.accounting is None

    def uncertainty_reasons(self) -> list[str]:
        reasons = list(self.issues)
        reasons += [f"model flagged ambiguity: {a}" for a in self.ambiguities]
        dropped = sorted(self.unverifiable)
        if self.out_of_band:
            reasons.append(
                f"{UNIT_ERROR} -- figure dropped: {', '.join(sorted(self.out_of_band))}"
            )
        if self.disagreements:
            reasons.append(
                f"{EXTRACTION_DISAGREEMENT} -- two runs of one source did not "
                f"agree on: {', '.join(sorted(self.disagreements))}"
            )
        adjusted = sorted(k for k, v in self.measures.items() if v == "adjusted")
        if adjusted:
            reasons.append(
                f"taken from an ADJUSTED measure, not the reported one: "
                f"{', '.join(adjusted)}"
            )
        missing = sorted(
            k for k, v in self.figures.items() if v is None and k not in self.unverifiable
        )
        if dropped:
            reasons.append(
                f"{PROVENANCE_UNVERIFIABLE} -- figure dropped: {', '.join(dropped)}"
            )
        if missing:
            reasons.append(f"not stated in source: {', '.join(missing)}")
        if self.basis is None:
            reasons.append("basis (reported vs constant-currency) not stated")
        if self.accounting is None:
            reasons.append("accounting (GAAP vs non-GAAP) not stated")
        return reasons


#: Prefixed to the source text when a period is named. A figure can be
#: stated in a document that is ABOUT another quarter -- SAP's Q2 2024
#: restructuring appears in the Q2 2025 statement's comparative column and
#: nowhere in the Q2 2024 release, because the line was not broken out at
#: the time. Reading it there and recording THAT document as the source is
#: more honest than attributing it to a release that does not contain it.
TARGET_PERIOD_INSTRUCTION = """TARGET PERIOD: {period}

Extract figures for {period} and for no other period.

{period} may be this document's OWN period, or it may appear only as a
COMPARATIVE column in a document about a later period. Read whichever
column is {period}. Read no other. A label names a span: YYYY-Qn is a
three-month quarter, YYYY-H1/H2 a six-month half-year, YYYY-FY a full
year -- read the column covering exactly that span.

  - Set "period" to {period}.
  - "period_column" must name the column you read, exactly as the
    document heads it, so a reader can see which one was taken.
  - Quote the row containing the number you took, as always. The row
    holds several periods; the quote shows the number, the column says
    which one it is.
  - If a figure is not stated for {period} anywhere in this document,
    return null. NEVER report another period's figure under this label --
    a neighbouring column is a different period, and that is the worst
    error available to you.

The source document follows.

----------------------------------------------------------------------

"""


def build_request(text: str, model: str, target_period: str | None = None) -> dict:
    content = text
    if target_period:
        content = TARGET_PERIOD_INSTRUCTION.format(period=target_period) + text
    return {
        "model": model,
        "temperature": 0,
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": content},
        ],
    }


def call_openrouter(text: str, *, model=None, api_key=None, transport=None,
                    target_period=None) -> str:
    """POST to OpenRouter and return the raw assistant message."""
    model = model or env.get(MODEL_ENV, DEFAULT_MODEL)
    api_key = api_key or env.get(KEY_ENV)
    if not api_key:
        raise ExtractionError(
            f"no API key: set {KEY_ENV} in the environment. vss never embeds keys."
        )

    payload = json.dumps(build_request(text, model, target_period)).encode("utf-8")
    request = urllib.request.Request(
        API_URL,
        data=payload,
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
    )
    try:
        opener = transport or urllib.request.urlopen
        with opener(request, timeout=TIMEOUT_SECONDS) as response:
            body = json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        detail = ""
        try:
            detail = exc.read().decode("utf-8", errors="replace")[:400]
        except Exception:
            pass
        raise ExtractionError(
            f"OpenRouter HTTP {exc.code} for model {model!r}: {detail}"
        ) from exc
    except Exception as exc:
        raise ExtractionError(f"{type(exc).__name__} calling OpenRouter: {exc}") from exc

    try:
        return body["choices"][0]["message"]["content"]
    except (KeyError, IndexError, TypeError) as exc:
        raise ExtractionError(f"unexpected OpenRouter response shape: {body}") from exc


#: The scalar claims, and the vocabulary each one is allowed.
CLAIM_VOCABULARY = {
    "basis": VALID_BASIS,
    "accounting": VALID_ACCOUNTING,
    "period_basis": VALID_PERIOD_BASIS,
    "guidance_action": VALID_GUIDANCE_ACTIONS,
}


def _claim(raw) -> tuple[str | None, str | None]:
    """Read a scalar claim in either shape the model sends it in.

    The schema asks for a bare "gaap", but a model that has just written
    several {"value": ..., "sentence": ...} nodes sometimes sends a
    seventh. The two say the same thing, and understanding only one shape
    turns a stylistic difference into a lost field: --compare found
    exactly that, nulling three correct claims about one Lindab quarter
    because one run wrapped them and the other did not.

    Returns (value, sentence). The sentence is a bonus when the node
    form carries one -- provenance for a claim that otherwise has none.
    """
    if isinstance(raw, dict):
        value, sentence = raw.get("value"), raw.get("sentence")
    else:
        value, sentence = raw, None
    if not isinstance(value, str) or not value.strip():
        return None, None
    return value.strip().lower(), (sentence or None)


def _coerce_float(value):
    if value is None or isinstance(value, bool):
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def parse_response(raw: str, url: str, model: str) -> Extraction:
    """Turn the model's JSON into an Extraction. Never raises on bad data."""
    result = Extraction(url=url, model=model, raw_response=raw)

    body = raw.strip()
    if body.startswith("```"):
        body = body.split("```")[1] if "```" in body[3:] else body[3:]
        body = body.split("\n", 1)[-1] if body.lower().startswith("json") else body
    try:
        data = json.loads(body)
    except json.JSONDecodeError as exc:
        result.issues.append(f"model did not return valid JSON: {exc}")
        result.figures = {f: None for f in EXTRACTABLE_FIELDS}
        return result
    if not isinstance(data, dict):
        result.issues.append("model returned JSON that is not an object")
        result.figures = {f: None for f in EXTRACTABLE_FIELDS}
        return result

    leaked = [f for f in FORBIDDEN_FIELDS if f in json.dumps(data)]
    if leaked:
        # Consensus is manual only. If it appears, discard it and say so.
        result.issues.append(
            f"model returned forbidden field(s) {', '.join(leaked)} -- discarded; "
            f"consensus is MANUAL ONLY and is never extracted"
        )

    def _node(value):
        return value if isinstance(value, dict) else {}

    period = _node(data.get("period"))
    result.period = period.get("value") if period.get("value") else None
    result.period_basis, period_basis_sentence = _claim(data.get("period_basis"))
    if period_basis_sentence:
        result.sentences["period_basis"] = period_basis_sentence
    if result.period and result.period_basis is None:
        result.issues.append(
            f"period {result.period!r} reported without period_basis -- a fiscal "
            f"Q4 and a calendar Q4 are different periods and the label alone "
            f"does not say which"
        )
    for name in ("basis", "accounting"):
        value, sentence = _claim(data.get(name))
        setattr(result, name, value)
        if sentence:
            result.sentences[name] = sentence

    guidance = _node(data.get("guidance_action"))
    guidance_value, guidance_sentence = _claim(data.get("guidance_action"))
    guidance_sentence = guidance_sentence or guidance.get("sentence") or None
    # "No guidance action" is a claim about the source like any other. An
    # unquoted "none" is indistinguishable from the model not looking.
    if guidance_value is not None and not guidance_sentence:
        result.issues.append(
            f"guidance_action {guidance_value!r} reported with no quote -- a claim "
            f"about the source needs provenance, including a negative one. "
            f"Set to null."
        )
        result.unverifiable["guidance_action"] = {
            "value": guidance_value, "sentence": None
        }
        guidance_value = None
    result.guidance_action = guidance_value
    if guidance_sentence:
        result.sentences["guidance_action"] = guidance_sentence

    # A claim the loader would reject is not a claim to propose: "ifrs"
    # is a real answer to "gaap or non_gaap?" and an invalid watchlist
    # value. Dropped here, where it can still be explained.
    for name, allowed in CLAIM_VOCABULARY.items():
        value = result.guidance_action if name == "guidance_action" else getattr(result, name)
        if value is None or value in allowed:
            continue
        result.issues.append(
            f"{name} reported as {value!r}, which is not one of "
            f"{'|'.join(allowed)}. Set to null."
        )
        if name == "guidance_action":
            result.guidance_action = None
        else:
            setattr(result, name, None)

    figures = _node(data.get("figures"))
    for name in EXTRACTABLE_FIELDS:
        node = _node(figures.get(name))
        value = _coerce_float(node.get("value"))
        sentence = node.get("sentence") or None
        source_type = node.get("source_type") or None
        column = node.get("period_column") or None
        measure = node.get("measure") or None

        # A quote that does not contain the number is not provenance.
        # Drop the figure rather than carry an unverifiable one forward.
        if value is not None and not figure_supported(value, sentence, name):
            result.issues.append(
                f"{PROVENANCE_UNVERIFIABLE}: {name} reported as {value} but the "
                f"quoted sentence does not contain that figure -- "
                f"{(sentence or 'no sentence given')!r}. Field set to null."
            )
            result.unverifiable[name] = {"value": value, "sentence": sentence}
            value = None

        # A ratio outside its band is in the wrong units -- a percentage
        # where the schema says fraction. It is NOT scaled to fit: 6.6
        # could be 6.6% misreported or a genuine 660%, and picking one
        # would be this module deciding what the source said. Dropped and
        # named, exactly like an unevidenced figure.
        low_high = FRACTION_BANDS.get(name)
        if value is not None and low_high and not (low_high[0] <= value <= low_high[1]):
            result.issues.append(
                f"{UNIT_ERROR}: {name} reported as {value:g}, outside "
                f"[{low_high[0]:g}, {low_high[1]:g}]. Ratios are fractions -- "
                f"{value:g} per cent is {value / 100:g}. Field set to null."
            )
            result.out_of_band[name] = {"value": value, "sentence": sentence}
            value = None

        if measure:
            result.measures[name] = measure
        # Policy is the unadjusted figure (SPEC.md section 2). An adjusted
        # one is kept -- some reports state nothing else -- but it is not
        # the measure 4.2 was written against, so it is said out loud.
        if value is not None and measure == "adjusted":
            result.issues.append(
                f"{name} was taken from an ADJUSTED measure. FRAMEWORK 4.2 is "
                f"written against the reported figure; verify whether the "
                f"source states one."
            )

        result.figures[name] = value
        if sentence:
            result.sentences[name] = sentence
        if source_type:
            result.source_types[name] = source_type
        if column:
            result.period_columns[name] = column
        # A balance-sheet figure with no column named is not attributable.
        if value is not None and source_type == "table" and column is None:
            result.issues.append(
                f"{name} was read from a table but no period_column was recorded -- "
                f"the source has more than one period column and this figure "
                f"cannot be attributed to one"
            )

    for name in FORBIDDEN_FIELDS:
        result.figures.pop(name, None)
        result.sentences.pop(name, None)

    for item in data.get("exec_changes") or []:
        if isinstance(item, dict) and item.get("role") and item.get("departed"):
            result.proposed_exec_changes.append(
                {"role": str(item["role"]), "departed": str(item["departed"]),
                 "sentence": item.get("sentence")}
            )
    result.ambiguities = [str(a) for a in (data.get("ambiguities") or [])]
    return result


def agreement(first: Extraction, second: Extraction) -> Extraction:
    """Keep only what two runs of the same source agree on.

    Two readings that disagree are not a figure. The value is dropped and
    both readings are reported, exactly as an unevidenced one is. The
    point of reading twice is to find where the model is guessing, and a
    guess that survives because it was made first is worse than a blank:
    a blank says DATA MISSING, where the guess says nothing at all.

    Values and claims are compared; quotes are not. Two runs may cite the
    same figure from the summary and from the statement and both be
    right. Where they agree on a figure but name a different column or a
    different measure for it, that is reported without dropping the
    value -- the number is corroborated, its attribution is not.
    """
    merged = Extraction(url=first.url, model=first.model, compared=True)
    merged.raw_response = "\n\n----- SECOND RUN -----\n\n".join(
        r for r in (first.raw_response, second.raw_response) if r
    ) or None

    for name in SCALAR_CLAIMS:
        mine, theirs = getattr(first, name), getattr(second, name)
        if mine == theirs:
            setattr(merged, name, mine)
            continue
        merged.disagreements[name] = {"first": mine, "second": theirs}
        merged.issues.append(
            f"{EXTRACTION_DISAGREEMENT}: {name} read as {mine!r} on the first "
            f"run and {theirs!r} on the second. Set to null."
        )

    for name in sorted(set(first.figures) | set(second.figures)):
        mine, theirs = first.figures.get(name), second.figures.get(name)
        if mine == theirs:
            merged.figures[name] = mine
        else:
            merged.figures[name] = None
            merged.disagreements[name] = {"first": mine, "second": theirs}
            merged.issues.append(
                f"{EXTRACTION_DISAGREEMENT}: {name} read as {mine} on the first "
                f"run and {theirs} on the second. Set to null."
            )

    for label, attribute in (("column", "period_columns"), ("measure", "measures")):
        mine, theirs = getattr(first, attribute), getattr(second, attribute)
        for name in sorted(set(mine) & set(theirs)):
            if mine[name] != theirs[name] and merged.figures.get(name) is not None:
                merged.attribution_differences.append({
                    "field": name, "kind": label,
                    "value": merged.figures[name],
                    "first": mine[name], "second": theirs[name],
                })
                merged.issues.append(
                    f"{EXTRACTION_DISAGREEMENT}: the runs agree that {name} is "
                    f"{merged.figures[name]} but took it from a different "
                    f"{label} -- {mine[name]!r} then {theirs[name]!r}. The "
                    f"figure stands; its attribution does not."
                )

    # The first run's provenance describes the figures that survived; the
    # second run's drops are carried too, so nothing goes unexplained.
    for attribute in ("sentences", "period_columns", "source_types", "measures",
                      "unverifiable", "out_of_band"):
        combined = dict(getattr(second, attribute))
        combined.update(getattr(first, attribute))
        setattr(merged, attribute, combined)

    for attribute in ("issues", "ambiguities", "proposed_exec_changes"):
        seen = list(getattr(merged, attribute))
        for item in list(getattr(first, attribute)) + list(getattr(second, attribute)):
            if item not in seen:
                seen.append(item)
        setattr(merged, attribute, seen)
    return merged


def extract(source, *, model=None, api_key=None, transport=None,
            target_period=None) -> Extraction:
    """Full extraction. Network failure yields an UNCERTAIN result, not a crash."""
    model = model or env.get(MODEL_ENV, DEFAULT_MODEL)
    try:
        raw = call_openrouter(source.text, model=model, api_key=api_key,
                              transport=transport, target_period=target_period)
    except ExtractionError as exc:
        result = Extraction(url=source.url, model=model)
        result.issues.append(str(exc))
        result.figures = {f: None for f in EXTRACTABLE_FIELDS}
        return result
    return parse_response(raw, source.url, model)
