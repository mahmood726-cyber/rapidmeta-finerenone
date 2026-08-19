#!/usr/bin/env python3
"""EVERY NUMERIC EFFECT CLAIM MUST TRACE TO THIS OBJECT'S OWN NUMBERS.

STATUS: NOT WIRED INTO THE HOOK. IT IS NOT READY, AND SAYING SO IS THE POINT.

It FIRES on the real contamination -- proven by replaying the block that actually shipped. But
it still reports 18 alarms on the corpus, and I HAVE NOT INSPECTED ALL EIGHTEEN. Those I did
inspect were correct text ("EARLY rhythm control" matching the EARLY trial). Baselining 18
uninspected hits as false positives would be asserting a conclusion I have not reached, which
is the defect this whole registry is about.

Five versions, each corrected by evidence: 61 alarms (numbers alone), 227 (root treated as one
block), 52 (case-insensitive matching), 18 (case-exact). The trend is right and the residue is
untriaged. Gate it when the 18 are adjudicated -- not before.

WHY THIS EXISTS RATHER THAN A SEVENTH SHAPE-MATCHER.

Six cross-topic contamination routes have now been found, and each defeated the guards built
for the previous five. The sixth reached a reader: a hardcoded

    "HR 0.87 (95% CI 0.79 to 0.96)" / "CLEAR Outcomes' OWN registry-posted analysis"

-- bempedoic acid's trial result -- rendered on a transthyretin amyloid CARDIOMYOPATHY page.
Different drug, different disease, a real number, shipped.

    THE FOREIGN-REGISTRATION-ID GUARD MATCHES NCT IDS, AND THAT TEXT NAMES NONE.
    THE IDENTICAL-OUTPUT ALARM COMPARES CASCADE KEYS, AND THAT TEXT LIVES IN r_output.
    TWO WORKING GUARDS, BOTH BLIND TO IT.

The count of contamination routes is not converging. Each new shape defeats the matchers written
for the last one, so writing a seventh matcher buys one shape and no more.

    THE ONLY FORM OF CHECK THAT DOES NOT NEED TO ANTICIPATE THE NEXT SHAPE IS ONE THAT ASSERTS
    A POSITIVE PROPERTY: EVERY SUBSTANTIVE CLAIM TRACES TO THIS OBJECT'S OWN TRIALS.

WHAT IT CHECKS. Effect estimates written in prose anywhere in a topic object -- `HR 0.87`,
`MD -54.82`, `RR 1.2 (0.9 to 1.6)` -- are extracted and matched against the numbers the object
itself holds: every `per_trial[].point`, every `pooled.point`, every declared CI bound, and any
numeric the object stores anywhere. A prose estimate that matches NO number the object holds did
not come from this object.

WHAT IT DOES NOT CLAIM, named rather than implied:
  - It does not verify a traced number is CORRECT, only that it is this object's.
  - A contaminating value that COINCIDES with one of this object's own numbers is invisible.
  - Non-numeric contamination -- a trial NAME, a population sentence -- is not covered. Those
    are the foreign-id guard's and the duplicate-text check's job.
It converts an open-ended "is anything foreign here" into a closed "does this number exist in
this object", which is the direction that does not require imagining the attacker.
"""
import io
import json
import os
import re
import sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SSOT = os.path.join(REPO, "ssot")
SKIP_TOKEN = "lint:allow-untraced-claim"

# THE NUMBER ALONE IS NOT THE SIGNAL, and a first version proved it: matching every prose
# effect estimate against the object's stored numbers raised 61 alarms of 236 claims, and the
# non-disclosure ones were all legitimate --
#     "MD = -57.1 - 6.3"                a DERIVATION showing its working; -57.1 is a component
#     "HR 0.63" in published_comparison an EXTERNAL synthesis's value, correctly attributed
#     "odds ratio of 0.4956"            a per-trial value at higher precision than stored
# A check that cannot tell a derivation from a contamination accuses the objects, which in this
# corpus are usually right.
#
# WHAT DISTINGUISHED THE REAL DEFECT was not the number but its PROVENANCE SENTENCE:
#     "HR 0.87 ... CLEAR Outcomes' OWN registry-posted analysis"
# CLEAR Outcomes is NCT02993406 -- bempedoic-acid-review's trial, and attr-cm-review does not
# include it. So the decidable form is:
#
#     A NUMERIC EFFECT CLAIM WHOSE OWN SENTENCE NAMES A TRIAL THAT BELONGS TO A DIFFERENT
#     TOPIC AND NOT TO THIS ONE.
#
# That needs no guess about which shape the contamination took, and it is closed on both sides:
# the acronym vocabulary is what the REGISTRY published, and the included set is what the
# OBJECT declares.
CLAIM = re.compile(
    r"\b(HR|OR|RR|MD|SMD|IRR|WMD|hazard ratio|odds ratio|risk ratio|mean difference)\b"
    r"\s*(?:=|of|:)?\s*(-?\d+\.\d+)", re.I)
NUM = re.compile(r"-?\d+\.\d+")

# published_comparison DESCRIBES OTHER SYNTHESES BY DESIGN. A foreign trial named there is the
# point of the section, not a defect.
EXTERNAL_BY_DESIGN = ("published_comparison", "removed_citations", "reconciliation")

CACHE = os.environ.get(
    "RM_CTGOV_CACHE",
    "F:/claude-temp/claude/F--rapidmeta-ssot-shell/"
    "eb4d84e5-8a24-4c3b-afe2-34bd91c20bc7/scratchpad/.ctgov-raw-cache")


def acronym_owners():
    """acronym AS THE REGISTRY PUBLISHED IT -> set of NCT ids. CASE PRESERVED, deliberately.

    Matching case-insensitively made ordinary prose hit registry acronyms that are also English
    words: "usual care" matched CARE, "pivotal trial" matched PIVOTAL -- 52 alarms, all on
    correct text. The alternative to a stopword list is not a longer stopword list.

        A STOPWORD LIST IS A PERMANENT ARGUMENT. CASE IS A FACT.

    The registry publishes CARE; prose writes care. Exact case separates them with no judgement.
    """
    vocab = {}
    if not os.path.isdir(CACHE):
        return vocab
    for fn in os.listdir(CACHE):
        if not fn.endswith(".json"):
            continue
        try:
            with io.open(os.path.join(CACHE, fn), encoding="utf-8") as fh:
                rec = json.load(fh)
        except (ValueError, OSError):
            continue
        idm = ((rec.get("protocolSection") or {}).get("identificationModule") or {})
        acr, nct = idm.get("acronym"), idm.get("nctId")
        if acr and nct and len(acr) >= 4:
            vocab.setdefault(acr, set()).add(nct)
    return vocab


def object_numbers(obj):
    """Every float the object holds ANYWHERE, as strings rounded to 2dp for comparison."""
    out = set()

    def walk(n):
        if isinstance(n, dict):
            for v in n.values():
                walk(v)
        elif isinstance(n, list):
            for v in n:
                walk(v)
        elif isinstance(n, (int, float)) and not isinstance(n, bool):
            out.add(round(float(n), 2))
    walk(obj)
    return out


def walk_blocks(node, path=""):
    """Every dict, represented by its OWN SCALAR FIELDS ONLY -- never its descendants.

    A BLOCK is the unit of attribution: a claim and the sentence saying where it came from are
    SIBLINGS. The contamination that shipped was exactly that shape --
        "estimate":   "HR 0.87 (95% CI 0.79 to 0.96)"
        "provenance": "CLEAR Outcomes' OWN registry-posted analysis"
    -- so a window inside one string could not see both.

    BUT INCLUDING DESCENDANTS MAKES THE ROOT OBJECT ONE BLOCK, and then every claim anywhere
    co-occurs with every acronym anywhere: 227 alarms, the first of them pairing an odds ratio
    with a trial named in an unrelated section. The smallest enclosing dict is the only scope
    that is both wide enough to see a sibling and narrow enough to mean anything.
    """
    if isinstance(node, dict):
        own = {k: v for k, v in node.items() if isinstance(v, (str, int, float))}
        if own:
            yield path, own
        for k, v in node.items():
            for r in walk_blocks(v, path + "." + k):
                yield r
    elif isinstance(node, list):
        for i, v in enumerate(node):
            for r in walk_blocks(v, "%s[%d]" % (path, i)):
                yield r


def walk_strings(node, path=""):
    if isinstance(node, dict):
        for k, v in node.items():
            for r in walk_strings(v, path + "." + k):
                yield r
    elif isinstance(node, list):
        for i, v in enumerate(node):
            for r in walk_strings(v, "%s[%d]" % (path, i)):
                yield r
    elif isinstance(node, str):
        yield path, node


def main():
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    vocab = acronym_owners()
    if not vocab:
        print("REFUSED: acronym vocabulary is EMPTY. A check with nothing to check against")
        print("passes everything, which is not a pass.")
        return 2
    # OVER-ESCAPED ONCE, AND IT IS THE MIRROR OF THE MANGLING CLASS. This read r"\\b(...)\\b",
    # which is a raw string containing backslash-backslash-b: it matches a literal backslash
    # followed by 'b', never a word boundary. It COMPILED, it RAN, the check reported
    # "0 foreign attributions" across 135 objects, and it could not have matched anything.
    #
    # lint_escape_hazards cannot see this: \\b inside a raw string is perfectly valid Python.
    # Under-escaping (\b -> 0x08) is detectable from the bytes; OVER-escaping is only
    # detectable by testing the pattern against a string it must match.
    #
    #     A GUARD THAT REPORTS SUCCESS WHILE UNABLE TO MATCH ANYTHING IS THE EXACT FAILURE
    #     THIS WHOLE FILE EXISTS TO PREVENT, AND IT HAPPENED INSIDE IT.
    # Caught only because the known-answer test replayed the REAL contamination.
    vocab_re = re.compile(r"\b(%s)\b"
                          % "|".join(re.escape(a) for a in sorted(vocab, key=len, reverse=True)))

    hits, scanned, claims_seen = [], 0, 0
    for d in sorted(os.listdir(SSOT)):
        p = os.path.join(SSOT, d, d + ".json")
        if not os.path.exists(p):
            continue
        try:
            with io.open(p, encoding="utf-8") as fh:
                obj = json.load(fh)
        except (ValueError, OSError):
            continue
        scanned += 1
        mine = {t.get("nct") for t in ((obj.get("inputs") or {}).get("trials") or [])
                if t.get("nct")}
        for path, block in walk_blocks(obj):
            if any(seg in path for seg in EXTERNAL_BY_DESIGN):
                continue
            text = json.dumps(block, ensure_ascii=False)
            if SKIP_TOKEN in text:
                continue
            claims = list(CLAIM.finditer(text))
            if not claims:
                continue
            claims_seen += len(claims)
            # CASE-EXACT, AND IT REPLACES A STOPWORD LIST. Uppercasing the text made ordinary
            # prose match registry acronyms that are also English words -- "usual care" hit
            # CARE, "pivotal trial" hit PIVOTAL. A stopword list is a permanent argument; case
            # is a fact. The registry publishes CARE and prose writes care.
            for g in vocab_re.finditer(text):
                owners = vocab.get(g.group(1)) or set()
                if owners & mine:
                    continue                  # this object's own trial: correct attribution
                hits.append((d, path, claims[0].group(0), g.group(1), sorted(owners)[:2],
                             " ".join(text.split())[:130]))
                break

    for d, path, claim, acr, owners, excerpt in hits:
        print("%s  %s" % (d, path))
        print("      claims %r attributed to %r -- a trial this object does NOT include"
              % (claim, acr))
        print("      %s belongs to %s" % (acr, owners))
        print("      ...%s..." % excerpt)
    print()
    print("topic objects scanned            %d" % scanned)
    print("numeric effect claims examined   %d" % claims_seen)
    print("acronym vocabulary               %d registry-published acronyms" % len(vocab))
    print("claims attributed to a FOREIGN trial %d" % len(hits))
    if hits:
        print()
        print("REFUSED: %d numeric claim(s) name a trial their own object does not include."
              % len(hits))
        print("A result attributed to another topic's trial did not come from this review.")
        print("Deliberate exception: %s on the line." % SKIP_TOKEN)
        return 1
    print()
    print("no numeric effect claim is attributed to a trial its object does not include.")
    print("NOT CHECKED, and named: a contaminating claim that names NO trial; one naming a")
    print("trial with no registry acronym; and whether a correctly-attributed number is right.")
    print("published_comparison and its neighbours are excluded -- naming other syntheses'")
    print("trials is what those sections are FOR.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
