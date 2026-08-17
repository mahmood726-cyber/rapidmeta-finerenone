"""ARM IDENTITY -- do the two arms differ, and are they the comparison the page claims?

WHY THIS EXISTS
    Five cardiology pages were assessed for whether their question was answerable.
    FOUR failed on ARM IDENTITY OR OUTCOME IDENTITY, not on arithmetic. Every
    pooled number was computed correctly from what it was given; what it was given
    did not answer the stated question.

    DOAC_AF_REVIEW is the starkest instance in the corpus. A review titled
    DOAC-versus-warfarin, containing no DOAC-versus-warfarin comparison in any of
    its three trials:
        RE-LY              intervention "Dabigatran dose 2" vs control "Dabigatran dose 1"
        ENGAGE AF-TIMI 48  intervention "Warfarin/placebo edoxaban" vs control "low dose edoxaban"
        ARISTOTLE          intervention "1" vs control "2"
    One is a dose comparison of the same drug, one has warfarin as the
    intervention, one has arms with no labels at all.

    HEPATITIS_B_TAF_TDF is the cleanest: both trials enter as
        intervention "TAF 25 mg" vs control "Open-label TAF"
    on a page titled TAF versus TDF. The comparator in the question does not exist
    anywhere in the data.

    This is the mavacamten shape at scale -- legitimate arithmetic on the wrong
    population -- and it is mechanically detectable from the object alone. It would
    have caught four of the five without reading a single trial report.

WHAT A FULL PASS DOES NOT ESTABLISH -- written in advance
    - NOT that the arms are the RIGHT ones for the question. It checks that the two
      arms are distinguishable and that neither obviously names the other's drug. A
      page comparing the wrong two distinct drugs passes here.
    - NOT that the arm ORIENTATION is correct. Intervention and control can be
      swapped and still be distinct; only the sign of the effect reveals that, and
      this check does not look at effects.
    - NOT that unlabelled arms ("1" vs "2") are wrong -- only that they cannot be
      checked. They are reported UNCHECKABLE, never PASS.
    - NOTHING about outcomes. Outcome identity is the other half of this defect
      class and is a separate check.
"""
from __future__ import annotations
import json, os, re, sys, io, glob

if __name__ == "__main__":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

OBJ = r"F:\E156\outputs\codex-corpus-scan\extract\full_run"
# an arm label that identifies nothing
OPAQUE = re.compile(r"^\s*(\d+|arm\s*\d+|group\s*\d+|[ab]|intervention|control|treatment)\s*$", re.I)
DOSE = re.compile(r"\bdose\s*\d|\b\d+\s*mg\b|\bhigh[- ]dose\b|\blow[- ]dose\b", re.I)


def core_tokens(label):
    """Drug-ish tokens: words that are not dose, route, or packaging noise."""
    # "placebo" is NOT noise -- it is the most informative token here. Stop-listing
    # it made every drug-versus-placebo trial look like drug-versus-drug:
    # 'colchicine' vs 'colchicine placebo' and 'MK-3415 + SOC' vs 'Placebo + SOC'
    # both FAILED as same-agent comparisons when both are exactly the comparison a
    # reader wants. A stop-list that removes the discriminating word inverts the
    # test. Backgrounds shared by both arms (SOC, methotrexate, letrozole) are the
    # ones that must not decide identity.
    STOP = {"mg", "dose", "daily", "twice", "once", "open", "label", "openlabel",
            "group", "arm", "matching", "oral", "iv", "sc", "qd", "bid",
            "the", "and", "of", "in", "to", "per", "day", "week", "phase", "part",
            "soc", "standard", "care", "background", "therapy", "plus"}
    # Split hyphens BEFORE matching. "Open-label TAF" tokenised as one hyphenated
    # word that no stop-list entry covered, so {taf} vs {open-label, taf} looked
    # like two different agents and the TAF-versus-TAF page PASSED. The tokeniser
    # was deciding drug identity on punctuation.
    txt = re.sub(r"[-/,()]", " ", (label or "").lower())
    return {w for w in re.findall(r"[a-z][a-z]{2,}", txt) if w not in STOP}


def assess(trial):
    arms = {a.get("role"): a for a in (trial.get("arms") or [])}
    i, c = arms.get("intervention"), arms.get("control")
    if not i or not c:
        return "UNCHECKABLE", "fewer than two labelled arms"
    li, lc = (i.get("label") or "").strip(), (c.get("label") or "").strip()
    if not li or not lc:
        return "UNCHECKABLE", "an arm carries no label"
    if OPAQUE.match(li) or OPAQUE.match(lc):
        return "UNCHECKABLE", "arm labels identify nothing: %r vs %r" % (li, lc)
    if li.lower() == lc.lower():
        return "FAIL", "both arms carry the SAME label: %r" % li
    # A placebo/control word on exactly one side settles it: that is a real
    # comparison whatever else the labels share.
    CTRL = re.compile(r"placebo|sham|vehicle|usual care|warfarin", re.I)
    if bool(CTRL.search(li)) != bool(CTRL.search(lc)):
        return "PASS", "%r vs %r (control arm identified)" % (li, lc)
    ti, tc = core_tokens(li), core_tokens(lc)
    if ti and tc and ti == tc:
        kind = "the same drug at two doses" if (DOSE.search(li) or DOSE.search(lc)) \
            else "the same agent in both arms"
        return "FAIL", "both arms name %s: %r vs %r" % (kind, li, lc)
    if ti and tc and (ti & tc) and not (ti - tc) and not (tc - ti):
        return "FAIL", "arms share every drug token: %r vs %r" % (li, lc)
    return "PASS", "%r vs %r" % (li, lc)


def page_verdict(path):
    d = json.loads(open(path, encoding="utf-8", errors="replace").read())
    rows = [assess(t) for t in ((d.get("canonical") or {}).get("trials") or [])]
    if not rows:
        return "UNCHECKABLE", []
    if any(v == "FAIL" for v, _ in rows):
        return "FAIL", rows
    if all(v == "UNCHECKABLE" for v, _ in rows):
        return "UNCHECKABLE", rows
    return "PASS", rows


def selftest() -> int:
    ok = True
    cases = [("POSITIVE DOAC_AF (RE-LY dabigatran vs dabigatran)", "DOAC_AF_REVIEW", "FAIL"),
             ("POSITIVE HEPATITIS_B (TAF vs TAF, no TDF arm)", "HEPATITIS_B_TAF_TDF_REVIEW", "FAIL"),
             ("NEGATIVE sotagliflozin trials (drug vs placebo)", "SOTAGLIFLOZIN_HF_REVIEW", "PASS"),
             ("NEGATIVE FINERENONE (finerenone vs placebo)", "FINERENONE_REVIEW", "PASS")]
    for name, stem, want in cases:
        p = os.path.join(OBJ, stem + ".html.canonical.json")
        if not os.path.exists(p):
            print("  %-48s object absent -- NOT PROVEN" % name); ok = False; continue
        v, rows = page_verdict(p)
        good = v == want
        ok &= good
        print("  %-48s -> %-11s (want %s) %s" % (name, v, want, "correct" if good else "WRONG"))
        for rv, why in rows:
            if rv != "PASS":
                print("        %s: %s" % (rv, why[:96]))
    print("\nWHAT A FAILURE WOULD LOOK LIKE: DOAC_AF passing, which would leave a review "
          "titled DOAC-versus-warfarin containing no such comparison in any trial.")
    print("-> SELFTEST PASS" if ok else "-> SELFTEST FAILED")
    return 0 if ok else 1


def main() -> int:
    if "--selftest" in sys.argv:
        return selftest()
    paths = sorted(glob.glob(sys.argv[1]))
    tot = {"PASS": 0, "FAIL": 0, "UNCHECKABLE": 0}
    hits = []
    for p in paths:
        try:
            v, rows = page_verdict(p)
        except Exception:
            continue
        tot[v] += 1
        if v == "FAIL":
            hits.append((os.path.basename(p).replace(".html.canonical.json", ""),
                         [w for rv, w in rows if rv == "FAIL"][:2]))
    n = sum(tot.values())
    print("objects swept: %d" % n)
    for k in ("PASS", "FAIL", "UNCHECKABLE"):
        print("  %-12s %d" % (k, tot[k]))
    d = tot["PASS"] + tot["FAIL"]
    print("  rate among CHECKABLE pages: %d/%d = %.1f%%"
          % (tot["FAIL"], d, 100 * tot["FAIL"] / d) if d else "  no checkable pages")
    for pg, why in sorted(hits)[:25]:
        print("    %-46s %s" % (pg[:46], why[0][:80] if why else ""))
    return 1 if tot["FAIL"] else 0


if __name__ == "__main__":
    sys.exit(main())
