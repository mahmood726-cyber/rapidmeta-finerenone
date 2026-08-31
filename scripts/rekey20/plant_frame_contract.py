# -*- coding: utf-8 -*-
"""PLANT for frame_contract.py -- five synthetic frames, each carrying exactly one
defect the contract claims to refuse, plus one clean frame that must pass.

A checker that only ever refuses is not a checker. The clean case is what proves
this one can say yes; the five defects are what prove it can say no. BOTH
directions must hold or this file exits non-zero and the scan does not run.

The frames are SYNTHETIC -- built here, in memory, from nothing. They are not
slices of the real frame, so fixing the real frame cannot retire them.
"""
import io, json, os, sys, tempfile
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace",
                              line_buffering=True)
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from frame_contract import load_frame, FrameRefused

OK = {"cd_base": "CD000024", "current_pubN": 3, "title": "Anticoagulants for acute ischaemic stroke.",
      "objectives_verbatim": "To assess the effectiveness and safety of early anticoagulation.",
      "record_kind": "review", "specialty": "cardiology", "provenance": {"frame_built": "synthetic"}}
OK2 = dict(OK, cd_base="CD000029", title="Oral antiplatelet therapy for acute ischaemic stroke.")


def frame(rows):
    fd, p = tempfile.mkstemp(suffix=".jsonl", text=False)
    os.close(fd)
    with io.open(p, "w", encoding="utf-8") as f:
        for r in rows:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
    return p


CASES = [
    # (name, rows, must_refuse, phrase the refusal must contain)
    ("clean frame passes", [OK, OK2], False, None),
    ("TITLE-KEYED frame refused",
     [dict(OK, cd_base="Anticoagulants for acute ischaemic stroke")], True, "keyed\nby title".replace("\n", " ")),
    ("duplicate base refused", [OK, dict(OK2, cd_base="CD000024")], True, "duplicate cd_base"),
    ("empty-string objectives refused", [dict(OK, objectives_verbatim="")], True, "UNOBTAINABLE"),
    ("missing contract field refused",
     [{k: v for k, v in OK.items() if k != "record_kind"}], True, "missing contract field"),
    ("bad record_kind refused", [dict(OK, record_kind="paper")], True, "record_kind"),
]

fails = []
for name, rows, must_refuse, needle in CASES:
    p = frame(rows)
    try:
        load_frame(p)
        refused, msg = False, ""
    except FrameRefused as e:
        refused, msg = True, str(e)
    finally:
        os.unlink(p)

    if refused != must_refuse:
        fails.append("%s: expected refuse=%s got refuse=%s  %s" % (name, must_refuse, refused, msg[:120]))
        verdict = "FAIL"
    elif must_refuse and needle and needle.lower() not in msg.lower():
        fails.append("%s: refused, but the reason never says %r -- a refusal that does not "
                     "name its rule is not checkable. got: %s" % (name, needle, msg[:160]))
        verdict = "FAIL"
    elif must_refuse and not msg.startswith(tuple("/" + chr(92) + "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz")):
        fails.append("%s: refusal does not begin with the offending path" % name)
        verdict = "FAIL"
    else:
        verdict = "PASS"
    print("  %-34s %s" % (name, verdict))
    if must_refuse and verdict == "PASS":
        print("        -> %s" % msg.replace("\n", "\n           "))

# The must-not-refuse case exists to catch an instrument that can only say no.
print("")
if fails:
    for f in fails:
        print("PLANT FAILED: " + f)
    sys.exit(1)
print("PLANT: 6/6 -- the contract refuses all five planted defects AND passes the clean frame.")
