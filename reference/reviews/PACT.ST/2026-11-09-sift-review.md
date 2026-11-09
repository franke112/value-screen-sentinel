# Proact IT Group AB (PACT.ST) -- review from the Nordic sift, 2026-11-09

Decided by the session (E141), on the owner's word 2026-11-09 ("rätta
screenern och granska båda"). A review on the issuer's own figures; no store
in `config/manual/` yet. Why it was looked at:
`reference/screens/NORDIC-SIFT-2026-11-09.md` (private).

**Verdict: CANDIDATE -- build the store and strike it after the Capital
Markets Day on 2026-11-11.** On the issuer's figures the price is under the
bear value. Two things to settle in the strike: how much of the 2026 margin
is the memory-price cycle, and the CMD's new targets.

## Sources (sources/, issuer's documents)

- Q3 2026 interim report, 2026-10-22, `PACT.ST_2026-Q3_*_en_a0.pdf` -- p.2
  summary, p.3 CEO and market, p.15 net debt and shares, p.16 cash flow.
- Year-end report 2025 (MFN), via the fetch agent: IAC 2025 -84 (cost
  programme -78.7, deal costs -5.3).
- Issuer mapping added to `config/nordic_issuers.yaml` ("ProAct IT Group AB").

## What it sells (Q5)

Data storage, data protection and cloud services for companies and public
bodies in the Nordics, the UK and Central Europe: it sells and runs the
systems that keep a customer's data. Recurring revenue (cloud and support)
459 m in Q3, annual rate 1.84 bn of 4.9 bn sales; the customer returns
because the data, the contract and the support sit with Proact.

## The reading

- **Q3 2026**: revenue 1,180 (+8.9 %, organic +8.3 %), adjusted EBITA 112
  (76), margin 9.5 % (7.0). Rolling 12 months: revenue 4,917, adj. EBITA
  417 (8.5 %).
- **Why the margin rose**: the cost programme of 2025 (its cost was the
  -84 IAC) and mix. The CEO also says memory components carry "high prices
  and long lead times" and expects that to last through 2027 -- part of the
  revenue growth is price, and a component cycle can turn.
- **Balance sheet**: cash 542, bank loans 227, net cash 315 ex leasing
  (30 Sep 2026); leasing liabilities 319 (partly equipment leased on to
  customers -- "financial leasing sales").
- **Shares**: 25,100,334 issued, 551,324 in treasury -> 24,549,010
  outstanding. Buyback running; dividend 66 m.
- **Cash flow** (p.16): before working capital TTM 487 (FY2025 344); capex
  TTM 25; lease amortisation TTM 123; interest is in financing (paid 22 TTM),
  so nothing is added back.

## The value (rough, issuer's figures; `vss.valuation.equity_value_per_share`, r 9.5 %)

FCF0 = before working capital - capex - lease amortisation: TTM 339,
FY2025 176 (the restructuring year), 2024 ~300. Taken at **~300 m** (not the
TTM: the memory cycle is in it). Net cash 315, shares 24.55 m.

| FCF0 \ growth | 0 % | 2 % | 3 % | 4 % |
|---|---:|---:|---:|---:|
| 272 (three-year mean) | 148 | 172 | 186 | 201 |
| 300 (taken) | 162 | 189 | 204 | 221 |
| 339 (TTM) | 181 | 212 | 229 | 248 |

Growth view (sift's, after the price was seen): base 2 % (revenue grew
~4.6 % a year 2017-2025 with deals; the cycle flatters 2026), bear 0 % on
the three-year mean, bull 4 % on the TTM.

**Price 139.80 (2026-11-09). Bear ~148, base ~189, bull ~248: base fv /
price 1.35, and the price is under the bear.**

## Checks still open (the strike's)

1. The CMD on 2026-11-11: new targets; whether the 9 % margin is a level or
   the cycle.
2. Gross margin by quarter 2024-2026: how much of the rise is component
   prices.
3. The 2024 cash flow before working capital, from the Annual Report 2025
   comparative column (the three-year leg).
4. Customer concentration and the BlakYaks / Consular deals (E142).
5. Store in `config/manual/PACT.ST.yaml` through `vss manual`, then the
   queue (`tools/build_queue.py`).
