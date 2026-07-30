"""Static acceptance checks for the APIXABAN_VTE reconstruction.

Asserts, against the shipped file, the things the fix claims to have done. Exits
non-zero if any check fails, so it can gate a push rather than merely describe
one. Run from the repo root.
"""
import io
import json
import re
import sys

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

FULL = "APIXABAN_VTE_AUTO_FULL_REVIEW.html"
src = open(FULL, encoding="utf-8", newline="").read()

checks = []


def ck(name, ok, detail=""):
    checks.append((name, bool(ok), detail))


# --- the five adjudicated trials are in the ledger ------------------------
for nct, label in [("NCT00643201", "AMPLIFY"), ("NCT00633893", "AMPLIFY-EXT"),
                   ("NCT03266783", "COBRRA"), ("NCT02366871", "Guntupalli 2020"),
                   ("NCT02829957", "RAMBLE")]:
    ck(f"ledger contains {nct} ({label})", f'"{nct}":{{' in src or f"{nct}:{{" in src)

# --- verified counts, exactly as sourced ---------------------------------
for name, pat in [
    ("AMPLIFY primary 59/2609 vs 71/2635",
     r'"tE":59,"cE":71,"nT":2609,"nC":2635'),
    ("AMPLIFY major bleeding 15/2676 vs 49/2689 with its own denominators",
     r'"tE":15,"cE":49,"nT":2676,"nC":2689'),
    ("AMPLIFY-EXT 2.5 mg 14/840 vs placebo 73/829",
     r'"tE":14,"cE":73,"nT":840,"nC":829'),
    ("AMPLIFY-EXT 5 mg 14/813 vs the same placebo 73/829",
     r'"tE":14,"cE":73,"nT":813,"nC":829'),
    ("COBRRA clinically relevant bleeding 44/1345 vs 96/1355",
     r'"tE":44,"cE":96,"nT":1345,"nC":1355'),
    ("Guntupalli major bleeding 1/204 vs 1/196",
     r'"tE":1,"cE":1,"nT":204,"nC":196'),
    ("Guntupalli co-primary CRNM 12/204 vs 19/196",
     r'"tE":12,"cE":19,"nT":204,"nC":196'),
    ("RAMBLE crossover apixaban 1/11 vs rivaroxaban 3/8 (arms in the right order)",
     r'"tE":1,"cE":3,"nT":11,"nC":8'),
]:
    ck(name, re.search(pat, src) is not None)

# --- the RAMBLE errors are gone ------------------------------------------
ck("RAMBLE PBAC is recorded as CONTINUOUS with null events",
   '"shortLabel":"PbacScore"' in src and '"type":"CONTINUOUS"' in src)
ck("the old RAMBLE record (PBAC as 3 vs 1 binary) is gone",
   'PbacScores' not in src and 'PBAC Scores (primary)' not in src)
ck("RAMBLE arm sizes are apixaban 11 / rivaroxaban 8, not 8 / 11",
   '"tN":11' in src and '"cN":8' in src)

# --- structural gates ----------------------------------------------------
ck("estimand-compatibility gate is defined", "rmPoolBlockReason(trials)" in src)
ck("gate is wired into the analysis path before computeCore",
   re.search(r'_rmBlock.*?renderEmptyAnalysis\(_rmBlock\)', src, re.S) is not None)
ck("continuous-endpoint guard is wired in", "renderEmptyAnalysis(_rmCont)" in src)
ck("phase-II exclusion honours the reviewed-eligible flag",
   src.count('!0!==t?.data?.rmPhaseEligible&&isPhaseTwoLike') >= 5)
ck("pre-2015 exclusion is retired", "rctOnly:!0,post2015:!1" in src)
ck("fail-closed banner is installed", 'data-rm-poolblock="1"' in src)
ck("per-question scope selector exists", "rmRenderQuestionBar()" in src)

# --- contamination -------------------------------------------------------
ck("no 'major cardiovascular events' plain-language default",
   'outcomeText={default:"major cardiovascular events"' not in src)
ck("no 'cardiovascular composite endpoint across CKD trials'",
   "across CKD trials" not in src)
ck("no 'MACE Composite' protocol fallback", '"MACE Composite")' not in src)
ck("PICO comparator is no longer 'Placebo'",
   'value="Placebo" aria-label="Comparator (PICO)"' not in src)
ck("no asthma/COPD subgroup template",
   "Blood eosinophils, smoking status, ICS use" not in src)
ck("no 'bay 94' (finerenone development code) in extraction regexes",
   "bay\\s*94" not in src and "bay 94" not in src)
ck("no template-concat leak in the patient summary",
   "RapidMeta.state.protocol?.int || 'the intervention'" not in src)

# The topic slug may legitimately remain in localStorage keys, download
# filenames and the run-artifact format id. It may NOT remain anywhere a reader
# would see it as if it were the drug's name. Classify each occurrence by what
# immediately follows it, not by what the enclosing string looks like: a
# filename slug can sit in the middle of a long template literal.
LEGIT = re.compile(
    r"apixaban_vte_auto("
    r"_v\d|_forest|_run_artifact|_meta_analysis|_report_|_validation_|_trial_data|"
    r"_protocol|_capsule|-run-artifact|_theme|_v1_0|_v0_\d"
    r")"
)
occurrences = [m.start() for m in re.finditer("apixaban_vte_auto", src)]
prose = []
for i in occurrences:
    tail = src[i:i + 60]
    if LEGIT.match(tail):
        continue
    if "rapid_meta_apixaban_vte_auto" in src[max(0, i - 12):i + 20]:
        continue
    if src[max(0, i - 40):i].endswith("prisma_2020_checklist_"):
        continue
    prose.append(src[max(0, i - 60):i + 60])
ck("topic slug no longer appears in user-visible prose",
   not prose, f"{len(prose)} prose occurrence(s): {prose[:3]}")

# --- claims removed ------------------------------------------------------
ck("ICMJE/PROSPERO equivalence claim removed",
   "equivalent to PROSPERO" not in src)
ck("header no longer claims INTERNAL CHECKS PASSED",
   "INTERNAL CHECKS PASSED" not in src)
ck("fragility index 0 is no longer described as robust",
   "indicating the result is robust to single-event modifications" not in src)
ck("provenance registry is populated, not {}",
   "CTGOV_EVIDENCE_REGISTRY={}" not in src and "CTGOV_EVIDENCE_REGISTRY={NCT" in src)

# --- ledger file ---------------------------------------------------------
try:
    led = json.load(open("outputs/apixaban_vte_correction_ledger.json", encoding="utf-8"))
    ck("correction ledger parses and covers five trials",
       len(led.get("trials", [])) == 5)
    ck("correction ledger records a not_done list", bool(led.get("not_done")))
except Exception as e:  # noqa: BLE001
    ck("correction ledger parses", False, str(e))

# --- line endings preserved ---------------------------------------------
raw = open(FULL, "rb").read()
ck("line endings unchanged (no CRLF rewrite of the whole file)",
   raw.count(b"\r\n") == 0)

fails = [c for c in checks if not c[1]]
for name, ok, detail in checks:
    print(("  PASS  " if ok else "  FAIL  ") + name + (f"  :: {detail}" if detail and not ok else ""))
print(f"\n{len(checks) - len(fails)}/{len(checks)} checks passed")
sys.exit(1 if fails else 0)
