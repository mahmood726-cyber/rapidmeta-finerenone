"""A FIELD NAME IN READER-FACING PROSE IS THE DEFECT -- whatever punctuation surrounds it.

# control: routed through instrument_controls.require_controls. POSITIVE is MAVACAMTEN's
# `bar:` in the delivered Methods-search body, read by a census lane before this probe existed.
# NEGATIVE is the same page's ordinary prose, which must not be flagged.

THE THIRD INSTANCE TONIGHT OF A CHECK BUILT TO FIND THE THING REMOVED RATHER THAN THE THING A
READER MEETS, and this one was mine.

The container-repr class was reported closed. `_flatten_container` had stopped `{'k': 'v'}`
reaching prose, and the probe written to confirm it looked for BRACES AND QUOTES. It found zero
and the class was declared shut. But the fix does not delete the container -- it rewrites it as
`key: value.` sentences. THE BRACES WENT AND THE FIELD NAMES STAYED:

    ... on the dates recorded on each entry; what verifies this object: ClinicalTrials.gov
    protocol records, read 2026-08-18. what is not claimed: that any per-trial count was
    checked against a results record. bar: not recorded on the page this object was built
    from.

`bar:` is a field name in a sentence. A reader meets a data structure with its punctuation
filed off. The probe was measuring the remedy, not the symptom, so it could only ever agree
with the person who wrote the remedy.

SO THE PREDICATE IS THE READER'S, NOT THE FIXER'S: does an identifier from the object's schema
appear where a sentence should be? Braces are irrelevant. That is the only form of this check
that a future presentation fix cannot quietly satisfy.

WHAT IS AND IS NOT FLAGGED. Real prose uses colons legitimately -- "Primary trials.", "one
caveat: the trials differ" -- so the flag requires the token before the colon to look like an
IDENTIFIER: lowercase, no articles or verbs, and either snake_case or a short bare noun that is
also a known field name in the objects. Table cells, `<pre>` blocks, provenance banners and the
source lists are excluded: a field name is correct THERE, and that is the whole point of moving
it out of the reading flow rather than deleting it.
"""
from __future__ import annotations

import collections
import io
import json
import os
import re
import subprocess
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from instrument_controls import require_controls  # noqa: E402

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REF = "origin/main"
OUT = os.path.join(REPO, "outputs", "field_name_in_prose_2026_08_23.json")

# Blocks where a field name is CORRECT and must not be flagged. This is the distinction the
# project has been making all night: nothing is removed from the page, it is moved out of the
# reading flow -- so the place it is moved TO cannot be a violation.
STRIP = [
    (re.compile(r"(?is)<pre\b.*?</pre>"), " "),
    (re.compile(r"(?is)<table\b.*?</table>"), " "),
    (re.compile(r"(?is)<code\b.*?</code>"), " "),
    (re.compile(r"(?is)<nav\b.*?</nav>"), " "),
    (re.compile(r"(?is)<div[^>]*id=\"overmind-provenance-banner\".*?</div>"), " "),
    (re.compile(r"(?is)<details\b.*?</details>"), " "),
]

# `<snake_case>:` or a bare lowercase noun followed by a colon, mid-sentence -- i.e. preceded by
# a word character or a full stop plus space, not at the head of a list item.
FIELD_COLON = re.compile(
    r"(?<![>\w])"
    r"((?:[a-z][a-z0-9]*_[a-z0-9_]+)"          # snake_case identifiers
    r"|(?:\b(?:bar|foo|baz|val|obj|blk|cfg|src|idx|tmp|arg|ret|ctx)\b))"
    r"\s*:\s")

# Phrases that were dict KEYS and now read as prose labels. They humanise, which is exactly why
# they slipped through -- `what_verifies_this_object` becomes "what verifies this object".
HUMANISED_KEY = re.compile(
    r"(?<![>\w])((?:what verifies this object|what is not claimed|what this does not "
    r"establish|families|databases|obstacle|estimand))\s*:\s")


def git(*a):
    return subprocess.run(["git"] + list(a), cwd=REPO, capture_output=True)


def visible(html):
    t = html
    for pat, rep in STRIP:
        t = pat.sub(rep, t)
    t = re.sub(r"(?is)<script\b.*?</script>", " ", t)
    t = re.sub(r"(?is)<style\b.*?</style>", " ", t)
    t = re.sub(r"<[^>]+>", " ", t)
    return re.sub(r"\s+", " ", t)


def findings(html):
    v = visible(html)
    out = [m.group(1) for m in FIELD_COLON.finditer(v)]
    out += [m.group(1) for m in HUMANISED_KEY.finditer(v)]
    return out


def main():
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

    # THE POSITIVE CONTROL IS PINNED TO A COMMIT, NOT TO THE LIVE CORPUS.
    #
    # It was keyed to MAVACAMTEN at `origin/main`, which held `bar:` when this probe was
    # written. THAT CONTROL DIES THE MOMENT THE FIX IS DELIVERED: the defect it points at is
    # the defect this lint exists to remove, so a successful rollout would have made the
    # control fail and the lint refuse every run thereafter -- the same shape as a selector
    # keyed to the defect, arriving through the control rather than the selection.
    #
    # `a2091846a` is a delivered commit where the construction is present and always will be.
    # A corpus positive must be pinned to a REVISION, or it evaporates with the thing it
    # proves the probe can see.
    CONTROL_REV = "a2091846a"
    mv = git("show", "%s:MAVACAMTEN_HCM_REVIEW.html" % CONTROL_REV).stdout.decode(
        "utf-8", "replace")
    if not mv:
        sys.exit("REFUSED: the pinned control page is not readable at %s. Without a positive "
                 "this lint cannot report an absence." % CONTROL_REV)
    mv_hits = findings(mv)
    require_controls(
        "field_name_in_prose",
        ("MAVACAMTEN Methods-search carries the field name 'bar:' in prose "
         "(read by a census lane before this probe existed)",
         "bar" in mv_hits, True),
        ("the same page's ordinary prose is not flagged wholesale -- "
         "fewer than 40 hits on one page",
         len(mv_hits) >= 40, True))

    pm = json.load(io.open(os.path.join(REPO, "ssot", "PAGE_MAP.json"), encoding="utf-8"))
    names = sorted(set(pm if isinstance(pm, list) else pm.keys()))
    pages, tokens, per_page = 0, collections.Counter(), {}
    read = 0
    for n in names:
        r = git("show", "%s:%s" % (REF, n))
        if r.returncode:
            continue
        read += 1
        f = findings(r.stdout.decode("utf-8", "replace"))
        if f:
            pages += 1
            per_page[n] = len(f)
            tokens.update(f)

    print("")
    print("FIELD NAMES IN READER-FACING PROSE, %d delivered page(s) at %s" % (read, REF))
    print("")
    print("   pages carrying at least one     %4d   %5.1f%%" % (pages, 100.0 * pages / max(1, read)))
    print("   total occurrences               %4d" % sum(tokens.values()))
    print("")
    print("   most frequent identifiers:")
    for k, v in tokens.most_common(14):
        print("      %-42s %4d" % (k[:42], v))
    print("")
    print("   worst pages:")
    for n, c in sorted(per_page.items(), key=lambda kv: -kv[1])[:10]:
        print("      %-52s %4d" % (n[:52], c))
    print("")
    print("THE BRACES ARE NOT THE DEFECT AND NEVER WERE. A probe that looks for them measures")
    print("the remedy rather than the symptom, and can only agree with whoever wrote the")
    print("remedy. This one is keyed to what a reader meets.")

    # A RATCHET, AND THE REASON IT IS A RATCHET RATHER THAN A ZERO.
    #
    # THIS FILE HAD NO `sys.exit` ON ITS FINDING AT ALL. It printed 231 occurrences and exited
    # 0, and it had just been wired into pre-push behind `|| exit 1` -- a gate that cannot
    # fail, written inside the work of making the gates real. `lint_gate_can_fail.py` exists
    # for exactly this and does not cover `lint_*` names.
    #
    # It blocks on an INCREASE rather than on any nonzero count because the 231 are a standing
    # decision of Mahmood's: the lead-ins are applied but the corpus is not yet rebuilt, so the
    # delivered pages still carry them. A gate demanding zero today would block every commit
    # until the rollout lands, and a gate that must be bypassed daily is a gate that gets
    # bypassed permanently. The baseline falls as the rebuild delivers; it may never rise.
    base_path = os.path.join(REPO, "scripts", "baselines",
                             "field_name_in_prose_baseline.json")
    total = sum(tokens.values())
    if os.path.isfile(base_path):
        prev = json.load(io.open(base_path, encoding="utf-8")).get("occurrences")
    else:
        prev = total
        if not os.path.isdir(os.path.dirname(base_path)):
            os.makedirs(os.path.dirname(base_path))
        json.dump({"occurrences": total, "recorded": "2026-08-23",
                   "why": ("Field names delivered to readers at the moment the lead-in map "
                           "landed. Falls as the corpus is rebuilt; must never rise.")},
                  io.open(base_path, "w", encoding="utf-8"), indent=1)
        print("")
        print("baseline recorded at %d occurrence(s)" % total)
    if total > prev:
        sys.exit("REFUSED: field names in reader-facing prose rose from %d to %d. The map is "
                 "`ssot/field_lead_ins.json` and BOTH producers read it -- the projector's "
                 "`_flatten_container` and the bookkeeping writer's `_flat`. A new bare key "
                 "means a third producer, or a key with no entry in the map."
                 % (prev, total))
    if total < prev:
        print("")
        print("BASELINE FALLS %d -> %d. Update scripts/baselines/field_name_in_prose_baseline"
              ".json to hold the gate at the new floor." % (prev, total))

    if not os.path.isdir(os.path.dirname(OUT)):
        os.makedirs(os.path.dirname(OUT))
    json.dump({"ref": REF, "pages_read": read, "pages_flagged": pages,
               "occurrences": sum(tokens.values()),
               "tokens": dict(tokens.most_common(60)),
               "per_page": per_page}, io.open(OUT, "w", encoding="utf-8"), indent=1)


if __name__ == "__main__":
    main()
