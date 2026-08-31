# -*- coding: utf-8 -*-
"""EVERY ALTERNATIVE OF EVERY PATTERN I ADDED TONIGHT, WITH ITS OWN HIT COUNT.

⛔⛔ WHY. The unanchored or over-specified pattern is this repo's most common defect --
eight instances in one night, the worst of them a gate matching `href="..."` against a
generator that emits `href='...'`, which scored ninety pages with perfectly good links as
broken and produced a headline that had to be retracted twice.

⇒ A DISJUNCTION IS GREEN AS SOON AS ONE BRANCH FIRES. `a|b|c|d` reports a healthy count
while `c` and `d` have never matched anything in the life of the instrument, and nothing in
the output distinguishes "this branch is not needed here" from "this branch is broken and
would never fire anywhere". So each alternative is counted SEPARATELY and dead ones are
NAMED.

⭐ AND A DEAD BRANCH IS NOT AUTOMATICALLY A DEFECT. `q4w` matching nothing in this corpus is
a branch that is CORRECT and UNEXERCISED; `placebo` matching nothing would be a broken
pattern. The audit reports the count and says which it cannot tell apart, rather than
guessing -- so a dead branch gets a SYNTHETIC PROBE that proves it can fire at all.

⚠️ ONE WALK. F: costs ~78 ms per file open, so every object is read once and all patterns
are evaluated against the same in-memory labels.
"""
import glob, io, json, os, re, sys
from collections import Counter

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, ".."))
sys.path.insert(0, os.path.join(HERE, "..", ".."))
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace",
                              line_buffering=True)
from search_topic import _SCHEDULE, _PLACEBO, _CONJ                     # noqa: E402

from instrument_controls import require_controls                        # noqa: E402

ROOT = "F:/rapidmeta-ssot-shell"

# ⭐ THE CONTROL CASE IS A REAL ARM LABEL, READ FROM THE OBJECT, NOT INVENTED HERE.
# ssot/colchicine-cvd-review, NCT02551094, role=control.
KNOWN_LABEL = "colchicine placebo"

# The alternatives, written out one per line so each can be counted alone. These are
# TRANSCRIBED from the shipped patterns; the transcription is itself checked below by
# asserting each alternative is accepted by the real compiled pattern.
SCHEDULE_ALTS = [r"q[0-9]*[dwmhy]", r"b\.?i\.?d", r"t\.?i\.?d", r"q\.?i\.?d", r"q\.?d",
                 r"q\.?h\.?s", r"prn", r"p\.?o", r"i\.?v", r"s\.?c", r"s\.?q", r"ac", r"pc"]
SCHEDULE_PROBE = {r"q[0-9]*[dwmhy]": "Q2W", r"b\.?i\.?d": "BID", r"t\.?i\.?d": "TID",
                  r"q\.?i\.?d": "QID", r"q\.?d": "QD", r"q\.?h\.?s": "QHS", r"prn": "PRN",
                  r"p\.?o": "PO", r"i\.?v": "IV", r"s\.?c": "SC", r"s\.?q": "SQ",
                  r"ac": "AC", r"pc": "PC"}
PLACEBO_ALTS = ["placebo", "sham", "vehicle", "dummy", "matching", "matched"]
# ⭐ PROBES FOR THE PLACEBO BRANCHES. The first run of this audit reported four of these as
# "ZERO and NO PROBE -- cannot tell broken from unexercised", which is the correct thing for
# it to say and a gap in the AUDIT rather than in the pattern. Each probe is a control-arm
# label of the kind the branch exists for, and deliberately contains no other branch's word,
# so a probe cannot pass through a sibling branch.
PLACEBO_PROBE = {"placebo": "placebo tablet", "sham": "sham procedure",
                 "vehicle": "vehicle control", "dummy": "double dummy",
                 "matching": "matching tablet", "matched": "dose-matched control"}
CONJ_ALTS = [r"\+", r"\bplus\b", r"\band\b"]

# ---------------------------------------------------------------- ONE WALK
dirs = sorted(glob.glob(os.path.join(ROOT, "ssot", "*", "")))
labels, kinds = [], Counter()
objects_read = objects_absent = 0
for d in dirs:
    name = os.path.basename(os.path.normpath(d))
    f = os.path.join(d, name + ".json")
    if not os.path.exists(f):
        objects_absent += 1
        continue
    objects_read += 1
    try:
        o = json.load(io.open(f, encoding="utf-8"))
    except Exception:                                          # noqa: BLE001
        kinds["unparseable"] += 1
        continue
    trials = ((o.get("inputs") or {}).get("trials")
              if isinstance(o.get("inputs"), dict) else None)
    if not isinstance(trials, list):
        kinds["no_trials_list"] += 1
        continue
    n = 0
    for t in trials:
        for a in ((t or {}).get("arms") or []) if isinstance(t, dict) else []:
            if isinstance(a, dict) and str(a.get("label") or "").strip():
                labels.append((name, a.get("role"), str(a["label"])))
                n += 1
    kinds["with_arm_labels" if n else "trials_but_no_arm_labels"] += 1

print("=== THE POPULATION, KINDS BEFORE THE NUMBER ===")
print("   ssot/ directories walked        : %d" % len(dirs))
print("   objects read                    : %d" % objects_read)
print("   NAMED ABSENT (no <name>.json)   : %d" % objects_absent)
print("   partition sums to the walk      : %d + %d == %d  %s"
      % (objects_read, objects_absent, len(dirs),
         "HOLDS" if objects_read + objects_absent == len(dirs) else "BROKEN"))
for k, v in kinds.most_common():
    print("      %-28s %d" % (k, v))
print("   ARM LABELS -- the population these patterns actually run on: %d" % len(labels))
roles = Counter(r for _, r, _ in labels)
print("      by role: %s" % dict(roles))
print("")

dead = []


def branch_row(a, corpus, probe=None, whole=False):
    """-> (n, kind). kind is 'live' | 'unexercised_ok' | 'dead'. The ONE place a branch
    acquires a verdict, so the controls below exercise the same code the report does."""
    rx = re.compile(("(?i)^(?:%s)\\.?$" % a) if whole else ("(?i)%s" % a))
    n = sum(1 for s in corpus if rx.search(s))
    if n:
        return n, "live"
    if probe and a in probe:
        prx = re.compile(("(?i)^(?:%s)\\.?$" % a) if whole else ("(?i)%s" % a))
        return 0, ("unexercised_ok" if prx.search(probe[a]) else "dead")
    return 0, "dead"


def audit(title, alts, corpus, probe=None, whole=False):
    print("=== %s ===" % title)
    print("   %-22s %8s  %s" % ("alternative", "hits", "verdict"))
    for a in alts:
        # ⛔ THE REPORT CALLS `branch_row`, THE SAME FUNCTION THE CONTROLS CALL.
        # These two used to be parallel implementations of the same rule, which would have
        # made the control above certify a reimplementation rather than the instrument --
        # the failure its own comment warns about. One source, or the control is decoration.
        n, kind = branch_row(a, corpus, probe, whole)
        if kind == "live":
            verdict = "live on this corpus"
        elif kind == "unexercised_ok":
            verdict = ("UNEXERCISED -- but fires on probe %r, so the branch works"
                       % probe[a])
        elif probe and a in probe:
            verdict = ("⛔ DEAD AND BROKEN -- does not even fire on its own probe %r"
                       % probe[a])
            dead.append((title, a))
        else:
            verdict = "⛔ ZERO and NO PROBE -- cannot tell broken from unexercised"
            dead.append((title, a))
        print("   %-22s %8d  %s" % (a, n, verdict))
    print("")


words = []
for _, _, lab in labels:
    words.extend(w for w in re.split(r"[\s/+,;:()-]+", lab) if w)

# ⛔ CONTROLS BEFORE ANY COUNT. Both sides exercise `branch_row`, the same function the
# report uses -- a control that runs a reimplementation certifies the reimplementation.
#
# POSITIVE  established INDEPENDENTLY of this instrument: `colchicine placebo` is the literal
#           control-arm label of NCT02551094 in ssot/colchicine-cvd-review. The `placebo`
#           branch must find it.
# NEGATIVE  ⭐ THE EXACT OVER-FLAG THIS INSTRUMENT COMMITTED AN HOUR AGO. Its first version
#           probed substring branches with a whole-token anchor, so `sham` -- unexercised on
#           this corpus but perfectly functional -- was reported "DEAD AND BROKEN". It must
#           NOT come back 'dead'. Over-flagging was the failure mode, so this side is the
#           one that matters.
require_controls(
    "audit_pattern_branches",
    positive=("the placebo branch matches a real control-arm label %r" % KNOWN_LABEL,
              branch_row("placebo", [KNOWN_LABEL], PLACEBO_PROBE)[1], "live"),
    negative=("an unexercised-but-working branch is called dead",
              branch_row("sham", [KNOWN_LABEL], PLACEBO_PROBE)[1] == "dead", True))
print("")

audit("_SCHEDULE -- each alternative, matched as a WHOLE token", SCHEDULE_ALTS, words,
      probe=SCHEDULE_PROBE, whole=True)
audit("_PLACEBO -- each alternative, over whole arm labels", PLACEBO_ALTS,
      [l for _, _, l in labels], probe=PLACEBO_PROBE)
audit("_CONJ -- each alternative, over whole arm labels", CONJ_ALTS,
      [l for _, _, l in labels])

# ---------------------------------------------------------------- TRANSCRIPTION CHECK
# ⚠️ The alternatives above are TRANSCRIBED from the shipped patterns. A transcription that
# drifts from the real pattern would audit a pattern that is not the one running. Each
# probe is therefore also fired through the REAL compiled objects.
print("=== TRANSCRIPTION CHECK -- the audited alternatives are the SHIPPED ones ===")
bad = []
for a, p in SCHEDULE_PROBE.items():
    if not _SCHEDULE.match(p):
        bad.append(("_SCHEDULE", a, p))
for a in PLACEBO_ALTS:
    if not _PLACEBO.search("control %s arm" % a):
        bad.append(("_PLACEBO", a, a))
for a, p in ((r"\+", "drug A + drug B"), (r"\bplus\b", "drug A plus drug B"),
             (r"\band\b", "drug A and drug B")):
    if len(_CONJ.split(p)) < 2:
        bad.append(("_CONJ", a, p))
if bad:
    for w, a, p in bad:
        print("   ⛔ %s alternative %r does NOT fire through the shipped pattern on %r "
              "-- the audit above is of a pattern that is not the one running" % (w, a, p))
else:
    print("   every audited alternative fires through the SHIPPED compiled pattern.  OK")

print("")
if dead:
    print("⛔ BRANCHES THAT ARE ZERO AND UNPROVEN: %d" % len(dead))
    for w, a in dead:
        print("      %s  %s" % (w, a))
    sys.exit(1)
print("NO BRANCH IS BOTH ZERO AND UNPROVEN. Every alternative either fires on the corpus "
      "or fires on a probe that shows it works.")
