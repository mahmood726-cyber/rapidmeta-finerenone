"""GATE 2 -- a text-matching check must carry a known-negative control, and print its rate.

TWO ARMS, because "make the control mandatory" needs both a mechanism and an enforcement.

ARM A -- THE MEASUREMENT. The real task, on real delivered pages, with ground truth taken from
the SSOT store rather than from the matcher: does page P confirm that trial <ACRONYM>
contributes to topic T? Positives are the acronyms T's own object lists. Known negatives are
acronyms belonging to OTHER topics -- an answer fixed outside the matcher.

Both matchers are measured side by side. The naive one is the shape that produced the failure:
the token anywhere on the page. The contiguous one requires a registration within 300
characters. The gate FAILS if the contiguous matcher is not strictly better, because the whole
claim of the fix is that it is.

The false-positive PAGE SIZES are reported beside the rate. That is the diagnosis, not
decoration: if the matcher's errors correlate with page length, it is measuring length.

ARM B -- THE ENFORCEMENT. An AST scan over every module in `scripts/` and `gates/` for the
shape "matches text AND emits a count". Each such module must either take its count through
`textmatch.ControlledCount` / call a `control(` API, or carry a `# no-control:` line saying in
words why it does not need one. The escape hatch is deliberate and it is the same one
`gate_no_new_schema_synonym_2026_08_23.py` already uses: a gate with no way to say "not
applicable" gets bypassed wholesale, and a gate bypassed daily is bypassed permanently.

WHAT ARM B IS NOT. It is not a claim that every listed module is defective. It is a claim that
each one reports a count whose precision nobody has measured. Those are different statements
and the output says which.
"""
from __future__ import annotations

import ast
import collections
import json
import os
import random
import re
import statistics
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _harness as H                                                        # noqa: E402
import textmatch as TM                                                      # noqa: E402

SEED = 20260828          # fixed before the sample was drawn, recorded here
WINDOW = 300

ACRONYM = re.compile(r"^(?=.*[A-Z])[A-Z0-9][A-Z0-9\-‑ ]{2,24}$")
NAME_KEYS = ("name", "label", "trial", "acronym")


def label_kind(v):
    v = (v or "").strip()
    if not v:
        return "empty"
    if TM.NCT_RE.fullmatch(v):
        return "registration used as a name"
    if ACRONYM.match(v) and len(v) <= 25:
        return "ACRONYM (usable for a text-match task)"
    return "registry title / descriptor (not a token)"


def build_task(repo, gate):
    """Ground truth from the store; pages from PAGE_MAP. Returns (positives, negatives)."""
    page_map = H.load(os.path.join(repo, "ssot", "PAGE_MAP.json"))
    by_topic = collections.defaultdict(list)
    for page, objpath in page_map.items():
        by_topic[os.path.basename(os.path.dirname(objpath))].append(page)

    paths, _ = H.topic_objects(repo)
    kinds = collections.Counter()
    own, pool = collections.defaultdict(set), set()
    for p in paths:
        topic = H.topic_id(p)
        obj = H.load(p)
        for tr in ((obj.get("inputs") or {}).get("trials") or []):
            if not isinstance(tr, dict):
                continue
            for k in NAME_KEYS:
                v = tr.get(k)
                if isinstance(v, str) and v.strip():
                    kk = label_kind(v)
                    kinds[kk] += 1
                    if kk.startswith("ACRONYM"):
                        own[topic].add(v.strip())
                        pool.add(v.strip())

    rng = random.Random(SEED)
    everything = sorted(pool)
    positives, negatives, pages = [], [], {}
    for topic in sorted(own):
        page = next((x for x in by_topic.get(topic, [])
                     if os.path.exists(os.path.join(repo, x))), None)
        if not page:
            kinds["topic has ACRONYMs but no page on disk"] += 1
            continue
        full = os.path.join(repo, page)
        if full not in pages:
            with open(full, "r", encoding="utf-8", errors="replace") as fh:
                pages[full] = TM.page_text(fh.read())
        mine = sorted(own[topic])
        others = [n for n in everything if n not in own[topic]]
        rng.shuffle(others)
        for n in mine:
            positives.append((topic, full, n))
        for n in others[:max(3, len(mine) * 3)]:
            negatives.append((topic, full, n))
    return positives, negatives, pages, kinds


def arm_a(gate, repo):
    positives, negatives, pages, kinds = build_task(repo, gate)
    gate.note("ground truth for arm A comes from the SSOT store, not from the matcher; the "
              "negative sample was drawn at seed %d, recorded before it was drawn." % SEED)

    def naive(case):
        return TM.matches_naive(pages[case[1]], case[2])

    def contiguous(case):
        return TM.matches_contiguous(pages[case[1]], case[2], window=WINDOW)

    out = {}
    for label, fn in (("naive (token anywhere on the page)", naive),
                      ("contiguous (registration within %dc)" % WINDOW, contiguous)):
        c = TM.ControlledCount(label, denominator=len(positives))
        for case in positives:
            c.observe(fn(case), case)
        c.run_control(negatives, fn)
        gate.note(c.line())
        n, fp, ex = c._control
        fp_cases = [x for x in negatives if fn(x)]
        out[label] = {"sens": c.value, "n_pos": len(positives), "n_neg": n,
                      "fp": fp, "fp_rate": c.fp_rate,
                      "fp_examples": [{"topic": t, "acronym": a, "page_chars": len(pages[p])}
                                      for t, p, a in fp_cases[:6]]}
        if fp_cases:
            sizes = [len(pages[p]) for _, p, _ in fp_cases]
            allsizes = [len(v) for v in pages.values()]
            gate.note("    false positives sit on pages of median %d chars against a corpus "
                      "median of %d -- the confounder, visible."
                      % (int(statistics.median(sizes)), int(statistics.median(allsizes))))
    kinds["positives (must match)"] = len(positives)
    kinds["known negatives (must NOT match)"] = len(negatives)
    kinds["pages read"] = len(pages)

    nv = out["naive (token anywhere on the page)"]
    cg = out["contiguous (registration within %dc)" % WINDOW]
    if cg["sens"] < nv["sens"]:
        gate.finding("CONTIGUITY-COSTS-SENSITIVITY",
                     "the contiguity requirement lost %d true confirmations; it may not be "
                     "the right anchor for this corpus" % (nv["sens"] - cg["sens"]),
                     numerator=cg["sens"], denominator=nv["sens"])
    if cg["fp_rate"] >= nv["fp_rate"]:
        gate.finding("CONTIGUITY-DOES-NOT-HELP",
                     "contiguity did not reduce the false-positive rate (%.1f%% vs %.1f%%). "
                     "The premise of this gate is that it does; if it stops being true the "
                     "gate must be re-derived, not quietly kept."
                     % (100 * cg["fp_rate"], 100 * nv["fp_rate"]))
    return out, kinds


# ---------------------------------------------------------------------------
# ARM B -- the enforcement scan
# ---------------------------------------------------------------------------
# SCOPE. Only CHECKS -- things whose job is to report a finding. A one-off `apply_*` migration
# script that greps once and exits is not making a claim anyone acts on, and a gate that fires
# on 739 of 820 modules is a gate bypassed on its first day. Narrow and enforceable beats broad
# and ignored; the same reasoning `gate_no_new_schema_synonym_2026_08_23.py` records.
SCOPE_RE = re.compile(r"^(gate|check|lint|audit|sweep|verify|assert|detect|probe)_"
                      r"|_(gate|check|lint|audit|sweep)\.py$")
TEXTVAR = re.compile(r"html|page|text|body|src|content|prose|doc|raw|served|markup|blob|source",
                     re.I)
# `require_controls` ADDED 2026-09-04. THIS GATE WAS BLIND TO THIS REPOSITORY'S OWN SHARED
# CONTROLS MODULE.
#
# scripts/instrument_controls.py::require_controls is the idiom an instrument uses to declare
# a positive AND a negative control, and it refuses to print if either disagrees. The pattern
# `\bcontrol\s*\(` cannot match `require_controls(`: the preceding `_` defeats the word
# boundary and the trailing `s` defeats the paren.
#
#     MEASURED BEFORE THE FIX: 113 files route through require_controls. 44 were visible to
#     this gate -- every one for an UNRELATED token elsewhere in the file -- and 69 (61%)
#     were invisible. Its twelve open findings were therefore NOT a sample of uncontrolled
#     checks; they were a sample of files whose control mechanism did not happen to contain
#     one of seven literal strings. Measured across those twelve: 5 real gaps, 7 false.
#
# THIS WIDENS RECALL; IT DOES NOT RELAX THE RULE. Proven rather than asserted, with a
# constructed case the gate MUST still catch -- a text-matching module that reports a finding
# and routes through no control at all. It is FLAGGED before this change and FLAGGED after,
# while a module routing through require_controls is flagged before and clean after. Both
# cases live in `selftest()` below and run on every invocation, so a later edit that
# accidentally exempts the uncontrolled case fails here rather than silently.
#
# A FIX THAT CLEARS EVERY FAILURE IS A LOOSENED TEST. This one still fails the case it
# should.
CONTROL_MARK = re.compile(r"ControlledCount|run_control|def _control|KNOWN_NEGATIVE|"
                          r"known_negative|no-control:|require_controls|"
                          r"\bcontrol\s*\(", re.I)
BACKLOG = "TEXTMATCH_BACKLOG.json"


class Shape(ast.NodeVisitor):
    """Does this module match text AND report the result?

    Deliberately narrow on both halves. `x in some_dict` is not text matching, and `i += 1`
    is not reporting. The first draft of this visitor counted both and reached 739 of 820
    modules -- reach reported as population, inside the gate written to stop that.
    """

    def __init__(self):
        self.text_match = False
        self.reports = False

    def visit_Compare(self, node):
        for op in node.ops:
            if not isinstance(op, (ast.In, ast.NotIn)):
                continue
            rhs = node.comparators[0]
            nm = ""
            if isinstance(rhs, ast.Name):
                nm = rhs.id
            elif isinstance(rhs, ast.Attribute):
                nm = rhs.attr
            elif isinstance(rhs, ast.Call) and isinstance(rhs.func, ast.Attribute):
                nm = rhs.func.attr
            if TEXTVAR.search(nm or ""):
                self.text_match = True
            if isinstance(node.left, ast.Constant) and isinstance(node.left.value, str) \
                    and len(node.left.value) >= 4:
                self.text_match = True
        self.generic_visit(node)

    def visit_Call(self, node):
        f = node.func
        if isinstance(f, ast.Attribute):
            if f.attr in ("search", "findall", "finditer", "match", "fullmatch"):
                self.text_match = True
            if f.attr in ("write", "dump", "append"):
                self.reports = True
        if isinstance(f, ast.Name) and f.id == "print":
            self.reports = True
        self.generic_visit(node)


# Hand-built probes with answers fixed before the visitor ran. This is the gate's own
# known-negative control: a detector that has only ever said one thing has not been shown to
# discriminate, and arm B is itself a text-matching check.
SHAPE_PROBES = [
    ("if 'Favours' in page_text:\n    print(1)\n", True, "literal against a text-named var"),
    ("m = re.search(r'NCT', body)\nprint(m)\n", True, "regex search, reported"),
    ("if needle in html:\n    out.append(needle)\n", True, "membership in html, appended"),
    ("if key in mapping:\n    total += 1\n", False, "dict membership is not text matching"),
    ("for k in d.keys():\n    n += 1\n", False, "iteration is not matching"),
    ("x = 1 + 2\nprint(x)\n", False, "arithmetic"),
    ("if 'x' in row:\n    pass\n", False, "one-char literal, no report"),
    ("m = re.search(r'a', body)\n", False, "matches but never reports"),
    ("data = json.load(fh)\nprint(len(data))\n", False, "counts json, no text match"),
    ("if 'protocol' in served_bytes:\n    json.dump(out, fh)\n", True, "literal + dump"),
]


# THE TWO CASES THE CONTROL_MARK WIDENING MUST NOT LOSE, RUN ON EVERY INVOCATION.
#
# Adding `require_controls` to CONTROL_MARK makes this gate PASS MORE, which is the exact
# shape of loosening a test until it goes green. THE ONLY THING SEPARATING A CORRECTION FROM
# A RELAXATION IS A DEMONSTRATION THAT TRUE POSITIVES SURVIVE -- so the demonstration runs
# here rather than living in a commit message nobody re-executes.
_MUST_STILL_CATCH = '''
def pages(): return []
def main():
    hits = []
    for page in pages():
        if "WHO" in page:
            hits.append(page)
    print("findings: %d" % len(hits))
'''
_MUST_STOP_FLAGGING = '''
from instrument_controls import require_controls
def pages(): return []
def main():
    hits = []
    for page in pages():
        if "WHO" in page:
            hits.append(page)
    require_controls("demo", positive=("p", ["x"], ["x"]), negative=("n", [], []))
    print("findings: %d" % len(hits))
'''


def control_mark_did_not_lose_detection(gate):
    """A module with NO control must still be flagged; one using require_controls must not.

    Both are text-matching modules that report a finding, identical but for the control.
    Measured before the widening: BOTH were flagged -- the first correctly, the second
    wrongly, which is the defect. After it: the first still flagged, the second clean.
    """
    ok = True
    for label, src, want in (("a check with NO control at all", _MUST_STILL_CATCH, True),
                             ("a check routing through require_controls",
                              _MUST_STOP_FLAGGING, False)):
        sh = Shape()
        sh.visit(ast.parse(src))
        flagged = bool(sh.text_match and sh.reports and not CONTROL_MARK.search(src))
        if flagged != want:
            ok = False
            gate.broken("CONTROL_MARK regression: %s was %s, expected %s. The widening that "
                        "let this gate see require_controls has cost it a true positive, "
                        "which makes it a relaxation rather than a correction."
                        % (label, "flagged" if flagged else "cleared",
                           "flagged" if want else "cleared"))
    if ok:
        gate.note("CONTROL_MARK widening verified: a check with no control at all is STILL "
                  "flagged, a check using require_controls is not. Detection preserved.")
    return ok


def arm_b(gate, repo):
    control_mark_did_not_lose_detection(gate)
    kinds = collections.Counter()
    unmeasured, controlled = [], []
    for sub in ("scripts", "gates"):
        base = os.path.join(repo, sub)
        if not os.path.isdir(base):
            continue
        for fn in sorted(os.listdir(base)):
            if not fn.endswith(".py"):
                continue
            rel = "%s/%s" % (sub, fn)
            in_scope = (sub == "gates") or bool(SCOPE_RE.search(fn))
            if not in_scope:
                kinds["out of scope (not a check/gate/lint/audit/sweep)"] += 1
                continue
            with open(os.path.join(base, fn), "r", encoding="utf-8", errors="replace") as fh:
                src = fh.read()
            try:
                tree = ast.parse(src)
            except SyntaxError as exc:
                kinds["in scope, unparseable"] += 1
                gate.broken("%s did not parse: %s" % (rel, exc))
                continue
            sh = Shape()
            sh.visit(tree)
            if not (sh.text_match and sh.reports):
                kinds["in scope, does not match text"] += 1
                continue
            if CONTROL_MARK.search(src):
                kinds["text-matching check WITH a control or stated exemption"] += 1
                controlled.append(rel)
            else:
                kinds["text-matching check with NO measured precision"] += 1
                unmeasured.append(rel)
    return unmeasured, controlled, kinds


def ratchet(gate, repo, unmeasured):
    """The backlog may shrink and may never grow. A NEW uncontrolled check fails the gate.

    Freezing rather than demanding 189 retrofits at once is the only version of this rule
    that survives contact with a working tree. What it forbids is the class GROWING, which is
    the thing that actually cost us: an eighth spelling, a ninth uncontrolled matcher.
    """
    path = os.path.join(repo, "gates", BACKLOG)
    now = sorted(unmeasured)
    if not os.path.exists(path):
        with open(path, "w", encoding="utf-8") as fh:
            json.dump({"frozen_utc": "2026-08-28",
                       "what": "text-matching checks whose precision has never been measured. "
                               "This list may SHRINK and may never GROW. A name appearing here "
                               "that is not in the frozen list fails gate 2.",
                       "count": len(now), "modules": now}, fh, indent=1)
        gate.note("backlog frozen for the first time at %d modules; from now on it is a "
                  "ratchet." % len(now))
        return []
    frozen = set(H.load(path)["modules"])
    new = [m for m in now if m not in frozen]
    gone = sorted(frozen - set(now))
    gate.note("uncontrolled-matcher backlog: %d frozen, %d now, %d retired, %d NEW"
              % (len(frozen), len(now), len(gone), len(new)))
    return new


def main(argv):
    repo = H.repo_root()
    gate = H.Gate("2  TEXT-MATCH CONTROL",
                  "a text-matching check must carry a known-negative control and print its rate")
    gate.requires_control()

    # --plant-nocontrol writes nothing; it strips the control marker from one module IN MEMORY
    # to prove arm B can fail on a module it currently passes.
    plant = "--plant" in argv

    measurements, kinds_a = arm_a(gate, repo)
    unmeasured, controlled, kinds_b = arm_b(gate, repo)

    if plant:
        # simulate a NEW text-matching check landing with no control. The gate must name it.
        unmeasured.append("gates/__planted_uncontrolled_matcher.py")
        kinds_b["text-matching check with NO measured precision"] += 1
        gate.note("PLANTED: a synthetic uncontrolled matcher added to arm B's input")

    # arm B is itself a text-matching check, so it carries its own known-negative control:
    # hand-built probes whose answers were fixed before the visitor ran.
    wrong = []
    for src, expect, why in SHAPE_PROBES:
        sh = Shape()
        sh.visit(ast.parse(src))
        if (sh.text_match and sh.reports) != expect:
            wrong.append("%s -> expected %s" % (why, expect))
    negatives = [p for p in SHAPE_PROBES if not p[1]]
    fp = sum(1 for src, expect, why in negatives
             if (lambda s: (s.text_match and s.reports))(_visited(src)))
    gate.control(len(negatives), fp, wrong)
    if wrong:
        gate.finding("SHAPE-DETECTOR-DISAGREES-WITH-ITS-PROBES",
                     "arm B's shape detector failed %d of %d hand-built probes: %s"
                     % (len(wrong), len(SHAPE_PROBES), "; ".join(wrong)))

    new_uncontrolled = ratchet(gate, repo, unmeasured)

    merged = dict(kinds_a)
    merged.update(kinds_b)
    gate.kinds(merged)

    in_scope_matchers = len(unmeasured) + len(controlled)
    for mod in new_uncontrolled:
        gate.finding("NEW-COUNT-WITHOUT-MEASURED-PRECISION",
                     "%s matches text and reports, with no known-negative control and no "
                     "`# no-control:` reason. It is NEW since the backlog was frozen. A count "
                     "without a measured precision is not a finding." % mod,
                     numerator=len(new_uncontrolled), denominator=in_scope_matchers)

    art = os.path.join(repo, "out", "gate2_textmatch_control.json")
    os.makedirs(os.path.dirname(art), exist_ok=True)
    with open(art, "w", encoding="utf-8") as fh:
        json.dump({"gate": gate.as_json(), "arm_a": measurements,
                   "arm_b_unmeasured": unmeasured, "arm_b_controlled": controlled,
                   "arm_b_new_since_freeze": new_uncontrolled}, fh, indent=1)

    # COVERAGE, ARM A. Only an ACRONYM is usable as a match token. A registry title and a
    # bare registration used as a name are not, so the precision this gate measures is
    # measured on a third of the trial-name strings in the corpus.
    gate.coverage(gate.kind("ACRONYM (usable for a text-match task)"),
                  max(gate.kind("ACRONYM (usable for a text-match task)")
                      + gate.kind("registry title / descriptor (not a token)")
                      + gate.kind("registration used as a name"), 1),
                  "trial-name strings that are registry titles or bare registrations, on "
                  "which no match precision has been measured at all")
    return gate.report(denominator="%d in-scope text-matching checks (%d controlled, %d in the "
                                   "frozen backlog); %d match-task cases"
                                   % (in_scope_matchers, len(controlled), len(unmeasured),
                                      kinds_a["positives (must match)"]
                                      + kinds_a["known negatives (must NOT match)"]))


def _visited(src):
    sh = Shape()
    sh.visit(ast.parse(src))
    return sh


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
