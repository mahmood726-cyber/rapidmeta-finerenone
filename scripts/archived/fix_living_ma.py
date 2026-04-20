#!/usr/bin/env python
"""Fix living-MA residues: cloned apps still have hardcoded 'sacubitril valsartan' in
the OpenAlex search, Europe PMC fallback, auto-screener regex, auto-extractor arm-
matching regex, and check-for-updates button. This script extracts each app's own
CT.gov query (which the cloner DID substitute correctly) and propagates it to the
5 broken locations so the living-MA functionality (search + auto-extract) works.

Idempotent: re-running is safe (skips apps already fixed).
"""
import io
import re
import sys
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

ROOT = Path("C:/Projects/Finrenone")

# Pattern that locates the app's own correct CT.gov query from executePrecision()
CTGOV_RE = re.compile(
    r"const ctgovUrl = 'https://clinicaltrials\.gov/api/v2/studies\?([^']+)';"
)
INTR_RE = re.compile(r"query\.intr=([^&]+)")


def extract_terms(html_text):
    """Return (drug_terms_raw, drug_regex_alts, full_intr_url_encoded, first_drug, all_terms_space_joined)
    or None if the ctgovUrl can't be found."""
    m = CTGOV_RE.search(html_text)
    if not m:
        return None
    params = m.group(1)
    im = INTR_RE.search(params)
    if not im:
        return None
    intr_full = im.group(1)
    # Split on " AND " only where it actually separates drug vs condition clauses
    parts = re.split(r"\s+AND\s+", intr_full, maxsplit=1)
    drug_terms = parts[0].strip()          # e.g. "dabigatran OR rivaroxaban OR apixaban OR edoxaban"
    # OR-list → regex alternation
    drug_list = [t.strip() for t in re.split(r"\s+OR\s+", drug_terms) if t.strip()]
    drug_regex = "|".join(t.lower() for t in drug_list)
    # Space-joined for OpenAlex
    space_joined = " ".join(drug_list)
    return {
        "drug_terms": drug_terms,
        "drug_regex": drug_regex,
        "drug_list": drug_list,
        "space_joined": space_joined,
        "intr_full": intr_full,
        "first_drug": drug_list[0] if drug_list else "",
    }


# Patterns to replace. Each replacement is string-in string-out to keep it simple.
# We only use terms from the app's own intr query.

FIX_MARKER = "/* LIVING_MA_FIX_APPLIED */"

OPENALEX_OLD = "const oaUrl = 'https://api.openalex.org/works?search=sacubitril valsartan&per_page=50&select=id,doi,title,ids,abstract_inverted_index,publication_year,type,authorships';"

EPMC_FALLBACK_OLD = "const fbQ = encodeURIComponent('sacubitril valsartan AND SRC:MED');"

CHECK_UPDATES_OLD = "const r = await fetch('https://clinicaltrials.gov/api/v2/studies?query.intr=sacubitril+AND+valsartan&pageSize=50&filter.overallStatus=COMPLETED');"

AUTOSCREENER_OLD = "[/sacubitril|valsartan|arni|entresto/i, 10, 'Sacubitril/Valsartan intervention'],"

# Arm-matching regex pattern (two identical locations)
ARM_OLD = "/sacubitril\\/valsartan|bay\\s*94|treatment|active/i"

# "no new completed sacubitril/valsartan trials found" banner text
BANNER_NO_NEW_OLD = "no new completed sacubitril/valsartan trials found on CT.gov"


def build_replacements(terms):
    """Return a dict of (old_string, new_string) replacements for one app."""
    drug_terms = terms["drug_terms"]
    drug_regex = terms["drug_regex"]
    intr_full = terms["intr_full"]
    space_joined = terms["space_joined"]

    openalex_new = (
        "const oaUrl = 'https://api.openalex.org/works?search="
        + space_joined
        + "&per_page=50&select=id,doi,title,ids,abstract_inverted_index,publication_year,type,authorships';"
    )
    epmc_fallback_new = (
        "const fbQ = encodeURIComponent('" + drug_terms + " AND SRC:MED');"
    )
    check_updates_new = (
        "const r = await fetch('https://clinicaltrials.gov/api/v2/studies?query.intr="
        + intr_full
        + "&pageSize=50&filter.overallStatus=COMPLETED');"
    )
    autoscreener_new = (
        "[/" + drug_regex + "/i, 10, 'Intervention match'],"
    )
    arm_new = "/" + drug_regex + "|treatment|active/i"
    banner_no_new_new = "no new completed " + drug_terms + " trials found on CT.gov"

    return {
        OPENALEX_OLD: openalex_new,
        EPMC_FALLBACK_OLD: epmc_fallback_new,
        CHECK_UPDATES_OLD: check_updates_new,
        AUTOSCREENER_OLD: autoscreener_new,
        ARM_OLD: arm_new,
        BANNER_NO_NEW_OLD: banner_no_new_new,
    }


def fix_app(html_path):
    text = html_path.read_text(encoding="utf-8")

    # Idempotency guard
    if FIX_MARKER in text:
        return "already_fixed"

    # Skip ARNI itself (it is the template; hardcoded sacubitril is actually correct there)
    if html_path.name == "ARNI_HF_REVIEW.html":
        text = text + "\n<!-- " + FIX_MARKER + " ARNI_TEMPLATE_NOP -->\n"
        html_path.write_text(text, encoding="utf-8")
        return "skipped_arni"

    terms = extract_terms(text)
    if not terms:
        return "no_ctgov_url"

    reps = build_replacements(terms)
    applied = {}
    for old, new in reps.items():
        hits = text.count(old)
        if hits > 0:
            text = text.replace(old, new)
            applied[old[:40] + "..."] = hits

    # Add marker so we can tell the fix has been applied
    text = text + "\n<!-- " + FIX_MARKER + " " + terms["drug_terms"].replace(" OR ", "|") + " -->\n"
    html_path.write_text(text, encoding="utf-8")
    return applied


def main():
    results = {"already_fixed": 0, "skipped_arni": 0, "no_ctgov_url": [], "fixed": {}, "skipped_other": []}
    for app in sorted(ROOT.glob("*_REVIEW.html")):
        if app.name in ("LivingMeta.html", "META_DASHBOARD.html", "AutoGRADE.html", "AutoManuscript.html"):
            results["skipped_other"].append(app.name)
            continue
        r = fix_app(app)
        if r == "already_fixed":
            results["already_fixed"] += 1
        elif r == "skipped_arni":
            results["skipped_arni"] += 1
        elif r == "no_ctgov_url":
            results["no_ctgov_url"].append(app.name)
        else:
            results["fixed"][app.name] = r

    print(f"Already fixed:     {results['already_fixed']}")
    print(f"Skipped (ARNI):    {results['skipped_arni']}")
    print(f"Skipped (tools):   {len(results['skipped_other'])}  -> {results['skipped_other']}")
    print(f"No ctgov URL:      {len(results['no_ctgov_url'])}  {results['no_ctgov_url'][:5] if results['no_ctgov_url'] else ''}")
    print(f"Newly fixed:       {len(results['fixed'])}")
    for app, hits in list(results["fixed"].items())[:5]:
        print(f"  {app}: {hits}")
    if len(results["fixed"]) > 5:
        print(f"  ... and {len(results['fixed']) - 5} more")


if __name__ == "__main__":
    main()
