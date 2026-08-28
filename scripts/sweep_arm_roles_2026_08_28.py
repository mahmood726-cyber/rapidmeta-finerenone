"""Does the `role` on each object arm match the assignment the trial registered?

WHY THIS IS WORSE THAN A MISSING ROLE. An absent role makes a page say less than it knows. An
INVERTED role makes it say the opposite with the same confidence: the arm the trial called
experimental is presented as the comparator, and every effect computed from that contrast has
its sign reversed while every gate in this project still passes. Nothing downstream can catch
it, because the object is internally consistent -- it is only wrong against the registry.

FOUND AS ONE PAGE. EVOLOCUMAB_MIXED_DYSLIPIDEMIA, trial BERSON (NCT02662569): the object
carries `Atorvastatin (Q2W)` as role=treatment and `Evolocumab QM + Atorvastatin` as
role=control. The registry posts the evolocumab arms as EXPERIMENTAL. The drug under study is
sitting in the control column.

THE VERDICT IS THREE-STATE, AND THE THIRD STATE IS THE POINT. A registry that marks both arms
ACTIVE_COMPARATOR (common in head-to-head trials) does not determine which arm a review should
call treatment. Reporting that as INVERTED would manufacture defects out of trials that are
simply not discriminated by the registry's own field.

    CONSISTENT   treatment<->EXPERIMENTAL, control<->a comparator/no-intervention type
    INVERTED     BOTH matched arms are wrong, and wrong in opposite directions
    UNDECIDABLE  labels did not match, or the registry types do not discriminate --
                 including when both arms carry an IDENTICAL intervention set, which marks a
                 dose comparison. A SHARED BACKGROUND drug is not that: arms differing by one
                 added drug stay decidable, and testing intersection rather than equality
                 reclassified two confirmed inversions as undecidable.

INVERTED REQUIRES BOTH DIRECTIONS TO FAIL TOGETHER. A single arm reading `control` against an
EXPERIMENTAL registry type is reported as SUSPECT, not INVERTED: multi-arm trials collapsed to
two arms produce that pattern honestly, and this corpus has 17 trials where the registry posts
more arms than the object holds.

MATCHING IS STRICT AND ADMITS DEFEAT. Arm labels are prose and this project has already been
burned by a substring matcher: it flagged `Catheter ablation` as absent from a registry whose
label for that arm is the literal string `1`. So a match is accepted only on normalised
equality or a token-overlap of 0.6 with a unique best candidate, and everything else is
UNDECIDABLE rather than a guess.

CONTROLS ARE SYNTHETIC, not corpus pages. A control anchored to a live page stops being a
control the moment the page is fixed -- it then passes for the wrong reason. BERSON is checked
too, but as a reported observation, never as the gate.
"""
import collections
import io
import json
import os
import re
import subprocess
import sys
import time

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(REPO, "scripts"))
CACHE = os.path.join(REPO, "outputs", "ctgov_arms_cache")
OUT = os.path.join(REPO, "outputs", "arm_role_sweep_2026_08_28.json")

API = ("https://clinicaltrials.gov/api/v2/studies/%s"
       "?fields=NCTId,ArmGroupLabel,ArmGroupType,ArmGroupInterventionName")

EXPERIMENTAL = {"EXPERIMENTAL"}
COMPARATOR = {"ACTIVE_COMPARATOR", "PLACEBO_COMPARATOR", "SHAM_COMPARATOR", "NO_INTERVENTION"}

STOP = {"mg", "mcg", "g", "kg", "ml", "daily", "once", "twice", "bid", "od", "qd", "the",
        "and", "of", "a", "an", "per", "day", "week", "dose", "group", "arm", "phase"}


def norm(s):
    return re.sub(r"[^a-z0-9 ]+", " ", str(s or "").lower()).strip()


def toks(s):
    return set(w for w in norm(s).split() if w and w not in STOP and not w.isdigit())


def match(label, registry):
    """Best registry arm for this object label, or None. Strict: exact, else 0.6 overlap
    with a UNIQUE best candidate."""
    n = norm(label)
    exact = [r for r in registry if norm(r[0]) == n]
    if len(exact) == 1:
        return exact[0]
    a = toks(label)
    if not a:
        return None
    scored = []
    for r in registry:
        b = toks(r[0])
        if not b:
            continue
        scored.append((len(a & b) / float(len(a | b)), r))
    if not scored:
        return None
    scored.sort(key=lambda x: -x[0])
    if scored[0][0] < 0.6:
        return None
    if len(scored) > 1 and abs(scored[0][0] - scored[1][0]) < 1e-9:
        return None                      # tie -> refuse to guess
    return scored[0][1]


def judge(arms, registry):
    """(verdict, detail) for ONE trial. arms = [(label, role)]."""
    pairs = []
    for label, role in arms:
        if role not in ("treatment", "control"):
            continue
        m = match(label, registry)
        pairs.append((label, role, m[0] if m else None, m[1] if m else None,
                      m[2] if m else ()))
    if not pairs:
        return "UNDECIDABLE", "no roles on arms", pairs
    matched = [p for p in pairs if p[3]]
    if not matched:
        return "UNDECIDABLE", "no arm label matched a registry arm", pairs
    # "The registry does not discriminate" is only a question once TWO arms matched. With one
    # matched arm there is nothing to discriminate BETWEEN, and reading a single type as
    # non-discriminating swallowed every SUSPECT case -- caught by the control, not by review.
    # SAME DRUG IN BOTH ARMS -> the registry's types are marking a DOSE comparison, not a
    # drug-vs-control one, and reading them as treatment/control manufactures an inversion.
    # APPRAISE (NCT00313300) posts A1 as ACTIVE_COMPARATOR and A4 as EXPERIMENTAL and BOTH
    # are apixaban; the first run of this sweep called that INVERTED. It is not.
    if len(matched) >= 2:
        drugs = [frozenset(p[4]) for p in matched if p[4]]
        if len(drugs) >= 2 and len(set(drugs)) == 1:
            return ("UNDECIDABLE",
                    "the matched arms carry an IDENTICAL intervention set (%s) -- the "
                    "registry's types mark a dose comparison, not treatment vs control"
                    % "; ".join(sorted(drugs[0]))[:60], pairs)
    types = set(p[3] for p in matched)
    if len(matched) >= 2 and len(types) == 1:
        return "UNDECIDABLE", "registry types do not discriminate (all %s)" % types.pop(), pairs

    wrong = []
    for label, role, rlabel, rtype, _drugs in matched:
        if role == "treatment" and rtype in COMPARATOR:
            wrong.append((label, role, rtype))
        elif role == "control" and rtype in EXPERIMENTAL:
            wrong.append((label, role, rtype))
    if not wrong:
        return "CONSISTENT", "", pairs
    dirs = set()
    for _, role, _ in wrong:
        dirs.add(role)
    if dirs == {"treatment", "control"}:
        return "INVERTED", "both matched arms wrong, in opposite directions", pairs
    return "SUSPECT", "one arm disagrees (%s labelled %s)" % (wrong[0][2], wrong[0][1]), pairs


def registry_arms(nct, allow_fetch=True):
    os.makedirs(CACHE, exist_ok=True)
    fp = os.path.join(CACHE, nct + ".json")
    if os.path.exists(fp) and os.path.getsize(fp) > 40:
        body = io.open(fp, encoding="utf-8", errors="replace").read()
    elif not allow_fetch:
        return None
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
        return [(a.get("label"), a.get("type"),
                 tuple(sorted(a.get("interventionNames") or []))) for a in ag]
    except (ValueError, AttributeError):
        return None


def run_controls():
    """Synthetic. A control anchored to a live page retires itself when the page is fixed."""
    from instrument_controls import require_controls
    reg = [("Evolocumab 140 mg", "EXPERIMENTAL", ("Drug: Evolocumab",)),
           ("Placebo", "PLACEBO_COMPARATOR", ("Drug: Placebo",))]
    inverted = [("Placebo", "treatment"), ("Evolocumab 140 mg", "control")]
    correct = [("Evolocumab 140 mg", "treatment"), ("Placebo", "control")]
    one_off = [("Evolocumab 140 mg", "control"), ("Nothing Comparable Here", "treatment")]
    flat = [("Drug A", "treatment"), ("Drug B", "control")]
    flatreg = [("Drug A", "ACTIVE_COMPARATOR", ("Drug: A",)),
               ("Drug B", "ACTIVE_COMPARATOR", ("Drug: B",))]
    samedrug = [("Apixaban low dose", "treatment"), ("Apixaban high dose", "control")]
    samedrugreg = [("Apixaban low dose", "ACTIVE_COMPARATOR", ("Drug: Apixaban",)),
                   ("Apixaban high dose", "EXPERIMENTAL", ("Drug: Apixaban",))]
    # The two states that separate this instrument from an over-flagger. Asserted before the
    # controls run, because if these collapse the positive control passes for a bad reason:
    # an instrument that calls everything INVERTED also detects a planted inversion.
    assert judge(one_off, reg)[0] == "SUSPECT", judge(one_off, reg)
    assert judge(flat, flatreg)[0] == "UNDECIDABLE", judge(flat, flatreg)
    assert judge(samedrug, samedrugreg)[0] == "UNDECIDABLE", judge(samedrug, samedrugreg)
    # A SHARED BACKGROUND drug must NOT make a trial undecidable. Using set INTERSECTION here
    # instead of equality silently reclassified BERSON and NEURO-TTRansform -- two confirmed
    # inversions -- as undecidable, because every arm sits on the same background therapy.
    bg = [("Atorvastatin alone", "treatment"), ("Evolocumab + Atorvastatin", "control")]
    bgreg = [("Atorvastatin alone", "ACTIVE_COMPARATOR", ("Drug: Atorvastatin",)),
             ("Evolocumab + Atorvastatin", "EXPERIMENTAL",
              ("Drug: Atorvastatin", "Drug: Evolocumab"))]
    assert judge(bg, bgreg)[0] == "INVERTED", judge(bg, bgreg)
    require_controls(
        "arm_role_sweep",
        ("a planted straight inversion is detected",
         judge(inverted, reg)[0], "INVERTED"),
        ("a correctly-assigned pair must NOT read INVERTED",
         judge(correct, reg)[0], "INVERTED"))


def main():
    run_controls()
    raw = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace",
                           write_through=True)

    def say(s):
        raw.write(s + chr(10))
        raw.flush()

    pm = json.load(io.open(os.path.join(REPO, "ssot", "PAGE_MAP.json"), encoding="utf-8"))
    c = collections.Counter()
    rows, inverted, suspect = [], [], []
    seen_ncts = set()

    for page, path in sorted(pm.items()):
        fp = os.path.join(REPO, path)
        if not os.path.exists(fp):
            continue
        try:
            o = json.load(io.open(fp, encoding="utf-8"))
        except ValueError:
            continue
        for t in ((o.get("inputs") or {}).get("trials") or []):
            nct = (t.get("nct") or "").strip()
            arms = [(a.get("label"), a.get("role")) for a in (t.get("arms") or [])
                    if a.get("role") is not None]
            if not arms:
                continue
            if not nct.startswith("NCT"):
                c["UNDECIDABLE"] += 1
                rows.append({"page": page, "nct": nct, "verdict": "UNDECIDABLE",
                             "detail": "no NCT on the trial"})
                continue
            reg = registry_arms(nct)
            if nct not in seen_ncts:
                seen_ncts.add(nct)
                time.sleep(0.15)
            if reg is None:
                c["UNDECIDABLE"] += 1
                rows.append({"page": page, "nct": nct, "verdict": "UNDECIDABLE",
                             "detail": "registry record unreadable"})
                continue
            verdict, detail, pairs = judge(arms, reg)
            c[verdict] += 1
            rec = {"page": page, "nct": nct, "verdict": verdict, "detail": detail,
                   "arms": [{"object_label": a, "role": r, "registry_label": rl,
                             "registry_type": rt, "registry_drugs": list(dr)}
                            for a, r, rl, rt, dr in pairs]}
            rows.append(rec)
            if verdict == "INVERTED":
                inverted.append(rec)
            elif verdict == "SUSPECT":
                suspect.append(rec)

    n = sum(c.values())
    say("trial-arm sets examined : %d   across %d distinct registrations"
        % (n, len(seen_ncts)))
    say("")
    for k in ("CONSISTENT", "INVERTED", "SUSPECT", "UNDECIDABLE"):
        say("  %-12s %4d / %d  (%.0f%%)" % (k, c[k], n, 100.0 * c[k] / n if n else 0))
    say("")
    say("INVERTED -- the drug under study is in the control column")
    for r in inverted:
        say("  %-44s %s  %s" % (r["page"][:44], r["nct"], r["detail"]))
        for a in r["arms"]:
            say("       role=%-9s object=%-38s registry=[%s]"
                % (a["role"], str(a["object_label"])[:38], a["registry_type"]))
    if not inverted:
        say("  (none)")
    say("")
    say("SUSPECT -- one arm disagrees; a collapsed multi-arm trial produces this honestly")
    for r in suspect[:12]:
        say("  %-44s %s  %s" % (r["page"][:44], r["nct"], r["detail"]))
    if len(suspect) > 12:
        say("  ... and %d more" % (len(suspect) - 12))

    berson = [r for r in rows if r["nct"] == "NCT02662569"]
    say("")
    say("BERSON NCT02662569, the case this sweep was built from -- reported, never the gate:")
    for r in berson:
        say("  %-44s %s" % (r["page"][:44], r["verdict"]))

    json.dump({"question": "does each object arm's role match the registered assignment",
               "verdicts": "CONSISTENT / INVERTED / SUSPECT / UNDECIDABLE; INVERTED requires "
                           "BOTH matched arms wrong in opposite directions",
               "matching": "normalised equality, else 0.6 token overlap with a unique best "
                           "candidate; anything else is UNDECIDABLE rather than a guess",
               "counts": dict(c), "n": n, "rows": rows},
              io.open(OUT, "w", encoding="utf-8"), indent=1)
    say("")
    say("wrote %s" % os.path.relpath(OUT, REPO))
    return 0


if __name__ == "__main__":
    sys.exit(main())
