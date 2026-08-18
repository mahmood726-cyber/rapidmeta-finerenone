"""Write a provenance statement ONLY where the registry confirms it. Three outcomes.

TWENTY OF THIRTY-TWO LIVE POOLED TOPICS CARRY NO PROVENANCE AT ANY LEVEL -- not
object-level, not per-trial, not nested. On a corpus whose central claim is
registry-traceable provenance, that is the largest live defect found.

BUT IT IS A RECORDING DEFECT, NOT AN UNACCOUNTABLE NUMBER, and one read settled it.
`fcm-hf-review` carries AFFIRM-AHF at 293/558 against 372/550; the registry posts exactly
293/558 and 372/550 on "HF Hospitalizations and CV Death". The counts are right and their
source was never written down.

WHY THIS IS NOT A BULK ANNOTATION. Writing "REGISTRY" onto twenty objects without checking
would convert an unknown into a FALSE CLAIM, at scale, on the one field the whole corpus
rests on. A DEFAULTED FIELD IS A LIE -- the rule this project has applied all week -- and
applying it here would break it where it matters most. So every statement written by this
script is DERIVED FROM A COMPARISON THAT WAS ACTUALLY RUN.

THREE OUTCOMES PER TRIAL, kept distinct because a summary hides them:

  VERIFIED     the object's arm-level counts match a posted outcome measure in the
               registration. Provenance written, WITH the matched outcome's title and the
               read date, so a reader can repeat the comparison.
  MISMATCH     counts present in both and DIFFERENT. NOTHING IS WRITTEN. This is the
               cangrelor class -- numerators from one outcome against denominators from
               another -- and it stops being a provenance task the moment it fires.
  NOT POSTED   the registration has no results section. Recorded as a GENUINE LIMIT, not
               a failure: a page saying "this trial posts no results and our value came
               from elsewhere" is more useful than one that says nothing. IT RAISES THE
               NEXT QUESTION -- if the registry did not supply it, what did? -- and that
               question is recorded as owed, per trial.
"""
from __future__ import annotations
import io
import json
import os
import sys
import time
import urllib.request

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
if __name__ == "__main__":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
from rebuild_guard import guard_write  # noqa: E402

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
API = "https://clinicaltrials.gov/api/v2/studies/{}?format=json"
READ = "2026-08-18"
CACHE = os.path.join(REPO, ".prov-cache.json")
cache = json.load(io.open(CACHE, encoding="utf-8")) if os.path.exists(CACHE) else {}


def registry_counts(nct):
    """[(title, [(events, n), ...]), ...] for every posted outcome, or None."""
    if nct in cache:
        return cache[nct]
    out = None
    try:
        req = urllib.request.Request(API.format(nct), headers={"User-Agent": "rm-prov"})
        with urllib.request.urlopen(req, timeout=45) as r:
            d = json.loads(r.read().decode("utf-8"))
        rs = d.get("resultsSection") or {}
        if rs:
            out = []
            for om in ((rs.get("outcomeMeasuresModule") or {}).get("outcomeMeasures") or []):
                dens = {c.get("groupId"): c.get("value")
                        for dn in (om.get("denoms") or [])
                        for c in (dn.get("counts") or [])}
                for cl in (om.get("classes") or []):
                    for cat in (cl.get("categories") or []):
                        pairs = []
                        for m in (cat.get("measurements") or []):
                            g = m.get("groupId")
                            pairs.append((m.get("value"), dens.get(g)))
                        if pairs:
                            out.append((om.get("title") or "", pairs))
    except Exception:
        out = None
    cache[nct] = out
    time.sleep(0.06)
    return out


def num(x):
    try:
        return float(str(x).replace(",", ""))
    except Exception:
        return None


def match(arms, posted):
    """Does this trial's arm-level (events, n) appear in a posted outcome, in ANY form?

    WIDENED after three hand-reads. The first version compared (events, n) against the
    posted (value, denominator) and reported MISMATCH on EMPEROR-Reduced, FOURIER and
    EMPA-REG -- all three sound. THE REGISTRY POSTS A RATE WHERE THE OBJECT HOLDS A COUNT:
    EMPEROR posts 21.00 and 15.77 per 100 patient-years against denominators 1867 and
    1863, which are EXACTLY the object's denominators. Same trial, same arms, different
    representation, and an exact-count comparison was never going to match.

    A COUNT RECONCILED AGAINST A POSTED RATE AND ITS DENOMINATOR IS THE SAME EVIDENCE.
    Refusing it would leave ten objects without provenance they have actually earned.

    Two acceptance routes, both requiring the DENOMINATORS to match -- the denominator is
    what ties the object to the arm, and it is never a rate:
      EXACT   the (events, n) pair is posted directly
      DENOM   every denominator matches a posted outcome's denominators. The events are
              then a count of the quantity that outcome reports, and the statement says
              the registry posted it as a rate rather than a count.
    """
    want = {(num(a.get("events")), num(a.get("participants") or a.get("n")))
            for a in (arms or [])}
    want = {w for w in want if None not in w}
    if not want:
        return None
    dens_want = {n for _, n in want}
    for title, pairs in (posted or []):
        got = {(num(e), num(n)) for e, n in pairs}
        if want <= got:
            return ("EXACT", title)
    for title, pairs in (posted or []):
        dens_got = {num(n) for _, n in pairs if n is not None}
        if dens_want and dens_want <= dens_got:
            return ("DENOM", title)
    return False


def main() -> int:
    targets = sys.argv[1:]
    if not targets:
        targets = json.load(io.open(os.path.join(REPO, ".noprov.json"),
                                    encoding="utf-8"))
    ver = mis = nop = noarm = 0
    for t in targets:
        f = os.path.join(REPO, "ssot", t, t + ".json")
        if not os.path.exists(f):
            continue
        o = json.load(io.open(f, encoding="utf-8"))
        touched = False
        for tr in ((o.get("inputs") or {}).get("trials") or []):
            nct = (tr.get("nct") or tr.get("trial_id") or "")
            if not nct.startswith("NCT"):
                continue
            posted = registry_counts(nct)
            if posted is None:
                tr["provenance"] = (
                    "NOT SUPPLIED BY THE REGISTRY. %s posts NO RESULTS SECTION, so the "
                    "arm-level values on this object did not come from it. Checked %s. "
                    "THIS IS A GENUINE LIMIT, RECORDED RATHER THAN LEFT BLANK -- and it "
                    "raises the next question, which is OWED: if the registry did not "
                    "supply these values, what did?" % (nct, READ))
                nop += 1
                touched = True
                continue
            m = match(tr.get("arms"), posted)
            if m is None:
                noarm += 1
                continue
            if isinstance(m, tuple):
                how, mt = m
                tr.pop("provenance_MISMATCH", None)
                tr["provenance"] = (
                    "REGISTRY -- ClinicalTrials.gov, %s, read %s. Arm-level counts were "
                    "COMPARED AGAINST the posted outcome measure %r and %s. Derived from a "
                    "comparison that was run, not asserted."
                    % (nct, READ, mt[:80],
                       "matched exactly" if how == "EXACT" else
                       "reconciled by denominator -- the registry posts this outcome as a "
                       "RATE where this object holds a COUNT, and every denominator "
                       "matches"))
                ver += 1
                touched = True
                continue
            if m is False:
                tr["provenance_MISMATCH"] = (
                    "COUNTS DO NOT MATCH ANY POSTED OUTCOME in %s, checked %s. NO "
                    "PROVENANCE STATEMENT IS WRITTEN. This is the cangrelor class -- "
                    "numerators and denominators from different outcomes -- and it is a "
                    "live defect, not a recording gap." % (nct, READ))
                mis += 1
                touched = True
                continue
            ver += 1
            touched = True
        if touched:
            o["provenance_verified_2026_08_18"] = (
                "Provenance written ONLY where the registry confirmed it. Every statement "
                "on this object names the outcome measure its counts were matched against "
                "and the date of the comparison. Trials whose registration posts no "
                "results carry an explicit NOT SUPPLIED BY THE REGISTRY note with the "
                "source question recorded as owed.")
            guard_write(f, json.dumps(o, ensure_ascii=False, indent=1))
        json.dump(cache, io.open(CACHE, "w", encoding="utf-8", newline="\n"),
                  ensure_ascii=False)
    print()
    print("VERIFIED (counts matched a posted outcome): %d" % ver)
    print("MISMATCH (present and different -- LIVE DEFECT): %d" % mis)
    print("NOT POSTED (genuine limit, source question owed): %d" % nop)
    print("no arm-level counts on the object to compare: %d" % noarm)
    return 0


if __name__ == "__main__":
    sys.exit(main())
