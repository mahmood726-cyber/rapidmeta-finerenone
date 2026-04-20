#!/usr/bin/env python
"""Second-pass living-MA cleanup: generic replacements for user-visible summary
strings and comments that still contain 'sacubitril/valsartan' template residue.
Leaves translation dictionaries alone (they're non-functional).
"""
import io
import sys
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

ROOT = Path("C:/Projects/Finrenone")

# User-visible template literal showing arm data with hardcoded arm label
SUMMARY_OLD = "Matched event counts (${sourceKind}): sacubitril\\/valsartan ${best.tE}/${best.tN} (${txPct}%) vs placebo ${best.cE}/${best.cN} (${ctPct}%)."
SUMMARY_NEW = "Matched event counts (${sourceKind}): active ${best.tE}/${best.tN} (${txPct}%) vs comparator ${best.cE}/${best.cN} (${ctPct}%)."

# Two JS code-comments (cosmetic but might surface in Search-tab info popovers)
COMMENT_1_OLD = "// Keep one-click workflow: autoscreener pre-proposes INCLUDE only for canonical sacubitril\\/valsartan studies."
COMMENT_1_NEW = "// Keep one-click workflow: autoscreener pre-proposes INCLUDE only for canonical pre-registered trials in the AUTO_INCLUDE_TRIAL_IDS set."

COMMENT_2_OLD = "// Fast mode: keep autoscreener focused on canonical sacubitril\\/valsartan RCTs only."
COMMENT_2_NEW = "// Fast mode: keep autoscreener focused on canonical pre-registered RCTs only."

# Arm-matching regex inside another function (auto-extractor) -- secondary occurrences
ARM_OLD = "/sacubitril\\/valsartan|bay\\s*94|treatment|active/i"

# Replacement uses same generic "treatment|active" pattern (arm label matching is
# intentionally loose in the auto-extractor; specific drug match is optional)
ARM_NEW = "/treatment|active|intervention/i"

fixed = 0
untouched = []
for html in sorted(ROOT.glob("*_REVIEW.html")):
    if html.name in ("LivingMeta.html", "META_DASHBOARD.html", "AutoGRADE.html", "AutoManuscript.html"):
        continue
    if html.name == "ARNI_HF_REVIEW.html":
        continue
    text = html.read_text(encoding="utf-8")
    original = text

    text = text.replace(SUMMARY_OLD, SUMMARY_NEW)
    text = text.replace(COMMENT_1_OLD, COMMENT_1_NEW)
    text = text.replace(COMMENT_2_OLD, COMMENT_2_NEW)
    # Residual arm-matching regex occurrences (there can be more than the two
    # the first pass handled)
    text = text.replace(ARM_OLD, ARM_NEW)

    if text != original:
        html.write_text(text, encoding="utf-8")
        fixed += 1
    else:
        untouched.append(html.name)

print(f"Cleaned {fixed} apps; {len(untouched)} had no remaining residues")
if untouched[:5]:
    print("Untouched (already clean):", untouched[:5])
