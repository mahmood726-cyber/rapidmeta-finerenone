# -*- coding: utf-8 -*-
"""PLANT for the rule-fingerprint assertion.

THE DEFECT THIS EXISTS TO CATCH, in its own words:
  AN INSTRUMENT CERTIFIED IN ONE CONFIGURATION AND RUN IN ANOTHER.
  Amendment 2 changed class_phrases. scan.py's controls called it live and got the
  amended splitter; the twenty read class_phrases frozen into twenty.json before the
  amendment. The positive control certified a splitter the twenty never used, so it
  was not measuring the twenty at all. A convention ("redraw after amending") would be
  broken silently by the next amendment; this makes the drift mechanical.

BOTH DIRECTIONS, or the assertion is not shown to work:
  - a fresh artefact must PASS       (else the check can only refuse)
  - a stale artefact must be REFUSED (else it never fires)
  - an artefact with NO fingerprint must be REFUSED (absence is not agreement)
  - the refusal must NAME both fingerprints, or it is not diagnosable
  - the probe must be SENSITIVE to the amendment that was missed -- proven by
    reconstructing the pre-amendment splitter and showing it fingerprints differently
"""
import io, os, re, sys

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace",
                              line_buffering=True)
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import rekey_rule
from rekey_rule import rule_fingerprint, assert_fingerprint

fails = []


def case(name, recorded, must_refuse, needles=()):
    try:
        assert_fingerprint(recorded, "synthetic-artefact.json", "plant_fingerprint.py")
        refused, msg = False, ""
    except SystemExit as e:
        refused, msg = True, str(e)
    ok = (refused == must_refuse)
    if ok and must_refuse:
        for n in needles:
            if n not in msg:
                ok = False
                msg += "  <-- refusal never says %r" % n
    print("  %-46s %s" % (name, "PASS" if ok else "FAIL"))
    if must_refuse and refused:
        print("        -> %s" % msg.replace("\n", "\n           "))
    if not ok:
        fails.append(name)


live = rule_fingerprint()
case("fresh artefact passes", live, False)
case("artefact with NO fingerprint refused", None, True, ("records no rule_fingerprint",))
case("stale artefact refused", "0" * 64, True, ("000000000000", live[:16], "DIFFERENT version"))

# THE PROBE MUST BE SENSITIVE TO THE AMENDMENT THAT WAS ACTUALLY MISSED.
# Reconstruct the pre-Amendment-2 splitter (no parenthesis split, no "<exemplar> type"
# removal) and confirm it fingerprints DIFFERENTLY. If it did not, the fingerprint would
# have passed the exact drift it exists to catch.
_real = rekey_rule.class_phrases


def _pre_amendment_2(stem_def):
    if not stem_def:
        return []
    out = []
    for part in re.split(r"[,:;]| or ", stem_def):
        p = rekey_rule.norm(part).strip()
        if not p:
            continue
        out.append(p)
        w = p.split()
        if len(w) >= 3:
            out.append(" ".join(w[-2:]))
    seen, uniq = set(), []
    for p in out:
        if p and p not in seen:
            seen.add(p)
            uniq.append(p)
    return uniq


rekey_rule.class_phrases = _pre_amendment_2
try:
    pre = rule_fingerprint()
finally:
    rekey_rule.class_phrases = _real

sensitive = (pre != live)
print("  %-46s %s" % ("probe detects the pre-Amendment-2 splitter", "PASS" if sensitive else "FAIL"))
print("        pre-amendment %s   amended %s" % (pre[:16], live[:16]))
if not sensitive:
    fails.append("probe is blind to the very amendment that was missed")

print("")
if fails:
    for f in fails:
        print("PLANT FAILED: " + f)
    sys.exit(1)
print("PLANT: 4/4 -- fresh passes, stale/absent refused with both fingerprints named, and the")
print("probe is provably sensitive to the amendment that failed to propagate.")
