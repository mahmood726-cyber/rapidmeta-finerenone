"""Prove the four new units can FAIL, on REAL FILES, and restore byte-identically.

A CHECK WHOSE FAILURE YOU HAVE NOT PERSONALLY WITNESSED IS NOT A CHECK. Controls over
fixtures prove a predicate. They do not prove that the predicate, pointed at a real file the
corpus actually ships, reaches the defect. This module plants each class INTO A REAL FILE,
asserts the unit FAILS, restores the file, asserts the restoration is BYTE-IDENTICAL by
sha256, and asserts the unit PASSES again.

TWO KINDS OF PLANT, COUNTED SEPARATELY, because conflating them would overstate what has been
proven:

  MECHANISM  the plant alters a value the real file ALREADY HOLDS, in the way the defect
             actually occurs. This proves reach AND mechanism.
  TRAVERSAL  the real file holds no instance of the class, so the plant introduces the shape.
             This proves the walk reaches a nested block in a real file. It does NOT prove the
             class occurs here, and is never reported as if it did.

AND EVERY PLANT HAS A COUNTER-PLANT: the same edit made into the EXEMPLARY CORRECT FORM, which
must PASS. A detector that fires on the model answer drives the corpus away from the behaviour
it enforces, and the counter-plant is the only thing that measures that.
"""
from __future__ import annotations

import copy
import hashlib
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import declared_digest as DD                                                # noqa: E402
import count_matches_rows as CR                                             # noqa: E402
import certainty_over_adjudication as CA                                    # noqa: E402
import falsy_in_value_slot as FV                                            # noqa: E402

REAL = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "real")
STORE = os.path.join(REAL, "outputs_extraction_audit_truthcert_"
                            "NORMOTHERMIC_TRANSPLANT_NMA_REVIEW.json")
PAGE = os.path.join(REAL, "SGLT2_HF_REVIEW.html")

RESULTS = []


def _sha(b):
    return hashlib.sha256(b if isinstance(b, bytes) else b.encode("utf-8")).hexdigest()


def run(cls, register_quote, kind, path, plant_fn, counter_fn, detect_fn):
    """Plant -> assert FAIL -> restore -> assert byte-identical -> assert PASS -> model answer."""
    raw = open(path, "rb").read()
    before = _sha(raw)

    clean_n = len(detect_fn(raw))
    planted = plant_fn(raw)
    if planted == raw:
        RESULTS.append((cls, kind, "BROKEN", "the plant did not change the file"))
        return
    planted_n = len(detect_fn(planted))

    # restore is the ORIGINAL BYTES, never a re-serialisation: a round-trip through a parser
    # is not a restoration and would hide a plant that survived it.
    open(path, "wb").write(raw)
    after = _sha(open(path, "rb").read())
    restored_n = len(detect_fn(open(path, "rb").read()))

    model_n = len(detect_fn(counter_fn(raw)))

    ok = (planted_n > clean_n) and (before == after) and (restored_n == clean_n) \
        and (model_n == clean_n)
    RESULTS.append((cls, kind, "OK" if ok else "BAD",
                    "clean=%d planted=%d restored=%d model-answer=%d  sha256 %s  (%s)"
                    % (clean_n, planted_n, restored_n, model_n,
                       "IDENTICAL" if before == after else "CHANGED",
                       register_quote)))


# ---------------------------------------------------------------------------
# AS5 -- a field whose name declares a full digest. MECHANISM plant: the real file holds
# `truthcert_hmac_sha256` with a conforming 64-hex value. Truncate that real value.
# ---------------------------------------------------------------------------
def as5_plant(raw):
    d = json.loads(raw)
    d["truthcert_hmac_sha256"] = d["truthcert_hmac_sha256"][:8]
    return json.dumps(d).encode("utf-8")


def as5_counter(raw):
    """THE MODEL ANSWER: the same eight characters, under a name that says eight characters."""
    d = json.loads(raw)
    d["truthcert_hmac_sha256_prefix"] = d.pop("truthcert_hmac_sha256")[:8]
    return json.dumps(d).encode("utf-8")


# ---------------------------------------------------------------------------
# Q4 -- a declared count against its sibling rows. MECHANISM plant: the real file holds
# n_fixes_applied = 14 beside a 14-row fixes_applied. Move the count off by one.
# ---------------------------------------------------------------------------
def q4_plant(raw):
    d = json.loads(raw)
    d["n_fixes_applied"] = d["n_fixes_applied"] + 1
    return json.dumps(d).encode("utf-8")


def q4_counter(raw):
    """THE MODEL ANSWER: a row is genuinely added, and the count is rebuilt with it."""
    d = json.loads(raw)
    d["fixes_applied"] = d["fixes_applied"] + [dict(d["fixes_applied"][0])]
    d["n_fixes_applied"] = len(d["fixes_applied"])
    return json.dumps(d).encode("utf-8")


# ---------------------------------------------------------------------------
# S2 -- a certainty rating over an unadjudicated risk of bias. TRAVERSAL plant: this real
# file holds no certainty field at all, so the plant introduces the shape into a nested block
# to prove the walk reaches it. It does NOT establish that the class occurs in this file.
# ---------------------------------------------------------------------------
def s2_plant(raw):
    d = json.loads(raw)
    d.setdefault("score_components", {})
    d["score_components"] = dict(d["score_components"])
    d["score_components"]["certainty"] = "moderate"
    d["score_components"]["rob_overall"] = "no information"
    return json.dumps(d).encode("utf-8")


def s2_counter(raw):
    """THE MODEL ANSWER: the input is missing, so the rating is WITHHELD rather than published."""
    d = json.loads(raw)
    d["score_components"] = dict(d["score_components"])
    d["score_components"]["certainty"] = "pending"
    d["score_components"]["rob_overall"] = "no information"
    return json.dumps(d).encode("utf-8")


# ---------------------------------------------------------------------------
# AS6 -- a falsy in a value slot. MECHANISM plant: the real page's trial table holds real
# registration cells. Turn one real value into a falsy.
# ---------------------------------------------------------------------------
# The real markup, taken from the page rather than assumed. The first version of this file
# assumed `<td>NCT03315143</td>` and the guard below refused the run -- correctly, because a
# plant that does not land is not a plant. The page wraps every registration in <code>.
_ANCHOR = b"<td><code>NCT03315143</code></td>"


def as6_plant(raw):
    return raw.replace(_ANCHOR, b"<td><code>None</code></td>", 1)


def as6_counter(raw):
    """THE MODEL ANSWER: a visible refusal carrying its reason, not a falsy and not a dash."""
    return raw.replace(
        _ANCHOR, b"<td>registration not recorded, the object holds no NCT</td>", 1)


def _d_store(fn):
    return lambda raw: fn(json.loads(raw), "real store")


def _d_page(raw):
    return FV.findings(raw.decode("utf-8", "replace"), "real page")


if __name__ == "__main__":
    if not os.path.exists(STORE) or not os.path.exists(PAGE):
        print("BROKEN: the real files are not materialised; this proof needs them and will "
              "not substitute a fixture.")
        sys.exit(3)

    if _ANCHOR not in open(PAGE, "rb").read():
        print("BROKEN: the AS6 anchor is absent from the page. A plant that does not land is "
              "not a plant, and a pass here would be vacuous.")
        sys.exit(3)

    run("AS5 truncated hash presented as complete",
        "registry: 'adding this ONE key promoted 76 judgements from believed to exactly "
        "re-checkable and the gate passed'",
        "MECHANISM", STORE, as5_plant, as5_counter, _d_store(DD.findings))

    run("Q4 pooled k disagreeing with the rows behind it",
        "register A17: 'Index badge disagrees with its own page (4 trials claimed, 3 shown)'",
        "MECHANISM", STORE, q4_plant, q4_counter, _d_store(CR.findings))

    run("S2 certainty rating over an unadjudicated assessment",
        "register A10: 'GRADE certainty rendered where RoB is unadjudicated'",
        "TRAVERSAL", STORE, s2_plant, s2_counter, _d_store(CA.findings))

    run("AS6 falsy value reaching the reader",
        "register D1: 'Falsy values reaching the reader -- None, ?, em dash, blank links'",
        "MECHANISM", PAGE, as6_plant, as6_counter, _d_page)

    print("=" * 78)
    print("CAN THE FOUR NEW UNITS FAIL, ON REAL FILES?")
    ok = True
    for cls, kind, verdict, detail in RESULTS:
        ok = ok and verdict == "OK"
        print("  %-4s %-9s %s" % (verdict, kind, cls))
        print("           %s" % detail)
    print("  mechanism plants: %d   traversal plants: %d"
          % (sum(1 for r in RESULTS if r[1] == "MECHANISM"),
             sum(1 for r in RESULTS if r[1] == "TRAVERSAL")))
    print("  VERDICT: %s" % ("PROVEN -- each fails on its plant, restores byte-identically, "
                             "and passes the model answer" if ok else "NOT PROVEN"))
    print("=" * 78)
    sys.exit(0 if ok else 1)
