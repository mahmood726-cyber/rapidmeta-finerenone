"""Close the adversarial findings from the laptop review of the SSOT signals.

Every one of these is a guard that would have passed a page it exists to catch.
The pattern across them is the same and worth naming: each was written to match
the shape of the ONE bad page I had in front of me, not the class of bad pages.
Attribute order, a hyphen, a full stop, a substring boundary -- none changes what
the defect IS, and every one of them defeated the check.
"""
import ast
import io
import re
import sys

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
N = [0]


def sub(path, old, new, tag):
    s = open(path, encoding="utf-8").read()
    if old not in s:
        raise SystemExit("ANCHOR MISSING (%s)" % tag)
    open(path, "w", encoding="utf-8").write(s.replace(old, new, 1))
    N[0] += 1
    print("  %s" % tag)


S = "scripts/ssot_signals.py"

# 6 -- READY-ISH passed because (?![A-Za-z]) permits a hyphen.
sub(S, r'r"(READY|NOT READY|NOT YET DETERMINED)(?![A-Za-z])", text)',
    r'r"(READY|NOT READY|NOT YET DETERMINED)(?![-\w])", text)',
    "sig_no_verdict: anchor rejects READY-ISH as well as READYISH")

# 7 -- the two-human check tested a SUBSTRING, so READYISH satisfied it.
sub(S, '    if "Submission readiness: READY" in text:\n        return None',
    '    # Substring, not state. "Submission readiness: READYISH" contains\n'
    '    # "Submission readiness: READY" and silenced the worst claim the page\n'
    '    # can carry. Anchored to the exact state.\n'
    '    if re.search(r"Submission readiness:\\s*READY(?![-\\w])", text):\n'
    '        return None',
    "sig_unsourced_two_human_claim: anchored, not substring")

# 5 -- attribute order. class before id was assumed.
sub(S, r'r\'<section class="panel" id="(pn-[a-z]+)"(.*?)</section>\'',
    r'r\'<section\\b(?=[^>]*class="[^"]*panel)(?=[^>]*id="(pn-[a-z]+)")[^>]*>(.*?)</section>\'',
    "sig_empty_panel: attribute-order agnostic")

# 11 -- a full stop after None broke the value-slot match.
sub(S, r'((r">\s*(?:None|undefined|NaN)\s*<", "bare None/undefined/NaN in a value slot"),',
    r'((r">\s*(?:None|undefined|NaN)\s*[.,;:]?\s*<",'
    r' "bare None/undefined/NaN in a value slot"),',
    "sig_placeholder_leak: trailing punctuation no longer hides it")

# 9 -- "badger-note" matched "badge".
sub(S, r'r"""class=["\'][^"\']*(?:badge|banner)[^"\']*["\'][^>]*>\s*"',
    r'r"""class=["\'][^"\']*\b(?:badge|banner)\b[^"\']*["\'][^>]*>(?:\s|<[^>]+>)*"',
    "sig_constant_verdict: word boundary, and reaches through a child element")

# 10 -- a NEGATED footer sentence satisfied the check.
sub(S, '    return (None if "projected from a single canonical object" in text\n'
       '            else "projection provenance footer missing")',
    '    # A negated sentence contains the phrase. "This page is NOT projected\n'
    '    # from a single canonical object" passed the check that exists to\n'
    '    # confirm the opposite claim.\n'
    '    if re.search(r"\\b(?:not|never|isn\'t|is not)\\s+projected from a single "\n'
    '                 r"canonical object", text, re.I):\n'
    '        return "page DENIES the projection claim the footer should make"\n'
    '    return (None if "projected from a single canonical object" in text\n'
    '            else "projection provenance footer missing")',
    "sig_no_projection_footer: rejects the negated form")

for f in (S,):
    ast.parse(open(f, encoding="utf-8").read())
print("\n%d fixes applied; module parses" % N[0])
