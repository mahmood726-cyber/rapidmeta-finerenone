"""The no-regression guard: data may improve, never silently regress.

WHY THIS EXISTS, and it is not hypothetical. On 2026-08-12 a newly registered,
methodologically stricter search was run for the ARNI review. Its screener dropped
PARACHUTE-HF -- a trial whose per-arm counts we already held, read at source and
doubly confirmed. Only a named human adjudication put it back. A better process
reduced the evidence base, and nothing in the system would have noticed.

The invariant: every verified cell, every included trial, and every recovered
artifact, once established with a source and a tier, is CARRIED FORWARD across
every rebuild, re-search and re-screen. A new process may add, may re-tier, may
correct with evidence. It may not silently drop.

THE HIGH-WATER MARK IS THE COMPARATOR, NOT THE PREVIOUS BUILD. Comparing against
the previous build would let a defect be laundered: build N loses a trial, build
N+1 compares against N, sees no change, and the loss becomes the new normal. The
ledger keeps the maximum ever verified, per key, so a loss stays visible until it
is either restored or explicitly justified.

A removal is legitimate only with a NAMED VIOLATION: the criterion failed, the
evidence, and who adjudicated it. Quarantine, never delete -- the row and its
history stay visible.
"""
import io, json, os, sys, glob, datetime

LEDGER = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                      "evidence", "LEDGER.json")


# ---------------------------------------------------------------- state


def state_of(obj):
    """The verifiable state of one canonical object, as a set of keys.

    Keys are deliberately granular: losing one arm's event count is a regression
    even if the trial survives, and losing a citation is a regression even if
    every trial survives.
    """
    app = obj.get("app_id", "?")
    cells, trials, cites, ptrs = set(), set(), set(), set()
    for t in obj.get("inputs", {}).get("trials", []):
        tid = t.get("id") or t.get("name")
        trials.add("%s::trial::%s" % (app, tid))
        for oid, b in (t.get("by_outcome") or {}).items():
            for role in ("treatment", "control"):
                c = b.get(role)
                if isinstance(c, dict) and c.get("events") is not None:
                    cells.add("%s::cell::%s::%s::%s::events" % (app, tid, oid, role))
                if isinstance(c, dict) and c.get("n") is not None:
                    cells.add("%s::cell::%s::%s::%s::n" % (app, tid, oid, role))
            if (b.get("effect") or {}).get("point") is not None:
                cells.add("%s::cell::%s::%s::effect" % (app, tid, oid))
        for r in ((t.get("component_endpoints") or {}).get("rows") or []):
            cells.add("%s::component::%s::%s" % (app, tid, r.get("endpoint")))
        if t.get("risk_of_bias"):
            cells.add("%s::rob_features::%s" % (app, tid))
    for pmid in (obj.get("citations") or {}):
        cites.add("%s::citation::%s" % (app, pmid))
    for r in ((obj.get("screening") or {}).get("records") or []):
        ptrs.add("%s::screened::%s" % (app, r.get("trial")))
    ks = {}
    for oid, r in obj.get("results", {}).get("by_outcome", {}).items():
        if r.get("k") is not None:
            ks["%s::k::%s" % (app, oid)] = r["k"]
    return {"app": app, "cells": cells, "trials": trials, "citations": cites,
            "screened": ptrs, "k": ks}


def _removals_declared(obj):
    """Keys whose loss the object explicitly accounts for.

    A record must name a criterion, evidence and an adjudicator. A record missing
    any of the three is not a justification -- it is a blank form, and the same
    rule applies here as to attestations.
    """
    out = {}
    for rec in (obj.get("removal_records") or []):
        k = rec.get("key")
        if not k:
            continue
        if rec.get("criterion") and rec.get("evidence") and rec.get("adjudicated_by"):
            out[k] = rec
    return out


# ---------------------------------------------------------------- ledger


def load_ledger():
    if os.path.exists(LEDGER):
        return json.load(open(LEDGER, encoding="utf-8"))
    return {"note": __doc__.strip().splitlines()[0], "apps": {}}


def update_ledger(led, st):
    """Monotonic: the ledger only ever grows. Union in, never subtract."""
    a = led["apps"].setdefault(st["app"], {"cells": [], "trials": [], "citations": [],
                                           "screened": [], "k": {}})
    for f in ("cells", "trials", "citations", "screened"):
        a[f] = sorted(set(a[f]) | st[f])
    for k, v in st["k"].items():
        a["k"][k] = max(a["k"].get(k, 0), v)     # high-water mark on k
    led["updated_utc"] = datetime.datetime.now(datetime.timezone.utc).strftime(
        "%Y-%m-%dT%H:%M:%SZ")
    return led


# ---------------------------------------------------------------- the guard


def check(obj, led):
    """Compare a candidate object against the high-water mark. Returns findings."""
    st = state_of(obj)
    prev = led["apps"].get(st["app"])
    if not prev:
        return {"verdict": "PASS", "reason": "no prior verified state; ledger seeded",
                "lost": {}, "justified": {}, "gained": _counts(st)}
    declared = _removals_declared(obj)
    lost, justified = {}, {}
    for f in ("cells", "trials", "citations", "screened"):
        gone = sorted(set(prev[f]) - st[f])
        for g in gone:
            (justified if g in declared else lost).setdefault(f, []).append(g)
    kdrop = {}
    for k, was in (prev.get("k") or {}).items():
        now = st["k"].get(k)
        if now is None:
            kdrop[k] = "%s -> absent" % was
        elif now < was:
            if declared.get(k):
                justified.setdefault("k", []).append("%s %s->%s" % (k, was, now))
            else:
                kdrop[k] = "%s -> %s" % (was, now)
    if kdrop:
        lost["k"] = kdrop
    verdict = "FAIL" if lost else "PASS"
    return {"verdict": verdict, "lost": lost, "justified": justified,
            "gained": _counts(st),
            "reason": ("data regressed with no named violation" if lost else
                       "no unjustified loss against the high-water mark")}


def _counts(st):
    return {f: len(st[f]) for f in ("cells", "trials", "citations", "screened")}


# ---------------------------------------------------------------- proof
def check_all(root):
    """Gate entry point: every canonical object against the ledger. Exit 1 on loss.

    Deliberately fails CLOSED on a missing ledger and on an unreadable object. A
    guard that passes because it found nothing to check is the failure mode this
    programme has hit three times in one day.
    """
    led = load_ledger()
    if not led.get("apps"):
        print("LEDGER EMPTY OR MISSING -- nothing to compare against. Seed it with "
              "scripts/seed_ledger.py before pushing. Failing closed.")
        return 1
    objs = sorted(glob.glob(os.path.join(root, "ssot", "*", "*.json")))
    if not objs:
        print("no canonical objects found -- failing closed rather than passing "
              "on an empty set")
        return 1
    bad, checked = [], 0
    for j in objs:
        try:
            obj = json.load(open(j, encoding="utf-8"))
        except Exception as ex:
            print("UNREADABLE OBJECT %s :: %s -- failing closed" % (j, ex))
            return 1
        if "results" not in obj or "inputs" not in obj:
            continue
        checked += 1
        r = check(obj, led)
        if r["verdict"] != "PASS":
            bad.append((obj.get("app_id"), r))
    print("no-regression guard: %d objects checked against %d ledgered apps"
          % (checked, len(led["apps"])))
    if not checked:
        print("zero objects checked -- failing closed")
        return 1
    for app, r in bad:
        print("  REGRESSION in %s: %s" % (app, r["reason"]))
        for f, keys in r["lost"].items():
            print("    lost %-10s %s" % (f, str(keys)[:160]))
    if bad:
        print("\n%d app(s) regressed against the high-water mark." % len(bad))
        return 1
    print("no unjustified loss in any object.")
    return 0


if __name__ == "__main__":
    import copy, glob
    if "--check-all" in sys.argv:
        sys.exit(check_all(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
    OBJ = sys.argv[1] if len(sys.argv) > 1 else (
        r"F:\rapidmeta-ssot-shell\ssot\arni-hfref\arni-hfref.json")
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    obj = json.load(open(OBJ, encoding="utf-8"))

    led = load_ledger()
    st = state_of(obj)
    print("current state: " + ", ".join("%s=%d" % (k, v) for k, v in _counts(st).items())
          + ", k=" + json.dumps(st["k"]))
    led = update_ledger(led, st)
    print("ledger seeded from the current verified state\n")

    print("=== the guard must FAIL on a silent loss, and PASS on a justified one ===")

    def run(label, mutate, expect):
        cand = copy.deepcopy(obj)
        mutate(cand)
        r = check(cand, led)
        ok = r["verdict"] == expect
        print("  %-46s %-4s expected=%-4s %s" % (label, r["verdict"], expect,
                                                 "correct" if ok else "*** WRONG ***"))
        if r["lost"]:
            first = next(iter(r["lost"].items()))
            print("        lost: %s %s" % (first[0], str(first[1])[:74]))
        return ok

    allok = True
    # the real incident: a re-screen silently drops a trial we already verified
    allok &= run("silent drop of PARACHUTE-HF (the real incident)",
                 lambda c: c["inputs"]["trials"].__setitem__(
                     slice(None), [t for t in c["inputs"]["trials"]
                                   if t["id"] != "parachute-hf"]), "FAIL")
    # the same drop, properly justified
    def justified_drop(c):
        c["inputs"]["trials"] = [t for t in c["inputs"]["trials"]
                                 if t["id"] != "parachute-hf"]
        keys = [k for k in led["apps"]["arni-hfref"]["trials"] if "parachute" in k]
        keys += [k for k in led["apps"]["arni-hfref"]["cells"] if "parachute" in k]
        c["removal_records"] = [{"key": k, "criterion": "population axis",
                                 "evidence": "registry record shows a different population",
                                 "adjudicated_by": "Mahmood Ahmad"} for k in keys]
    allok &= run("same drop WITH a named violation per key", justified_drop, "PASS")
    # a blank removal record must not count
    def blank_record(c):
        c["inputs"]["trials"] = [t for t in c["inputs"]["trials"]
                                 if t["id"] != "parachute-hf"]
        c["removal_records"] = [{"key": "arni-hfref::trial::parachute-hf",
                                 "criterion": "", "evidence": "", "adjudicated_by": ""}]
    allok &= run("drop with a BLANK removal record", blank_record, "FAIL")
    # losing a recovered per-arm count while keeping the trial
    allok &= run("recovered per-arm count silently lost",
                 lambda c: c["inputs"]["trials"][0]["by_outcome"]
                 ["cvdeath_or_hfh_first"]["treatment"].pop("events"), "FAIL")
    # losing a citation
    allok &= run("a recovered citation silently lost",
                 lambda c: c.get("citations", {}).pop("25176015", None), "FAIL")
    # k going down
    def kdrop(c):
        c["results"]["by_outcome"]["cvdeath_or_hfh_first"]["k"] = 2
    allok &= run("k reduced with no record", kdrop, "FAIL")
    # adding is always fine
    def add(c):
        c["citations"]["99999999"] = {"pmid": "99999999"}
    allok &= run("adding a citation (improvement)", add, "PASS")
    # unchanged
    allok &= run("unchanged rebuild", lambda c: None, "PASS")

    print("\nregression guard proved able to fail on every silent loss:", allok)
    os.makedirs(os.path.dirname(LEDGER), exist_ok=True)
    json.dump(led, open(LEDGER, "w", encoding="utf-8"), indent=1)
    print("ledger written:", LEDGER)
    # EXIT CODE ON THE DIRECT-FILE PATH. Codex found this by attacking the guard:
    # `regression_guard.py <obj>` printed its proof and exited 0 whatever it found,
    # so the one command a person would run by hand could not fail. That is the
    # fifth guard-that-cannot-fire found today, and it was in the guard meant to be
    # load-bearing. The self-test result now decides the exit code.
    sys.exit(0 if allok else 1)
