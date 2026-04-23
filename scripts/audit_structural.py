#!/usr/bin/env python3
# sentinel:skip-file — developer tool; hardcoded ROOT is intentional (local Finrenone checkout only)
"""Pass 1: structural integrity audit across all 99 _REVIEW.html apps.

Checks:
  - Div balance (`<div[\s>]` opens vs `</div>` closes); CFTR baseline is +1
  - Literal `</script>` inside JS string literals (fatal)
  - Expected sentinels per migration (present or absent as expected)
  - Unique top-level function definitions (no accidental duplicates)
"""
import pathlib, re, sys, io

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

ROOT = pathlib.Path(r"C:\Projects\Finrenone")

SENTINELS_EXPECTED = [
    ("const AbstractHydrator = {",     "AbstractHydrator",       "all"),
    ("const EvidenceHydrator = {",     "EvidenceHydrator",       "all"),
    ("__rmExportPatched",              "Plotly export patch",    "all"),
    ("/* Defensive re-hydration",      "setView rehydrate",      "all"),
    ("// Outcome metadata for journal-style language.", "Enhanced journal text", "all"),
    ("function generateNMAManuscriptText()", "NMA text generator", "nma"),
    ("_getNetworkOutcomeKeys",         "Multi-outcome NMA",      "nma"),
    ("// Preserve trial-level tE/cE when the outcome entry omits them", "undefined/N fix", "most"),
]

# The 3 legacy-template apps that lack the undefined/N fix (deliberate skip).
LEGACY_SKIP_UNDEFINED_FIX = {"COLCHICINE_CVD_REVIEW.html", "GLP1_CVOT_REVIEW.html", "SGLT2_HF_REVIEW.html"}


def audit(path: pathlib.Path):
    text = path.read_text(encoding="utf-8", newline="")
    is_nma = bool(re.search(r"^        const NMA_CONFIG = \{", text, re.MULTILINE)) and "NMA_CONFIG = null" not in text

    findings = []

    # Div balance
    opens  = len(re.findall(r"<div[\s>]", text))
    closes = len(re.findall(r"</div>", text))
    balance = opens - closes
    if balance != 1:
        findings.append(f"DIV_BALANCE({balance})")

    # Literal </script> inside string/template literals (rough heuristic — look for quoted </script>)
    script_hazards = len(re.findall(r"""['"`]\s*</script>\s*['"`]""", text))
    if script_hazards:
        findings.append(f"SCRIPT_HAZARD({script_hazards})")

    # Expected sentinels
    for sentinel, name, scope in SENTINELS_EXPECTED:
        expected_present = (
            scope == "all"
            or (scope == "nma" and is_nma)
            or (scope == "most" and path.name not in LEGACY_SKIP_UNDEFINED_FIX)
        )
        present = sentinel in text
        if expected_present and not present:
            findings.append(f"MISSING_SENTINEL({name})")
        elif scope == "nma" and not is_nma and present:
            findings.append(f"UNEXPECTED_NMA_CODE_IN_PAIRWISE({name})")

    # Duplicate top-level function definitions. Match `        function XYZ(` at column 8
    # (the common indent for top-level inline script functions in this template).
    fn_names = re.findall(r"^        function (\w+)\(", text, re.MULTILINE)
    dup = [n for n in set(fn_names) if fn_names.count(n) > 1]
    if dup:
        findings.append(f"DUP_FN({','.join(dup)})")

    return findings


def main():
    targets = sorted(ROOT.glob("*_REVIEW.html"))
    clean = 0
    problems = {}
    for p in targets:
        f = audit(p)
        if f:
            problems[p.name] = f
        else:
            clean += 1
    print(f"Pass 1 — structural integrity")
    print(f"  {clean}/{len(targets)} clean, {len(problems)} with findings")
    if problems:
        print()
        for name, f in sorted(problems.items()):
            print(f"  {name}: {'; '.join(f)}")


if __name__ == "__main__":
    main()
