"""Repair arm METADATA where it disagrees with the registry -- without touching any effect.

THE FINDING THAT CHANGED THE REPAIR. My sweep flagged five trials as "role inverted" and the
obvious fix -- swap the roles -- would have INVERTED THREE CORRECT ESTIMATES.

PLATO stores `Clopidogrel role=treatment ev=864 n=9333` and `Ticagrelor role=control ev=1014
n=9291`. Those counts are ticagrelor's arm and clopidogrel's arm respectively: the object's
own `analysed.intervention = 9333` says the intervention arm is the n=9333 one, and the
stored OR 0.833 favours it, matching PLATO's published direction. So the ROLE is right, the
counts are right, the effect is right -- and the two LABELS are on the wrong arms.

  Same for ARISTOTLE (treatment n=9120 ev=212 is apixaban, labelled "1", which the registry
  says is warfarin) and IRONMAN (treatment n=569 ev=336 is the IV-iron arm, labelled
  "Standard care").

  BERSON and NEURO-TTRansform have NO counts, and there the labels name real registry arms
  while the stored effect contradicts the roles: BERSON's MD -71.8 is evolocumab lowering
  LDL-C, computed with evolocumab as the intervention, yet evolocumab is stored role=control.

SO THERE IS ONE RULE, AND THE EFFECT IS NEVER THE THING THAT MOVES:

    counts present  -> the counts anchor the roles; the LABELS are wrong
    counts absent   -> the labels anchor the drugs; the ROLES are wrong

Both end in the same place: the arm carrying role=treatment is the arm the registry marks
EXPERIMENTAL, and every stored estimate is byte-identical afterwards.

THIS IS THE THIRD TIME TONIGHT A FLAG WAS RIGHT THAT SOMETHING WAS WRONG AND WRONG ABOUT
WHAT -- after the ablation figure legends and the HFrEF "omnibus" charge. A detector that
names a defect class is a hypothesis about the data; the data decides which member it is.
"""
import io
import json
import os
import sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CACHE = os.path.join(REPO, "outputs", "ctgov_arms_cache")
OUT = os.path.join(REPO, "outputs", "arm_metadata_repair_2026_08_28.json")

EXPERIMENTAL = {"EXPERIMENTAL"}
COMPARATOR = {"ACTIVE_COMPARATOR", "PLACEBO_COMPARATOR", "SHAM_COMPARATOR", "NO_INTERVENTION"}

CASES = [
    ("ACS_ANTIPLATELET_REVIEW.html", "NCT00391872", "PLATO"),
    ("APIXABAN_AF_AUTO_FULL_REVIEW.html", "NCT00412984", "ARISTOTLE"),
    ("ATTR_PN_REVIEW.html", "NCT04136184", "NEURO-TTRansform"),
    ("EVOLOCUMAB_MIXED_DYSLIPIDEMIA_AUTO_FULL_REVIEW.html", "NCT02662569", "BERSON"),
    ("FCM_HF_REVIEW.html", "NCT02642562", "IRONMAN"),
]


def registry(nct):
    fp = os.path.join(CACHE, nct + ".json")
    d = json.load(io.open(fp, encoding="utf-8"))
    ag = (d.get("protocolSection") or {}).get("armsInterventionsModule") or {}
    return [(a.get("label"), a.get("type"), tuple(a.get("interventionNames") or []))
            for a in (ag.get("armGroups") or [])]


def effect_fingerprint(obj):
    """Every stored estimate, so the repair can prove it moved none of them."""
    return json.dumps(
        [(oid, [(r.get("nct"), r.get("point"), r.get("ci_low"), r.get("ci_high"))
                for r in (blk.get("per_trial") or [])],
          (blk.get("pooled") or {}).get("point"))
         for oid, blk in sorted(((obj.get("results") or {}).get("by_outcome") or {}).items())
         if isinstance(blk, dict)], sort_keys=True)


def main():
    apply_ = "--apply" in sys.argv
    raw = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace",
                           write_through=True)

    def say(s):
        raw.write(s + chr(10))
        raw.flush()

    pm = json.load(io.open(os.path.join(REPO, "ssot", "PAGE_MAP.json"), encoding="utf-8"))
    log, refusals = [], []

    for page, nct, name in CASES:
        rel = pm[page]
        path = os.path.join(REPO, rel)
        obj = json.load(io.open(path, encoding="utf-8"))
        before_fp = effect_fingerprint(obj)

        trial = [t for t in (obj.get("inputs") or {}).get("trials") or []
                 if t.get("nct") == nct]
        if len(trial) != 1:
            refusals.append((name, "expected exactly one trial record"))
            continue
        trial = trial[0]
        arms = trial.get("arms") or []
        trt = [a for a in arms if a.get("role") == "treatment"]
        ctl = [a for a in arms if a.get("role") == "control"]
        if len(trt) != 1 or len(ctl) != 1:
            refusals.append((name, "expected one treatment and one control arm"))
            continue
        trt, ctl = trt[0], ctl[0]

        reg = registry(nct)
        exp = [r for r in reg if r[1] in EXPERIMENTAL]
        cmp_ = [r for r in reg if r[1] in COMPARATOR]
        if len(exp) < 1 or len(cmp_) < 1:
            refusals.append((name, "registry does not name both an experimental and a "
                                   "comparator arm"))
            continue

        has_counts = (trt.get("events") is not None and trt.get("participants") is not None
                      and ctl.get("events") is not None
                      and ctl.get("participants") is not None)

        if has_counts:
            # counts anchor the roles -> the LABELS move. Pick the registry labels whose
            # types match the roles; where the registry label carries no drug identity
            # (ARISTOTLE's "1"/"2") append the intervention name so a reader can read it.
            def pick(cands):
                lab, typ, drugs = cands[0]
                if drugs and (len(str(lab)) <= 3 or str(lab).isdigit()):
                    nice = "; ".join(d.split(": ", 1)[-1] for d in drugs)
                    return "%s (%s)" % (nice, lab)
                return lab
            new_trt, new_ctl = pick(exp), pick(cmp_)
            change = {"trial": name, "nct": nct, "page": page, "mode": "LABELS",
                      "why": "counts are present and the stored effect derives from them, so "
                             "the roles are load-bearing and the labels are the free "
                             "variable",
                      "treatment_label": [trt.get("label"), new_trt],
                      "control_label": [ctl.get("label"), new_ctl]}
            if apply_:
                trt["label"], ctl["label"] = new_trt, new_ctl
                trt["label_repaired_2026_08_28"] = (
                    "was %r. Counts (%s events / %s analysed) identify this as the arm the "
                    "registry marks EXPERIMENTAL; the two arm labels were on the wrong arms. "
                    "No count and no estimate changed."
                    % (change["treatment_label"][0], trt.get("events"),
                       trt.get("participants")))
                ctl["label_repaired_2026_08_28"] = (
                    "was %r. Same repair, comparator side." % change["control_label"][0])
        else:
            # no counts -> the labels name real registry arms; the ROLES move.
            def matches(lab, cands):
                l = str(lab or "").lower()
                return any(str(c[0] or "").lower() == l for c in cands)
            if not (matches(ctl.get("label"), exp) and matches(trt.get("label"), cmp_)):
                refusals.append((name, "labels do not map cleanly onto the registry's "
                                       "experimental/comparator arms"))
                continue
            change = {"trial": name, "nct": nct, "page": page, "mode": "ROLES",
                      "why": "no counts exist, the labels name real registry arms, and the "
                             "stored effect was computed with the registry's experimental "
                             "arm as the intervention",
                      "treatment_label": [trt.get("label"), ctl.get("label")],
                      "control_label": [ctl.get("label"), trt.get("label")]}
            if apply_:
                trt["role"], ctl["role"] = "control", "treatment"
                trt["role_repaired_2026_08_28"] = (
                    "was role=treatment. The registry marks this arm a comparator and the "
                    "stored effect was computed with the other arm as the intervention. "
                    "No estimate changed.")
                ctl["role_repaired_2026_08_28"] = "was role=control. Same repair."

        after_fp = effect_fingerprint(obj)
        if after_fp != before_fp:
            refusals.append((name, "AN ESTIMATE MOVED -- refusing"))
            continue
        change["effects_unchanged"] = True
        log.append(change)

        if apply_:
            io.open(path, "w", encoding="utf-8").write(
                json.dumps(obj, indent=1, ensure_ascii=False))

    say("%-18s %-8s %s" % ("trial", "mode", "repair"))
    for c in log:
        say("%-18s %-8s treatment %r -> %r" % (c["trial"], c["mode"],
                                               c["treatment_label"][0],
                                               c["treatment_label"][1]))
        say("%-18s %-8s control   %r -> %r" % ("", "", c["control_label"][0],
                                               c["control_label"][1]))
    say("")
    say("estimates moved: %d (must be 0)" % len([c for c in log
                                                 if not c.get("effects_unchanged")]))
    say("refusals: %d" % len(refusals))
    for n, why in refusals:
        say("   %-18s %s" % (n, why))
    if not apply_:
        say("")
        say("(dry run -- nothing written; pass --apply)")
        return 0
    json.dump({"rule": "counts present -> labels are wrong; counts absent -> roles are "
                       "wrong. The stored effect never moves.",
               "repairs": log, "refusals": [{"trial": n, "why": w} for n, w in refusals]},
              io.open(OUT, "w", encoding="utf-8"), indent=1)
    say("wrote %s" % os.path.relpath(OUT, REPO))
    return 1 if refusals else 0


if __name__ == "__main__":
    sys.exit(main())
