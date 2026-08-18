"""Split the closed topics into PENDING (no data yet) and IMPOSSIBLE (a limb fails).

MALARIA_ACT forced this. Its participants, intervention and outcome limbs all PASS -- five
registry strings describing one disease, every trial registering an
adequate-clinical-and-parasitological-response primary -- and it cannot be built only
because NOT ONE of its five registrations posts results. That is not the same verdict as
CEFTOLOZANE_INFECTION, whose trials answer three different questions and would remain
unpoolable however good the data.

WHY IT MATTERS BEYOND BOOKKEEPING. The corpus headline is "roughly one topic in five
supports a pool". If a material share of the other four are WAITING ON DATA rather than
INCAPABLE OF BEING POOLED, that sentence means something quite different and the paper has
to say which. A pending topic is revivable the day results appear; an impossible one never
is.

CLASSIFICATION, from the object rather than from memory:
  IMPOSSIBLE  which_limb_fails names a limb (PARTICIPANTS / INTERVENTION / COMPARATOR /
              OUTCOME, alone or combined).
  PENDING     the limbs pass and the block is data availability -- no registration posts
              results, or k<2 because the topic seeds too few trials to compare.
  REFERRED    a scope decision is outstanding and no pool is displayed pending it.
  DUPLICATE   the analysis exists on another page; this one is not a separate verdict.

THIS READS THE OBJECTS. It does not re-derive the verdicts, and where an object does not
carry enough to classify it, THE TOPIC IS REPORTED AS UNCLASSIFIED rather than guessed.
"""
from __future__ import annotations
import io
import json
import os
import re
import sys

if __name__ == "__main__":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LIMB = re.compile(r"PARTICIPANTS|INTERVENTION|COMPARATOR|OUTCOME", re.I)
NODATA = re.compile(
    r"posts? no results|no posted results|NONE has a posted results|"
    r"no registration posts results|results_posted.{0,6}false|data are not there|"
    r"no results section", re.I)


def classify(o, blob):
    # blob is NO LONGER USED for the data-gap test. Searching the whole raw file matched
    # any object that merely MENTIONED absent results -- including in a "what this does not
    # establish" note -- and classified ACS_ANTIPLATELET and COLCHICINE as PENDING when
    # their recorded reasons say plainly that the trials answer different questions. The
    # test now reads ONLY the verdict fields. Instrument artefact, caught by spot-check
    # before the number was reported.
    st = (o.get("topic_state") or "")
    wl = (o.get("which_limb_fails") or "")
    if o.get("DUPLICATION_NOTICE") and "DUPLICATE" in st.upper():
        return "DUPLICATE", "analysis built on another page"
    if "REFERRED" in st.upper() or "REFERRED" in wl.upper():
        return "REFERRED", "scope decision outstanding, no pool displayed"
    if "POOLED" in st.upper() and "NOT POOLABLE" not in st.upper():
        return "BUILT", st[:56]
    # closed topics: pending or impossible
    if wl and LIMB.search(wl) and "NONE" not in wl.upper():
        return "IMPOSSIBLE", "limb fails: %s" % wl[:40]
    verdict_text = " ".join([st, wl,
                             str(((o.get("results") or {}).get("by_outcome") or {})
                                 .get("primary", {}).get("poolable_reason") or "")])
    if NODATA.search(verdict_text):
        return "PENDING", "limbs pass; no registration posts results"
    prim = ((o.get("results") or {}).get("by_outcome") or {}).get("primary") or {}
    if prim.get("poolable") is None and not st and not wl:
        return "UNCLASSIFIED", "no verdict recorded on the object at all"
    k = prim.get("k")
    if isinstance(k, int) and 0 < k < 2:
        return "PENDING", "k=%d -- one trial is a trial, not a synthesis" % k
    if prim.get("poolable") is False:
        r = prim.get("poolable_reason") or ""
        if NODATA.search(r):
            return "PENDING", "limbs pass; data absent"
        if LIMB.search(r):
            return "IMPOSSIBLE", "limb named in the reason text"
        return "UNCLASSIFIED", "closed, but the object does not name a limb or a data gap"
    return "UNCLASSIFIED", "no verdict recorded on the object"


def main() -> int:
    ss = os.path.join(REPO, "ssot")
    buckets = {}
    for d in sorted(os.listdir(ss)):
        f = os.path.join(ss, d, d + ".json")
        if not os.path.exists(f):
            continue
        try:
            raw = io.open(f, encoding="utf-8").read()
            o = json.loads(raw)
        except Exception:
            continue
        cat, why = classify(o, raw)
        buckets.setdefault(cat, []).append((d, why))

    order = ["BUILT", "PENDING", "IMPOSSIBLE", "REFERRED", "DUPLICATE", "UNCLASSIFIED"]
    total = sum(len(v) for v in buckets.values())
    print("topics with a canonical object: %d" % total)
    print()
    for c in order:
        rows = buckets.get(c) or []
        print("%-14s %3d" % (c, len(rows)))
    print()
    for c in ["PENDING", "REFERRED", "UNCLASSIFIED"]:
        rows = buckets.get(c) or []
        if not rows:
            continue
        print("--- %s (%d)" % (c, len(rows)))
        for d, why in rows[:40]:
            print("    %-46s %s" % (d[:45], why[:52]))
        print()
    json.dump({k: [{"topic": a, "why": b} for a, b in v] for k, v in buckets.items()},
              io.open(os.path.join(REPO, ".pending-split.json"), "w", encoding="utf-8"),
              ensure_ascii=False, indent=1)
    print("THE UNCLASSIFIED BUCKET IS NOT A PASS. Those objects do not carry enough to "
          "say whether the topic is waiting on data or incapable of being pooled, and "
          "each needs reading before any headline number is quoted.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
