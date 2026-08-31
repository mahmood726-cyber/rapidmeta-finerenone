# -*- coding: utf-8 -*-
"""PLANT for the label-vs-reason gate. Both directions."""
import io, json, os, sys
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace", line_buffering=True)
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from gate_label_vs_reason import check

ROW = {("t", "CD000001"): "Endothelin receptor antagonists for pulmonary arterial hypertension. "
                          "To evaluate the efficacy of endothelin receptor antagonists (ERAs) in "
                          "pulmonary arterial hypertension."}

GOOD = {"app_id": "t", "cd_base": "CD000001", "label": "COUNTERPART",
        "reason": "names the class and the condition",
        "quotes_intervention": ["endothelin receptor antagonists (ERAs)"],
        "quotes_condition": ["pulmonary arterial hypertension"]}

CASES = [
    ("clean judgement passes", GOOD, 0),
    ("fabricated quote refused", dict(GOOD, quotes_condition=["chronic kidney disease"]), 1),
    ("COUNTERPART with one limb refused",
     {k: v for k, v in GOOD.items() if k != "quotes_condition"}, 1),
    ("NOT_COUNTERPART with no disqualifying quote refused",
     dict(GOOD, label="NOT_COUNTERPART", reason="it is not one",
          quotes_intervention=["endothelin receptor antagonists (ERAs)"],
          quotes_condition=["pulmonary arterial hypertension"]), 1),
    ("label contradicting its own reason refused",
     dict(GOOD, label="NOT_COUNTERPART",
          reason="the review evaluates exactly this class in exactly this condition",
          quotes_disqualifying=["endothelin receptor antagonists (ERAs)"]), 1),
    ("judgement about an unshown row refused",
     dict(GOOD, cd_base="CD999999"), 1),
    ("unknown label refused", dict(GOOD, label="PROBABLY"), 1),
]

fails = []
for name, j, expect in CASES:
    r = check([j], ROW, path="plant")
    got = 1 if r else 0
    ok = got == (1 if expect else 0)
    print("  %-52s %s" % (name, "PASS" if ok else "FAIL"))
    if ok and r:
        print("        -> %s" % r[0].replace("\n", "\n           "))
    if not ok:
        fails.append(name + ("  (refused when it should not: %s)" % r[0][:100] if r else "  (accepted when it should refuse)"))
print("")
if fails:
    for f in fails:
        print("PLANT FAILED: " + f)
    sys.exit(1)
print("PLANT: 7/7 -- the gate refuses six planted defects AND passes the clean judgement.")
