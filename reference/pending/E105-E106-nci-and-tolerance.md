# E105 + E106 — the code, written and held. 2026-09-04

**Both rulings are landed. The code is in
`E105-E106-nci-and-tolerance.patch` and is NOT in `vss/`.**

## Where it stands

E105's leg and E106's tolerance are both implemented in the patch:

* `manual.FIELDS` — `nci_dividends_paid`, `reads=("5.1C",)`;
* `valuation.free_cash_flow_zero` — the leg, summed like capex, its refusal
  in `_require_nci` and **asked LAST** so a new leg never rewrites an older
  leg's DATA MISSING message;
* `runrecord.INCOMPLETE_LEG_TOLERANCE = 0.035` and `Undetermined(name,
  bound, page)`;
* `RunRecord.tolerance()` — strikes the record **twice**, once with every
  undetermined leg at zero and once with each at its bound in the direction
  that reduces value, and takes the difference. Exact, not approximated: the
  DCF is linear in FCF0 only until net cash is added, so an approximation
  would be wrong by the bridge;
* `RunRecord._strike_unchecked()` — because `strike` asks `missing`,
  `missing` asks `tolerance`, and `tolerance` has to value the record, so
  the valuation and the gate cannot be the same call;
* `missing()` — a BOUNDED leg inside the tolerance is not a gap; the summed
  check (clause 4) is asked after every hard gap;
* `runrecord.NCI_IN_THE_FLOW` — the bridge stops saying "no field in this
  schema" and says where the answer is.

## What is NOT built, and it is the part that decides the answer

**Nothing in the store can yet SAY what E106 needs it to say.** The schema
has no way to record either of the two states the ruling turns on:

1. **a BOUND** — "this leg is absent and is at most X", which under clause 3
   is itself a figure and needs its evidence;
2. **a SEARCHED ABSENCE** — clause 5's determined zero, E85's shape: *no
   non-controlling interest line in the balance sheet, no such caption
   anywhere in a searched report*, recorded **with what was searched**.

Until a store can state one of those, every absent leg is an UNBOUNDED
absence, and E106 clause 3 refuses it. **So none of the seventeen comes back
on the patch as it stands** — not because the tolerance is too tight, but
because nothing has been read yet.

## Therefore, honestly: the report asked for cannot yet be produced

| asked | answer today |
|---|---|
| which of the seventeen come back | **none** — no store states a bound or a searched absence |
| which are bounded at zero by their balance sheets | **unknown** — clause 5 needs a SEARCH recorded, and a search that found nothing is a fact about the search until it names what it looked at |
| which still refuse | **all seventeen** |
| what SAP.DE prints | **DATA MISSING** — and it has no document under `sources/` at all, its host having refused automated fetch |

## What closes it

1. **A schema form for both states.** Roughly:

```yaml
      nci_dividends_paid:
        value: null
        bound: 40                 # E106: at most, in the store's money unit
        page: "p.NN: non-controlling interests are 0.4% of equity"
        status: UNVERIFIED
```

```yaml
      nci_dividends_paid:
        value: 0
        zero_basis: searched      # E85/E106 clause 5 — a DETERMINED zero
        page: "searched FY2025 20-F for 'non-controlling', 'minority':
               no such caption; balance sheet shows no NCI line (p.NN)"
        status: UNVERIFIED
```

  `zero_basis` currently accepts `caption|note|subtotal`; clause 5 needs
  `searched` beside them, and that is a change to E25's evidence vocabulary
  — **which is the owner's, not a session's.**

2. **Then one search per store**, recorded. For most of the seventeen it
   will be clause 5's determined zero and they return immediately; for the
   rest it is a bound or a figure.

3. **IMB.L needs neither**: FY2025 = **−156**, from Imperial's own build,
   which E101 reconciled to the pound.

## Why it was held rather than half-landed

Applying the patch today takes seventeen names to DATA MISSING and reds
61 tests, and E106 cannot rescue one of them until a store can state a
bound. Landing that would leave the repo worse than either finishing or not
starting. The suite is green at 2,321 and the tree is clean.
