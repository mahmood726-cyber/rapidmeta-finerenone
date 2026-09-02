# -*- coding: utf-8 -*-
"""Does anything actually READ outputs/r_validation/<file>.json?

My first enumeration matched the artefact NAME and found 50-57 "readers" each. That
was a name-matcher, written immediately after I said a name is not an identity:
APIXABAN_ACS_AUTO_FULL appears in APIXABAN_ACS_AUTO_REVIEW.html because that page IS
the topic, not because it loads the sidecar.

This looks for a PATH -- r_validation/<something>.json -- which is what consumption
actually looks like. It reports which paths are referenced and by whom, and it
reports its own budget so an unfinished scan cannot be read as an absence.
"""
import io
import os
import re
import time

ROOT = r"F:\rapidmeta-ssot-shell"
PAT = re.compile(r"r_validation[\\/]([A-Za-z0-9_\-]+)\.json")
TARGETS = ("APIXABAN_ACS_AUTO_FULL", "APIXABAN_AF_AUTO_FULL",
           "BOCOCIZUMAB_LIPID_AUTO_FULL")
EXTS = (".html", ".js", ".json", ".py", ".md")
BUDGET = 900

hits, scanned, unsearched = {}, 0, []
t0 = time.time()
stopped = False
for dp, dn, fns in os.walk(ROOT):
    dn[:] = [d for d in dn if d not in (".git", "node_modules", "__pycache__")]
    if "r_validation" in dp:
        continue                       # self-reference is not consumption
    for fn in fns:
        if time.time() - t0 > BUDGET:
            stopped = True
            unsearched.append(os.path.relpath(dp, ROOT))
            break
        if not fn.lower().endswith(EXTS):
            continue
        p = os.path.join(dp, fn)
        try:
            if os.path.getsize(p) > 12_000_000:
                continue
            t = io.open(p, encoding="utf-8", errors="replace").read()
        except Exception:
            continue
        scanned += 1
        for stem in set(PAT.findall(t)):
            hits.setdefault(stem, set()).add(os.path.relpath(p, ROOT))
    if stopped:
        break

print("PATH-REFERENCE TEST (consumption, not name mention)")
print("  files scanned : %d" % scanned)
print("  stopped early : %s" % stopped)
if unsearched:
    print("  UNSEARCHED    : %s" % sorted(set(unsearched))[:4])
print()
print("  distinct r_validation/*.json PATHS referenced anywhere: %d" % len(hits))
for k in sorted(hits)[:15]:
    print("    %-46s by %d file(s): %s"
          % (k, len(hits[k]), sorted(hits[k])[:2]))
print()
print("VERDICT for the three stale artefacts:")
any_hit = False
for t in TARGETS:
    got = sorted(hits.get(t, []))
    print("  %-30s %s" % (t, ("READ BY " + ", ".join(got[:3])) if got else "NO PATH REFERENCE"))
    any_hit = any_hit or bool(got)
print()
if any_hit:
    print("  -> CONSUMED. Hold the push on the affected pages.")
else:
    print("  -> NO PATH REFERENCE FOUND on the surfaces scanned. Consistent with")
    print("     ORPHAN, and consistent with the sidecar lane's 744-orphan figure.")
    print("     ABSENCE OF EVIDENCE bounded by the scan above -- not proof. The")
    print("     earlier name-match verdict of CONSUMED was MY error and is withdrawn.")
