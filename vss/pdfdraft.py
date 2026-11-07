"""LLM pre-fill from PDF pages -- HANDOFF 2026-11-07 part B.

For the names ESEF does not reach: First North issuers (an MTF; Zinzino),
interim reports, figures only a PDF prints. A model reads a FEW pages and
proposes statement lines; deterministic gates decide what survives, and
what survives is a DRAFT (decision (a)), every figure UNVERIFIED, which E149
forbids the machine read-back to verify.

THE STEPS:

1. `source.pdf_pages` -- the report page by page.
2. `locate` -- a deterministic locator scores pages by statement headings in
   en, sv, fi, da and no, prefers the group over the parent company, and
   only the top pages go to the model.
3. The model returns, per field, the value AS PRINTED, the verbatim row, the
   verbatim column header, the verbatim unit sentence and the PDF page. It is
   asked twice (`extract.agreement`'s pattern): a value the two runs do not
   agree on is dropped.
4. THE GATES, each failure drops the field to DATA MISSING:
   - the row is on the page it names (`quotecheck.find_quote` EXACT or NEAR)
     and the value is among the row's numbers (`quotecheck.value_in`);
   - the column header is on that page and names the TARGET period: its year,
     and for a quarter that quarter's span, never a year-to-date one;
   - the unit sentence is on that same page; the file's money unit is the
     one it states (nothing is rescaled: the figure stays as printed and the
     draft declares the unit); a field in a minority unit is dropped;
   - `config.unit_problem` on revenue / operating income vs the stated margin;
   - one scale (`manual.parse_manual` on the draft, which runs
     `_check_one_scale`);
   - no zero (E25's zero_basis is a human claim), an outflow must be printed
     as one (never sign-flipped), and no judgement field is asked for.
5. Origin `llm-pdf`; a sidecar run record beside the draft holds the model
   id, the PDF's digest, the pages sent and the SHA-256 of both raw
   responses.
"""

from __future__ import annotations

import hashlib
import json
import re
import urllib.request
from dataclasses import dataclass, field
from datetime import date, datetime
from pathlib import Path
from typing import Any

from . import env
from . import extract as X
from . import quotecheck as Q
from . import source as S

DRAFTS_DIR = Path("config/manual/drafts")
ORIGIN = "llm-pdf"

#: Statement lines only -- a subset of `manual.FIELDS`. No judgement field
#: (interest_source, lease classification, not_presented, bound) and no
#: share count (its unit is a second question). `op_margin` is asked for
#: only to run the unit check; it is never drafted.
FIELDS: dict[str, str] = {
    "revenue": "net sales / revenue for the period (the top line; total revenue if that is the only line)",
    "operating_income": "operating profit / EBIT for the period, as stated (not adjusted)",
    "net_income": "profit for the period attributable to the parent's shareholders (else profit for the period)",
    "operating_cash_flow": "cash flow from operating activities (after changes in working capital)",
    "capex_ppe": "investments in / acquisition of property, plant and equipment (cash flow statement)",
    "capex_intangibles": "investments in / acquisition of intangible assets (cash flow statement)",
    "lease_payments_capital": "amortisation / repayment of lease liabilities (financing activities)",
    "cash_and_equivalents": "cash and cash equivalents at the end of the period (balance sheet)",
    "total_equity": "total equity at the end of the period (balance sheet)",
    "total_assets": "total assets at the end of the period (balance sheet)",
    "diluted_eps": "earnings per share after dilution for the period",
    "op_margin": "operating margin for the period in per cent, ONLY if printed",
}
CHECK_ONLY = ("op_margin",)
PER_SHARE = ("diluted_eps",)
#: Printed as outflows; a positive print is not flipped, it is dropped.
OUTFLOWS = ("capex_ppe", "capex_intangibles", "lease_payments_capital")

# --- 2. the locator ------------------------------------------------------------

HEADINGS: dict[str, tuple[str, ...]] = {
    "income": ("income statement", "statement of comprehensive income", "comprehensive profit/loss",
               "statement of profit or loss", "profit and loss", "resultaträkning",
               "tuloslaskelma", "resultatregnskap", "resultatopgørelse", "totalresultat"),
    "balance": ("balance sheet", "financial position", "balansräkning",
                "taseen", "tase ", "balanse", "balansen"),
    "cash": ("cash flow", "cash flows", "kassaflöde", "rahavirtalaskelma", "rahoituslaskelma",
             "kontantstrøm", "pengestrøm"),
}
GROUP_WORDS = ("consolidated", "group", "koncern", "konsern", "konserni", "koncernens")
PARENT_WORDS = ("parent company", "moderbolag", "emoyhtiö", "morselskap", "modervirksomhed",
                "moderselskab")
PAGES_PER_STATEMENT = 1


def _score(text: str, kind: str) -> int:
    low = text.lower()
    head = low[:400]
    # a statement page is mostly numbers; a page of prose is never one
    digits = sum(c.isdigit() for c in low)
    if digits < 0.08 * max(len(low), 1):
        return 0
    score = 0
    for h in HEADINGS[kind]:
        if h in head:
            score += 3
        elif h in low:
            score += 1
    if not score:
        return 0
    if any(w in head for w in GROUP_WORDS):
        score += 2
    if any(w in head for w in PARENT_WORDS):
        score -= 5
    if digits > 0.15 * max(len(low), 1):
        score += 2
    return score


def locate(pages: list[tuple[int, str, str]]) -> list[int]:
    """The pdf indices to send: the best page per statement, in page order."""
    picked: set[int] = set()
    for kind in HEADINGS:
        ranked = sorted(((_score(t, kind), i) for i, _, t in pages), key=lambda x: (-x[0], x[1]))
        for sc, i in ranked[:PAGES_PER_STATEMENT]:
            if sc > 0:
                picked.add(i)
    return sorted(picked)


# --- 3. the model --------------------------------------------------------------

SYSTEM_PROMPT = """You copy figures out of a company report's financial statement pages.

You get a TARGET PERIOD and a few pages, each headed "=== PAGE <n> ===".
For each requested field, find the line on the page and the column for the
TARGET PERIOD exactly (for a quarter: that quarter's three months, never a
year-to-date or twelve-month column; for a full year: that year).

Return ONLY a JSON object: {"fields": {<field>: <entry or null>}}. An entry is
  {"value": <the number exactly as printed in that cell: same digits, same
             sign (a minus or parentheses means negative), NO scaling>,
   "row": "<the whole row as printed on the page, verbatim>",
   "column": "<the column header as printed, verbatim>",
   "unit": "<the sentence or caption on that page stating the unit, verbatim,
            e.g. 'Amounts in SEK thousands'>",
   "page": <the page number n>}
Use null where the field is not printed for the target period. Never compute,
add, convert or infer a figure. Never use a figure from another column."""


def build_request(pages_text: str, model: str, target: str) -> dict:
    asked = "\n".join(f"- {k}: {v}" for k, v in FIELDS.items())
    return {"model": model, "temperature": 0,
            "messages": [{"role": "system", "content": SYSTEM_PROMPT},
                         {"role": "user", "content": f"TARGET PERIOD: {target}\n\nFIELDS:\n{asked}\n\n{pages_text}"}]}


def call_model(pages_text: str, *, target: str, model: str, api_key: str | None = None,
               transport=None) -> str:
    """One POST to the same endpoint `extract.call_openrouter` uses."""
    api_key = api_key or env.get(X.KEY_ENV)
    if not api_key:
        raise X.ExtractionError(f"no API key: set {X.KEY_ENV}. vss never embeds keys.")
    payload = json.dumps(build_request(pages_text, model, target)).encode("utf-8")
    request = urllib.request.Request(X.API_URL, data=payload, headers={
        "Authorization": f"Bearer {api_key}", "Content-Type": "application/json"})
    try:
        opener = transport or urllib.request.urlopen
        with opener(request, timeout=X.TIMEOUT_SECONDS) as response:
            body = json.loads(response.read().decode("utf-8"))
        return body["choices"][0]["message"]["content"]
    except Exception as exc:  # noqa: BLE001 -- reported, never swallowed
        raise X.ExtractionError(f"{type(exc).__name__} calling the model: {exc}") from exc


def number(v) -> float | None:
    """The model's value as a number: a JSON number, or a string printed
    with thousands groups ("881,712", "1 079 808") or a decimal comma with
    one or two decimals ("1,80"). Anything else is not a number -- and a
    misreading is caught again when the value must be found in the row."""
    if isinstance(v, bool):
        return None
    if isinstance(v, (int, float)):
        return float(v)
    if not isinstance(v, str):
        return None
    t = v.strip().replace("\u2212", "-").replace("\u2013", "-").replace("\xa0", " ").replace("\u202f", " ")
    neg = t.startswith("(") and t.endswith(")")
    t = t.strip("()").replace(" ", "")
    if re.fullmatch(r"-?\d{1,3}(,\d{3})+(\.\d+)?", t):
        t = t.replace(",", "")
    elif re.fullmatch(r"-?\d+,\d{1,2}", t):
        t = t.replace(",", ".")
    elif not re.fullmatch(r"-?\d+(\.\d+)?", t):
        return None
    x = float(t)
    return -x if neg else x


def parse_reply(raw: str) -> dict[str, dict | None]:
    text = raw.strip()
    m = re.search(r"\{.*\}", text, re.S)
    if not m:
        raise X.ExtractionError("the reply holds no JSON object")
    data = json.loads(m.group(0))
    got = data.get("fields") if isinstance(data, dict) else None
    if not isinstance(got, dict):
        raise X.ExtractionError("the reply has no 'fields' object")
    return {k: (v if isinstance(v, dict) else None) for k, v in got.items() if k in FIELDS}


# --- 4. the gates ----------------------------------------------------------------

QUARTER_SPANS = {1: ((1, 1), (3, 31)), 2: ((4, 1), (6, 30)), 3: ((7, 1), (9, 30)), 4: ((10, 1), (12, 31))}
MONTHS = {m: i + 1 for i, names in enumerate((
    ("jan", "januari", "january", "tammi"), ("feb", "februari", "february", "helmi"),
    ("mar", "mars", "march", "maalis"), ("apr", "april", "huhti"), ("may", "maj", "touko"),
    ("jun", "juni", "june", "kesä"), ("jul", "juli", "july", "heinä"), ("aug", "augusti", "august", "elo"),
    ("sep", "sept", "september", "syys"), ("oct", "okt", "oktober", "october", "loka"),
    ("nov", "november", "marras"), ("dec", "dek", "december", "joulu"))) for m in names}
_DATE_RE = re.compile(r"\b(\d{1,2})[./](\d{1,2})[./](20\d\d)\b|\b(20\d\d)-(\d{2})-(\d{2})\b")


def target_bounds(target: str) -> tuple[date, date]:
    m = re.fullmatch(r"(20\d\d)-(Q[1-4]|FY)", target)
    if not m:
        raise ValueError(f"target period {target!r} is not YYYY-Qn or YYYY-FY")
    y = int(m.group(1))
    if m.group(2) == "FY":
        return date(y, 1, 1), date(y, 12, 31)
    (sm, sd), (em, ed) = QUARTER_SPANS[int(m.group(2)[1])]
    return date(y, sm, sd), date(y, em, ed)


#: Balance-sheet lines: their column is the period's END DATE, not a span.
INSTANT = ("cash_and_equivalents", "total_equity", "total_assets")


def column_names_target(column: str, target: str, *, instant: bool = False) -> str | None:
    """None when the header names the target period; else why not. An
    instant (balance-sheet) column must name the period's end date and no
    other date."""
    start, end = target_bounds(target)
    if str(end.year) not in column:
        return f"the column {column!r} does not carry the year {end.year}"
    low = column.lower()
    dates = []
    for g in _DATE_RE.findall(column):
        try:
            dates.append(date(int(g[2]), int(g[1]), int(g[0])) if g[2] else date(int(g[3]), int(g[4]), int(g[5])))
        except ValueError:
            continue
    if instant:
        if dates:
            return None if set(dates) == {end} else f"the column dates {sorted(set(dates))} are not {end}"
        months = [MONTHS[w] for w in re.findall(r"[a-zäöå]+", low) if w in MONTHS]
        days = [int(d) for d in re.findall(r"\b(\d{1,2})\b", low)]
        if months == [end.month] and (not days or end.day in days):
            return None
        return f"the column {column!r} does not name {end}"
    if len(dates) >= 2:
        if (min(dates), max(dates)) == (start, end):
            return None
        return f"the column spans {min(dates)}..{max(dates)}, not {start}..{end}"
    months = [MONTHS[w] for w in re.findall(r"[a-zäöå]+", low) if w in MONTHS]
    if len(months) >= 2:
        if (months[0], months[-1]) == (start.month, end.month):
            return None
        return f"the column names months {months[0]}..{months[-1]}, not {start.month}..{end.month}"
    if target.endswith("FY"):
        if re.search(r"\b(q[1-4]|h[12]|[1-9]m)\b|quarter|kvartal|neljännes|half|halvår", low):
            return f"the column {column!r} is not a full year"
        return None
    q = target[-1]
    if re.search(rf"\bq{q}\b", low) or re.search(rf"\b{q}q\b", low):
        return None
    return f"the column {column!r} does not name {target}"


UNIT_WORDS = (
    (r"\b(thousands?|tkr|tsek|teur|tnok|tdkk|ksek|keur|'000|000s)\b|tusen|tuhatta|tusinde", "thousands"),
    (r"\b(millions?|mkr|msek|meur|mnok|mdkk|mln|meur|sek ?m|eur ?m|nok ?m|dkk ?m|m€|€m)\b|miljoner|miljoonaa|millioner", "millions"),
    (r"\b(billions?|mdkr|bn)\b|miljarder", "billions"),
)


def unit_of(sentence: str) -> str | None:
    low = (sentence or "").lower()
    hits = {u for pat, u in UNIT_WORDS if re.search(pat, low)}
    return hits.pop() if len(hits) == 1 else None


def _page_doc(idx: int, text: str) -> Q.Doc:
    return Q.Doc(f"page {idx}", text, Q._flat(text), Q._spaced(text),
                 Q._flat(re.sub(r"-[ \t]*\n\s*", "", text)))


@dataclass
class Gated:
    figures: dict = field(default_factory=dict)    # field -> entry (kept)
    dropped: dict = field(default_factory=dict)    # field -> reason
    money_unit: str | None = None


def gate(entries: dict[str, dict | None], pages: dict[int, tuple[str, str]], target: str,
         *, require_unit: bool = True) -> Gated:
    out = Gated()
    units: dict[str, str] = {}
    for name, e in entries.items():
        if e is None:
            continue
        value = number(e.get("value"))
        if value is None:
            out.dropped[name] = f"{e.get('value')!r} is not a number"
            continue
        idx = e.get("page")
        if not isinstance(idx, int) or idx not in pages:
            out.dropped[name] = f"page {idx!r} was not among the pages sent"
            continue
        doc = _page_doc(idx, pages[idx][1])
        row, column, unit = (str(e.get(k) or "") for k in ("row", "column", "unit"))
        if not row or Q.find_quote(row, doc) not in (Q.EXACT, Q.NEAR):
            out.dropped[name] = f"the row is not on page {idx}"
            continue
        if not Q.value_in(value, [row]):
            out.dropped[name] = f"{value:g} is not among the row's numbers"
            continue
        if not column or Q.find_quote(column, doc) not in (Q.EXACT, Q.NEAR):
            out.dropped[name] = f"the column header is not on page {idx}"
            continue
        why = column_names_target(column, target, instant=name in INSTANT)
        if why:
            out.dropped[name] = why
            continue
        if name in CHECK_ONLY:
            out.figures[name] = {**e, "value": value}
            continue
        if value == 0:
            out.dropped[name] = "zero; a zero is never machine-emitted"
            continue
        if name in OUTFLOWS and value > 0:
            out.dropped[name] = "an outflow printed positive; the sign is not flipped"
            continue
        if name not in PER_SHARE and require_unit:
            if not unit or Q.find_quote(unit, doc) not in (Q.EXACT, Q.NEAR):
                out.dropped[name] = f"the unit sentence is not on page {idx}"
                continue
            u = unit_of(unit)
            if u is None:
                out.dropped[name] = f"the unit sentence {unit!r} states no one scale"
                continue
            units[name] = u
        out.figures[name] = {**e, "value": value}
    if units:
        counts: dict[str, int] = {}
        for u in units.values():
            counts[u] = counts.get(u, 0) + 1
        main = max(counts, key=lambda u: (counts[u], u))
        if list(counts.values()).count(counts[main]) > 1:
            for n in units:
                out.figures.pop(n, None)
                out.dropped[n] = f"the pages state more than one unit {sorted(counts)}; not chosen between"
        else:
            out.money_unit = main
            for n, u in units.items():
                if u != main:
                    out.figures.pop(n, None)
                    out.dropped[n] = f"stated in {u}, the rest in {main}"
    # the unit check: revenue / operating income against the stated margin
    from .config import unit_problem
    margin = out.figures.pop("op_margin", None)
    if margin is not None and "revenue" in out.figures and "operating_income" in out.figures:
        problem = unit_problem({"revenue": out.figures["revenue"]["value"],
                                "op_income": out.figures["operating_income"]["value"],
                                "op_margin": margin["value"] / 100})
        if problem:
            for n in ("revenue", "operating_income"):
                out.figures.pop(n, None)
                out.dropped[n] = f"unit check: {problem}"
    return out


# --- 5. the run and the draft ---------------------------------------------------

def _num(v: float) -> str:
    return str(int(v)) if float(v).is_integer() else repr(float(v))


def _q(text: str) -> str:
    return '"' + str(text).replace("\\", "\\\\").replace('"', '\\"').replace("\n", " ") + '"'


@dataclass
class Run:
    gated: Gated
    disagreements: dict
    record: dict


def run(pdf: Path, *, ticker: str, target: str, model: str | None = None,
        api_key: str | None = None, transport=None, now: datetime | None = None,
        require_unit: bool = True) -> Run:
    """``require_unit=False`` is for a COMPARISON ONLY (E151's second
    reading): the printed digits are compared with another source's printed
    digits and no figure is ever written from this reading."""
    pdf = Path(pdf)
    raw = pdf.read_bytes()
    pages = S.pdf_pages(raw, where=str(pdf))
    picked = locate(pages)
    if not picked:
        raise X.ExtractionError(f"{pdf.name}: no statement page found by the locator")
    by_idx = {i: (lab, t) for i, lab, t in pages}
    text = "\n\n".join(f"=== PAGE {i} ===\n{by_idx[i][1]}" for i in picked)
    model = model or env.get(X.MODEL_ENV, X.DEFAULT_MODEL)
    replies = [call_model(text, target=target, model=model, api_key=api_key, transport=transport)
               for _ in range(2)]
    first, second = (parse_reply(r) for r in replies)
    agreed, disagreements = {}, {}
    for name in FIELDS:
        a, b = first.get(name), second.get(name)
        va = number(a.get("value")) if a else None
        vb = number(b.get("value")) if b else None
        if va is None and vb is None:
            continue
        if va != vb:
            disagreements[name] = {"first": va, "second": vb}
            continue
        agreed[name] = a
    gated = gate(agreed, {i: by_idx[i] for i in picked}, target, require_unit=require_unit)
    for name, d in disagreements.items():
        gated.dropped[name] = f"the two runs disagree: {d['first']!r} then {d['second']!r}"
    record = {
        "ticker": ticker, "target_period": target, "origin": ORIGIN, "model": model,
        "pdf": f"sources/{pdf.name}", "pdf_sha256": hashlib.sha256(raw).hexdigest(),
        "pages_sent": [{"pdf_index": i, "printed": by_idx[i][0]} for i in picked],
        "responses_sha256": [hashlib.sha256(r.encode("utf-8")).hexdigest() for r in replies],
        "run_at": (now or datetime.now().astimezone()).isoformat(timespec="seconds"),
        "kept": sorted(gated.figures), "dropped": gated.dropped,
    }
    return Run(gated=gated, disagreements=disagreements, record=record)


def draft_yaml(ticker: str, name: str, currency: str, result: Run, *, pdf: Path,
               target: str, run_ts: datetime) -> str:
    g = result.gated
    if not g.figures:
        raise X.ExtractionError(f"{ticker} {target}: no figure survived the gates")
    start, end = target_bounds(target)
    out = [f"# {ticker} -- DRAFT from a model's reading of PDF pages. NOT the live store.",
           "#",
           f"# GENERATED by `vss pdfdraft` on {run_ts.isoformat(timespec='seconds')}: model "
           f"{result.record['model']}, read twice;",
           f"# sidecar run record {ticker}.llm-pdf.run.json. Every figure passed the gates in",
           "# vss/pdfdraft.py and is UNVERIFIED; E149: only the owner verifies.",
           f"# Merge with `vss manual --merge-draft --ticker {ticker} --origin llm-pdf`.",
           "",
           f"ticker: {ticker}", f"name: {_q(name)}", f"reporting_currency: {currency}",
           f"money_unit: {g.money_unit or 'whole'}   # as the unit sentence on the page states it",
           "share_unit: whole", f"origin: {ORIGIN}", ""]
    doc = f"{pdf.name} (sha256 {result.record['pdf_sha256']}), sources/{pdf.name}"
    figs = []
    for fname in FIELDS:
        e = g.figures.get(fname)
        if not e:
            continue
        page = (f"LLM-PDF p.{e['page']}, row '{e['row']}', column '{e['column']}'"
                + (f", unit '{e['unit']}'" if fname not in PER_SHARE else ""))
        figs += [f"      {fname}:", f"        value: {_num(e['value'])}",
                 f"        source: {_q(f'llm-pdf: sources/{pdf.name}')}",
                 f"        page: {_q(page)}", "        status: UNVERIFIED"]
    if target.endswith("FY"):
        out += ["annual:", f"  - fiscal_year: {end.year}", f"    period_end: {end.isoformat()}"]
    else:
        out += ["periods:", f"  - period: {target}", f"    period_end: {end.isoformat()}",
                "    period_basis: calendar"]
    out += [f"    document: {_q(doc)}", f"    url: {_q('sources/' + pdf.name)}", "    figures:"] + figs
    return "\n".join(out) + "\n"


def write(ticker: str, text: str, record: dict, *, directory: Path = DRAFTS_DIR) -> Path:
    import yaml

    from .manual import parse_manual
    target = Path(directory) / f"{ticker}.{ORIGIN}.yaml"
    parse_manual(yaml.safe_load(text), path=target)        # one scale, schema: fail closed
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(text, encoding="utf-8")
    (Path(directory) / f"{ticker}.{ORIGIN}.run.json").write_text(
        json.dumps(record, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return target


def render(result: Run) -> str:
    g = result.gated
    out = [f"pages sent: {[p['pdf_index'] for p in result.record['pages_sent']]}; "
           f"money unit: {g.money_unit or '-'}",
           f"kept ({len(g.figures)}):"]
    for n, e in g.figures.items():
        col = " ".join(str(e['column']).split())
        out.append(f"  {n} = {e['value']:,.10g}  p.{e['page']}  [{col}]")
    out.append(f"dropped ({len(g.dropped)}):")
    for n, why in g.dropped.items():
        out.append(f"  {n}: {why}")
    return "\n".join(out)
