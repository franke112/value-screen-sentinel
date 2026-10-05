# Can a fetcher download report PDFs on its own? — survey, 2026-08-24

**Status: SURVEYED 2026-08-24; the Nasdaq Nordic route was BUILT on
2026-08-24 as `vss/nordic.py` (`vss nordic`).** Everything else below
remains investigation only. The four traps this survey found in that
feed — the loose `market` filter, the multi-value `cnscategory`
no-op, the ignored date filters and `start`-not-`offset` pagination —
are encoded in that module and covered by `tests/test_nordic.py`. The question was: what is available free and without an account,
what covers `PNDORA.CO` and `BETS-B.ST`, and what would be required per
company for the rest of Europe.

Every HTTP result below was measured on 2026-08-24 from this host with a
plain `curl` and an honest user agent. Nothing was scraped behind a login, no
robots directive was overridden, and no request pretended to be a browser
except where noted — the LSE and FCA sites are Angular applications that
return their shell to any agent, so the browser-shaped user agent changed
nothing about what came back.

---

## THE ONE QUESTION THAT DECIDES BUILDABILITY

Not "does a feed exist". **Does the feed carry a direct link to the report
document, or only to a landing page?** A feed of landing pages needs a
scraper per issuer and is not a fetcher; a feed of document URLs is a fetcher
with a `for` loop in it.

**Three of the four sources below carry direct document links.** That is the
finding.

---

## 1. MFN.se — Nordic, free, no account, direct PDF links

`https://mfn.se/all/a.rss`, `.atom` and `.json` all answer **HTTP 200 to an
anonymous request**. No key, no login, no rate-limit response observed.

The **JSON** form is the one worth reading: it carries, per announcement, the
full body HTML *and* an `attachments` array of typed document URLs.

```
GET https://mfn.se/all/a.json?limit=48&offset=0     -> 200, 684 KB
```

Each item carries `author` (name, slug, **ISINs**, **tickers** as `XSTO:BETS B`
/ `XCSE:PNDORA`, LEI), `properties.tags` (`:regulatory`, `sub:report`,
`sub:report:interim`), `content.html`, `content.text` and
`content.attachments`.

**Both target names are covered, and both carry a primary PDF:**

| | ISIN | Tickers in the feed | Newest results release found | Attachment |
|---|---|---|---|---|
| Pandora | `DK0060252690` | `XCSE:PNDORA`, `XLON:0NQC` | 2026-08-12 *"Pandora delivers 3% organic growth in Q2"*, tags `sub:report:interim` | `Pandora Q2 2026 Interim Report…pdf`, tagged `:primary`, on `ml-eu.globenewswire.com` — **downloaded: HTTP 200, `application/pdf`, 1,460,181 bytes** |
| Betsson | `SE0022726485` | `XSTO:BETS B`, `CAPA:BETSBs`, `XLON:0A37` | 2026-07-17 *"Betsson AB interim report January – June 2026"*, tags `sub:report:interim` | PDF on `mb.cision.com` — **downloaded: HTTP 200, `application/pdf`, 415,675 bytes** |

So Denmark is covered, not merely "the Nordics" in the abstract. Pandora's
releases reach MFN through GlobeNewswire and Betsson's through Cision; MFN
normalises both into one schema, and the attachment URL points at the
distributor's own host, not at a page about it.

**Three limitations, measured, and the third is the important one.**

1. **The per-company feed path does not work.** `https://mfn.se/a/pandora/a.json`
   returns `"items": null` although `pandora` is the slug the platform itself
   uses. Selection has to be done client-side on `author.isins` /
   `author.tickers` out of the `/all/` feed.
2. **`query=` is full-text, not an author filter.** `query=Pandora` returns
   Ubisoft, Bang & Olufsen and a GXO logistics release, because each mentions
   the word. `query=DK0060252690` returns only announcements whose *body*
   quotes the ISIN — 115 items, all between 2010 and 2020, none of them a
   results release. **An ISIN in the query is not an ISIN filter.** Filter on
   the `author` object after parsing, never on the search string.
3. **`/all/` is a monitor, not an archive.** It paginates by offset without an
   observed ceiling — `offset=4800` still answered, reaching 2026-08-06 — but
   the whole Nordic tape runs at roughly **320 items a day**. Walking back two
   years for one name means reading on the order of 230,000 items. So MFN
   answers *"has a new report been published?"* and does not answer *"fetch the
   last eight quarters."* **Backfill is a different problem from monitoring,
   and this source solves only the second.**

## 2. Nasdaq Nordic's own news API — free, no account, per-company filter

The exchange publishes what MFN redistributes, and it has the per-company
filter MFN lacks.

```
GET https://api.news.eu.nasdaq.com/news/query.action
      ?type=json&showAttachments=true&showCompany=true
      &market=Main%20Market,%20Copenhagen&company=Pandora%20A/S&limit=3
-> 200, application/json
```

Measured results:

- `market=Main Market, Copenhagen` + `company=Pandora A/S` → 3 of 3 items are
  Pandora's, each with one `application/pdf` attachment on
  `attachment.news.eu.nasdaq.com`, and each carrying a `cnsCategory`
  (`Inside information`, `Managers' Transactions`, `Major shareholder
  announcements`).
- `market=Main Market, Stockholm` + `company=Betsson AB` → 3 of 3 Betsson,
  including **`cnsCategory: "Half Year financial report"`** for the
  2026-07-17 interim report, with its PDF.
- The cross pairs (Betsson on Copenhagen, Pandora on Stockholm) correctly
  return **zero** items, so the market/company pair is a real filter and not a
  relevance ranking.

**Caveat measured:** `cnscategory=Financial%20Reports` in the query string did
**not** restrict the result set — other categories still came back. Category
selection has to happen client-side on `cnsCategory`.

**This is the better Nordic route of the two** for a named watchlist: exact
per-company selection, the exchange as the publisher rather than a
redistributor, typed attachments, and an explicit category naming which
releases are the financial reports.

## 3. The UK — RNS is reachable, but not the way it was assumed

**The LSE website is not a source.** `londonstockexchange.com/news` and the
JD Sports company page both return the **same 54,995-byte Angular shell** to
any agent; the content arrives from `api.londonstockexchange.com`, an
undocumented private API keyed on opaque `componentId` values. A POST to it
answered `200 []`. Buildable in principle, fragile by construction, and not a
published interface.

**The FCA's National Storage Mechanism is the source, and it is open.** The
NSM is the UK's Officially Appointed Mechanism — the statutory archive of
regulated information — and its search API answers an anonymous **POST**:

```
POST https://api.data.fca.org.uk/search?index=nsm-search&start=0&size=8
     Content-Type: application/json
     {"from":0,"size":8,"sort":"publication_date","sortorder":"desc",
      "keyword":"213800HROV6Y9MUU8375","criteriaObj":{"criteria":[],"dateCriteria":[]}}
-> 200
```

The keyword is JD Sports Fashion PLC's **LEI**, and it selects cleanly: **675
matching records**, every one of them `company: "JD SPORTS FASHION PLC"`.
(The equivalent **GET** returns `{"message":"Missing Authentication Token"}` —
the endpoint is POST-only, which is why a casual probe reads as locked.)

Each record carries `document_date`, `source` (`RNS` or `Direct Upload`),
`category_group`, `type`, `headline` and a relative `download_link` resolving
under `https://data.fca.org.uk/artefacts/`. Measured, unauthenticated:

| Document | Path | Result |
|---|---|---|
| Q2 2026/27 trading statement, 2026-08-20 | `NSM/RNS/28fb2877-…html` | **200, `text/html`, 66,097 bytes** |
| Annual Report and Accounts, PDF | `NSM/DirectUpload/NI-000145270/NI-000145270.pdf` | **200, `application/pdf`, 9,010,830 bytes** |
| Annual Report and Accounts, **ESEF / iXBRL tagged** | `NSM/DirectUpload/NI-000145262/NI-000145262_213800HROV6Y9MUU8375-2026-01-31.zip` | **200, `application/zip`, 25,974,469 bytes** — a valid taxonomy package: `_cal/_def/_pre/_lab-en/_ref.xml`, `.xsd`, `META-INF/taxonomyPackage.xml`, and the inline-XBRL report HTML |

### The UK answer is HTML, not PDF — and the repo already has the evidence

`sources/jd-20260820-2026_27-Q2-trading-statement_RNS_vF.pdf` is **not an RNS
document**. Its PDF metadata says `Creator: Microsoft® Word for Microsoft 365`,
`Author: Neil Greenhalgh` (JD's CFO), with an MSIP sensitivity label and a
`_vF` filename — it is the company's own Word export, downloaded from JD's
investor-relations site. RNS delivers text.

Flattened through `vss/source.py`'s own `html_to_text`, the NSM copy of that
same announcement is **15,639 characters against the local PDF's 14,782**, and
every probe checked (`Q2 2026/27 TRADING STATEMENT`, the group figure
`(1.3)%`, `Finish Line`) is present in both. **The HTML is the better source**:
the table rows survive as rows, so `source.PDF_WARNING` — *"a PDF stores
glyphs at coordinates, not rows"* — does not apply to it at all.

**And the ESEF package changes what is possible for a UK issuer.** It is
inline XBRL: tagged facts with contexts and units, from the filer, in the
statutory archive. That is the same *kind* of provenance `vss/xbrl.py` was
built on, for a company that has no CIK to look up. (A foreign private issuer
filing a 20-F does have one — SAP.DE and UNA.AS both do — so `vss xbrl --cik`
is worth trying before any of this.) It is a heavier lift than
`companyfacts` JSON — an IFRS taxonomy rather than us-gaap, one zip per year
rather than one endpoint per company — but it is not the same problem as
reconstructing a PDF.

## 4. The rest of Europe — one mechanism, twenty-seven front doors

The regime, not the vendors, is what generalises. The Transparency Directive
requires every EEA state to run an **Officially Appointed Mechanism** for
regulated information, and the ESEF regulation has required annual financial
reports on EU regulated markets to be filed as inline XBRL since FY2020. So
for a name on any EU regulated market the annual report exists as tagged data
in *some* national archive — the archives are simply twenty-seven different
systems with twenty-seven different interfaces, of which the FCA's is one and
is the one measured here.

**What would be required per company, in order of cost:**

1. **The market it is listed on** — which decides the archive. Already implied
   by the ticker suffix the store carries.
2. **The LEI**, not the ticker. The FCA's NSM keys on it and every EU OAM
   records it; it is the only identifier that is the same string in every
   archive. This is the same shape as `vss xbrl`'s `cik:` — a MANUAL fact
   about the issuer that no endpoint here can be asked to guess.
3. **A per-archive adapter**, because there is no common API today. Nordic
   names are covered by the two sources above without one.
4. **Nothing at all** for a name whose IR host refuses automated requests.
   `sap.com` returns 403 to this tool, which is why `source.py` already
   answers a 401/403/429 by naming the door that is still open (*"download the
   report in a browser and pass it with `--text-file`"*) rather than by
   dressing up as a browser. **A refusal is a finding, not a failed search:**
   those names are exactly the ones the manual schema exists for.

   **CORRECTED 2026-08-26 (REVIEW-4 report B 7.1).** This sentence read
   *"`sap.com` returns 403 to this tool and `www.sec.gov` refuses it
   outright"*. **The second half was false and it was false about US, not
   about them.** `www.sec.gov` refuses the survey's own User-Agent —
   `vss/1.0 (personal watchlist tool)` (`source.py:22`) — because it carries
   **no contact address**, which is the one thing SEC's published access
   policy asks for. With a contact address it answers **HTTP 200**:
   `www.sec.gov/files/company_tickers.json` returned 794,966 bytes and 10,388
   rows on 2026-08-25, and `data.sec.gov` has answered `vss xbrl` all along
   through `VSS_SEC_CONTACT`. The same correction is B40 in
   `reference/FRAMEWORK-EDITS.md`; this was the last note carrying the old
   claim. **There is no closed door at SEC — there is a header this survey's
   fetcher does not send.**

**This is scheduled to collapse into one interface, and not yet.** ESMA's
**European Single Access Point** began collecting from the OAMs and national
competent authorities on 2026-07-10, covering Transparency Directive,
Prospectus and Short-selling data first, and is required to be **publicly
accessible by July 2027**. A fetcher built per-archive today is a bridge with
a published expiry date on it. That is an argument for building the *Nordic*
route now — where two open, per-company, document-linked feeds already exist —
and for waiting on the rest.

---

## Summary

| Source | Free | Account | Covers | Direct document link | Verdict |
|---|---|---|---|---|---|
| MFN.se JSON/RSS/Atom | yes | no | SE, DK, NO, FI, IS | yes — typed `attachments` | Monitor only; no per-company feed, no practical backfill |
| Nasdaq Nordic news API | yes | no | Nordic main markets | yes — `attachmentUrl` | **Best Nordic route.** Exact `market`+`company` filter; covers **both** `PNDORA.CO` and `BETS-B.ST` |
| LSE website / private API | — | — | UK | no — SPA shell | Not a source |
| FCA NSM (POST search) | yes | no | UK | yes — RNS **HTML**, annual report **PDF** and **ESEF/iXBRL** | **The UK route.** Keyed on LEI. HTML beats the PDF for extraction |
| Rest of EU | varies | varies | per country | per archive | One OAM per state until ESAP opens (July 2027) |

**Neither Nordic source, nor NSM, answers the backfill question** — eight
quarters of history for a name entering the pipeline. Every one of them is a
publication feed read forward from today. Backfill remains the company's own
IR archive, by hand, which is what `config/manual/<TICKER>.yaml` was built for.
