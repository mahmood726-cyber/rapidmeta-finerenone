# -*- coding: utf-8 -*-
"""THE TWO-AXIS RUN OVER THE TWENTY. A named state per topic, never a silent drop.

The plants gate the counts: if `plant_axis_match.py` does not exit 0, NO NUMBER IS PRINTED.
A gate that can only delay is not a gate.

Reported per topic, always, in this order:
    state · why · axis_I (n + set sha) · axis_C (n + set sha) · both · verified · judged
and the per-term liveness of BOTH axes, so a match carried by one bare fragment is visible
rather than inferred.

⛔ candidates -> verified -> judged is reported as three separate numbers and never padded
to a target. A topic with no counterpart is a result.
"""
import io, json, os, subprocess, sys
from collections import Counter

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.chdir(os.path.dirname(os.path.abspath(__file__)))
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace",
                              line_buffering=True)
from axis_match import prepare, score, ref, terms_for                 # noqa: E402
from axis_states import ALL_STATES, MATCHED, REFUSED_NO_TERMS         # noqa: E402

FRAME = "F:/claude-temp/pend/cdsr_frame_cardiology.jsonl"
CORR = "../../evidence/2026-08-31-rekey/corrected"
TWENTY = CORR + "/twenty.json"
JUDGE = CORR + "/judgements.json"
OUT = "../../evidence/2026-08-31-axis/axis_states_twenty.json"

# ---------------------------------------------------------------- CONTROLS FIRST
print("=== CONTROLS RUN FIRST AND GATE THE COUNTS ===")
# ⛔ NOT `text=True`. The plants print ⛔/⭐/⚠️ and text=True decodes with the DEFAULT
# CODEPAGE -- cp1252 here -- so the gate's own output would be mojibake or would raise, and
# a controls-gate that cannot report its result is not a gate. Refused by
# scripts/lint_subprocess_decode.py, correctly, on this exact line.
p = subprocess.run([sys.executable, "plant_axis_match.py"], capture_output=True)
stdout = p.stdout.decode("utf-8", "replace")
tail = [l for l in stdout.splitlines() if l.startswith("PLANTS:")]
print("   plant_axis_match.py exit=%d   %s" % (p.returncode, tail[0] if tail else "(no summary)"))
if p.returncode != 0:
    print(stdout[-3000:])
    print("\nCONTROLS FAILED -- NO COUNT PRINTED.")
    sys.exit(1)

R = ref(FRAME, TWENTY)
print("")
print("=== REF -- every number below is addressed to this and only this ===")
for k in ("matcher", "rule_fingerprint", "frame_path", "frame_bytes", "frame_rows",
          "frame_kinds", "frame_base_set_sha256", "twenty_path", "twenty_n",
          "twenty_app_id_set_sha256"):
    v = R[k]
    print("   REF.%-24s %s" % (k, (v[:16] if isinstance(v, str) and len(v) == 64 else v)))

rows, reviews = prepare(FRAME)
print("   REF.%-24s %d   (protocols cannot be a counterpart and are not scanned)"
      % ("reviews_scanned", len(reviews)))

twenty = json.load(io.open(TWENTY, encoding="utf-8"))["topics"]
judged = json.load(io.open(JUDGE, encoding="utf-8"))
JMAP = {(j["app_id"], j["cd_base"]): j["label"] for j in judged}

# ---------------------------------------------------------------- THE RUN
out = []
for t in sorted(twenty, key=lambda x: x["app_id"]):
    dt, ct, cfail = terms_for(t.get("drug") or {})
    iterms = sorted(set(dt) | set(ct))
    cterms = t.get("condition_terms") or []
    s = score(reviews, iterms, cterms)
    s["app_id"] = t["app_id"]
    s["title"] = t["title"]
    s["rule_outcome"] = (t["fail"][0] if t.get("fail") else "REKEYED")
    s["class_refusal"] = cfail
    s["drug_terms"], s["class_terms"] = dt, ct
    s["judged"] = ([{"cd_base": b, "label": JMAP.get((t["app_id"], b), "UNJUDGED")}
                    for b in (s["verified"]["bases"] if s["verified"] else [])])
    s["n_judged_counterpart"] = sum(1 for j in s["judged"] if j["label"] == "COUNTERPART")
    out.append(s)

print("")
print("=== THE TWENTY -- a NAMED STATE for every one. No topic is dropped. ===")
print("   %-46s %-22s %6s %6s %5s %5s %5s" %
      ("app_id", "state", "axisI", "axisC", "both", "ver", "cpart"))
for s in out:
    print("   %-46s %-22s %6s %6s %5s %5s %5s" %
          (s["app_id"], s["state"],
           "-" if s["axis_intervention"] is None else s["axis_intervention"]["n"],
           "-" if s["axis_condition"] is None else s["axis_condition"]["n"],
           "-" if s["both"] is None else s["both"]["n"],
           "-" if s["verified"] is None else s["verified"]["n"],
           s["n_judged_counterpart"]))

print("")
print("=== STATE TALLY -- the parts sum to the population ===")
c = Counter(s["state"] for s in out)
for st in ALL_STATES:
    print("   %-24s %2d" % (st, c.get(st, 0)))
print("   %-24s %2d   sums to the twenty: %s"
      % ("TOTAL", sum(c.values()), "HOLDS" if sum(c.values()) == len(twenty) else "BROKEN"))

# ---------------------------------------------------------------- THE VACUOUS SET
print("")
print("=== THE VACUOUS SET -- zeros that were never measurements ===")
vac_c = [s["app_id"] for s in out if "condition" in s["vacuous_axes"]]
vac_i = [s["app_id"] for s in out if "intervention" in s["vacuous_axes"]]
noclass = [s["app_id"] for s in out if not s["class_terms"]]
print("   topics with an EMPTY condition term list : %d   %s" % (len(vac_c), ", ".join(vac_c)))
print("   topics with an EMPTY intervention list   : %d   %s" % (len(vac_i), ", ".join(vac_i)))
print("   topics where the rule REFUSED a class    : %d   %s"
      % (len(noclass), ", ".join("%s(%s)" % (s["app_id"], s["class_refusal"])
                                 for s in out if not s["class_terms"])))
print("   ⇒ the old scan printed `B 0/0` for each of those %d and it was NOT a class that" % len(noclass))
print("     was searched and missed -- the class was never searched at all.")

# ---------------------------------------------------------------- THE FUNNEL
print("")
print("=== candidates -> verified -> judged. Three numbers, never padded. ===")
cand = sum(s["both"]["n"] for s in out if s["both"])
ver = sum(s["verified"]["n"] for s in out if s["verified"])
cp = sum(s["n_judged_counterpart"] for s in out)
unj = sum(1 for s in out for j in s["judged"] if j["label"] == "UNJUDGED")
print("   candidate pairs (both axes, title+objectives) : %d" % cand)
print("   verified pairs  (both axes, objectives ALONE) : %d" % ver)
print("   judged COUNTERPART                            : %d" % cp)
print("   verified but UNJUDGED (never counted either way): %d" % unj)
print("")
print("   topics MATCHED                    : %2d / 20" % c.get(MATCHED, 0))
print("   topics with >=1 judged COUNTERPART: %2d / 20" % sum(1 for s in out if s["n_judged_counterpart"]))
bases = sorted({j["cd_base"] for s in out for j in s["judged"] if j["label"] == "COUNTERPART"})
print("   INDEPENDENT reviews behind them   : %2d      %s" % (len(bases), ", ".join(bases)))
print("   ⚠️ topics is not the portable number: three bosentan topics are one question")
print("     under three names, and they share a single review.")

# --------------------------------------------------- WHICH AXIS KILLED EACH FAILURE
print("")
print("=== WHICH AXIS KILLED IT -- the question the old `0/0` could not answer ===")
for s in out:
    if s["state"] in (MATCHED,):
        continue
    print("   %-46s %s" % (s["app_id"], s["state"]))
    print("        %s" % s["reason"])
    if s["axis_intervention"] is not None:
        liv_i = ", ".join("%s=%d" % (k, v) for k, v in sorted(s["axis_intervention"]["liveness"].items()))
        liv_c = ", ".join("%s=%d" % (k, v) for k, v in sorted(s["axis_condition"]["liveness"].items()))
        print("        term liveness  I: %s" % liv_i)
        print("        term liveness  C: %s" % liv_c)

json.dump({"ref": R, "topics": out}, io.open(OUT, "w", encoding="utf-8"),
          ensure_ascii=False, indent=1)
print("")
print("   written: %s" % OUT)
