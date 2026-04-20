#!/usr/bin/env python
"""Third-pass living-MA cleanup.

Catches two residues that escaped passes 1 and 2 in more recently-cloned apps:

  A. Auto-screener single-term regex /sacubitril/i (newer clones have this
     collapsed form instead of the /sacubitril|valsartan|arni|entresto/i form
     that pass 1 targeted).
  B. Europe PMC MAIN query 'sacubitril valsartan AND (TITLE:randomized ...)'
     in executePrecision (pass 1 only handled the FALLBACK variant).
  C. hasDrug regex /\\bsacubitril|valsartan|arni|entresto\\b/i used during
     auto-screening of abstract text.

Idempotent: skips apps already updated with the marker.
"""
import io
import re
import sys
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

ROOT = Path("C:/Projects/Finrenone")

CTGOV_RE = re.compile(r"const ctgovUrl = 'https://clinicaltrials\.gov/api/v2/studies\?([^']+)';")
INTR_RE = re.compile(r"query\.intr=([^&]+)")
TERM_RE = re.compile(r"query\.term=([^&]+)")
COND_RE = re.compile(r"query\.cond=([^&]+)")


def derive_drug_regex(html_text):
    """Extract a drug-regex from the app's own CT.gov query. Handles both
    query.intr=drug1 OR drug2 AND condition  and  query.term=... styles.
    Returns (drug_regex_or_None, drug_terms_space_joined)."""
    m = CTGOV_RE.search(html_text)
    if not m:
        return None, None
    params = m.group(1)
    im = INTR_RE.search(params)
    if im:
        intr = im.group(1)
        parts = re.split(r"\s+AND\s+", intr, maxsplit=1)
        drug_terms = parts[0].strip()
        drug_list = [t.strip() for t in re.split(r"\s+OR\s+", drug_terms) if t.strip()]
        drug_regex = "|".join(t.lower() for t in drug_list)
        return drug_regex, " ".join(drug_list)
    tm = TERM_RE.search(params)
    if tm:
        term_val = tm.group(1).replace("%20", " ").strip()
        # query.term is free-text; first word is usually the drug class
        tokens = [t for t in re.split(r"\s+", term_val) if t]
        if not tokens:
            return None, None
        drug_regex = tokens[0].lower()
        return drug_regex, " ".join(tokens)
    return None, None


# Patterns to replace. Each takes (app_drug_regex, app_space_joined).

def build_subs(drug_regex, space_joined):
    subs = []
    # A. Auto-screener single-term /sacubitril/i  → /drug_regex/i
    subs.append((
        "[/sacubitril/i, 10, 'Intervention match'],",
        f"[/{drug_regex}/i, 10, 'Intervention match'],"
    ))
    # Also the original scorer label (older clones with no substitution yet)
    subs.append((
        "[/sacubitril/i, 10, 'Sacubitril/Valsartan intervention'],",
        f"[/{drug_regex}/i, 10, 'Intervention match'],"
    ))
    # B. Europe PMC MAIN query
    old_epmc = ("const epmcQuery = encodeURIComponent('sacubitril valsartan "
                'AND (TITLE:randomized OR PUB_TYPE:"Randomized Controlled Trial" '
                'OR PUB_TYPE:"Clinical Trial") AND SRC:MED\');')
    new_epmc = ("const epmcQuery = encodeURIComponent('" + space_joined
                + ' AND (TITLE:randomized OR PUB_TYPE:"Randomized Controlled Trial" '
                  'OR PUB_TYPE:"Clinical Trial") AND SRC:MED\');')
    subs.append((old_epmc, new_epmc))
    # C. hasDrug regex
    subs.append((
        "/\\bsacubitril|valsartan|arni|entresto\\b/i",
        f"/\\b{drug_regex}\\b/i",
    ))
    return subs


FIX_MARKER_V3 = "/* LIVING_MA_FIX_V3_APPLIED */"

fixed = 0
skipped_arni = 0
already_v3 = 0
no_query = []
totals = {"a_screener": 0, "b_epmc": 0, "c_hasdrug": 0}

for html in sorted(ROOT.glob("*_REVIEW.html")):
    if html.name in ("LivingMeta.html", "META_DASHBOARD.html", "AutoGRADE.html", "AutoManuscript.html"):
        continue
    if html.name == "ARNI_HF_REVIEW.html":
        skipped_arni += 1
        continue
    text = html.read_text(encoding="utf-8")
    if FIX_MARKER_V3 in text:
        already_v3 += 1
        continue
    drug_regex, space_joined = derive_drug_regex(text)
    if not drug_regex:
        no_query.append(html.name)
        continue
    subs = build_subs(drug_regex, space_joined)
    changed = False
    for i, (old, new) in enumerate(subs):
        if old in text:
            text = text.replace(old, new)
            changed = True
            key = ["a_screener", "a_screener", "b_epmc", "c_hasdrug"][i]
            totals[key] += 1
    if changed:
        text = text + "\n<!-- " + FIX_MARKER_V3 + " -->\n"
        html.write_text(text, encoding="utf-8")
        fixed += 1

print(f"Fixed:            {fixed}")
print(f"Skipped (ARNI):   {skipped_arni}")
print(f"Already v3:       {already_v3}")
print(f"No CT.gov query:  {len(no_query)}  {no_query[:5]}")
print(f"Substitutions by class: {totals}")
