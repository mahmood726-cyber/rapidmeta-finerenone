# Asserted Verdicts Scan

Scope scanned: top-level `scripts/*.py` and `ssot/*.py` only.

Files scanned: 580 total: 540 in `scripts`, 40 in `ssot`.

Parse failures: 0.

Findings counted: 28.

Signature counts, primary classification only:

- (a) `prop(<CONST>, ...)` with no alternate verdict at that property site: 6 findings.
- (b) function explicitly returns the same verdict on every reporting path: 2 findings.
- (c) hardcoded verdict/state/status/verification payload: 14 findings.
- (d) gate/validation command can print failures or flags but has no failing process outcome: 6 findings.
- Literal dict key `passed`: 0 findings.
- Literal dict key `valid`: 0 findings.

I did not count ordinary mutation-log labels such as `{"status": "NULLED_PMID"}` or `{"verdict": "AACT_NOT_FOUND"}` where the enclosing branch is itself data/action-derived and the file can append other statuses elsewhere. Those are literal labels, but not asserted pass/fail/refusal checks in the defect class.

## False-negative direction first

### 1. `scripts/r_validate.py:384-391`, `410-416`, `444-451`

Signature: (d)

Exact code:

```python
if rc != 0 or not json_path.exists():
    n_failed += 1; print(f"  FAIL {topic}: rc={rc} {stderr[:200]}"); continue
try: res = json.loads(json_path.read_text())
except Exception as e:
    n_failed += 1; print(f"  FAIL {topic}: parse {e}"); continue
if "error" in res: n_failed += 1; continue
```

```python
if rc != 0 or not json_path.exists():
    n_failed += 1; print(f"  FAIL {topic} (cont): rc={rc} {stderr[:200]}"); continue
try: res = json.loads(json_path.read_text())
except Exception as e:
    n_failed += 1; print(f"  FAIL {topic} (cont): parse {e}"); continue
if "error" in res: n_failed += 1; continue
```

```python
print(f"  Failed:                    {n_failed}")
print(f"  Manifest:                  {OUTDIR / 'index.json'}")


if __name__ == "__main__":
    main(sys.argv[1:])
```

Can ever report the other outcome? It can print `FAIL`, but the process cannot return failure from those counted failures. There is no `sys.exit(1)` or `return 1`.

Direction: false-negative, because automation sees success even when `n_failed > 0`.

### 2. `scripts/r_validate_dta.py:112-124`

Signature: (d)

Exact code:

```python
else:
    print(f"  {stem}: [WARN] fit failed -- {result.get('error')}")
    n_fail += 1
else:
    print(f"  {stem}: [FAIL] Rscript failed: {msg}")
    n_fail += 1
print(f"\nOK: {n_ok}  skipped: {n_skip}  failed: {n_fail}")


if __name__ == "__main__":
    main()
```

Can ever report the other outcome? It can print warning/fail and increment `n_fail`, but the command exits 0 unless it crashes.

Direction: false-negative.

### 3. `scripts/internal_consistency_gate.py:154-162`

Signature: (d)

Exact code:

```python
print("REPORTS ONLY. Each finding is two fields disagreeing, and WHICH ONE IS WRONG IS")
print("A READING, NEVER A COMPUTATION. All three were specified by an outside review")
print("that read fields against each other -- the only way any of them is visible,")
print("because every field involved is individually valid.")
return 0


if __name__ == "__main__":
    sys.exit(main())
```

Can ever report the other outcome? No process-level failure path. It can print contradiction counts, then always returns 0.

Direction: false-negative if used as a gate.

### 4. `scripts/arm_role_gate.py:154-162`

Signature: (d)

Exact code:

```python
print("TRIAGE, NEVER A VERDICT. Registry arm types are not always reliable -- RE-LY")
print("typed all three of its arms ACTIVE_COMPARATOR -- so a flag means READ THE TRIAL.")
print("But an inversion IMPROVES every statistic a reviewer looks at, so nothing")
print("downstream will ever flag it. This is the only place it can be caught.")
return 0


if __name__ == "__main__":
    sys.exit(main())
```

Can ever report the other outcome? No. It can print role/mirror flags, but exits 0.

Direction: false-negative if automation treats the gate as pass/fail.

### 5. `scripts/metric_consistency_gate.py:149-160`

Signature: (d)

Exact code:

```python
print("  flagged but not publishing a pool: %d" % (len(bad) - len(live)))
print("  unassessable: %d   (NOT a pass)"
      % sum(1 for r in rows if r[2] == "UNASSESSABLE"))
print()
print("TRIAGE, NOT A VERDICT. A shared unit somewhere does not prove the POOLED")
print("quantity used it; NO shared unit is the strong signal. Units are read from the")
print("registry's own unitOfMeasure field, never parsed from titles.")
return 0


if __name__ == "__main__":
    sys.exit(main())
```

Can ever report the other outcome? No process-level failure path. It can print live pool flags and still returns 0.

Direction: false-negative if used as a gate.

### 6. `scripts/subject_role_gate.py:131-142`

Signature: (d)

Exact code:

```python
print("subject found in an experimental arm: %d" % ok)
print("UNASSESSABLE (not a pass): %d" % len(unassessable))
for d, s, k, why in unassessable[:10]:
    print("   %-42s %s" % (d[:41], why))
print()
print("TRIAGE, NEVER A VERDICT. Arm types lie -- RE-LY typed all three of its arms")
print("ACTIVE_COMPARATOR. The subject token is a guess. A flag means READ THE TRIALS.")
return 0


if __name__ == "__main__":
    sys.exit(main())
```

Can ever report the other outcome? No. Flags/unassessables are printed, then exit 0.

Direction: false-negative if used as a gate.

### 7. `ssot/build_to_standard.py:620-631`

Signature: (c), also overlaps (a)

Exact code:

```python
"trials": [dict(_prior_trials.get(t.get("nct"), {}),
                **{"nct": t.get("nct"), "verified": True,
                   "link": f"https://clinicaltrials.gov/study/{t.get('nct')}"})
           for t in ((obj.get("inputs") or {}).get("trials") or [])],
```

```python
props["P8_registration_identity"] = prop(
    HELD, f"{_n} of {_n} trial(s) verified live against the registry.")
```

Can ever report the other outcome? No. The builder writes `verified: True` for every trial it iterates and then reports `_n of _n verified live`. This block does not fetch or compare a returned registry `nctId`.

Direction: false-negative, because it can assert successful live verification without doing the live verification in this block.

### 8. `ssot/build_to_standard.py:399-404`

Signature: (a)

Exact code:

```python
_dbs = len(spec["search"].get("databases") or [])
_rem = spec["k_cascade"].get("k_unscreened_remainder")
props["P1_executed_search"] = prop(
    HELD, f"{_dbs} database queries recorded verbatim with dates and counts; PRISMA "
          f"arithmetic reconciles and the {_rem}-trial unscreened remainder is stated "
          f"as a number rather than omitted.")
```

Can ever report the other outcome? No at this property site. Missing/malformed `spec` would abort or error, not produce `REFUSING`/`FAIL`.

Direction: false-negative/over-assertion risk, because the property state is always `HELD`.

### 9. `ssot/build_to_standard.py:421-428`

Signature: (a)

Exact code:

```python
"keyed_on": "registration id",
}
props["P2_k_cascade"] = prop(
    HELD, f"k at every stage: surfaced {spec['k_cascade']['k0_surfaced']}, located "
          f"{spec['k_cascade']['k2_role_located']}, experimental "
          f"{spec['k_cascade']['k3_experimental']}, comparator "
          f"{spec['k_cascade']['k4_comparator']}, included "
          f"{spec['k_cascade']['k_included_in_object']}, unscreened remainder {_rem}.")
```

Can ever report the other outcome? No at this property site. It can only emit `HELD` or abort on missing keys.

Direction: false-negative/over-assertion risk.

### 10. `ssot/build_to_standard.py:481-486`

Signature: (a)

Exact code:

```python
_na = sum(1 for v in verdicts.values() if v["verdict"] == NOT_ASSESSABLE)
_cp = verdicts["criteria_predefined"]["verdict"]
props["P4_preconditions"] = prop(
    HELD, f"All {len(P.PRECONDITIONS)} recorded with verdict and cited authority: "
          f"{n_fail} FAIL, {_na} NOT-ASSESSABLE. criteria_predefined is {_cp} -- "
          f"{'post hoc criteria, which R107 permits and C5/C7 does not satisfy' if _cp == FAIL else 'this object declares neither a provenance block nor a protocol statement, so pre-specification cannot be decided either way'}.")
```

Can ever report the other outcome? No at the property level. It can include `FAIL` and `NOT_ASSESSABLE` counts in the prose, but the page property remains `HELD`.

Direction: false-negative/over-assertion risk if readers interpret `HELD` as the gate state rather than merely "recorded".

### 11. `ssot/build_to_standard.py:532-536`

Signature: (a)

Exact code:

```python
_cells = obj["extraction"].get("cells") or []
_read = sum(1 for c in _cells if c.get("label") == "READ")
props["P5_extraction_table"] = prop(
    HELD, f"{len(_cells)} cells: {_read} READ with source path and verbatim text, "
          f"{len(_cells) - _read} DERIVED with the method named.")
```

Can ever report the other outcome? No at this property site. Zero cells would still produce `HELD` with `0 cells`.

Direction: false-negative/over-assertion risk.

### 12. `scripts/fix_apixaban_acs_gate_round3.py:107-115`

Signature: (c)

Exact code:

```python
VERDICT = {
    "verdict": "UNCERTAIN",
    "preliminary": True,
    "preliminary_note": PRELIM,
    "gate_status": (
        "Re-gated 2026-07-30 (Codex gpt-5.5 + Gemini, both verified to the live registry). "
        "Substance PASSED: the APPRAISE-2 ISTH-secondary rewrite and the AUGUSTUS "
        "factorial-cell rewrite verify verbatim to source, the pooled estimate is unchanged, "
```

Can ever report the other outcome? No. This replacement payload can only write `UNCERTAIN` plus a `gate_status` string saying `Substance PASSED`.

Direction: false-negative for the `Substance PASSED` claim; under-reporting/neutral for the fixed `UNCERTAIN` verdict.

### 13. `scripts/update_ledger_round3.py:23-27`, `46-48`

Signature: (c)

Exact code:

```python
d["status"] = (
    "RE-GATED 2026-07-30 (Codex gpt-5.5 + Gemini, both verified to the live registry). Substance "
    "PASSED; four wording defects fixed in round 3 with no number changed. Committed locally, "
    "NOT PUSHED. Queued release-ready pending Mahmood's go."
)
```

```python
d["cross_family_gate_round_2_regate"] = {
    "outcome": "Substance PASSED. Four wording defects fixed; no number changed.",
    "verified_verbatim_to_source": [
```

Can ever report the other outcome? No. Both ledger status/outcome strings are asserted constants.

Direction: false-negative because they record a pass state without a branch that can record failure.

## Under-reporting / can-only-refuse / fixed non-success direction

### 14. `ssot/assessment.py:307-318`

Signature: (b)

Exact code:

```python
def eligibility_met(canon, full_text_read=False, path="screening.eligibility"):
    """Did each trial MEET the criteria? Not answerable from JSON, and never inferred."""
    r = read(canon, path)
    if not r.readable:
        return NOT_ASSESSABLE, (f"cannot assess: criteria are not stated ({r.detail}), so "
                                f"whether any trial met them cannot be decided")
    if not full_text_read:
        return NOT_ASSESSABLE, (f"cannot assess: {r.path} is stated, but inclusion logic is "
                                f"conditional prose and no full text was read this pass")
    raise NotImplementedError(
```

Can ever report the other outcome? No. It returns `NOT_ASSESSABLE` on every explicit reporting path; with `full_text_read=True`, it raises rather than returning `PASS`/`FAIL`.

Direction: under-reporting/refusal-only.

### 15. `ssot/preconditions.py:416-441`

Signature: (b)

Exact code:

```python
def eligibility_met(obj):
    """Did THIS topic's trials meet the stated criteria?
...
    cr = read(obj, "screening.eligibility")
    if not cr.readable:
        return NOT_ASSESSABLE, (
            f"cannot assess: criteria are not stated ({cr.detail}), so whether any trial met "
            f"them cannot be decided")
    sr = read(obj, "sources")
    if not sr.readable:
        return NOT_ASSESSABLE, (
            f"cannot assess: criteria are stated, but {sr.detail} -- no full text was "
            f"available this pass, and inclusion logic is conditional prose")
    return NOT_ASSESSABLE, (
        "cannot assess: criteria are stated and sources are present, but no full text was "
        "READ this pass. This precondition never infers from the auditability check.")
```

Can ever report the other outcome? No. It can only return `NOT_ASSESSABLE`.

Direction: under-reporting/refusal-only.

### 16. `ssot/build_to_standard.py:663-666`

Signature: (a)

Exact code:

```python
props["P6_analysis_output"] = prop(
    REFUSING, "No quotable model output exists because k=1 and nothing was pooled. The "
              "absence is recorded as a finding with its cause and its trigger, and the "
              "registry's own analysis is quoted verbatim in its place.")
```

Can ever report the other outcome? Not inside `_p6_refuse`. The caller can avoid this helper when existing R output is present, but this site itself can only write `REFUSING`.

Direction: under-reporting/refusal-only if the helper is reached incorrectly.

### 17. `ssot/build_to_standard.py:668-670`

Signature: (a)

Exact code:

```python
props["P6_analysis_output"] = prop(
    REFUSING, "No quotable model output exists because k=1 and nothing was pooled. The "
              "absence is recorded as a finding with its cause and its trigger.")
```

Can ever report the other outcome? No. This second assignment overwrites the previous P6 refusal in the same helper and can only write `REFUSING`.

Direction: under-reporting/refusal-only.

### 18. `scripts/fix_apixaban_acs.py:363-368`

Signature: (c)

Exact code:

```python
OR, lo, hi, se = mh_or([(d["tE"], d["tN"], d["cE"], d["cN"]) for d in POOL.values()])
verdict = {
    "verdict": "UNCERTAIN",
    "counts": {
        "P0_internal": 0,
```

Can ever report the other outcome? No. This patch payload always writes `UNCERTAIN`.

Direction: fixed non-success verdict; can under-report or over-report depending on the target page state.

### 19. `scripts/fix_apixaban_acs.py:525-529`

Signature: (c)

Exact code:

```python
verdict_js = (
    '<script>window.__verdict = {"verdict":"UNCERTAIN","counts":{"n_trials_seen":2,'
    '"n_trials_quarantined":2,"p0_total":0},"reasons":["Redirect stub. Verdict mirrors '
```

Can ever report the other outcome? No. The stub verdict string is literal.

Direction: fixed non-success verdict.

### 20. `scripts/fix_apixaban_acs_gate_round2.py:114-118`

Signature: (c)

Exact code:

```python
VERDICT = {
    "verdict": "UNCERTAIN",
    "gate_status": (
        "Revised 2026-07-30 after a cross-family review (Codex gpt-5.5 + Gemini). The "
```

Can ever report the other outcome? No. This payload can only write `UNCERTAIN`.

Direction: fixed non-success verdict.

### 21. `scripts/fix_apixaban_acs_gate_round2.py:523-526`

Signature: (c)

Exact code:

```python
stub_verdict = {
    "verdict": "UNCERTAIN",
    "counts": {"n_trials_seen": 2, "n_trials_quarantined": 2, "p0_total": 0,
```

Can ever report the other outcome? No. The stub verdict is literal.

Direction: fixed non-success verdict.

### 22. `scripts/fix_apixaban_acs_gate_round3.py:514-516`

Signature: (c)

Exact code:

```python
stub_verdict = {
    "verdict": "UNCERTAIN", "preliminary": True, "preliminary_note": PRELIM,
    "counts": {"n_trials_seen": 2, "n_trials_quarantined": 2, "p0_total": 0,
```

Can ever report the other outcome? No.

Direction: fixed non-success verdict.

### 23. `scripts/fix_false_green_zero_data.py:47-52`

Signature: (c)

Exact code:

```python
return {
    "verdict": "NO_DATA",
    "counts": {
        "n_trials_in_ledger": 0,
        "n_trials_analysed": 0,
```

Can ever report the other outcome? No. `build_verdict(subject)` always returns `NO_DATA`.

Direction: fixed non-success verdict. The caller asserts emptiness before applying it, but the verdict function itself has no alternate outcome.

### 24. `scripts/fix_false_green_zero_data.py:248-252`

Signature: (c)

Exact code:

```python
verdict_js = (
    '<script>window.__verdict = {"verdict":"NO_DATA","counts":{"n_trials_in_ledger":0,'
    '"n_trials_analysed":0,"n_trials_seen":0},"reasons":["Redirect stub. Verdict mirrors '
```

Can ever report the other outcome? No.

Direction: fixed non-success verdict.

### 25. `scripts/fix_mislabelled_apps.py:201-206`

Signature: (c)

Exact code:

```python
V1 = {
    "verdict": "UNCERTAIN",
    "preliminary": True,
    "identity_correction": {
        "file_and_url_say": "TIRZEPATIDE_ARDS",
```

Can ever report the other outcome? No.

Direction: fixed non-success verdict.

### 26. `scripts/fix_mislabelled_apps.py:361-364`

Signature: (c)

Exact code:

```python
stub_v = {"verdict": "UNCERTAIN", "preliminary": True,
          "identity_correction": V1["identity_correction"],
          "counts": {"n_trials_in_ledger": 0, "n_trials_quarantined": 3, "n_trials_seen": 0},
```

Can ever report the other outcome? No.

Direction: fixed non-success verdict.

### 27. `scripts/fix_mislabelled_apps.py:385-389`

Signature: (c)

Exact code:

```python
V2 = {
    "verdict": "UNCERTAIN",
    "preliminary": True,
    "identity_correction": {
        "file_and_url_say": "ICAGEN",
```

Can ever report the other outcome? No.

Direction: fixed non-success verdict.

### 28. `scripts/fix_mislabelled_apps.py:501-504`

Signature: (c)

Exact code:

```python
stub_v2 = {"verdict": "UNCERTAIN", "preliminary": True,
           "identity_correction": V2["identity_correction"],
           "counts": {"n_trials_seen": 3},
```

Can ever report the other outcome? No.

Direction: fixed non-success verdict.

