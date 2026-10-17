# GLP-1 CVOT trial-baseline enrollment reconciliation — 17 October 2026

**Scope:** `GLP1_CVOT_REVIEW.html` trial enrollment metadata only. This is
a source-traceability and duplicate-JavaScript-property correction, **not**
independent validation of treatment effects, meta-analytic assumptions, clinical
outcomes, risk of bias, or trial-population comparability.

## Defect and remedy

Before this patch, each of ten `realData` trial objects contained two
`baseline:{...}` properties. JavaScript retains the second, silently
discarding the first property's `n` enrollment total. We remove the
shadowed first object and put its source-checked `n` into the retained
baseline object, without modifying the retained demographic fields, the
treatment/control denominators, event counts, hazard ratios, or intervals.

Some shadowed first baseline `age` values conflict with the later
`meanAge` values (e.g., ELIXA 60.6 versus 60.3). We **do not restore**
the previously unreachable `age` alias or `pct_female` in AMPLITUDE-O;
those require a separate outcome-compatible reconciliation. Keeping the
previously effective `meanAge` is a compatibility-preserving decision,
not independent confirmation of its accuracy.

## Enrollment source ledger

The enrollment values below were checked on 17 October 2026 against the
linked original primary trial publications, and against the *unchanged*
`tN + cN` fields already present in the app.

| Trial | NCT ID | Total N | Original trial report |
| --- | --- | ---: | --- |
| ELIXA | NCT01147250 | 6,068 | [NEJM, Pfeffer et al.](https://doi.org/10.1056/NEJMoa1509225) |
| LEADER | NCT01179048 | 9,340 | [NEJM, Marso et al.](https://doi.org/10.1056/NEJMoa1603827) |
| SUSTAIN-6 | NCT01720446 | 3,297 | [NEJM, Marso et al.](https://doi.org/10.1056/NEJMoa1607141) |
| EXSCEL | NCT01144338 | 14,752 | [NEJM, Holman et al.](https://doi.org/10.1056/NEJMoa1612917) |
| HARMONY Outcomes | NCT02465515 | 9,463 | [Lancet, Hernandez et al.](https://doi.org/10.1016/S0140-6736(18)32261-X) |
| REWIND | NCT01394952 | 9,901 | [Lancet, Gerstein et al.](https://doi.org/10.1016/S0140-6736(19)31149-3) |
| PIONEER 6 | NCT02692716 | 3,183 | [NEJM, Husain et al.](https://doi.org/10.1056/NEJMoa1901118) |
| SELECT | NCT03574597 | 17,604 | [NEJM, Lincoff et al.](https://doi.org/10.1056/NEJMoa2307563) |
| AMPLITUDE-O | NCT03496298 | 4,076 | [NEJM, Gerstein et al.](https://doi.org/10.1056/NEJMoa2108269) |
| SOUL | NCT03914326 | 9,650 | [NEJM, McGuire et al.](https://doi.org/10.1056/NEJMoa2501006) |

## Regression invariants

The dedicated GitHub Actions workflow runs
`tests/test_glp1_cvot_baseline.py` on a PR modifying the app or its test.

- The ten named trials each have **exactly one** baseline object.
- The one baseline contains `n`, `meanAge`, `pctMale`, `meanBMI`,
  and `meanHbA1c` without reintroducing the superseded `age` alias.
- Each `n` matches both the linked primary publication and its current
  `tN+cN`.
- Each baseline object is valid JavaScript syntax (Node.js parse-only test).

**Explicit limitations:** source-count agreement is not source-adjudication
of endpoints, effect types, shared control groups, underlying enrollment
definitions, or risk-of-bias. The full portfolio's mandatory independent
published multi-trial meta-analysis benchmark gate remains unchanged.
No reviewer, clinical adjudication, or additional external benchmark is
claimed by these tests.
