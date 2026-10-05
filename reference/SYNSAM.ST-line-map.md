# SYNSAM.ST — which line of which statement answers which schema field

**This is NOT `config/manual/maps/SYNSAM.ST.yaml`, and it deliberately is not.**
That directory is `vss appendix`'s input: its schema is `{sheet, label, section,
after, note}` and it reads an issuer's **xlsx figures appendix** through a
committed cell map. **Synsam publishes no xlsx.** All five documents in
`sources/` are PDFs, and the Nordic feed carries no spreadsheet attachment on
any of the five releases. A file in `config/manual/maps/` carrying `page:`
instead of `sheet:` would fail the run the moment anyone pointed `vss appendix`
at it, and its presence would imply a workbook that does not exist. So the map
lives here, in the form the documents actually have.

**What it keeps from the PNDORA.CO map is the discipline that matters: rows are
identified by their LABEL, never by position.** A row inserted next year does
not shift a figure by one. Where a label occurs more than once, the statement
and the column are named, exactly as `section:` does there.

**BASIS:** `TTM 2025-Q3 + 2025-Q4 + 2026-Q1 + 2026-Q2`, ending **2026-06-30**.
Synsam prints a standalone quarter column in every periodic report — verified
document by document, including the year-end report, whose income statement
heads its first column `Q4`. Page numbers are the PRINTED page, which for all
five documents equals the PDF page.

## The documents

| period | document | IS | BS | CF | other financial information |
|---|---|---|---|---|---|
| 2025-Q3 | Q3 report 2025, published 2025-11-18 | p.20 | p.21 | p.22 | p.28 |
| 2025-Q4 | Year-end report 2025, published 2026-02-20 | p.20 | p.21 | p.22 | p.27 |
| 2026-Q1 | Q1 report 2026, published 2026-05-08 | p.18 | p.19 | p.20 | p.25 |
| 2026-Q2 | Q2 report 2026, published 2026-08-21 | p.21 | p.22 | p.23 | p.29 |

Every figure is read from **its own quarter's report**, never from a later
report's comparative column — which is what leaves the Q2 2026 report's
`QUARTERLY DATA` table (p.29) free to serve as an **independent second read** of
all four quarters.

## Flows — one column per quarter

| field | statement | row label | note |
|---|---|---|---|
| `revenue` | income statement | **`Total revenue`** | NOT `Net sales` — see below |
| `operating_income` | income statement | `EBIT` | |
| `operating_income_adjusted` | income statement | `EBITA` | non-GAAP memo |
| `ebitda` | income statement | `EBITDA` | equals Adjusted EBITDA; p.29 fn.2 states no items affecting comparability arose |
| `depreciation_amortisation` | **cash flow statement** | `Depreciation and amortisation` | the IS splits it in two and never totals them |
| `net_income` | income statement | `PROFIT FOR THE PERIOD` | |
| `finance_costs_period` | income statement | `Financial expenses` | printed negative; entered as a **positive magnitude** (E18) |
| `finance_income_period` | income statement | `Financial income` | positive magnitude |
| `operating_cash_flow` | cash flow statement | `Cash flow from operating activities` | after tax — `Income taxes paid` sits above it |
| `income_tax_paid` | cash flow statement | `Income taxes paid` | outflow, negative as filed |
| `capex_ppe` | cash flow statement | `Investments in tangible non-current assets` | negative |
| `capex_intangibles` | cash flow statement | `Investments in intangible non-current assets` | negative |
| `lease_payments_capital` | cash flow statement | `Amortisation of leasing liabilities` | in financing |
| `diluted_eps` | other financial information → `QUARTERLY DATA` | `Earnings per share, SEK` | Synsam states ONE figure before and after dilution |
| `diluted_weighted_average_shares` | other financial information → `PERFORMANCE MEASURES` | `Average number of shares during the period` | see the defect note below |
| `op_margin` | other financial information → `QUARTERLY DATA` | `EBIT margin, %` | stored as a fraction |

**`EBIT` and `EBIT margin, %` each occur TWICE on the same page** — once in
`QUARTERLY DATA` and once in `PERFORMANCE MEASURES`, under different column
layouts (`Q2 | Q1 | FY | Q4 | Q3 | …` against `Q2 | Q2 prior | Jan-Jun | Jan-Jun
prior | Jan-Dec`). **The table is named, not just the label.** This is the one
ambiguity on the page and it is exactly the `section:` case the PNDORA map
exists to handle; reading the wrong table returns Jan-Jun figures for a quarter.

## Stocks — taken at 2026-06-30 only (E19)

| field | statement | row label |
|---|---|---|
| `total_assets` | statement of financial position | `TOTAL ASSETS` |
| `net_ppe` | statement of financial position | `Tangible non-current assets` |
| `cash_and_equivalents` | statement of financial position | `Cash and cash equivalents` |
| `financial_liabilities_current` | statement of financial position | `Other current liabilities, interest-bearing` — a dash at 30 Jun 2026 (E25) |
| `shares_outstanding_period_end` | other financial information → `PERFORMANCE MEASURES` | `Number of shares at end of period` |
| `shares_issued_period_end` | other financial information, footnote 1 | *"The total number of shares at the end of the period amounts to 145,313,746"* |
| `treasury_shares_period_end` | other financial information, footnote 1 | *"of which 3,333,635 are repurchased shares in own custody"* — a COUNT, as stated (E22) |

## Stated ratio

| field | where | note |
|---|---|---|
| `net_debt_ebitda` | other financial information → `PERFORMANCE MEASURES`, **Jan-Jun column** | Footnote 2: calculated on a **rolling 12-month basis for January-June** — the twelve months ending 2026-06-30, which IS the basis. The three-month `Q2` column prints `n/a`. |

## `revenue` is `Total revenue`, and this is why

Synsam's income statement prints three lines where most issuers print one:

```
Net sales                    2,049
Other operating income          33
Total revenue                2,081
```

The issuer's own definitions, Q2 2026 report **p.37**, settle it:

> **EBIT margin** — EBIT as a percentage of **total revenue**.
> **Gross profit** — **Total revenue** less the cost of goods for resale.

And the arithmetic confirms which line the margin was struck on: EBIT 290 ÷
**Total revenue** 2,081 = **13.9%**, which is the figure Synsam states; 290 ÷
Net sales 2,049 = 14.2%, which it does not. The schema's own note for the field
says *"Total Revenue"*. **`Net sales` is the base of a different family of
stated measures** — `Gross margin, %`, `Net sales growth, %`, `Organic growth,
%`, `Investments/net sales, %` — and is entered nowhere in the manual file.

*This is also why `revenue_yoy` is left blank: Synsam states `Net sales growth,
%` and no growth rate on total revenue, so entering it would put a net-sales
rate beside a total-revenue level.*

## What is NOT mapped, and why

- **`gross_profit`** — Synsam defines it in prose and states `Gross margin, %`,
  but **no statement prints the line**. `Total revenue − Goods for resale` is
  arithmetic the accounts do not state, which is the one thing this path exists
  not to do. A ranking-key field; no method of §5 reads it.
- **`finance_costs_paid`, `finance_income_received`, `net_interest_paid`** —
  the interim cash flow statement carries **no interest lines at all**. They
  appear only in the ANNUAL cash flow statement, whose window ends 2025-12-31,
  and **E20 bars an annual flow from filling a gap at a basis ending
  2026-06-30**. Not mapped, not reached for.
- **`financial_liabilities_noncurrent`** — **E26**: the balance sheet presents
  `Non-current loans from financial institutions` (2,741) and `Other non-current
  liabilities, interest-bearing` (34) and **never totals them**.
- **`lease_liabilities`** — **E26**: `Non-current lease liabilities` (508) and
  `Current lease liabilities` (404), never totalled.
- **`operating_cash_flow_pretax`** — the statement presents OCF *after* tax; the
  `before changes in working capital` subtotal is a different quantity, not a
  pre-tax OCF.
- **`capex_combined`** — Synsam prints the split pair, so E23 reads that.
- **`proceeds_from_disposals_ppe`, `free_cash_flow_reported`,
  `other_current_financial_assets`, `noncurrent_derivative_assets_on_debt`,
  `diluted_eps_adjusted`** — no such caption anywhere in the interim reports.

## A defect this file makes visible, and does not fix

`diluted_weighted_average_shares` is classed as a FLOW, so the basis **sums**
four quarterly average share counts: 144,404,338 + 143,365,510 + 142,261,532 +
141,994,156 = **572,025,536**, roughly four times any real share count. It is a
known B18 successor — the 2026-08-25 handoff records the field as *"pinned by a
test and deliberately unchanged"*. The figures are entered as the accounts state
them so the defect is visible in a real file rather than hidden behind an empty
cell, which is how `op_margin`'s identical summing bug was found.

**`diluted_eps` is NOT the same case, and lumping the two together is wrong.**
Summing four quarterly EPS gives 4.02, and TTM net income 576 ÷ the *mean* of
the four share counts (143,006,384) gives 4.03. **Summed EPS is a sound TTM EPS;
a summed share count is not a share count.** The two fields sit side by side on
the handoff's "summable non-flows" list and only one of them is broken.
