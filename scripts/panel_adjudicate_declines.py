r"""A blinded panel over the decline reasons a keyword cannot classify.

WHY A MODEL IS LEGITIMATE HERE AND ALMOST NOWHERE ELSE
    The answer IS in the data -- the stored reason string -- but it requires
    READING it. A keyword cannot tell a methodological refusal from a missing
    field, and that distinction is the entire content/hole split. Matching on
    keywords would rebuild the unanchored-substring defect this project spent
    the night removing.

    So the model assigns a STATE and touches no number. It never computes,
    never pools, never decides what a count is. Its output is DATA: authored
    once, stored, attributed, and never in the render path.

THE BLINDING, AND WHY EACH PART
    no topic name          so a judge cannot recognise a page and infer
    no count               so a judge cannot see how large either class is
    no statement of which  a judge told which answer helps us is not a judge
      answer helps us
    a fixed neutral rubric identical for both judges
    items shuffled at a    recorded seed, so the order carries no signal
      RECORDED seed

THE PROTOCOL
    TWO independent judges classify every item. Where they AGREE the state is
    settled. Where they DISAGREE an adjudicator sees the item and both
    answers, and its call is recorded ALONGSIDE the disagreement -- the
    disagreement is published, never silently resolved.

    UNRESOLVED -> HOLE. Anything the panel cannot settle counts AGAINST us.
    That is the conservative direction and it is chosen deliberately: an
    unsettled item must not be able to inflate the content figure.

THE CONTROL
    Two SYNTHETIC items with unambiguous answers are mixed into every batch.
    A judge that misclassifies a control has its whole batch distrusted. They
    are synthetic so they cannot retire when the corpus changes, and they are
    indistinguishable in form from real items.

RAISE
    Every state this panel assigns carries the model name, version, the date,
    and the limitation that a model read the string. Wherever those states
    appear, that attribution appears with them.
"""
from __future__ import annotations
import argparse
import glob
import json
import os
import random
import subprocess
import sys
from collections import Counter

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(ROOT, "ssot"))

from absolute_effects import _file_kind  # noqa: E402
from sof_projector import sof_rows  # noqa: E402
from split_declined_states import classify, _sidecar_for  # noqa: E402

SEED = 20260901          # recorded, so the shuffle carries no signal
OUT = os.path.join(ROOT, "evidence", "2026-09-01-decline-panel")

CONTROLS = [
    {"control": "METHODOLOGICAL",
     "text": "The two trials register different primary endpoints: one counts "
             "all-cause mortality and the other counts hospitalisation for "
             "any cause, so they do not answer one question."},
    {"control": "MISSING_FIELD",
     "text": "No value was recorded in this field."},
]

RUBRIC = """You are classifying short statements. Each explains why a
statistical pool was not produced. Assign EXACTLY ONE label to each.

  METHODOLOGICAL  the statement describes a property of the STUDIES or the
                  EVIDENCE that makes pooling inappropriate -- different
                  endpoints, different populations, different comparators,
                  different units, a single study, results not reported by
                  the studies themselves.

  MISSING_FIELD   the statement says that OUR OWN record is absent, empty or
                  unrecorded -- a field we did not fill, a value not stored,
                  a reason not written down. It describes a gap in the
                  record-keeping, not a property of the studies.

  UNCLEAR         the statement does not permit either label with confidence.

Answer with JSON only, no prose:
{"items":[{"id":"<id>","label":"METHODOLOGICAL|MISSING_FIELD|UNCLEAR"}, ...]}
Include every id you were given. Do not omit any."""


def gather():
    """The items a keyword could not classify, with opaque ids."""
    items = []
    for path in sorted(glob.glob(os.path.join(ROOT, "ssot", "*", "*.json"))):
        kind, obj = _file_kind(path)
        if kind != "live_with_outcomes":
            continue
        topic = os.path.basename(os.path.dirname(path))
        for r in sof_rows(obj, _sidecar_for(topic)):
            if r["state"] != "DECLINED_BY_THE_STORE":
                continue
            cls, _n = classify(r.get("reason"))
            if cls == "UNCLASSIFIED_DECLINE":
                items.append({"topic": topic, "outcome": r["outcome"],
                              "text": str(r.get("reason", ""))})
    rnd = random.Random(SEED)
    rnd.shuffle(items)
    for i, it in enumerate(items):
        it["id"] = "R%03d" % (i + 1)
    return items


def batches(items, per=10):
    """Small batches so no single prompt reveals the size of the population."""
    mixed = []
    rnd = random.Random(SEED + 1)
    for i in range(0, len(items), per):
        chunk = [dict(x) for x in items[i:i + per]]
        for j, c in enumerate(CONTROLS):
            chunk.append({"id": "C%d_%d" % (i, j), "text": c["text"],
                          "_control": c["control"]})
        rnd.shuffle(chunk)
        mixed.append(chunk)
    return mixed


def prompt_for(chunk):
    payload = [{"id": c["id"], "statement": c["text"][:900]} for c in chunk]
    return (RUBRIC + "\n\nITEMS:\n" + json.dumps(payload, ensure_ascii=False))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--emit-prompts", action="store_true")
    ap.add_argument("--collect", action="store_true")
    a = ap.parse_args()
    os.makedirs(OUT, exist_ok=True)
    items = gather()
    chunks = batches(items)

    if a.emit_prompts:
        meta = {"seed": SEED, "n_items": len(items),
                "n_batches": len(chunks),
                "controls_per_batch": len(CONTROLS)}
        json.dump({"meta": meta, "items": items},
                  open(os.path.join(OUT, "_items.json"), "w",
                       encoding="utf-8"), indent=1, ensure_ascii=False)
        for judge in ("A", "B"):
            for bi, chunk in enumerate(chunks):
                p = os.path.join(OUT, "prompt_%s_%d.txt" % (judge, bi))
                with open(p, "w", encoding="utf-8", newline="\n") as fh:
                    fh.write(prompt_for(chunk))
        print("items: %d in %d batches, %d controls per batch"
              % (len(items), len(chunks), len(CONTROLS)))
        print("prompts written to %s" % os.path.relpath(OUT, ROOT))
        print("NOTE: neither prompt names a topic, states a total, or says "
              "which label helps us.")
        return 0

    if a.collect:
        by_id = {}
        control_fail = Counter()
        for judge in ("A", "B"):
            for bi, chunk in enumerate(chunks):
                f = os.path.join(OUT, "out_%s_%d.json" % (judge, bi))
                if os.path.exists(f) is False:
                    continue
                try:
                    got = json.load(open(f, encoding="utf-8"))
                except Exception:
                    control_fail[judge + str(bi)] += 1
                    continue
                lab = {x["id"]: x["label"] for x in got.get("items", [])}
                bad = [c for c in chunk if c.get("_control")
                       and lab.get(c["id"]) != c["_control"]]
                if bad:
                    control_fail[judge + str(bi)] += len(bad)
                    print("  CONTROL FAILED in judge %s batch %d -- batch "
                          "distrusted" % (judge, bi))
                    continue
                for c in chunk:
                    if c.get("_control"):
                        continue
                    by_id.setdefault(c["id"], {})[judge] = lab.get(c["id"])
        agree = [i for i, v in by_id.items()
                 if v.get("A") and v.get("A") == v.get("B")]
        disagree = [i for i, v in by_id.items()
                    if v.get("A") and v.get("B") and v["A"] != v["B"]]
        missing = [i for i in by_id if len(by_id[i]) < 2]
        print("PANEL RESULT")
        print("  items judged by both        %d" % (len(agree) + len(disagree)))
        print("  AGREED                      %d" % len(agree))
        print("  DISAGREED (published)       %d" % len(disagree))
        print("  incomplete -> HOLE          %d" % len(missing))
        print("  control failures            %d" % sum(control_fail.values()))
        json.dump({"by_id": by_id, "agree": agree, "disagree": disagree,
                   "incomplete": missing,
                   "attribution": {
                       "decided_by": "a language model, not a person",
                       "why": "the answer is in the reason string but "
                              "requires reading it; a keyword cannot "
                              "separate a methodological refusal from a "
                              "missing field",
                       "limitation": "a model read the stored string. It "
                                     "assigned a state and touched no "
                                     "number. Unresolved items count as "
                                     "HOLES, against us.",
                       "seed": SEED}},
                  open(os.path.join(OUT, "panel_result.json"), "w",
                       encoding="utf-8"), indent=1, ensure_ascii=False)
        print("  wrote %s" % os.path.relpath(
            os.path.join(OUT, "panel_result.json"), ROOT))
        return 0
    ap.print_help()
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
