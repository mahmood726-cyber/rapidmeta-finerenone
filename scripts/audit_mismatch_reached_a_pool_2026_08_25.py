"""Did any trial-identity mismatch actually reach a PUBLISHED pooled estimate?

MAHMOOD: "Establish whether any COMPARATOR mismatch actually reached a pooled estimate, and
if so whether the direction was flipped correctly. That's the question that decides whether
this is a matching defect or a published error."

Same question he asked about the screening defect, and for the same reason. A wrong trial
listed on a page that pools nothing is a DISPLAY defect: the reader sees a trial that does
not belong, which is bad, but no number is wrong. A wrong trial inside a pooled estimate is a
PUBLISHED ERROR, and where the mismatch is a COMPARATOR-role trial the error may be a sign
flip -- the drug the page is about sitting in the control arm, contributing an effect
pointing the wrong way.

Those are different orders of severity and they get different remedies, so they are counted
separately and never summed.

THE THREE OUTCOMES THIS DISTINGUISHES:

  NOT POOLED        the page publishes no pooled estimate at all. A display defect.
  POOLED, TRIAL OUT the page pools, but the mismatched trial is not among the contributors.
                    Still a display defect -- the trial is listed and not used.
  POOLED, TRIAL IN  the mismatched trial contributes to a published number. THIS is the
                    class that can be a published error, and for COMPARATOR-role trials it
                    is where a direction flip would live.

WHAT THIS CANNOT SETTLE ALONE. Whether a contributing comparator-role trial had its direction
handled correctly is a question about the extracted arm assignment, not about the pool's
existence. Where a trial lands in POOLED, TRIAL IN this reports the fields that would carry
the flip and refers the case out rather than guessing. An instrument that reported "direction
correct" from the absence of evidence would be the flattering-default failure again.
"""
import io
import json
import os
import re
import sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(REPO, "scripts"))
import instrument_controls
SWEEP = os.path.join(REPO, "outputs", "trial_identity_sweep_2026_08_25.jsonl")


def contributors(block):
    """NCT ids the object records as contributing to this outcome's pool."""
    out = set()
    pt = block.get("per_trial")
    items = []
    if isinstance(pt, list):
        items = pt
    elif isinstance(pt, dict):
        items = list(pt.values())
        out |= {k for k in pt if isinstance(k, str) and k.upper().startswith("NCT")}
    for t in items:
        if isinstance(t, dict):
            v = t.get("nct") or t.get("trial_id") or t.get("trial") or t.get("id")
            if isinstance(v, str) and v.upper().startswith("NCT"):
                out.add(v)
        elif isinstance(t, str) and t.upper().startswith("NCT"):
            out.add(t)
    # Some objects name contributors only in the forest/figure rows.
    blob = json.dumps(block)
    if not out:
        out |= set(re.findall(r"NCT\d{8}", blob))
    return out


def pool_is_published(block):
    """True only where a point estimate exists and is not withdrawn."""
    p = block.get("pooled")
    if not isinstance(p, dict):
        return False
    if p.get("point") is None:
        return False
    return not bool(p.get("withdrawn"))


def control(pmap):
    """A zero here must be a measurement, not an instrument that cannot see.

    Every mismatched trial landed in NOT POOLED on the first run -- 27 of 27, a clean
    sweep, which is the exact shape this repository has been wrong about eight times in one
    day. So before that zero is reported the detector is shown real pooling pages and must
    find their real contributors. If it cannot, no count is printed.
    """
    probed = found = 0
    for page, path in sorted(pmap.items()):
        full = os.path.join(REPO, path)
        if not os.path.exists(full):
            continue
        try:
            o = json.load(io.open(full, encoding="utf-8"))
        except Exception:
            continue
        res = (o.get("results") or {}).get("by_outcome") or {}
        pub = [b for b in res.values() if isinstance(b, dict) and pool_is_published(b)]
        if not pub:
            continue
        probed += 1
        if contributors(pub[0]):
            found += 1
        if probed >= 8:
            break
    # A page with NO pool must not be reported as having contributors -- the negative
    # direction, without which the control only proves the detector can say yes.
    empty_seen = contributors({"pooled": {"point": None}, "per_trial": []})

    instrument_controls.require_controls(
        "mismatch-reached-a-pool",
        ("contributors detected on pages that really do publish a pool "
         "(%d of %d probed)" % (found, probed), found == probed and probed > 0, True),
        ("an outcome block with no pool and no per-trial rows",
         bool(empty_seen), True))
    return True


def main():
    if not os.path.exists(SWEEP):
        print("REFUSED: the sweep ledger is not on disk, so there is nothing to classify. "
              "NO COUNT IS PRINTED.")
        return 2
    pmap = json.load(io.open(os.path.join(REPO, "ssot", "PAGE_MAP.json"), encoding="utf-8"))
    if not control(pmap):
        return 2

    recs = []
    for line in io.open(SWEEP, encoding="utf-8"):
        try:
            d = json.loads(line)
        except ValueError:
            continue
        if d.get("status") == "ok" and d.get("page_verdict") == "MISMATCH":
            recs.append(d)

    buckets = {"NOT POOLED": [], "POOLED, TRIAL OUT": [], "POOLED, TRIAL IN": []}
    by_role = {}
    for d in recs:
        page = d["page"]
        path = os.path.join(REPO, pmap.get(page, ""))
        if not os.path.exists(path):
            continue
        o = json.load(io.open(path, encoding="utf-8"))
        res = (o.get("results") or {}).get("by_outcome") or {}
        published = {oid: b for oid, b in res.items()
                     if isinstance(b, dict) and pool_is_published(b)}
        for t in d.get("trials", []):
            if t.get("studies_subject") != "NO":
                continue
            nct, role = t.get("nct"), t.get("role")
            by_role[role] = by_role.get(role, 0) + 1
            if not published:
                buckets["NOT POOLED"].append((page, nct, role, ""))
                continue
            hit = [oid for oid, b in published.items() if nct in contributors(b)]
            if hit:
                buckets["POOLED, TRIAL IN"].append((page, nct, role, ",".join(hit)))
            else:
                buckets["POOLED, TRIAL OUT"].append((page, nct, role, ""))

    print("MISMATCH pages classified: %d   mismatched trial records: %d"
          % (len(recs), sum(len(v) for v in buckets.values())))
    print("by role: %s" % by_role)
    print()
    for name in ("NOT POOLED", "POOLED, TRIAL OUT", "POOLED, TRIAL IN"):
        rows = buckets[name]
        sev = {"NOT POOLED": "display defect -- no number is wrong",
               "POOLED, TRIAL OUT": "display defect -- listed but not used",
               "POOLED, TRIAL IN": "PUBLISHED ERROR -- contributes to a live number"}[name]
        print("== %-20s %3d   (%s)" % (name, len(rows), sev))
        for page, nct, role, oids in rows:
            print("     %-42s %-12s role=%-12s %s" % (page[:40], nct, role, oids))
        print()

    live = buckets["POOLED, TRIAL IN"]
    comp = [r for r in live if r[2] == "COMPARATOR"]
    print("THE ANSWER TO THE QUESTION ASKED:")
    print("  mismatched trials inside a published pool          : %d" % len(live))
    print("  of those, the page's own drug is the COMPARATOR arm: %d" % len(comp))
    if not live:
        print()
        print("  So on the pages classified so far this is a MATCHING and DISPLAY defect,")
        print("  not a published error. No pooled number on any of them draws on a trial")
        print("  that does not study the subject.")
    else:
        print()
        print("  Each of these needs its arm assignment read before the direction can be")
        print("  called correct or flipped. This instrument does not guess that.")
    out = os.path.join(REPO, "outputs", "mismatch_pool_classification_2026_08_25.json")
    json.dump({k: [list(r) for r in v] for k, v in buckets.items()},
              io.open(out, "w", encoding="utf-8"), indent=1)
    print()
    print("written: %s" % os.path.relpath(out, REPO))
    return 0


if __name__ == "__main__":
    sys.exit(main())
