"""Facts out of ONE ESEF report package, in the companyfacts API's shape.

WHY THIS EXISTS. A company listed on an EU regulated market files its annual
report under ESEF: the report is inline XBRL, tagged in the IFRS taxonomy,
and comes as a zipped report package beside the PDF. MFN carries it
(`tools/fetch_mfn.py` saves it as ``.zip`` and records it in
``sources/manifest.json``). The tagged statement lines are then read the way
a 20-F filer's are -- through `vss/ixbrl.py` and `vss/xbrl.py`'s IFRS map --
instead of by hand from the PDF.

WHAT IT READS. The package's ``reports/*.xhtml``, through
`ixbrl.facts_from_inline`: ``ix:nonFraction`` in ``ifrs-full`` only, no
dimensional context (a dimensional fact is a part of a line, never the
line), the element's own ``scale`` and ``sign``, a dash as zero. Each entry
keeps its ``decimals``, its context id and its displayed text.

WHAT IT REFUSES (fail closed, `EsefError`):

- a ZIP that is not a report package (no ``META-INF/taxonomyPackage.xml``),
  or one with no ``reports/*.xhtml``, or more than one;
- an issuer LEI in the contexts that is not the LEI recorded for the ticker
  in ``config/mfn_entities.yaml`` -- or no recorded LEI to compare with.
  A package filed by someone else is not this company's report.

WHAT IT NEVER MAPS. The issuer's own extension concepts (``evo:``,
``pan:``...). They are counted and reported as "extension, not read": an
extension has no shared definition, and choosing what it means is the
judgement this reader does not make.

In place of an SEC accession each entry carries ``esef:<sha256[:12]>:<file>``
-- the package's digest and the report file -- and the filing date is the
release date in the manifest.
"""

from __future__ import annotations

import hashlib
import io
import json
import re
import zipfile
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml
from lxml import etree

from .ixbrl import NS_IX, NS_XBRLI, IxbrlError, facts_from_inline

LEI_SCHEME = "http://standards.iso.org/iso/17442"
FORM = "ESEF"
STANDARD_PREFIXES = {"ifrs-full"}
#: Prefixes that are infrastructure, not concepts (never an "extension").
_NOT_CONCEPTS = {"xbrli", "link", "xlink", "iso4217", "xbrldi", "dei"}
ENTITIES_PATH = Path("config/mfn_entities.yaml")
MANIFEST_PATH = Path("sources/manifest.json")


class EsefError(Exception):
    """The package cannot be read as this issuer's ESEF report."""


@dataclass
class EsefPackage:
    path: Path
    sha256: str
    report_file: str
    lei: str
    filed: str
    facts: dict                          # companyfacts shape, ifrs-full only
    currencies: dict = field(default_factory=dict)   # unit -> fact count
    extensions: dict = field(default_factory=dict)   # concept -> fact count
    dimensional_skipped: int = 0
    numeric_facts: int = 0

    @property
    def accession(self) -> str:
        return accession_for(self.sha256, self.report_file)


def accession_for(sha256: str, report_file: str) -> str:
    return f"esef:{sha256[:12]}:{report_file}"


def report_document(raw: bytes, _depth: int = 0) -> tuple[str, bytes]:
    """(file name, bytes) of the package's one inline-XBRL report. A wrapper
    holding exactly ONE inner package (a validator's bundle) is opened to
    it; two or more is a refusal."""
    try:
        z = zipfile.ZipFile(io.BytesIO(raw))
    except zipfile.BadZipFile as exc:
        raise EsefError(f"not a ZIP: {exc}") from exc
    names = [n.replace("\\", "/") for n in z.namelist()]
    if not any(n.endswith("META-INF/taxonomyPackage.xml") for n in names):
        inner = [n for n in z.namelist() if n.lower().endswith((".zip", ".xbri"))]
        if not _depth and len(inner) == 1:
            return report_document(z.read(inner[0]), 1)
        raise EsefError("not an XBRL report package: no META-INF/taxonomyPackage.xml"
                        + (f" (and {len(inner)} inner archives; which is the "
                           f"report is not guessed)" if len(inner) > 1 else ""))
    reports = [n for n, orig in zip(names, z.namelist())
               if re.search(r"(^|/)reports/[^/]+\.x?html?$", n)]
    if not reports:
        raise EsefError("the package holds no reports/*.xhtml")
    if len(reports) > 1:
        raise EsefError(f"the package holds {len(reports)} report documents "
                        f"({reports}); which one is the report is not guessed")
    original = z.namelist()[names.index(reports[0])]
    return reports[0].rsplit("/", 1)[-1], z.read(original)


def _scan(xhtml: bytes) -> tuple[set[str], dict[str, int], int, int]:
    """(LEIs in the contexts, extension concept counts, dimensional numeric
    facts skipped, numeric facts in all)."""
    root = etree.fromstring(xhtml, parser=etree.XMLParser(recover=True, huge_tree=True))
    if root is None:
        raise EsefError("the report document is empty")
    leis: set[str] = set()
    dimensional: set[str] = set()
    for ctx in root.iter(f"{{{NS_XBRLI}}}context"):
        ident = ctx.find(f".//{{{NS_XBRLI}}}identifier")
        if ident is not None:
            if (ident.get("scheme") or "").rstrip("/") != LEI_SCHEME:
                raise EsefError(f"context {ctx.get('id')}: identifier scheme "
                                f"{ident.get('scheme')!r} is not the LEI scheme")
            leis.add((ident.text or "").strip())
        if ctx.find(f".//{{{NS_XBRLI}}}segment") is not None or \
                ctx.find(f".//{{{NS_XBRLI}}}scenario") is not None:
            dimensional.add(ctx.get("id"))
    extensions: dict[str, int] = {}
    dims = numeric = 0
    for fact in root.iter(f"{{{NS_IX}}}nonFraction"):
        numeric += 1
        name = fact.get("name") or ""
        prefix = name.split(":", 1)[0] if ":" in name else ""
        if fact.get("contextRef") in dimensional:
            dims += 1
            continue
        if prefix not in STANDARD_PREFIXES and prefix not in _NOT_CONCEPTS:
            extensions[name] = extensions.get(name, 0) + 1
    return leis, extensions, dims, numeric


def recorded_lei(ticker: str, path: Path = ENTITIES_PATH) -> str | None:
    if not path.exists():
        return None
    ent = (yaml.safe_load(path.read_text(encoding="utf-8")) or {}).get(ticker) or {}
    leis = ent.get("leis") or []
    return leis[0] if len(leis) == 1 else None


def manifest_release(file_name: str, path: Path = MANIFEST_PATH) -> str | None:
    if not path.exists():
        return None
    for r in json.loads(path.read_text(encoding="utf-8")).get("downloads", []):
        if r.get("file") == file_name:
            return (r.get("released") or "")[:10] or None
    return None


def read_package(path: Path, *, ticker: str, expected_lei: str | None = None,
                 filed: str | None = None,
                 entities: Path = ENTITIES_PATH,
                 manifest: Path = MANIFEST_PATH) -> EsefPackage:
    """Read one package. ``expected_lei`` and ``filed`` default to the
    recorded LEI (``config/mfn_entities.yaml``) and the manifest's release
    date; either missing is a refusal."""
    path = Path(path)
    raw = path.read_bytes()
    sha = hashlib.sha256(raw).hexdigest()
    report_file, xhtml = report_document(raw)

    expected = expected_lei or recorded_lei(ticker, entities)
    if not expected:
        raise EsefError(f"{ticker}: no single LEI recorded in {entities}; the "
                        f"package's issuer cannot be checked, so it is not read")
    leis, extensions, dims, numeric = _scan(xhtml)
    if not leis:
        raise EsefError(f"{path.name}: no entity identifier in any context")
    if leis != {expected}:
        raise EsefError(f"{path.name}: the contexts name LEI {sorted(leis)}, and "
                        f"{ticker}'s recorded LEI is {expected}. Not this "
                        f"issuer's report; nothing read")

    filed = filed or manifest_release(path.name, manifest)
    if not filed:
        raise EsefError(f"{path.name}: no release date in {manifest}; the "
                        f"filing date is not guessed (run tools/fetch_mfn.py)")

    try:
        facts = facts_from_inline(xhtml, accession=accession_for(sha, report_file),
                                  form=FORM, filed=filed, detail=True)
    except IxbrlError as exc:
        raise EsefError(f"{path.name}: {exc}") from exc
    blocks = facts.get("facts", {})
    other = sorted(set(blocks) - STANDARD_PREFIXES)
    for t in other:              # ixbrl also reads us-gaap; ESEF is IFRS
        blocks.pop(t)
    if not blocks.get("ifrs-full"):
        raise EsefError(f"{path.name}: no non-dimensional ifrs-full fact")
    currencies: dict[str, int] = {}
    for node in blocks["ifrs-full"].values():
        for unit, entries in node["units"].items():
            currencies[unit] = currencies.get(unit, 0) + len(entries)
    return EsefPackage(path=path, sha256=sha, report_file=report_file,
                       lei=expected, filed=filed, facts=facts,
                       currencies=currencies, extensions=extensions,
                       dimensional_skipped=dims, numeric_facts=numeric)


def render(pkg: EsefPackage) -> str:
    """A short plain report of what was read and what was not."""
    tags = pkg.facts["facts"]["ifrs-full"]
    n = sum(len(e) for node in tags.values() for e in node["units"].values())
    out = [f"ESEF {pkg.path.name}",
           f"  sha256 {pkg.sha256}  report {pkg.report_file}",
           f"  LEI {pkg.lei} (matches the recorded LEI)  filed {pkg.filed}",
           f"  numeric facts {pkg.numeric_facts}; ifrs-full read {n} on {len(tags)} concepts; "
           f"dimensional skipped {pkg.dimensional_skipped}",
           f"  units: " + ", ".join(f"{u} {c}" for u, c in sorted(pkg.currencies.items()))]
    if pkg.extensions:
        out.append(f"  extension, not read: {len(pkg.extensions)} concept(s), "
                   f"{sum(pkg.extensions.values())} fact(s)")
        for c, k in sorted(pkg.extensions.items()):
            out.append(f"    {c} ({k})")
    return "\n".join(out)


# --- A3: the mapping ---------------------------------------------------------
#
# The IFRS map a 20-F filer goes through -- `xbrl.IFRS_ANNUAL_FIELDS` and
# `xbrl.IFRS_TAXONOMY`, UNCHANGED -- so a Nordic name and SAP face the same
# judgements: the same tags, the same E23 capex shapes, the same refusals.
# A field with no tagged fact is in the year's `missing`: DATA MISSING.
# The reporting currency is measured the same way too (`reporting_currency`).

def annual(pkg: EsefPackage) -> tuple[list, list]:
    """(fiscal years, windows passed over), oldest first, through
    `xbrl.build_annual` on the IFRS map. The package's comparatives give
    the prior year."""
    from . import xbrl
    return xbrl.build_annual(pkg.facts, taxonomy=xbrl.IFRS_TAXONOMY)


# --- A4: the draft ------------------------------------------------------------
#
# Decision (a): a pre-fill writes a DRAFT, never the live store. Decision
# (c): every figure UNVERIFIED. E149: only the owner verifies. The hard
# rules: no zero is machine-emitted (E25's zero_basis is a human claim);
# no figure built from two others (`composite`) and no searched zero; no
# judgement field (interest_source, lease classification, not_presented,
# bound) -- the draft carries figures only.

DRAFTS_DIR = Path("config/manual/drafts")
SOURCES_DIR = Path("sources")
DRAFT_LIMIT = 12


def draft_path(ticker: str, directory: Path = DRAFTS_DIR) -> Path:
    return Path(directory) / f"{ticker.strip().upper()}.esef-ixbrl.yaml"


def packages_for(ticker: str, *, sources: Path = SOURCES_DIR, **kw
                 ) -> tuple[list[EsefPackage], list[str]]:
    """Every ESEF package on disk for the ticker, read; and one line per
    ZIP refused (not a package, foreign LEI, no release date...)."""
    read, refused = [], []
    for p in sorted(Path(sources).glob(f"{ticker}_*.zip")):
        try:
            read.append(read_package(p, ticker=ticker, **kw))
        except EsefError as exc:
            refused.append(f"{p.name}: {exc}")
    return read, refused


def merged_facts(packages: list[EsefPackage]) -> dict:
    from .ixbrl import merge_facts
    facts: dict = {"facts": {}}
    for pkg in sorted(packages, key=lambda k: k.filed):
        facts = merge_facts(facts, pkg.facts)
    return facts


def _entry_for(facts: dict, fig) -> dict | None:
    node = facts["facts"].get("ifrs-full", {}).get(fig.tag) or {}
    for entries in node.get("units", {}).values():
        for e in entries:
            if (e.get("accn") == fig.accession and e["end"] == fig.end
                    and e.get("start") == fig.start):
                return e
    return None


def _q(text: str) -> str:
    return '"' + str(text).replace("\\", "\\\\").replace('"', '\\"') + '"'


def _num(v: float) -> str:
    return str(int(v)) if float(v).is_integer() else repr(float(v))


def draft_yaml(ticker: str, name: str, packages: list[EsefPackage], *,
               run_ts) -> tuple[str, list[str]]:
    """(the draft's text, one line per figure NOT drafted and why)."""
    from . import xbrl
    if not packages:
        raise EsefError(f"{ticker}: no readable ESEF package; nothing to draft")
    facts = merged_facts(packages)
    years, _ = xbrl.build_annual(facts, taxonomy=xbrl.IFRS_TAXONOMY, limit=DRAFT_LIMIT)
    currency = xbrl.reporting_currency(facts, xbrl.IFRS_TAXONOMY)
    by_sha = {p.sha256[:12]: p for p in packages}
    left: list[str] = []
    out = [
        f"# {ticker} -- DRAFT from the issuer's ESEF report package(s). NOT the live store.",
        "#",
        f"# GENERATED by `vss esef --ticker {ticker} --draft` on {run_ts.isoformat(timespec='seconds')}",
        "# through `vss/esef.py` and the ifrs-full map in `vss/xbrl.py`, unchanged.",
        f"# Merge into config/manual/{ticker}.yaml with `vss manual --merge-draft --ticker {ticker}`:",
        "# it adds what the store lacks, never overwrites a figure, and prints a",
        "# conflict side by side. EVERY FIGURE IS UNVERIFIED (decision (c)); E149:",
        "# only the owner verifies, quotecheck is an audit aid.",
        "# NOT drafted: zeros (E25's zero_basis is a human claim), sums of",
        "# captions, searched zeros, issuer extension concepts, and every",
        "# judgement field (interest_source, lease classification, not_presented, bound).",
        "#",
        "# Packages read:",
    ]
    for p in sorted(packages, key=lambda k: k.filed):
        out.append(f"#   sources/{p.path.name}  sha256 {p.sha256}  filed {p.filed}  LEI {p.lei}")
    out += ["",
            f"ticker: {ticker}",
            f"name: {_q(name)}",
            f"reporting_currency: {currency}",
            "money_unit: whole     # as the package tags them, after its own scale attribute",
            "share_unit: whole",
            "origin: esef-ixbrl",
            "",
            "annual:"]
    for y in years:
        lines = []
        used: dict[str, int] = {}
        for fname, fig in y.figures.items():
            if fig.composite or fig.zero_basis or not fig.tag:
                left.append(f"FY{y.fiscal_year} {fname}: not a single tagged fact "
                            f"(a sum or a searched zero); not drafted")
                continue
            if fig.value == 0:
                left.append(f"FY{y.fiscal_year} {fname}: zero; a zero is never machine-emitted")
                continue
            sha12 = fig.accession.split(":")[1] if fig.accession.startswith("esef:") else ""
            pkg = by_sha.get(sha12)
            entry = _entry_for(facts, fig)
            if pkg is None or entry is None:
                left.append(f"FY{y.fiscal_year} {fname}: its fact cannot be traced to a package; not drafted")
                continue
            used[pkg.path.name] = used.get(pkg.path.name, 0) + 1
            window = f"{fig.start}..{fig.end}" if fig.start else f"as of {fig.end}"
            page = (f"ESEF {pkg.sha256[:8]} ifrs-full:{fig.tag} ctx {entry.get('ctx')} {window}, "
                    f"displayed '{entry.get('shown')}', decimals {entry.get('decimals')}"
                    f"{fig.concept_note}{fig.split_note}")
            if fig.restated_from is not None:
                page += f"; an earlier package stated {_num(fig.restated_from)}"
            lines += [f"      {fname}:",
                      f"        value: {_num(fig.value)}",
                      f"        source: {_q('esef-ixbrl: sources/' + pkg.path.name)}",
                      f"        page: {_q(page)}",
                      "        status: UNVERIFIED"]
        if not lines:
            continue
        main = max(used, key=used.get)
        mp = next(p for p in packages if p.path.name == main)
        out += [f"  - fiscal_year: {y.fiscal_year}",
                f"    period_end: {y.end.isoformat()}",
                f"    document: {_q(f'ESEF report package sources/{main} (sha256 {mp.sha256}), released {mp.filed}')}",
                f"    url: {_q('sources/' + main)}",
                "    figures:"] + lines
        for m in y.missing:
            left.append(f"FY{y.fiscal_year} {m}: no tagged fact -- DATA MISSING")
    return "\n".join(out) + "\n", left


def write_draft(ticker: str, text: str, *, directory: Path = DRAFTS_DIR) -> Path:
    """Validate the draft as a manual file, then write it. Fails closed."""
    from .manual import parse_manual
    target = draft_path(ticker, directory)
    parse_manual(yaml.safe_load(text), path=target)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(text, encoding="utf-8")
    return target
