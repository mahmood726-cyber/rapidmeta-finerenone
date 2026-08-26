"""Stage 1 of the batch: derive, per topic, the facts a protocol must be written against.

WHY THIS EXISTS RATHER THAN A GENERIC PROMPT LOOP. Two topics tonight could not be
protocolised as written, and neither defect is visible without reading the object:

  sotagliflozin-hf   "In both phase 3 trials that supported approval..."  -- the question
                     defines eligibility as membership in its own answer, so a search
                     against it tests nothing.
  finerenone-review  question says three trials; the object holds four.

A loop that drafted 138 protocols without these checks would register 138 questions,
some of which cannot be searched, and the defect would be inside an anchored artefact.

So this stage GATES rather than generates. Every topic gets a verdict:
  READY    -- facts extracted, safe to draft
  BLOCKED  -- a named defect a protocol would inherit; NOT drafted, reported instead

BLOCKED IS A RESULT, NOT A SKIP. It is reported in its own count with its reason.
"""
import io, json, os, re, sys
from itertools import combinations

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
S = r"F:\claude-temp\claude\C--Users-mahmo\f842b4e4-f3de-4ce2-83d8-0adf7aa7cfb1\scratchpad"
SSOT = os.path.join(S, "main-wt", "ssot")

# The question must not define eligibility as membership in its own answer.
SELF_NAMING = re.compile(
    r"\b(both|the\s+(two|three|four|five|six|\d+))\b[\w\s,'\-]{0,60}?\btrials?\b"
    r"|trials that supported|could be sourced here|\bin this review\b", re.I)
WORDS = {"two": 2, "three": 3, "four": 4, "five": 5, "six": 6}
COMPARATOR = re.compile(r"\b(versus|vs\.?|compared with|compared to|against|placebo|"
                        r"standard of care|usual care|control|comparator)\b", re.I)
# STEMS MUST NOT CARRY A TRAILING WORD BOUNDARY. The first version was
#   \b(...|mortalit|hospitalis|...)\b
# where the closing \b applies to EVERY alternative, so `mortalit` could never match
# "mortality" and `hospitalis` never matched "hospitalisation". It reported 109 topics
# as stating no outcome, many of which state one plainly. A regex that looks right and
# cannot match is the defect this corpus keeps finding; here it was mine, and it was
# one hand-check away from being reported as a property of the corpus.
OUTCOME = re.compile(r"\b(?:hazard|risk|odds|rate|incidence|mortalit\w*|death\w*|"
                     r"hospitali\w*|cure\w*|failure|response|remission|relaps\w*|"
                     r"progression|clearance|surviv\w*|recurren\w*|event\w*|"
                     r"endpoint\w*|proportion|infection\w*|exacerbation\w*)\b", re.I)

# TESTING FOR THE PRESENCE OF AN OUTCOME WAS THE WRONG SHAPE, AND THE SECOND VERSION
# OF THIS FILE STILL HAD IT. Outcomes are an UNBOUNDED set -- LDL cholesterol,
# intraocular pressure, HIV-1 seroconversion, six-minute walking distance, time to
# recovery, PCR-corrected treatment failure. Any keyword list is a sample of that set
# and every question naming an outcome outside the sample is falsely blocked. Reading
# all 25 residual flags found 16 that state an outcome plainly.
#
# The BOUNDED set is the ways of failing to state one. So the test is inverted: a
# question is blocked when it MATCHES a no-estimand pattern, not when it fails to
# match an outcome vocabulary. A closed enumeration of failure modes can be complete;
# an open enumeration of outcomes cannot.
DEFERRED_OUTCOME = re.compile(
    r"(each|the)\s+trial'?s?\s+own\s+registered\s+primary"
    r"|its\s+own\s+registered\s+primary"
    r"|the\s+outcome\s+each\s+trial\s+register"
    r"|the\s+\w+\s+each\s+trial\s+registered\s+as\s+its\s+primary", re.I)

NO_ESTIMAND = re.compile(
    r"what\s+do\s+the\s+contributing\s+trials\s+show"
    r"|what\s+did\s+(these|the)\s+[\w\s\-]{0,40}?trials\s+(actually\s+)?measure"
    r"|is\s+a\s+pooled\s+estimate\s+possible"
    r"|multiple\s+trial-declared\s+outcomes", re.I)

# A topic whose own question says the topic cannot ask it. Registering that would
# register a contradiction.
SELF_NEGATING = re.compile(r"CANNOT ASK THAT QUESTION|no trial on this page tests", re.I)
DOUBLED = re.compile(r"\b(versus|vs\.?|compared with)\b[^.?]{0,120}?"
                     r"\b(versus|vs\.?|compared with)\b", re.I)


def topology(trials):
    """Nodes, edges and independent loops from the object's own arms."""
    nodes, edges = set(), set()
    for t in trials:
        arms = [a.get("label") for a in (t.get("arms") or []) if isinstance(a, dict)]
        arms = [a for a in arms if a]
        nodes.update(arms)
        for a, b in combinations(sorted(arms), 2):
            edges.add(tuple(sorted((a, b))))
    if not nodes:
        return None
    adj = {n: set() for n in nodes}
    for a, b in edges:
        adj[a].add(b); adj[b].add(a)
    seen, stack = set(), [next(iter(nodes))]
    while stack:
        n = stack.pop()
        if n in seen:
            continue
        seen.add(n); stack.extend(adj[n] - seen)
    V, E = len(nodes), len(edges)
    return {"nodes": sorted(nodes), "n_nodes": V, "n_edges": E,
            "edges": sorted(edges), "connected": len(seen) == V,
            "independent_loops": E - V + 1 if V else 0,
            "is_network": V > 2,
            "consistency_testable": (E - V + 1) > 0 if V else False}


def prepare(topic):
    p = os.path.join(SSOT, topic, topic + ".json")
    obj = json.load(open(p, encoding="utf-8"))
    q = (obj.get("question") or "").strip()
    trials = ((obj.get("inputs") or {}).get("trials") or [])
    ncts = sorted({n for t in trials for n in re.findall(r"NCT\d{8}", json.dumps(t))})
    blocked = []

    m = SELF_NAMING.search(q)
    if m:
        blocked.append("QUESTION NAMES OR LIMITS ITS OWN INCLUDED SET: " + repr(m.group(0))
                       + " -- a search against it tests nothing until the question is "
                         "reframed, which is a scientific decision and not a rewording.")
    cm = re.search(r"\b(two|three|four|five|six|\d+)\s+trials\b", q, re.I)
    if cm:
        stated = WORDS.get(cm.group(1).lower())
        if stated is None:
            try:
                stated = int(cm.group(1))
            except ValueError:
                stated = None
        if stated is not None and stated != len(trials):
            blocked.append("QUESTION CONTRADICTS THE OBJECT: says " + str(stated)
                           + " trials, object holds " + str(len(trials)))
    if not q:
        blocked.append("NO QUESTION ON THE OBJECT")
    elif len(q) < 40:
        blocked.append("QUESTION TOO SHORT TO PROTOCOLISE: " + repr(q))
    if q and DOUBLED.search(q):
        blocked.append("QUESTION IS GRAMMATICALLY BROKEN (doubled comparator clause)")
    if q and not COMPARATOR.search(q):
        blocked.append("QUESTION STATES NO COMPARATOR")
    if q and SELF_NEGATING.search(q):
        blocked.append("QUESTION NEGATES ITSELF: the object states that this topic cannot "
                       "ask its own question")
    elif q and NO_ESTIMAND.search(q):
        blocked.append("NO ESTIMAND: the question asks what the trials show or measure "
                       "rather than naming a quantity, so section 2 of a protocol would "
                       "register nothing")
    elif q and DEFERRED_OUTCOME.search(q):
        blocked.append("OUTCOME DEFERRED TO THE TRIALS: the estimand is defined as whatever "
                       "each included trial registered, so no estimand can be pre-specified")
    elif q and q.rstrip().endswith(".") and "?" not in q:
        blocked.append("NOT A QUESTION: the field holds a statement, so there is nothing to "
                       "frame a protocol around")
    if len(trials) < 1:
        blocked.append("OBJECT HOLDS NO TRIALS")

    topo = topology(trials)
    return {"topic": topic, "question": q, "n_trials": len(trials), "ncts": ncts,
            "title": (obj.get("title") or "").strip(),
            "build_mode": obj.get("build_mode"),
            "topology": topo, "status": "BLOCKED" if blocked else "READY",
            "blockers": blocked}


if __name__ == "__main__":
    pop = json.load(open(os.path.join(S, "batch138_population.json"), encoding="utf-8"))
    todo = pop["todo"]
    out = [prepare(t) for t in todo]
    ready = [r for r in out if r["status"] == "READY"]
    blocked = [r for r in out if r["status"] == "BLOCKED"]
    nets = [r for r in ready if r["topology"] and r["topology"]["is_network"]]
    star = [r for r in nets if not r["topology"]["consistency_testable"]]
    print("STAGE 1 -- GATE, not generate")
    print("  topics needing a search record : " + str(len(out)))
    print("  READY to draft                 : " + str(len(ready)))
    print("  BLOCKED, not drafted           : " + str(len(blocked)))
    print()
    reasons = {}
    for r in blocked:
        for b in r["blockers"]:
            k = b.split(":")[0]
            reasons[k] = reasons.get(k, 0) + 1
    print("  BLOCKERS BY KIND (a topic may have more than one):")
    for k, v in sorted(reasons.items(), key=lambda x: -x[1]):
        print("    " + str(v).rjust(4) + "  " + k)
    print()
    print("  among READY: " + str(len(nets)) + " are NETWORKS (>2 nodes), of which "
          + str(len(star)) + " have ZERO independent loops")
    print("               so consistency is untestable by geometry, not by omission")
    json.dump(out, open(os.path.join(S, "batch138_prepared.json"), "w", encoding="utf-8"),
              indent=1)
    print("\nwrote batch138_prepared.json")

    # ------------------------------------------------------------------------------
    # EXIT CONTRACT. This file is named *_gate.py and a gate that cannot fail is not a
    # gate -- the pre-commit hook refused the first version for exactly that, and was
    # right. Named topics are the gated set:
    #
    #   python scripts/registration_batch_gate.py finerenone-cv colchicine-pericarditis
    #     exit 0  every named topic is READY to draft
    #     exit 1  at least one named topic is BLOCKED -- do not draft it
    #     exit 2  none of the named topics exists -- a NON-VERDICT, not a pass
    #
    # With no arguments it surveys and exits 0, because a survey has nothing to refuse.
    # ------------------------------------------------------------------------------
    named = [a for a in sys.argv[1:] if not a.startswith("-")]
    if not named:
        raise SystemExit(0)
    index = {r["topic"]: r for r in out}
    found = [t for t in named if t in index]
    if not found:
        print("\nNONE of the named topics is in the population -- non-verdict, not a pass.")
        raise SystemExit(2)
    print("\nGATED SET (" + str(len(found)) + " of " + str(len(named)) + " named found):")
    bad = 0
    for t in found:
        r = index[t]
        print("  " + r["status"].ljust(8) + t)
        for b in r["blockers"]:
            print("           " + b)
        bad += r["status"] == "BLOCKED"
    if bad:
        print("\nREFUSED: " + str(bad) + " named topic(s) BLOCKED. A protocol drafted "
              "against a blocked question registers the defect inside an anchored artefact.")
        raise SystemExit(1)
    print("\nall named topics READY")
    raise SystemExit(0)
