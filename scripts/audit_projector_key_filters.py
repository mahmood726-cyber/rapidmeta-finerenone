"""Renderers that enumerate the keys they know, and the objects carrying a key they drop.

THE INSTANCE. `_grade_step_words` rendered a GRADE rating step by naming five fields --
domain, levels, from, to, reason -- and SILENTLY DISCARDED every other key. On
`alirocumab-lipid` one step carries `reason_superseded_2026_08_20`: "k = 8 and the interval
(-60.23 to -49.42) excludes the null." That sentence, holding the pool's own interval,
vanished from the delivered page. INTRODUCED BY THE FIX FOR READABILITY.

A FORMATTER THAT HANDLES FIVE KEYS AND DISCARDS THE REST IS A FILTER, AND THE DIFFERENCE IS
INVISIBLE UNTIL THE SIXTH KEY EXISTS.

AND THE SELECTION EFFECT IS THE OPPOSITE OF THE INTUITIVE ONE, WHICH IS WHY IT IS RECORDED
HERE RATHER THAN LEFT AS A DETAIL. A filter that drops unusual keys does its damage on the
objects with the MOST correction history -- the ones carrying `reason_superseded_*`,
`restated_*`, `corrected_from`, `why_this_replaces_*`. Those are the topics that have been
worked on hardest. THE NEGLECTED PAGES WERE SAFE FROM IT, because a thin object has nothing
unusual to lose. Every quality signal we have points at the pages this class hurts most.

WHAT THIS SWEEPS. Two halves, and only together do they mean anything:

  RENDERERS  a function in the projectors that reads a dict by naming fields -- three or
             more `.get("literal")` calls on the same value -- and emits text. Reported as
             CANDIDATES. Naming fields is not wrong; a renderer that names five fields AND
             prints nothing else is.
  OBJECTS    the corpus, asked whether any current object carries a key outside a
             renderer's known set. THIS IS THE HALF THAT DECIDES, because a filter with no
             unusual key to drop is latent rather than firing.

Reported separately and never summed. A latent filter is a real risk and is not a defect on
any page today; conflating the two would overstate the finding, and the overstatement would
be in the accusing direction.

HOW THE COUNT WAS ARRIVED AT, AND WHERE THE JUDGEMENT SITS. This matters more than the
number and it is stated here rather than in a commit message that scrolls away.

    PREDICTED, before the sweep ran:  6 to 10 renderers, 1 to 3 objects at risk.
    MEASURED:                        42 renderers, 27 of which print only the keys they
                                     name, and 192 object-side hits across four sites.

THE PREDICTION WAS WRONG BY A FACTOR OF FIVE, IN THE DIRECTION THAT UNDERSTATED THE RISK.

And then the number came down again -- because of the sole-rendering discriminator: a
renderer is a FILTER only where it is the node's ONLY rendering. A GRADE step is: the table
cell IS the step, so a key not printed there is not printed anywhere. `pooled.withdrawn_utc`
is not: the pooled node's parts appear across several sentences and tables, and a timestamp
that does not recite inside an effect sentence has not been lost.

THE DISCRIMINATOR WAS FORMULATED AFTER SEEING 192 HITS, NOT BEFORE. That is exactly where
motivated reasoning enters -- a rule invented while looking at an uncomfortable number, that
happens to shrink it. The test is sound on its merits and it is kept. But it was not
predicted, it was not pre-registered, and it must not be read as a measurement.

SO THE HONEST STATE IS: 42 renderers found, ONE adjudicated (`_grade_step_words`, which was
a real filter and lost a delivered sentence), and 27 SOLE-PRINTING RENDERERS UNADJUDICATED.
Deciding which of those 27 are the only rendering of their node requires reading each one
against the pages it produces. It is queued, not done, and nobody should read "42, mostly
fine" as a finding until it is.
"""

import io
import os
import re
import sys
import ast
import json
import glob

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from instrument_controls import require_controls

PROJECTORS = ["ssot/paper_projector.py", "ssot/projectors.py", "ssot/projectors2.py",
              "ssot/build_tabbed.py"]

# Known-key sets that are ALREADY enforced against the objects, keyed by the object path
# they render. Each is (dotted path to a list-of-dicts, known keys, why).
OBJECT_SITES = [
    ("grade.by_outcome.*.steps",
     set(["domain", "levels", "from", "to", "reason"]),
     "the GRADE rating steps -- THE INSTANCE, now printing every key"),
    ("results.by_outcome.*.heterogeneity",
     set(["i2", "tau2", "q", "df", "p", "tau", "h2", "i2_ci_low", "i2_ci_high",
          "method", "note"]),
     "the heterogeneity block, read field by field into a sentence"),
    ("results.by_outcome.*.pooled",
     set(["measure", "point", "ci_low", "ci_high", "ci_level", "scale", "withdrawn",
          "withdrawn_reason", "pooled_ve_percent", "pooled_ve_ci_low_percent",
          "pooled_ve_ci_high_percent", "pi_low", "pi_high"]),
     "the pooled estimate block"),
    ("inputs.trials.*.arms",
     set(["label", "role", "events", "participants", "n", "mean", "sd"]),
     "the arms table"),
]

GETTER = re.compile(r'\.get\(\s*["\']([A-Za-z_][\w]*)["\']')


def renderers():
    """Functions that read a dict by naming three or more literal keys and emit text."""
    out = []
    for rel in PROJECTORS:
        path = os.path.join(REPO, rel)
        if not os.path.exists(path):
            continue
        src = io.open(path, encoding="utf-8", errors="replace").read()
        try:
            tree = ast.parse(src)
        except SyntaxError:
            out.append((rel, 0, "UNPARSED", []))
            continue
        lines = src.split("\n")
        for node in ast.walk(tree):
            if not isinstance(node, (ast.FunctionDef,)):
                continue
            seg = "\n".join(lines[node.lineno - 1:getattr(node, "end_lineno", node.lineno)])
            keys = GETTER.findall(seg)
            if len(set(keys)) < 3:
                continue
            emits = ("return" in seg and ('"' in seg or "'" in seg)) or ".append(" in seg
            if not emits:
                continue
            prints_rest = ("for k, v in" in seg or ".items()" in seg)
            out.append((rel, node.lineno, node.name, sorted(set(keys)), prints_rest))
    return out


def walk_star(obj, dotted):
    """Yield every value at a dotted path where `*` matches any dict key or list index."""
    parts = dotted.split(".")

    def rec(node, i):
        if node is None:
            return
        if i == len(parts):
            yield node
            return
        p = parts[i]
        if p == "*":
            if isinstance(node, dict):
                for v in node.values():
                    for r in rec(v, i + 1):
                        yield r
            elif isinstance(node, list):
                for v in node:
                    for r in rec(v, i + 1):
                        yield r
            return
        if isinstance(node, dict):
            for r in rec(node.get(p), i + 1):
                yield r
    return list(rec(obj, 0))


def object_side():
    """-> [(topic, site, unknown keys)] for keys a known-key renderer would not print."""
    hits = []
    for path in sorted(glob.glob(os.path.join(REPO, "ssot", "*", "*.json"))):
        topic = os.path.basename(os.path.dirname(path))
        if os.path.basename(path) != topic + ".json":
            continue
        try:
            obj = json.load(io.open(path, encoding="utf-8"))
        except Exception:
            continue
        for dotted, known, _why in OBJECT_SITES:
            for node in walk_star(obj, dotted):
                items = node if isinstance(node, list) else [node]
                extra = set()
                for it in items:
                    if isinstance(it, dict):
                        extra |= (set(it) - known)
                if extra:
                    hits.append((topic, dotted, sorted(extra)))
    return hits


def main():
    # CONSTRUCTED CONTROLS -- class 58. The positive is the exact step that lost a sentence
    # on alirocumab; the negative is a step with only known keys, which must NOT be flagged.
    known = OBJECT_SITES[0][1]
    pos = set({"domain": 1, "levels": 1, "reason": 1,
               "reason_superseded_2026_08_20": 1}) - known
    neg = set({"domain": 1, "levels": 1, "from": 1, "to": 1, "reason": 1}) - known
    require_controls(
        "audit_projector_key_filters",
        positive=("the alirocumab GRADE step that lost its interval sentence", bool(pos),
                  True),
        negative=("a GRADE step carrying only the five known keys", bool(neg), True))

    rs = renderers()
    print("")
    print("RENDERERS THAT NAME THREE OR MORE LITERAL KEYS AND EMIT TEXT: %d" % len(rs))
    print("CANDIDATES, NOT DEFECTS. Naming fields is normal; naming five and printing")
    print("nothing else is the filter. The right-hand column says whether the function also")
    print("iterates the remaining items.")
    for row in rs:
        if len(row) == 4:
            print("    %s:%d  %s  UNPARSED" % row[:3] + "")
            continue
        rel, ln, name, keys, rest = row
        print("    %-28s %-34s %s  keys=%d" % ("%s:%d" % (os.path.basename(rel), ln), name,
                                               "prints the rest" if rest else "KNOWN ONLY",
                                               len(keys)))

    hits = object_side()
    print("")
    print("OBJECTS CARRYING A KEY A KNOWN-KEY RENDERER WOULD DROP: %d" % len(hits))
    print("THIS IS THE HALF THAT DECIDES. A filter with nothing unusual to drop is latent.")
    for topic, dotted, extra in hits:
        print("    %-40s %-38s %s" % (topic, dotted, ", ".join(extra)))

    print("")
    print("THE SELECTION EFFECT, STATED BECAUSE IT IS COUNTERINTUITIVE: a filter that drops")
    print("unusual keys does its damage on the objects with the MOST correction history.")
    print("The thin, neglected pages have nothing unusual to lose. This class hurts our best")
    print("topics and spares our worst.")


if __name__ == "__main__":
    main()
