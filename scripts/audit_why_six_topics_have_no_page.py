"""Six topics hold all four P46 limbs and reach no reader. WHY is each absent from PAGE_MAP?

THE QUESTION IS COMPUTABLE AND THE ANSWER DECIDES THE FIX. Six topics -- apixaban-vte-
prophylaxis, attr-pn-review, empagliflozin-hf, icosapent-lipid, rosuvastatin, tigecycline-ciai
-- hold every limb the page standard asks for, several carry the best findings of the run, and
NONE OF IT EXISTS FOR ANYBODY. Moving those six from held to delivered takes the delivered
count from 9 to 15, which is more than the eight remaining closures could add and for less
work.

BUT NOT BEFORE KNOWING WHY EACH IS ABSENT, because the fix is different for each cause:

    NEVER MAPPED, PAGE EXISTS AND IS OURS   one PAGE_MAP edit and a rebuild
    NEVER MAPPED, NO PAGE AT ALL            a new page, which is a publication decision
    PAGE EXISTS BUT IS A DIFFERENT OBJECT'S a naming collision -- mapping it would OVERWRITE
                                            somebody else's delivered page
    PAGE EXISTS FROM ANOTHER BUILDER        mapping it replaces a page a reader already has
                                            with one built by different code
    DELIBERATELY EXCLUDED                   leave it, and record the reason

A STUB THAT APPEARS WHERE A READER EXPECTED NOTHING IS THE TOMBSTONE PROBLEM, so this file
builds nothing and edits nothing. It reports.

HOW "IS THIS PAGE OF THIS OBJECT" IS DECIDED -- from the object's own numbers, not from the
filename. The filename is what got us here. Each candidate page is tested for
    (a) the object's pooled point(s), formatted as the renderers format them, and
    (b) the object's contributing NCT identifiers,
and a page carrying neither is NOT this object's page whatever it is called.
"""
import glob
import io
import json
import os
import re
import subprocess
import sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from instrument_controls import require_controls          # noqa: E402

SIX = ["apixaban-vte-prophylaxis", "attr-pn-review", "empagliflozin-hf-auto-full-review",
       "icosapent-lipid-auto-full-review", "rosuvastatin-auto-full-review",
       "tigecycline-ciai"]

# A tabbed page built by ssot/build_tabbed.py is ~1 MB. Anything far smaller was built by
# different code, and mapping it would REPLACE what a reader has rather than add to it.
TABBED_FLOOR = 300_000


def obj_fingerprint(obj):
    """The numbers only this object holds: its pooled points and its trial NCTs."""
    points, ncts = set(), set()
    for blk in ((obj.get("results") or {}).get("by_outcome") or {}).values():
        if not isinstance(blk, dict):
            continue
        pt = (blk.get("pooled") or {}).get("point")
        if isinstance(pt, (int, float)):
            points.add("%g" % pt)
            points.add("%.4f" % pt)
        for t in blk.get("per_trial") or []:
            if isinstance(t, dict) and t.get("nct"):
                ncts.add(str(t["nct"]))
    for t in (obj.get("inputs") or {}).get("trials") or []:
        if isinstance(t, dict) and t.get("nct"):
            ncts.add(str(t["nct"]))
    return points, ncts


def _who_else_holds(points, topic):
    """Which OTHER objects hold any of these pooled points? Empty means no collision."""
    out = []
    for p in sorted(glob.glob(os.path.join(REPO, "ssot", "*", "*.json"))):
        t = os.path.basename(os.path.dirname(p))
        if os.path.basename(p) != t + ".json" or t == topic:
            continue
        try:
            oo = json.load(io.open(p, encoding="utf-8"))
        except ValueError:
            continue
        for blk in ((oo.get("results") or {}).get("by_outcome") or {}).values():
            q = (blk.get("pooled") or {}).get("point") if isinstance(blk, dict) else None
            if isinstance(q, (int, float)) and ("%g" % q) in points:
                out.append(t)
    return sorted(set(out))


def ever_mapped(topic):
    """Was this topic ever an entry in PAGE_MAP.json? Read from git, not from memory."""
    # NOT text=True. On Windows that decodes with the locale codec (cp1252) and a commit
    # subject carrying an em dash or a macron comes back mangled or raises -- and this
    # function's answer decides whether a topic is called NEVER MAPPED. Decode explicitly.
    r = subprocess.run(["git", "log", "--oneline", "-S", topic, "--", "ssot/PAGE_MAP.json"],
                       cwd=REPO, capture_output=True)
    out = r.stdout.decode("utf-8", "replace")
    return [l for l in out.splitlines() if l.strip()]


def main():
    pm_path = os.path.join(REPO, "ssot", "PAGE_MAP.json")
    M = json.load(io.open(pm_path, encoding="utf-8"))
    mapped_pages = set(M)
    owner = dict((pg, os.path.basename(os.path.dirname(op))) for pg, op in M.items())

    pages = sorted(os.path.basename(x) for x in glob.glob(os.path.join(REPO, "*.html")))

    # CONTROLS. The positive is a topic KNOWN to be mapped and delivered (verified on the
    # public host this session); the negative asserts that a page carrying none of an
    # object's numbers is never called that object's page.
    cab = json.load(io.open(os.path.join(REPO, "ssot", "cab-prep-hiv-review",
                                         "cab-prep-hiv-review.json"), encoding="utf-8"))
    cab_pts, cab_ncts = obj_fingerprint(cab)
    cab_html = io.open(os.path.join(REPO, "CAB_PREP_HIV_REVIEW.html"),
                       encoding="utf-8", errors="replace").read()
    unrelated = io.open(os.path.join(REPO, "ATTR_CM_REVIEW.html"),
                        encoding="utf-8", errors="replace").read()
    require_controls(
        "audit_why_six_topics_have_no_page",
        positive=("cab-prep-hiv-review's own NCTs are found in its own delivered page",
                  bool(cab_ncts) and all(n in cab_html for n in cab_ncts), True),
        negative=("cab-prep-hiv-review's NCTs are claimed to be in an unrelated topic's page",
                  any(n in unrelated for n in cab_ncts), True))

    print("")
    print("SIX TOPICS THAT HOLD ALL FOUR LIMBS AND REACH NO READER")
    print("")
    verdicts = {}
    for topic in SIX:
        p = os.path.join(REPO, "ssot", topic, topic + ".json")
        obj = json.load(io.open(p, encoding="utf-8"))
        pts, ncts = obj_fingerprint(obj)

        # Candidate pages: any delivered file sharing the topic's leading word.
        stem = re.split(r"[-_]", topic)[0].upper()
        cands = [pg for pg in pages if pg.startswith(stem)]

        print("== %s" % topic)
        print("   object holds %d pooled point(s), %d NCT(s)" % (len(pts), len(ncts)))

        # RESOLVED SINCE THIS FILE WAS WRITTEN? Candidates exclude pages already mapped, so
        # once a topic IS mapped its own page stops being a candidate and the file reported
        # NAME COLLISION -- an instrument contradicting the act it recommended, purely
        # because it was re-run afterwards. A verdict must survive its own remedy.
        own = [pg for pg, t in owner.items() if t == topic]
        if own:
            v = ("ALREADY DELIVERED", "mapped to %s" % ", ".join(own))
            verdicts[topic] = v
            print("   -> %-18s %s" % v)
            print("")
            continue
        hist = ever_mapped(topic)
        print("   PAGE_MAP history: %s"
              % ("%d commit(s) touched this name -- %s" % (len(hist), hist[0][:60])
                 if hist else "NEVER APPEARED IN PAGE_MAP.json IN ANY COMMIT"))

        best = None
        for pg in cands:
            h = io.open(os.path.join(REPO, pg), encoding="utf-8", errors="replace").read()
            hit_n = [n for n in ncts if n in h]
            hit_p = [x for x in pts if x in h]
            size = len(h)
            mine = bool(hit_n) or bool(hit_p)
            note = []
            if pg in mapped_pages:
                note.append("MAPPED TO %s" % owner[pg])
            if size < TABBED_FLOOR:
                note.append("SMALL (%d bytes) -- NOT built by build_tabbed" % size)
            print("     %-48s %s%s%s"
                  % (pg[:48],
                     ("%d/%d NCT, %d/%d point" % (len(hit_n), len(ncts), len(hit_p), len(pts)))
                     if mine else "carries NONE of this object's numbers",
                     "  | " if note else "", "; ".join(note)))
            # RANK BY IDENTITY, THEN BY SIZE -- NEVER BY SIZE FIRST.
            #
            # The first version took the LARGEST matching page. On
            # apixaban-vte-prophylaxis that chose APIXABAN_VTE_TREATMENT_REVIEW.html
            # (1,231,653 bytes, 5/5 NCT, 0/1 point) over
            # APIXABAN_VTE_PROPHYLAXIS_REVIEW.html (5/5 NCT, 1/1 POINT), because the two
            # topics were SPLIT FROM ONE OBJECT and share every trial. Acting on that
            # verdict would have mapped this topic onto ANOTHER TOPIC'S DELIVERED PAGE --
            # precisely the collision this file exists to detect, walked into by its own
            # tie-break. The pooled point is what separates two topics built from the same
            # trials; the byte count separates nothing.
            if mine and pg not in mapped_pages:
                rank = (len(hit_p), len(hit_n), size)
                if best is None or rank > best[2]:
                    best = (pg, size, rank)

        # AND A TOPIC WHOSE BEST CANDIDATE MATCHES NO POOLED POINT IS NOT SETTLED.
        # Two topics split from one object share every NCT, so trials alone cannot tell
        # them apart; only the pooled point can. Reported as its own verdict rather than
        # folded into ONE MAP EDIT.
        if best and best[2][0] == 0 and len(pts) > 0:
            # A PAGE MISSING THE POINT IS EITHER SOMEBODY ELSE'S OR STALE, AND THE TWO ARE
            # DISTINGUISHABLE. If NO OTHER OBJECT IN THE CORPUS holds this object's pooled
            # point, the page cannot be another topic's rendering of it -- it is an older
            # build of ours, made before the current value was stored. Mapping and
            # rebuilding is then safe; mapping a collision would not be.
            rival = _who_else_holds(pts, topic)
            if rival:
                v = ("IDENTITY UNSETTLED",
                     "%s carries this object's trials but NONE of its %d pooled point(s), "
                     "AND %s also holds one of those points. Mapping on trial overlap alone "
                     "risks overwriting another topic's page."
                     % (best[0], len(pts), ", ".join(rival)))
            else:
                v = ("STALE BUILD OF OURS",
                     "%s carries this object's own trials and none of its current pooled "
                     "point(s), and NO OTHER OBJECT IN THE CORPUS HOLDS THOSE POINTS -- so "
                     "it is an older build of this topic, not another topic's page. One map "
                     "edit and a rebuild." % best[0])
            verdicts[topic] = v
            print("   -> %-18s %s" % v)
            print("")
            continue

        if best and best[1] >= TABBED_FLOOR:
            v = ("ONE MAP EDIT", "%s is unmapped, carries this object's own numbers, and is "
                                 "a full tabbed build (%d bytes)" % (best[0], best[1]))
        elif best:
            v = ("DIFFERENT BUILDER", "%s carries this object's numbers but is only %d bytes "
                                      "-- built by other code. Mapping it REPLACES a page a "
                                      "reader already has." % (best[0], best[1]))
        elif cands:
            v = ("NAME COLLISION", "every candidate page belongs to another object; none "
                                   "carries this object's numbers")
        else:
            v = ("NO PAGE AT ALL", "no delivered file shares this topic's name. Creating one "
                                   "is a publication decision, not a map edit.")
        verdicts[topic] = v
        print("   -> %-18s %s" % v)
        print("")

    print("VERDICTS")
    for k in sorted(set(v[0] for v in verdicts.values())):
        names = [t for t, v in verdicts.items() if v[0] == k]
        print("   %-18s %d   %s" % (k, len(names), ", ".join(names)))
    print("")
    print("NOTHING WAS BUILT AND NOTHING WAS MAPPED BY THIS FILE. A stub appearing where a")
    print("reader expected nothing is the tombstone problem, and which of these six should")
    print("have a page is a publication decision.")


if __name__ == "__main__":
    main()
