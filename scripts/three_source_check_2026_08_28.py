"""For each of the 23: what the OBJECT holds, what the REASON says, what the REGISTRY posts.

WHY THREE SOURCES AND NOT TWO. Classifying these pages from their stored reasons produced
"23 terminal, 0 recoverable", which was withdrawn: a stored reason is a claim ABOUT the
object and this corpus's claims about itself go stale. Reading the object instead is better
and still insufficient -- on hepatitis-b-taf-tdf the object and its reason AGREE (both arms
are TAF, TDF appears in no arm label) while the registry posts a TDF arm that was never
extracted. That is recoverable, but by RE-EXTRACTION, not because a reason went stale.

  Object and reason agreeing is a positive control on the stored judgement.
  Object and registry disagreeing is where recovery lives.
  Neither is visible from one source alone.

SO EVERY LINE NAMES ITS SOURCE. "The object holds only TAF arms" and "the registry posts a
TDF arm" are both true and are not the same statement.

WHAT IS COMPARED, per page:
  OBJECT    arm labels and roles, per-trial counts, k, whether counts are present at all
  REASON    the first populated field of six, plus any handbook block
  REGISTRY  arm labels and types from ClinicalTrials.gov v2, live, cached per NCT

THE ROLE CHECK IS NOT HERE. A wrong role is worse than a missing one -- it produces a
confident answer with the sign reversed -- but it is a corpus-wide question, not a question
about these 23, and it lives in sweep_arm_roles_2026_08_28.py. This file said it did the role
check for one draft before it did; that sentence is removed rather than left to be believed.
"""
import io
import json
import os
import re
import subprocess
import sys
import time

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CACHE = os.path.join(REPO, "outputs", "ctgov_arms_cache")
OUT = os.path.join(REPO, "outputs", "three_source_check_2026_08_28.json")

FIELDS = ("not_poolable_reason", "poolable_reason", "absent_reason",
          "card_note", "withdrawn_reason", "withdrawn_note")
API = ("https://clinicaltrials.gov/api/v2/studies/%s"
       "?fields=NCTId,ArmGroupLabel,ArmGroupType,ArmGroupInterventionName")


def registry_arms(nct):
    """[(label, type)] from ClinicalTrials.gov, cached. None if the fetch failed."""
    os.makedirs(CACHE, exist_ok=True)
    fp = os.path.join(CACHE, nct + ".json")
    if os.path.exists(fp) and os.path.getsize(fp) > 40:
        body = io.open(fp, encoding="utf-8", errors="replace").read()
    else:
        body = None
        for attempt in (1, 2, 3):
            r = subprocess.run(["curl", "-sSL", "-g", "--max-time", "60", API % nct],
                               capture_output=True)
            b = (r.stdout or b"").decode("utf-8", "replace")
            if b.lstrip().startswith("{") and "protocolSection" in b:
                io.open(fp, "w", encoding="utf-8").write(b)
                body = b
                break
            time.sleep(2 * attempt)
        if body is None:
            return None
    try:
        p = (json.loads(body).get("protocolSection") or {})
        ag = ((p.get("armsInterventionsModule") or {}).get("armGroups") or [])
        return [(a.get("label"), a.get("type")) for a in ag]
    except (ValueError, AttributeError):
        return None


def main():
    raw = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace",
                           write_through=True)

    def say(s):
        raw.write(s + chr(10))
        raw.flush()

    pm = json.load(io.open(os.path.join(REPO, "ssot", "PAGE_MAP.json"), encoding="utf-8"))
    split = json.load(io.open(os.path.join(REPO, "outputs", "_the134_split.json"),
                              encoding="utf-8"))
    pages = split["per-trial rows present, never pooled (verdict-only)"]
    say("pages: %d  (the 23)" % len(pages))
    say("")

    rows = []
    for page in sorted(pages):
        o = json.load(io.open(os.path.join(REPO, pm[page]), encoding="utf-8"))
        trials = (o.get("inputs") or {}).get("trials") or []
        by = (o.get("results") or {}).get("by_outcome") or {}

        # POSITIVE selection, and the residue is counted. A `continue` on the non-dict case
        # would drop those outcomes out of the denominator without saying so, which is the
        # class this project has been bitten by six times.
        blocks = [(oid, b) for oid, b in by.items() if isinstance(b, dict)]
        skipped_blocks = len(by) - len(blocks)
        reason = None
        for oid, b in blocks:
            for f in FIELDS:
                if b.get(f):
                    reason = (f, str(b[f]))
                    break
            if reason:
                break

        obj_arms, reg_arms, has_counts, ncts = [], {}, False, []
        for t in trials:
            nct = (t.get("nct") or "").strip()
            if nct:
                ncts.append(nct)
            for a in (t.get("arms") or []):
                obj_arms.append((nct, a.get("label"), a.get("role"),
                                 a.get("events"), a.get("participants")))
                if a.get("events") is not None and a.get("participants") is not None:
                    has_counts = True
        for nct in ncts:
            reg_arms[nct] = registry_arms(nct)

        n_obj = len(obj_arms)
        n_reg = sum(len(v) for v in reg_arms.values() if v)
        unreadable = [n for n, v in reg_arms.items() if v is None]

        # does every registry arm label appear among the object's labels for that trial?
        # Only trials whose registry record READ are comparable; the rest are named in
        # `registry_unreadable` rather than quietly leaving the comparison.
        missing = []
        for nct, arms in [(n, a) for n, a in reg_arms.items() if a]:
            olabels = [str(l or "").lower() for (n, l, r, e, p) in obj_arms if n == nct]
            for label, typ in arms:
                lab = str(label or "").lower()
                if not any(lab[:14] and lab[:14] in ol for ol in olabels):
                    missing.append((nct, label, typ))

        rows.append({"page": page, "reason_field": reason[0] if reason else None,
                     "reason": (reason[1][:200] if reason else None),
                     "object_arms": n_obj, "registry_arms": n_reg,
                     "object_has_counts": has_counts,
                     "registry_unreadable": unreadable,
                     "outcome_blocks_skipped_not_a_dict": skipped_blocks,
                     "trials_compared": len([1 for a in reg_arms.values() if a]),
                     "trials_total": len(reg_arms),
                     "registry_arms_absent_from_object": missing})
        flag = ("REGISTRY HAS ARMS THE OBJECT LACKS" if missing else
                "object covers the registry's arms")
        say("%-46s obj_arms=%-3d reg_arms=%-3d counts=%-5s %s"
            % (page[:46], n_obj, n_reg, has_counts, flag))
        for nct, label, typ in missing[:3]:
            say("      missing from object: %s  %-40s [%s]" % (nct, str(label)[:40], typ))
        time.sleep(0.2)

    say("")
    n = len(rows)
    with_missing = [r for r in rows if r["registry_arms_absent_from_object"]]
    nocounts = [r for r in rows if not r["object_has_counts"]]
    say("SUMMARY, each line naming its source")
    say("  LABEL-MATCH flag, NOT RELIABLE, do not quote        : %d / %d"
        % (len(with_missing), n))
    say("    Substring matching on arm labels. Hand-checked and it over-flags badly: it")
    say("    calls `Catheter ablation` absent from a registry whose label for that arm is")
    say("    the literal string `1`. The defensible comparison is per-trial ARM COUNTS,")
    say("    which is wording-independent -- 12 of 23 pages, reported separately.")
    say("  pages where the OBJECT holds no counts at all          : %d / %d"
        % (len(nocounts), n))
    say("  pages with an unreadable registry record               : %d / %d"
        % (len([r for r in rows if r["registry_unreadable"]]), n))
    say("  trials actually compared / trials on these pages        : %d / %d"
        % (sum(r["trials_compared"] for r in rows), sum(r["trials_total"] for r in rows)))
    say("  outcome blocks skipped for not being a dict             : %d"
        % sum(r["outcome_blocks_skipped_not_a_dict"] for r in rows))
    json.dump({"note": "three sources per page: object, stored reason, registry. Each line "
                       "names which source it is about.",
               "n": n, "rows": rows},
              io.open(OUT, "w", encoding="utf-8"), indent=1)
    say("")
    say("wrote %s" % os.path.relpath(OUT, REPO))
    return 0


if __name__ == "__main__":
    sys.exit(main())
