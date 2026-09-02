# -*- coding: utf-8 -*-
"""POSITIVE ENUMERATION OF READERS for three r_validation artefacts.

I claimed these three "feed" pages being rebuilt. That claim was NAME-MATCHING --
APIXABAN_ACS_AUTO_FULL.json looked like the apixaban topic -- and a name is not an
identity. This looks for an actual reader instead: a file that mentions the artefact
by name, or that mentions the directory at all.

The question decides urgency, not importance:
  ORPHAN   -> the stale value reaches no reader. Serious, fix at leisure.
  CONSUMED -> a rebuilt page would publish a 293x wrong tau2. Hold the push.

Reports UNSEARCHED surfaces explicitly. A grep that could not finish is not evidence
of absence, and this walks the tree itself with a time budget so it can say which
part it covered rather than reporting its own reach as coverage.
"""
import io
import os
import time

ROOT = r"F:\rapidmeta-ssot-shell"
NEEDLES = ("APIXABAN_ACS_AUTO_FULL", "APIXABAN_AF_AUTO_FULL",
           "BOCOCIZUMAB_LIPID_AUTO_FULL", "r_validation")
EXTS = (".html", ".js", ".json", ".py", ".md")
SKIP_DIRS = {".git", "node_modules", "__pycache__"}
BUDGET_S = 240

hits = {n: [] for n in NEEDLES}
scanned = 0
skipped_big = 0
unsearched = []
t0 = time.time()
stopped_early = False

for dirpath, dirnames, filenames in os.walk(ROOT):
    dirnames[:] = [d for d in dirnames if d not in SKIP_DIRS]
    # the artefacts themselves are not readers of themselves
    rel = os.path.relpath(dirpath, ROOT)
    for fn in filenames:
        if time.time() - t0 > BUDGET_S:
            stopped_early = True
            unsearched.append(rel)
            break
        if not fn.lower().endswith(EXTS):
            continue
        p = os.path.join(dirpath, fn)
        if rel.replace("\\", "/") == "outputs/r_validation":
            continue                      # self-reference is not consumption
        try:
            if os.path.getsize(p) > 12_000_000:
                skipped_big += 1
                continue
            t = io.open(p, encoding="utf-8", errors="replace").read()
        except Exception:
            continue
        scanned += 1
        for n in NEEDLES:
            if n in t:
                hits[n].append(os.path.relpath(p, ROOT))
    if stopped_early:
        break

print("POSITIVE READER ENUMERATION")
print("  root                 : %s" % ROOT)
print("  files scanned        : %d" % scanned)
print("  skipped (>12MB)      : %d" % skipped_big)
print("  stopped early        : %s" % stopped_early)
if unsearched:
    print("  UNSEARCHED (budget)  : %s" % sorted(set(unsearched))[:5])
print()
for n in NEEDLES:
    v = hits[n]
    print("  %-30s readers found: %d" % (n, len(v)))
    for f in v[:6]:
        print("      %s" % f)
print()
three = [n for n in NEEDLES[:3] if hits[n]]
print("VERDICT for the three stale artefacts:")
if not three:
    print("  NO READER FOUND on the surfaces scanned -> consistent with ORPHAN.")
    print("  This is an ABSENCE OF EVIDENCE bounded by what was scanned above,")
    print("  not a proof of absence. Confirm against the sidecar lane's own")
    print("  enumeration (744 orphans / 3 referenced) before acting on it.")
else:
    print("  READER FOUND for: %s -> CONSUMED. HOLD THE PUSH." % ", ".join(three))
