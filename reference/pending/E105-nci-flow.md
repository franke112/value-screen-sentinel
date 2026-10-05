# E105 — the code, written and NOT applied. 2026-09-04

**The ruling is landed (`FRAMEWORK-EDITS`, E105). The code is in
`E105-nci-flow.patch` beside this note and is NOT committed to `vss/`.**

## Why it is not applied

E105 says an absent `nci_dividends_paid` is **DATA MISSING and §5 does not
run**. That is right, and it is the whole point — a coerced zero would report
a record complete while overstating the flow by the whole of a group's
distributions.

Applied today it takes **17 stores** from a complete record to DATA MISSING:

```
ACN  APN.L  AUTO.L  CTSH  DECK  EXE  GDDY  IMB.L  KAR.ST  LIAB.ST
LII  NVR  RKT.L  RMV.L  SAP.DE  ULTA  ZZ-B.ST
```

Every fair value on the watchlist stops printing until each store carries the
leg — including SAP.DE's 140.37.

## Why I did not fill them

**`nci_dividends_paid` is a BASIS figure, so E103's automatic path is
forbidden.** E103 licenses automatic UNVERIFIED entry only for REFERENCE
figures — ones compared against a valuation, never used to build one — and
`reference_fields_in_basis` refuses §5 outright if that fence is ever
crossed. This leg builds the valuation, so E40 applies in full and it is
hand entry from a primary document.

I searched the documents already under `sources/` for LIAB.ST, AUTO.L, CTSH,
GDDY and RKT.L and found no dividends-to-minorities line by pattern. **That
is not a named zero.** E25 requires the issuer to STATE there are none, cited
to its page; a search that found nothing is a fact about my search. Entering
seventeen zeros on that basis is the exact substitution E105's own text
forbids, so it was not made.

## What each store needs

One figure per basis period, from the **cash flow statement's financing
section**, entered NEGATIVE as printed:

```yaml
      nci_dividends_paid:
        value: -156          # or, where the group has none:
        page: "p.NN, consolidated cash flow statement, financing activities:
               'Dividends paid to non-controlling interests (156)'"
        status: UNVERIFIED
```

and where there are no minorities:

```yaml
      nci_dividends_paid:
        value: 0
        zero_basis: note     # or `caption` where the line is shown nil
        page: "p.NN: 'The Group has no non-controlling interests.'"
        status: UNVERIFIED
```

**One is already known and needs no reading: IMB.L FY2025 = −156**, from
Imperial's own build, which E101 reconciled to the pound.

## What the patch contains

* `manual.FIELDS` — the `nci_dividends_paid` spec, `reads=("5.1C",)`, with
  E25's zero form and E105's ground on it;
* `valuation.free_cash_flow_zero` — the leg, summed like capex, its refusal
  in `_require_nci` and **asked LAST** so a new leg never rewrites an older
  leg's DATA MISSING message;
* `runrecord.RunRecord.nci_dividends_paid`, read on the basis in
  `from_store`, and in `missing()`;
* `runrecord.NCI_IN_THE_FLOW` — the bridge's `non_controlling_interests`
  entry stops saying "no field in this schema" and says where the answer is;
* `tests/_records.py` — the synthetic record declares a named zero.

Sixty-one tests go red on the patch alone, all of them stores and fixtures
without the leg. That is the ruling working, not a defect in it.
