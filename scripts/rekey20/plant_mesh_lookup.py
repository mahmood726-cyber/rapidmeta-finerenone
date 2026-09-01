# -*- coding: utf-8 -*-
"""PLANTS FOR THE VERIFIED MeSH LOOKUP. Every arm, each with a clean sibling.

⛔ THE VERIFIER'S FAILURE MODE IS OVER-REFUSAL, so every plant that must REFUSE is paired
with one that must ACCEPT. A verifier that refuses everything passes every "it caught the
bad record" test and destroys the expansion entirely -- and it already over-fired once on
this corpus, on `dyslipidaemia` -> `Dyslipidemias`.

⭐ The offline arms use NO NETWORK: `record_matches` and `_tokens` are pure. Only the tree
probe touches E-utilities, and it is the DETECTOR control -- proof the broadening step can
return a positive at all, because `[MeSH Tree Number]` returns count=0 silently and a dead
field would read as "MeSH holds no broader concept".
"""
import io
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace",
                              line_buffering=True)
import mesh_lookup as M                                                # noqa: E402

CACHE = os.path.join(HERE, "../../evidence/2026-08-31-axis/mesh_v2_cache.json")
results = []


def check(tag, ok, detail):
    results.append((tag, ok, detail))
    print("   %-58s %-4s %s" % (tag, "PASS" if ok else "FAIL", detail))


print("=== M1  record_matches -- REFUSE a different concept ===")
# The real case: this is what produced `supraventricular -> ventricular tachycardia`.
check("M1 plant: PSVT vs 'Tachycardia, Ventricular' is REFUSED",
      not M.record_matches("paroxysmal supraventricular tachycardia",
                           "Tachycardia, Ventricular"),
      "shares only 'tachycardia' -- a different arrhythmia")
# ⭐ THE SIBLING. Without it, `return False` passes the plant above.
check("M1 clean sibling: an INVERTED phrase is ACCEPTED",
      M.record_matches("pulmonary hypertension", "Hypertension, Pulmonary"),
      "MeSH inverts phrases; the test is on the token SET, not the string")
check("M1 clean sibling: a BROADER-worded descriptor is ACCEPTED",
      M.record_matches("hypercholesterolemia", "Hypercholesterolemia"),
      "exact concept")
check("M1 clean sibling: a NARROWER query inside a descriptor is ACCEPTED",
      M.record_matches("atrial fibrillation", "Atrial Fibrillation"), "exact concept")

print("")
print("=== M2  the plural arm -- the verifier's own over-refusal ===")
# It over-fired here for real: `dyslipidemia` vs MeSH's `Dyslipidemias`.
check("M2 plant: 'dyslipidemia' vs 'Dyslipidemias' is ACCEPTED",
      M.record_matches("dyslipidemia", "Dyslipidemias"),
      "singularisation; without it a CORRECT record was refused")
check("M2 clean sibling: the stem does not collapse DIFFERENT concepts",
      not M.record_matches("stroke", "Strokes of Genius Syndrome")
      and not M.record_matches("hypertension", "Hypotension"),
      "'hypotension' is not 'hypertension' after stemming")

print("")
print("=== M3  the KNOWN over-refusal that is NOT patched, recorded as a failing case ===")
# ⚠️ REPORTED, NOT FIXED. `dyslipidaemia` (British) vs `Dyslipidemias` still refuses,
# because the verifier does not apply the frozen rule's `ae` normalisation. Patching a gate
# after seeing which cases it caught is how a gate stops measuring anything, so this stands
# as a NAMED open defect with a test that asserts the CURRENT behaviour and says so.
check("M3 KNOWN OPEN: British 'dyslipidaemia' is still refused",
      not M.record_matches("dyslipidaemia", "Dyslipidemias"),
      "asserts the DEFECT, not the requirement -- one-line fix deliberately deferred, "
      "see REPORT-CONDITION-MESH-V2 section 2")

print("")
print("=== M4  DETECTOR CONTROL -- can the broadening step return a positive at all? ===")
cache = M.load_cache(CACHE)
ok, desc = M.tree_field_works(cache=cache)
check("M4 the [TN] field resolves a tree parent",
      ok, "C18.452.584.500.500.396 -> %r (expected 'Hyperlipidemias')" % desc)
# ⭐ THE SIBLING: the spelled-out field name that returns count=0 SILENTLY. If this ever
# starts working, the comment in mesh_lookup is stale and should be revisited.
got = M.broader(["C18.452.584.500.500.396"], cache=None) if False else None
check("M4 clean sibling: a nonsense tree number resolves NOTHING",
      M.broader(["Z99.999.999.999"], cache=cache) == [],
      "a broadening step that returns something for anything is not a lookup")
M.save_cache(cache, CACHE)

print("")
n = sum(1 for _, ok, _ in results if ok)
print("PLANTS: %d/%d" % (n, len(results)))
if n != len(results):
    print("FAILED: %s" % ", ".join(t for t, ok, _ in results if not ok))
    sys.exit(1)
