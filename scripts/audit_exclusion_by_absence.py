"""How many exclusion criteria in this pipeline are phrased as a MISSING property?

CLASS 49, ONE LAYER OUT. A skip criterion is a claim about the population it excludes, and
stating it as an absence excludes everything that lacks the property FOR ANY REASON -- only
one of which is the reason meant.

Two instances already on the record:

    the reading-order rollout    skipped pages with ZERO `paper-*` sections as "not built by
                                 this generator". Three were current-generator pages with no
                                 paper tab, and two of those serve nothing for a pooled point
                                 their object holds.
    a phase filter               dropped CABANA and RAFT-AF because they DECLINED TO DECLARE
                                 A PHASE. `NA` is not a phase, and enumerating phases drops
                                 every registrant who declared none.

Both are the identical error: `absence of X` used where `is a Y` was meant.

WHAT THIS COUNTS. Exclusion or skip conditions expressed negatively -- `if not x`, `if x is
None`, `if not x.get(...)`, `== 0`, `== []` -- followed by a `continue`, `skip`, `return` or
an exclusion append. And, in the objects, recorded exclusion reasons whose text is an
absence.

IT COUNTS AND NAMES. It does not rewrite: several of these are correct -- excluding a record
that genuinely has no comparator is right -- and only reading each settles which. THE POINT
IS THE POPULATION, NOT A VERDICT.

1,281 IS A POPULATION AND NOT A FINDING. DO NOT READ THEM.

THE SUBSET WORTH FINDING LATER, and the criterion for finding it, recorded now so the search
is a query rather than a re-derivation:

    A guard that excludes an item from a CORPUS-WIDE OPERATION -- a rollout, a rebuild, a
    corpus sweep, a batch verification -- rather than from a single-item computation.

Those are the ones where an absence standing in for something else SILENTLY REMOVES ITEMS
FROM A FIX, which is exactly what cost us two objectless-serving pages: the reading-order
rollout's `zero paper sections` excluded three live pages, two of which do not serve a
pooled point their object holds. A negative guard inside one page's rendering is a local
decision; a negative guard inside a loop over the corpus decides what a fix reaches.

That is a much smaller set than 1,281. Find it by looking for negative guards whose
enclosing function iterates a corpus listing -- `os.listdir(SSOT)`, `PAGE_MAP`, a glob over
`*.html` -- rather than a single object. LEFT FOR TOMORROW.

AND THE OBJECT-SIDE COUNT OF 4 IS NOT TRUSTED. `screening.excluded` is empty on most
objects, so a sweep over it measures the emptiness of the field rather than the phrasing of
the criteria -- the same instrument-shaped error as a resolver sweep reporting zero across
782 files. Reported as unreliable rather than as 4.
"""
import io
import json
import os
import re
import sys

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

NEG_GUARD = re.compile(
    r"if\s+(?:not\s+[\w\.\[\]\(\)'\"]+|[\w\.\[\]\(\)'\"]+\s+is\s+None|"
    r"[\w\.\[\]\(\)'\"]+\s*==\s*(?:None|\[\]|\{\}|0|''|\"\")|"
    r"len\([^)]+\)\s*==\s*0)\s*:")
EXIT = re.compile(r"^\s*(continue|break|return|raise)\b|excluded\.append|skip", re.M)

# Exclusion reasons in the objects, phrased as an absence.
ABSENCE_TEXT = re.compile(
    r"\bno\s+(?:comparator|control|placebo|results?|posted|randomis|phase|estimand|"
    r"registered|declared)|\bnot\s+(?:declared|posted|recorded|reported|registered|"
    r"stated|available)\b|\bdoes not (?:declare|post|report|record)\b|\blacks?\b|"
    r"\babsent\b|\bmissing\b|\bunstated\b|\bnone declared\b", re.I)


def code_sweep():
    hits = []
    files = 0
    for root in (os.path.join(REPO, "scripts"), os.path.join(REPO, "ssot")):
        if not os.path.isdir(root):
            continue
        for dp, _d, names in os.walk(root):
            for nm in sorted(names):
                if not nm.endswith(".py"):
                    continue
                fp = os.path.join(dp, nm)
                try:
                    src = io.open(fp, encoding="utf-8", errors="replace").read()
                except Exception:
                    continue
                files += 1
                lines = src.split("\n")
                for i, ln in enumerate(lines):
                    if not NEG_GUARD.search(ln):
                        continue
                    nxt = "\n".join(lines[i + 1:i + 3])
                    if EXIT.search(nxt):
                        hits.append((os.path.relpath(fp, REPO).replace("\\", "/"),
                                     i + 1, ln.strip()[:88]))
    return files, hits


def object_sweep():
    ssot = os.path.join(REPO, "ssot")
    reasons = []
    objects = 0
    for name in sorted(os.listdir(ssot)):
        d = os.path.join(ssot, name)
        if not os.path.isdir(d):
            continue
        fp = os.path.join(d, name + ".json")
        if not os.path.exists(fp):
            continue
        try:
            obj = json.load(io.open(fp, encoding="utf-8"))
        except Exception:
            continue
        objects += 1
        exc = ((obj.get("screening") or {}).get("excluded")) or []
        for e in exc:
            if not isinstance(e, dict):
                continue
            txt = " ".join(str(v) for k, v in e.items()
                           if isinstance(v, str) and k in ("reason", "why", "criterion",
                                                           "failed_limb", "detail"))
            if txt and ABSENCE_TEXT.search(txt):
                reasons.append((name, txt[:100]))
    return objects, reasons




# ---------------------------------------------------------------------------------------
# THE ENUMERABLE SUBSET, AND THE ONLY PART OF THIS FILE THAT CAN REFUSE.
#
# 1,300 negative guards is a POPULATION. Reading it is not work anyone should do, and a
# check that blocks on a population blocks everything. The subset that actually cost us
# something is narrow and countable:
#
#     A NEGATIVE GUARD INSIDE A LOOP OVER THE CORPUS.
#
# A negative guard inside one page's rendering is a local decision. A negative guard inside
# a loop over every object or every page DECIDES WHAT A FIX REACHES -- and `zero paper-*
# sections` standing in for `built by an older generator` silently removed three live pages
# from the reading-order rollout, two of which serve nothing for a pooled point their own
# object holds.
#
# RATCHET, NOT CLEARANCE. The subset present today is recorded in a baseline. It must not
# grow. Each entry is a candidate, not a verdict: excluding a record that genuinely has no
# comparator arm is correct, and only reading settles which. What the ratchet buys is that
# THE NEXT ONE IS SEEN WHEN IT IS WRITTEN, rather than after it has quietly excluded
# something from a corpus-wide pass.
# ---------------------------------------------------------------------------------------

CORPUS_LOOP = re.compile(
    r"for\s+\w+.*\bin\b.*(?:glob\.glob\(|os\.listdir\(|os\.walk\(|PAGE_MAP|apps\b|"
    r"topics\b|objects\b|pages\b)")

BASELINE = os.path.join(REPO, "scripts", "baselines", "exclusion_by_absence_baseline.json")


def indent_of(line):
    return len(line) - len(line.lstrip())


def corpus_wide_subset():
    """Negative guards lexically inside a loop that iterates the corpus."""
    out = []
    for root in (os.path.join(REPO, "scripts"), os.path.join(REPO, "ssot")):
        if not os.path.isdir(root):
            continue
        for dp, _d, names in os.walk(root):
            for nm in sorted(names):
                if not nm.endswith(".py"):
                    continue
                fp = os.path.join(dp, nm)
                rel = os.path.relpath(fp, REPO).replace("\\", "/")
                try:
                    lines = io.open(fp, encoding="utf-8", errors="replace").read().split("\n")
                except Exception:
                    continue
                # Stack of open corpus loops as (indent, header line number).
                stack = []
                for i, ln in enumerate(lines):
                    if not ln.strip() or ln.strip().startswith("#"):
                        continue
                    ind = indent_of(ln)
                    while stack and ind <= stack[-1][0]:
                        stack.pop()
                    if CORPUS_LOOP.search(ln):
                        stack.append((ind, i + 1))
                        continue
                    if not stack:
                        continue
                    if not NEG_GUARD.search(ln):
                        continue
                    nxt = "\n".join(lines[i + 1:i + 3])
                    if EXIT.search(nxt):
                        out.append((rel, i + 1, stack[-1][1], ln.strip()[:76]))
    return out


def keys_for(subset):
    """Baseline keys: FILE :: GUARD TEXT # nth-occurrence-of-that-text-in-that-file.

    KEYED BY LINE NUMBER, THIS RATCHET REPORTED UNCHANGED GUARDS AS NEW EVERY TIME ANYTHING
    ABOVE THEM WAS EDITED. `audit_p46_limbs_reach_a_reader.py`'s three guards were re-baselined
    THREE TIMES for that reason alone -- the baseline's own note says so -- and a fourth
    re-baselining was what blocked the commit that prompted this change. Re-writing the entries
    a fourth time would have been the symptom fix; the key is the cause.

    IT IS NOT MERELY LOOSER. A bare file+text key would collapse two identical guard lines in
    one file into a single entry, and a genuinely new second instance would then hide behind
    the first -- three files carry such a pair today. The occurrence index keeps them distinct,
    so the ratchet still rises when a duplicate guard is ADDED, and stops rising when a line is
    merely MOVED. `prove_ratchet` demonstrates both directions on every run.

    The line number stays in the printed report, where it helps a reader open the file. It is
    no longer part of the identity, because it was never the thing that made a guard the guard.
    """
    seen = {}
    out = []
    for h in subset:
        base = "%s::%s" % (h[0], h[3])
        n = seen.get(base, 0)
        seen[base] = n + 1
        out.append("%s#%d" % (base, n))
    return out


def ratchet(subset, write_if_missing=True):
    """-> (known, new, healed). Exits non-zero from main() when `new` is non-empty."""
    present = sorted(keys_for(subset))
    if not os.path.exists(BASELINE):
        if not write_if_missing:
            return set(), [], []
        os.makedirs(os.path.dirname(BASELINE), exist_ok=True)
        json.dump({
            "written": "2026-08-20",
            "what": ("Negative guards lexically inside a loop over the corpus. A guard here "
                     "decides what a corpus-wide fix REACHES, which is how the reading-order "
                     "rollout's `zero paper sections` silently dropped three live pages."),
            "not_a_verdict": ("Each entry is a CANDIDATE. Many are correct. The ratchet "
                              "exists so the next one is seen when it is written."),
            "guards": present,
        }, io.open(BASELINE, "w", encoding="utf-8", newline="\n"), indent=1,
            ensure_ascii=False)
        print("wrote baseline %s with %d guards" % (BASELINE, len(present)))
        return set(present), [], []
    base = json.load(io.open(BASELINE, encoding="utf-8"))
    known = set(base.get("guards") or [])
    new = sorted(set(present) - known)
    healed = sorted(known - set(present))
    return known, new, healed


def main():
    files, hits = code_sweep()
    objects, reasons = object_sweep()
    if files == 0 and objects == 0:
        print("NOT_ASSESSABLE: read no files and no objects.")
        return 2

    print("python files read                            %d" % files)
    print("NEGATIVE guards that exclude, skip or return %d" % len(hits))
    print()
    print("objects read                                 %d" % objects)
    print("recorded exclusions phrased as an absence    %d" % len(reasons))
    print()
    byfile = {}
    for rel, ln, txt in hits:
        byfile.setdefault(rel, []).append((ln, txt))
    print("TOP FILES BY NEGATIVE-EXCLUSION COUNT:")
    for rel, rows in sorted(byfile.items(), key=lambda kv: -len(kv[1]))[:16]:
        print("   %-56s %3d" % (rel, len(rows)))
    print()
    if reasons:
        from collections import Counter
        c = Counter(n for n, _t in reasons)
        print("OBJECTS WITH THE MOST ABSENCE-PHRASED EXCLUSIONS:")
        for n, k in c.most_common(8):
            print("   %-46s %4d" % (n, k))
        print()
        print("   examples:")
        for n, t in reasons[:5]:
            print("     %-30s %s" % (n[:30], t))
    print()
    print("COUNTED AND NAMED, NOT ADJUDICATED. Many of these are correct -- excluding a")
    print("record that genuinely has no comparator arm is right. The defect is only where")
    print("the absence stands in for a DIFFERENT property that was meant, as `zero paper")
    print("sections` stood in for `built by an older generator` and `phase not in the")
    print("enumerated list` stood in for `not a phase 3 trial`. Reading each settles it.")
    return 0


def prove_ratchet():
    """A guard not in the baseline must come back NEW. Otherwise the ratchet is decorative."""
    subset = corpus_wide_subset()
    fake = ("scripts/PROOF_not_a_real_file.py", 1, 1, "if not x:")
    _k, new, _h = ratchet(subset + [fake], write_if_missing=False)
    if "scripts/PROOF_not_a_real_file.py::if not x:#0" not in new:
        sys.exit("PROOF FAILED: a guard absent from the baseline was NOT reported as new. "
                 "The ratchet cannot rise and therefore cannot fall either.")
    # THE DUPLICATE DIRECTION, WHICH THE NEW KEY COULD HAVE LOST AND THIS FORBIDS.
    # Keying on file+text alone would let a SECOND copy of an already-baselined guard line
    # slip in silently. Take a real baselined guard, add an identical one, and require the
    # ratchet to see it. Without this the looser key would be an unmeasured weakening.
    if subset:
        dup = subset[0]
        _k, newd, _h = ratchet(subset + [dup], write_if_missing=False)
        if not newd:
            sys.exit("PROOF FAILED: a SECOND copy of an already-baselined guard line was not "
                     "reported as new. The occurrence index is not distinguishing duplicates, "
                     "so the key is looser than the line-number key it replaced.")
    _k, new2, _h = ratchet(subset, write_if_missing=False)
    if new2:
        sys.exit("PROOF FAILED: the unmodified corpus reports %d new guards, so the "
                 "baseline does not describe the corpus it was written from." % len(new2))
    print("PROOF PASSED: an unbaselined corpus-wide negative guard is reported NEW, a DUPLICATE")
    print("of a baselined one is reported NEW, and the corpus as it stands reports none.")


def report_corpus_subset(gate):
    subset = corpus_wide_subset()
    print("")
    print("THE ENUMERABLE SUBSET -- negative guards INSIDE a loop over the corpus: %d"
          % len(subset))
    print("A guard here decides what a corpus-wide FIX REACHES. The reading-order rollout's")
    print("`zero paper-* sections` excluded three live pages, two of which serve nothing for")
    print("a pooled point their object holds.")
    for rel, ln, loop, txt in subset[:40]:
        print("    %s:%d  (loop opened at line %d)" % (rel, ln, loop))
        print("        %s" % txt)
    if len(subset) > 40:
        print("    ... +%d more" % (len(subset) - 40))
    known, new, healed = ratchet(subset)
    if healed:
        print("")
        print("%d guard(s) in the baseline are gone." % len(healed))
    if new:
        print("")
        print("REFUSED: %d NEW negative guard(s) inside a corpus-wide loop:" % len(new))
        for k in new:
            print("    %s" % k)
        print("")
        print("State the POSITIVE property instead -- `built by generator X`, not `has zero")
        print("X sections` -- or add it to the baseline with a line saying why the absence")
        print("IS the property you mean.")
        if gate:
            sys.exit(1)
    elif os.path.exists(BASELINE):
        print("NO NEW CORPUS-WIDE NEGATIVE GUARD. The baseline has not risen.")


if __name__ == "__main__":
    if "--prove" in sys.argv:
        prove_ratchet()
    else:
        main()
        report_corpus_subset("--gate" in sys.argv)
