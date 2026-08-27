# -*- coding: utf-8 -*-
"""What the two assessors actually disagreed about, per domain and per direction.

THE PROPOSED REPAIR RESTS ON A PREMISE THAT DOES NOT HOLD. The claim was that
`second_assessor_prompt.py` withholds the decision rule, because the blinding guard refuses
any text containing a verdict word and the rule is written in verdict words. The guard scans
`body` only -- the assembled fact blocks -- and never the HEADER, and the HEADER carries the
rule in full: "a domain that cannot be judged from the facts given is NO_INFORMATION, never
LOW." That text is present verbatim in commit 0f6764f42, dated 2026-08-21, which is the
version the second assessor ran under.

So before re-running anything, this measures the disagreement itself: which domains, which
direction, and whether the shape is consistent with two readers applying different rules or
with two readers reading the same thin evidence differently.
"""
import collections
import glob
import io
import json
import os
import re
import sys

# GUARDED. A module-level stdout reassignment closes the CALLER's stdout the moment
# this file is imported, and every script here is now importable -- three separate
# checks of this lane's own output died that way before it was fixed at the source.
if __name__ == "__main__":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8",
                                  errors="replace", line_buffering=True)
REPO = r"F:\rapidmeta-ssot-shell"
os.chdir(REPO)
sys.path.insert(0, os.path.join(REPO, "ssot"))
from rob_block import rob_block  # noqa: E402

pairs = collections.Counter()
per_domain = collections.Counter()
topics = set()
n_topics_dual = 0
for p in sorted(glob.glob("ssot/*/*.json")):
    t = os.path.basename(os.path.dirname(p))
    if os.path.basename(p) != t + ".json":
        continue
    try:
        obj = json.load(io.open(p, encoding="utf-8"))
    except Exception:
        continue
    b = rob_block(obj)
    if not b or len(b.get("assessors") or []) < 2:
        continue
    n_topics_dual += 1
    for tr in b["trials"]:
        for d in tr["domains"]:
            js = d.get("judgements") or []
            if len(js) < 2 or js[0] is None or js[1] is None:
                continue
            a, c = str(js[0]).upper().replace(" ", "_"), str(js[1]).upper().replace(" ", "_")
            dom = (d.get("domain") or "?")[:2]
            per_domain[(dom, a == c)] += 1
            if a != c:
                pairs[(dom, a, c)] += 1
                topics.add(t)

tot = sum(per_domain.values())
agree = sum(v for (d, ok), v in per_domain.items() if ok)
print("POPULATION")
print("  dual-assessed topics                      %3d" % n_topics_dual)
print("  domain comparisons with both answers      %3d  == the denominator" % tot)
print("  agreed                                    %3d  (%.1f%%)"
      % (agree, 100.0 * agree / tot if tot else 0))
print("  disagreed                                 %3d  (%.1f%%)"
      % (tot - agree, 100.0 * (tot - agree) / tot if tot else 0))
print("")
print("BY DOMAIN")
doms = sorted({d for d, _ in per_domain})
for d in doms:
    a = per_domain[(d, True)]
    x = per_domain[(d, False)]
    print("  %-4s agreed %3d   disagreed %3d   (%.0f%% disagreement)"
          % (d, a, x, 100.0 * x / (a + x) if (a + x) else 0))
print("")
print("DIRECTION OF EVERY DISAGREEMENT (assessor 1 -> assessor 2)")
for (d, a, c), n in pairs.most_common(24):
    print("  %-4s %-16s -> %-16s %3d" % (d, a, c, n))
print("")
# Is the pattern one-directional per domain? A rule difference should show one arrow
# dominating; thin evidence read differently should not be so clean.
print("ONE-DIRECTIONALITY, per domain")
for d in doms:
    sub = [(k, v) for k, v in pairs.items() if k[0] == d]
    if not sub:
        continue
    tot_d = sum(v for _, v in sub)
    top = max(sub, key=lambda kv: kv[1])
    print("  %-4s %3d disagreements, largest single direction %s -> %s = %d (%.0f%%)"
          % (d, tot_d, top[0][1], top[0][2], top[1], 100.0 * top[1] / tot_d))
