"""GATE 3 -- one authoritative reason for not pooling; a divergence between spellings refuses.

WHAT THIS REFUSES. Two spellings of "why was this outcome not pooled" holding two DIFFERENT
substantive answers. Whichever surface reads first wins, silently, and a reader receives one
of two incompatible explanations depending on which file rendered the page. That is not a
stylistic problem: the reason an estimate was withdrawn is the single thing this project
exists to not withhold.

WHAT IT DOES NOT REFUSE, AND WHY EACH EXCLUSION IS EARNED RATHER THAN ASSUMED. Kinds were
enumerated before the number was read, and the number moved by a factor of two when they were:

    identical         91  the same text under two names -- redundant, not contradictory
    cross-reference    6  "see poolable_reason" -- the corpus pointing AT the authority
    subset             9  one is a summary of the other ("k=1; there is nothing to combine")
    DIVERGENT         12  two substantive answers that are not the same answer

A first pass that scored any multi-name outcome as a divergence reported 118. The honest
figure is 12, and the difference is entirely kinds.

THE ANNOTATIONS ARE NOT ALIASES. `withdrawn_note` and `card_note` sit beside the reason and
say what the withdrawal does NOT establish. Counting them as competing spellings adds 26
false divergences. That exclusion is the single biggest source of precision here and it is
measured by the control below, not asserted.
"""
from __future__ import annotations

import collections
import copy
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _harness as H                                                        # noqa: E402
import reason as R                                                          # noqa: E402

# The known-negative control. Each MUST NOT be called DIVERGENT, and the answer to each is
# fixed by what the fields mean, not by what this gate does with them.
KNOWN_NEGATIVES = [
    ("identical text under two names",
     {"poolable_reason": "the trials measure different things",
      "pooled": {"withdrawn_reason": "the trials measure different things"}}),
    ("a bare cross-reference",
     {"poolable_reason": "THE THREE TRIALS REGISTER THREE DIFFERENT PRIMARY COMPOSITES.",
      "pooled": {"withdrawn_because": "see poolable_reason"}}),
    ("a cross-reference with a lead-in",
     {"poolable_reason": "THE THREE TRIALS DO NOT SHARE AN ENDPOINT. Decomposed into "
                         "components and compared as sets.",
      "pooled": {"withdrawn_reason": "no shared estimand -- see poolable_reason"}}),
    ("a summary that is a subset of the full reason",
     {"poolable_reason": "k=1; there is nothing to combine, and the single trial is named",
      "pooled": {"withdrawn_because": "k=1; there is nothing to combine"}}),
    ("a note beside the reason is not a competing reason",
     {"poolable_reason": "the trials measure different things",
      "pooled": {"withdrawn_note": "WHAT THIS DOES NOT ESTABLISH: not that the drug is "
                                   "ineffective.",
                 "card_note": "confirmed on re-verification"}}),
    ("one spelling only",
     {"poolable_reason": "a single effect measure across trials sharing no participant"}),
    ("no reason recorded at all -- absence, not divergence",
     {"pooled": {"withdrawn": False}}),
    ("whitespace and case differences are not divergence",
     {"poolable_reason": "The Trials Measure Different Things",
      "pooled": {"withdrawn_reason": "the  trials   measure different things"}}),
]

# And the positive control: this MUST be called DIVERGENT, or the gate cannot see its own class.
KNOWN_POSITIVE = ("two substantive answers that are not the same answer",
                  {"poolable_reason": "The extractor recovered a pooled result, so the page "
                                      "pooled these trials.",
                   "pooled": {"withdrawn_reason": "TWO OF THE THREE CONTRIBUTING TRIALS ARE "
                                                  "NOT MEASURED AGAINST A RANDOMISED "
                                                  "CONCURRENT CONTROL."}})


def scan(objects):
    rows, kinds = [], collections.Counter()
    for topic, obj in objects.items():
        res = (obj.get("results") or {}).get("by_outcome")
        if not isinstance(res, dict):
            kinds["object with no by_outcome mapping"] += 1
            continue
        for oid, outcome in res.items():
            if not isinstance(outcome, dict):
                continue
            kind, vals = R.divergence(outcome)
            found = R.spellings_present(outcome)
            if not found:
                kinds["outcome with NO reason under any spelling"] += 1
                continue
            if kind == "none":
                kinds["outcome with exactly one spelling"] += 1
                continue
            kinds["multi-spelling: " + kind] += 1
            if kind == "DIVERGENT":
                value, spelling = R.not_pooled_reason(outcome)
                rows.append({"topic": topic, "outcome": oid,
                             "authoritative_spelling": spelling,
                             "reader_receives": (value or "")[:200],
                             "discarded": {k: v[:200] for k, v in vals.items()
                                           if k != spelling}})
    return rows, kinds


def run_control(gate):
    fp, examples = 0, []
    for why, outcome in KNOWN_NEGATIVES:
        kind, _ = R.divergence(outcome)
        if kind == "DIVERGENT":
            fp += 1
            examples.append(why)
    gate.control(len(KNOWN_NEGATIVES), fp, examples)
    # the positive control is separate: a detector that cannot fire is not a detector
    why, outcome = KNOWN_POSITIVE
    kind, _ = R.divergence(outcome)
    if kind != "DIVERGENT":
        gate.broken("the POSITIVE control (%s) was classified %r, not DIVERGENT. This gate "
                    "cannot see the class it exists for." % (why, kind))
    else:
        gate.note("positive control fires: %s -> DIVERGENT" % why)


PINNED_BLOB = "c623a213fb46011c22fc01d3709dd5df1d112be0"


def _pinned_case(gate, repo, case):
    """Assert the gate still sees the real motivating case, in the bytes it was found in.

    Reads the blob, not the working file. A page NAME is not an artefact identity; a name plus
    an immutable object id is.
    """
    import subprocess
    try:
        raw = subprocess.run(["git", "cat-file", "-p", PINNED_BLOB], cwd=repo,
                             capture_output=True, check=True).stdout.decode("utf-8")
        outcome = json.loads(raw)["results"]["by_outcome"]["primary"]
    except Exception as exc:
        gate.broken("the pinned regression blob %s could not be read: %s. The gate cannot "
                    "show it still sees its motivating case." % (PINNED_BLOB[:8], exc))
        return
    kind, _ = R.divergence(outcome)
    if kind == "DIVERGENT":
        gate.saw(case)
    else:
        gate.broken("the pinned blob classified %r, not DIVERGENT. Either the classifier "
                    "changed or the pin is wrong; both are failures." % kind)


def main(argv):
    repo = H.repo_root()
    gate = H.Gate("3  ONE REASON FIELD",
                  "the reason an outcome was not pooled is stored under one authority; two "
                  "spellings holding different answers refuse the build")
    gate.requires_control()

    paths, kinds_pop = H.topic_objects(repo)
    objects = {}
    for p in paths:
        try:
            objects[H.topic_id(p)] = H.load(p)
        except Exception as exc:
            gate.broken("unparseable object %s: %s" % (p, exc))

    # THE NAMED POSITIVE IS PINNED TO AN IMMUTABLE BLOB, NOT TO THE LIVE CORPUS.
    #
    # It was anchored to live `attr-pn-review/primary` first, and running --repair exposed why
    # that is wrong: the moment the divergence is fixed the case stops existing, the gate goes
    # VACUOUS forever, and a control that retires itself at the moment of success is not a
    # control. The blob sha below is the object as it stood when the divergence was found by
    # hand on 2026-08-28; git cannot change it.
    case = gate.expect_case(
        "blob:c623a213 attr-pn-review/primary",
        "pinned: poolable_reason says the page pooled them; withdrawn_reason says two of "
        "three have no randomised concurrent control")
    _pinned_case(gate, repo, case)

    if "--plant" in argv:
        # plant a divergence on an object that is currently clean, to watch the gate fail
        t = "ablation-af-review"
        obj = copy.deepcopy(objects[t])
        obj["results"]["by_outcome"]["primary"]["pooled"]["withdrawn_reason"] = (
            "a completely different explanation that shares no text with the poolable_reason")
        objects[t] = obj
        gate.note("PLANTED: a contradictory withdrawn_reason on %s/primary (in memory)" % t)

    if "--repair" in argv:
        # collapse every divergence onto the authority, to prove the gate can reach PASS
        for t, obj in objects.items():
            res = (obj.get("results") or {}).get("by_outcome")
            if not isinstance(res, dict):
                continue
            for oid, outcome in res.items():
                if not isinstance(outcome, dict):
                    continue
                if R.divergence(outcome)[0] != "DIVERGENT":
                    continue
                value, spelling = R.not_pooled_reason(outcome)
                outcome = copy.deepcopy(outcome)
                for name in R.ALIASES:
                    if name != spelling:
                        outcome.pop(name, None)
                        if isinstance(outcome.get("pooled"), dict):
                            outcome["pooled"].pop(name, None)
                res[oid] = outcome
        gate.note("REPAIRED in memory: every divergence collapsed onto its authority")

    run_control(gate)
    rows, kinds = scan(objects)

    for r in rows:
        if r["topic"] + "/" + r["outcome"] == case:
            gate.saw(case)

    merged = dict(kinds_pop)
    merged.update(kinds)
    gate.kinds(merged)
    gate.note("authority: %s, then %s" % (R.AUTHORITATIVE, ", ".join(R.ALIASES[1:])))
    gate.note("annotations held BESIDE the reason, never instead of it: %s"
              % ", ".join(R.ANNOTATIONS))

    n_outcomes = sum(v for k, v in kinds.items() if k.startswith(("outcome", "multi-spelling")))
    keys = ["%s/%s" % (r["topic"], r["outcome"]) for r in rows]
    new = set(H.ratchet(gate, "GATE3_KNOWN_DIVERGENCES.json", keys,
                        "outcomes whose reason for not pooling is stored under two spellings "
                        "holding different substantive answers.",
                        escalated="out/ESCALATIONS.jsonl 2026-08-28T16:35Z"))
    if os.path.exists(os.path.join(repo, "gates", "GATE3_KNOWN_DIVERGENCES.json")):
        rows = [r for r in rows if "%s/%s" % (r["topic"], r["outcome"]) in new]
    for r in rows:
        gate.finding("REASON-DIVERGENCE",
                     "%s/%s: a reader receives the %s (%r) and the corpus also holds %s. Two "
                     "substantive answers to one question; whichever surface reads first wins."
                     % (r["topic"], r["outcome"], r["authoritative_spelling"],
                        r["reader_receives"][:110],
                        " and ".join("%s (%r)" % (k, v[:80])
                                     for k, v in r["discarded"].items())),
                     numerator=len(rows), denominator=n_outcomes)

    art = os.path.join(repo, "out", "gate3_one_reason_field.json")
    os.makedirs(os.path.dirname(art), exist_ok=True)
    with open(art, "w", encoding="utf-8") as fh:
        json.dump({"gate": gate.as_json(), "divergences": rows}, fh, indent=1)

    # COVERAGE. An outcome with NO reason under any spelling cannot be compared against a
    # second spelling: it is silent, not consistent.
    _noreason = kinds.get("outcome with NO reason under any spelling", 0)
    _outcomes = sum(v for k, v in kinds.items()
                    if k.startswith("multi-spelling") or k.startswith("outcome"))
    gate.coverage(max(_outcomes - _noreason, 0), max(_outcomes, 1),
                  "outcomes carrying no reason under any spelling, where there is nothing "
                  "for a second spelling to contradict")
    return gate.report(denominator="%d outcomes across %d topic objects"
                                   % (n_outcomes, len(objects)))


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
