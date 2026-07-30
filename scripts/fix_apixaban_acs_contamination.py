"""Third-stage APIXABAN_ACS fix: two pre-existing HFrEF base-engine leftovers.

Both findings are PRE-EXISTING - the contamination gate reports the identical two
HARD findings against the unmodified file at HEAD, so nothing here was introduced
by the data correction. They are fixed because the gate cannot go clean while
foreign trial identifiers sit in a claim-adjacent code path.

C1. KNOWN_TRIAL_ALIASES was keyed on NCT01035255 / NCT01920711 / NCT02924727 /
    NCT03988634 - PARADIGM-HF, PARAGON-HF, PARADISE-MI and PARAGLIDE-HF, the
    sacubitril-valsartan heart-failure trials of the base engine this app was
    cloned from. None appears in this app. The table feeds
    findConflictingTrialAlias(), the guard that detects when page text names a
    trial the row does not belong to; seeding that guard with another domain's
    trials makes it look for the wrong conflicts and miss its own.

C2. NMAEngine.run() carried a hardcoded ["NCT01035255","NCT01920711",
    "NCT02924727"] - the same HF trials - while labelling its output
    "Apixaban vs Placebo". It is inert today only because those keys are absent
    from realData, so the lookup yields an empty list and the function returns
    null. That is an accident, not a design. Replaced with a derivation from the
    app's own ledger, which is what the code meant.
"""
import io
import sys

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

FULL = "APIXABAN_ACS_AUTO_FULL_REVIEW.html"

s = open(FULL, encoding="utf-8").read()
before = len(s)
done = []

# ---- C1: alias table -> this app's own trials -----------------------------
old = (
    'const KNOWN_TRIAL_ALIASES={NCT01035255:["paradigm-hf","paradigm"],'
    'NCT01920711:["paragon-hf","paragon"],NCT02924727:["paradise-mi","paradise"],'
    'NCT03988634:["paraglide-hf","paraglide"]}'
)
if s.count(old) == 1:
    # Older lineage: the table still holds the sacubitril/valsartan HF trials.
    new = (
        'const KNOWN_TRIAL_ALIASES={NCT00313300:["appraise","appraise-1","apixaban for prevention '
        'of acute ischemic and safety events"],NCT00852397:["appraise-j","appraise j"],'
        'NCT00831441:["appraise-2","appraise 2"],NCT02415400:["augustus"]}'
    )
    s = s.replace(old, new, 1)
    done.append("KNOWN_TRIAL_ALIASES: PARADIGM/PARAGON/PARADISE/PARAGLIDE -> APPRAISE trials")
elif "const KNOWN_TRIAL_ALIASES={}" in s:
    # main already purged it (5e63960c9). KEEP IT EMPTY - that purge IS the
    # anti-contamination fix, and getExpectedTrialAliases() still derives
    # aliases from each row's own title. Only re-add real keys if the app is
    # shown to fail resolving its own NCTs; verified in-browser after this run.
    done.append("KNOWN_TRIAL_ALIASES: already EMPTY on main (5e63960c9) - left empty, main's fix preserved")
else:
    raise AssertionError("KNOWN_TRIAL_ALIASES in an unrecognised state")

# ---- C2: NMA engine reads the app's own ledger ----------------------------
old = (
    'trialData=["NCT01035255","NCT01920711","NCT02924727"]'
    ".filter(id=>!RapidMeta.state.excludedTrials?.[id])"
)
assert s.count(old) == 1, f"NMAEngine anchor count = {s.count(old)}"
new = (
    "trialData=Object.keys(RapidMeta.realData??{})"
    ".filter(id=>!RapidMeta.state.excludedTrials?.[id])"
)
s = s.replace(old, new, 1)
done.append("NMAEngine.run: hardcoded HF trial list -> derived from this app's realData")

open(FULL, "w", encoding="utf-8", newline="").write(s)
print(f"{FULL}: {before} -> {len(s)} bytes")
for d in done:
    print("  -", d)
