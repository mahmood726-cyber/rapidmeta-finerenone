"""REFUSAL READS THE OUTCOME GROUPS GATE -- a refusal is a claim, and it is checked.

WHY THIS ONE MATTERS MOST. Our documented refusals are the output we most rely on:
they are what we point at when we say this review did not pool something it could
have. A FALSE WARNING IS WORSE THAN A MISSING ONE, because it discredits the true
ones, and a reader who catches us refusing for a reason that is not there has no
way to tell which of the other refusals are sound.

WHAT WAS FOUND. The bococizumab object warns that SPIRE-AI compares against the
wrong placebo:

    "SPIRE-AI registers FOUR arms in a dose-matched double-dummy ... THIS POOL'S
    SPIRE-AI ROW PAIRS THE 150 MG DOSE WITH THE 75 MG PLACEBO. Both are real
    registered arms and together they are not a registered contrast. Established
    from the registry's arm table"

The last sentence is the defect. The registry's TRIAL-LEVEL arm table lists all
four arms of the whole trial and cannot say which two belong to a given outcome.
The registry's OUTCOME-SPECIFIC group table can, and for this outcome it reads:

    "Percent Change From Baseline at Week 12 in Fasting Low Density Lipoprotein
    Cholesterol (LDL-C) Level for Bococizumab 150 mg Dose Group and Matched
    Placebo" -- type PRIMARY, two groups.

The contrast the pool uses IS a registered contrast, on the only table that could
have settled it. We read the trial-level arm list where we should have read the
outcome-specific group table, and published a warning against a sound analysis.

THE THREE RULES

    REFUSAL_NAMES_ITS_TABLE
        A refusal or warning that turns on arm identity must say which table it
        was resolved from. A refusal that does not name its source cannot be
        audited, and an unauditable refusal is an assertion.

    REFUSAL_READ_THE_WRONG_TABLE
        Naming a TRIAL-LEVEL source -- "the registry's arm table", the design
        module, arms_as_the_registry_lists_them, per-arm counts -- without also
        naming an OUTCOME-SPECIFIC one is reading a table that cannot answer the
        question asked.

    OUTCOME_GROUPS_CONTRADICT_THE_REFUSAL
        Where the object itself holds an outcome-specific entry whose title names
        a matched comparator for the outcome in question, a refusal asserting the
        contrast is unregistered is contradicted by the object's own registry
        capture, and the title is quoted back.

WHAT IT CANNOT SEE -- printed with every verdict

    * A refusal that turns on something other than arm identity. Out of scope by
      design; this gate is about one class of claim.
    * Whether the outcome-specific table is itself correctly captured. It checks
      which table was consulted, not whether the registry is right.
    * A trial whose object holds no outcome-specific counts at all: the third
      rule is UNDETERMINABLE there, not a pass, and the coverage line says how
      many.
    * Refusal wording outside the marker lists below.
    * It does not decide whether a contrast SHOULD be pooled. It decides whether
      the reason given for refusing was resolved from a table that could answer.

USAGE

    python scripts/refusal_reads_outcome_groups_gate.py --selftest
    python scripts/refusal_reads_outcome_groups_gate.py ssot/<app>/<app>.json ...
    python scripts/refusal_reads_outcome_groups_gate.py --diff origin/main
    python scripts/refusal_reads_outcome_groups_gate.py --all

Exit code: +1 if anything FAILED, +2 if anything could not be judged.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)
if HERE not in sys.path:
    sys.path.insert(0, HERE)

PASS, FAIL, UNDET, NA = "PASS", "FAIL", "UNDETERMINABLE", "NOT_APPLICABLE"

# A refusal that turns on ARM IDENTITY: it says something about which arms were
# compared, not merely that arms exist.
_ARM_CLAIM = re.compile(
    r"(?i)(not a registered contrast|wrong placebo|other dose'?s placebo|"
    r"unmatched placebo|mismatched (?:arm|placebo|comparator)|"
    r"pairs? .{0,60}with .{0,60}placebo|compares? against the wrong|"
    r"arm pair is not|is not the matched placebo|not the registered comparator)")

# Where the claim says it was resolved from.
_TRIAL_LEVEL = re.compile(
    r"(?i)(registry'?s arm table|the arm table|registry_arm_table|"
    r"REGISTRY_ARM_TABLE|arms_as_the_registry_lists_them|"
    r"design module|arm groups|per[_ -]arm counts|aact_per_arm_counts|"
    r"trial[- ]level arm|\bBG0\d\d\b|\bEG0\d\d\b)")
_OUTCOME_LEVEL = re.compile(
    r"(?i)(outcome[- ]specific group|outcome group table|outcome[- ]specific "
    r"table|per[- ]outcome group|registration_primary_counts|"
    r"registration_other_outcome_counts|outcome measure group|\bOG0\d\d\b|"
    r"results section'?s outcome|outcome'?s own group)")

# An outcome-specific title that names its comparator.
_MATCHED = re.compile(r"(?i)\b(and|versus|vs\.?|compared with|against)\s+"
                      r"(the\s+)?(matched|matching)?\s*placebo\b")


def as_list(value):
    """A list, or [] for anything that is not one.

    THE CORPUS DOES NOT KEEP THE SHAPE ITS SCHEMA IMPLIES. Some objects store
    `screening.excluded` as an INTEGER -- a count rather than a collection --
    and iterating it killed a corpus sweep on the first such object, so
    everything after it was never examined at all. A crash mid-sweep is worse
    than a wrong verdict, because the wrong verdict is visible and the
    unexamined remainder is not.
    """
    return value if isinstance(value, list) else []


class Finding(object):
    def __init__(self, rule, where, state, detail):
        self.rule, self.where, self.state, self.detail = rule, where, state, detail

    def as_dict(self):
        return {"rule": self.rule, "where": self.where, "state": self.state,
                "detail": self.detail}


def _walk_strings(obj, path=""):
    if isinstance(obj, dict):
        for k, v in obj.items():
            for r in _walk_strings(v, "%s.%s" % (path, k)):
                yield r
    elif isinstance(obj, list):
        for i, v in enumerate(obj):
            for r in _walk_strings(v, "%s[%d]" % (path, i)):
                yield r
    elif isinstance(obj, str):
        yield path, obj


_NCT = re.compile(r"NCT\d{8}")


def _outcome_capture(obj):
    """{nct: (n_entries_held, [entries whose title names a comparator])}.

    THE TWO NUMBERS ARE KEPT APART ON PURPOSE. "this object holds no
    outcome-specific capture" and "it holds one and no entry names a comparator"
    are opposite facts, and collapsing them would make the third rule capable of
    only FAIL and UNDETERMINABLE -- a rule that can never pass is a rule nobody
    can satisfy.
    """
    out = {}
    for t in as_list((obj.get("inputs") or {}).get("trials")):
        if not isinstance(t, dict):
            continue
        nct = t.get("nct")
        if not nct:
            continue
        held, naming = 0, []
        for field in ("registration_primary_counts",
                      "registration_other_outcome_counts"):
            v = t.get(field)
            entries = v if isinstance(v, list) else ([v] if isinstance(v, dict)
                                                     else [])
            for e in entries:
                if isinstance(e, dict) and isinstance(e.get("title"), str):
                    held += 1
                    if _MATCHED.search(e["title"]):
                        naming.append((field, e.get("type"), e["title"]))
        out[nct] = (held, naming)
    return out


def judge_object(path, repo):
    rec = {"object": os.path.relpath(path, repo).replace(os.sep, "/"),
           "state": None, "detail": "", "findings": [], "refusals": 0}
    try:
        with open(path, "rb") as fh:
            obj = json.loads(fh.read().decode("utf-8", "replace"))
    except Exception as exc:
        rec["state"] = "NO_RECORD"
        rec["detail"] = "object unreadable: %s" % exc
        return rec

    titles = _outcome_capture(obj)
    trial_names = {}
    for t in as_list((obj.get("inputs") or {}).get("trials")):
        if isinstance(t, dict) and t.get("nct"):
            for key in ("name", "id"):
                if t.get(key):
                    trial_names[str(t[key]).upper()] = t["nct"]

    fs = []
    seen = set()
    for where, text in _walk_strings(obj):
        if not _ARM_CLAIM.search(text):
            continue
        # one finding per distinct claim, not per copy of it
        key = re.sub(r"\s+", " ", text)[:120]
        if key in seen:
            continue
        seen.add(key)
        rec["refusals"] += 1

        # THE FIELD NAME IS PART OF THE CLAIM. This corpus writes its provenance
        # into keys as often as into sentences --
        # `risk_of_bias.IDENTITY_ESTABLISHED_FROM_THE_REGISTRY_ARM_TABLE` names
        # the table it read and says nothing about it in the prose. Reading only
        # the prose would report "names no table" about a field whose entire name
        # is the answer, which is a statement about the reader.
        source_text = where + " " + text
        trial_level = _TRIAL_LEVEL.search(source_text)
        outcome_level = _OUTCOME_LEVEL.search(source_text)

        if not trial_level and not outcome_level:
            fs.append(Finding(
                "REFUSAL_NAMES_ITS_TABLE", where, FAIL,
                "this refusal turns on arm identity and names no table it was "
                "resolved from. Name the outcome-specific group table it was "
                "read from, or withdraw it. Claim: %r" % key))
        elif trial_level and not outcome_level:
            fs.append(Finding(
                "REFUSAL_READ_THE_WRONG_TABLE", where, FAIL,
                "this refusal says it was resolved from %r -- a TRIAL-LEVEL "
                "source, which lists every arm of the trial and cannot say "
                "which two belong to one outcome. Only the outcome-specific "
                "group table can. Claim: %r"
                % (trial_level.group(0), key)))
        else:
            fs.append(Finding(
                "REFUSAL_READ_THE_WRONG_TABLE", where, PASS,
                "resolved from an outcome-specific source (%r)"
                % outcome_level.group(0)))

        # does the object's own outcome-specific capture contradict the refusal?
        ncts = set(_NCT.findall(text))
        for name, nct in trial_names.items():
            if re.search(r"\b%s\b" % re.escape(name), text.upper()):
                ncts.add(nct)
        if not ncts:
            fs.append(Finding(
                "OUTCOME_GROUPS_CONTRADICT_THE_REFUSAL", where, UNDET,
                "the refusal names no trial this object holds, so its "
                "outcome-specific groups cannot be looked up"))
            continue
        for nct in sorted(ncts):
            got = titles.get(nct)
            if got is None:
                fs.append(Finding(
                    "OUTCOME_GROUPS_CONTRADICT_THE_REFUSAL", where, UNDET,
                    "%s is not among this object's trials, so its "
                    "outcome-specific groups cannot be read" % nct))
                continue
            held, naming = got
            if not held:
                fs.append(Finding(
                    "OUTCOME_GROUPS_CONTRADICT_THE_REFUSAL", where, UNDET,
                    "this object holds NO outcome-specific capture for %s, so "
                    "the only table that could settle the refusal was never "
                    "read into it" % nct))
            elif not naming:
                fs.append(Finding(
                    "OUTCOME_GROUPS_CONTRADICT_THE_REFUSAL", where, PASS,
                    "%d outcome-specific entr(y/ies) held for %s and none names "
                    "a comparator that contradicts the refusal" % (held, nct)))
            else:
                field, typ, title = naming[0]
                fs.append(Finding(
                    "OUTCOME_GROUPS_CONTRADICT_THE_REFUSAL", where, FAIL,
                    "the refusal says the %s contrast is not registered, while "
                    "this object's own %s for %s holds a %s entry titled %r. "
                    "The outcome names its own comparator; the refusal is "
                    "contradicted by the capture it should have read."
                    % (nct, field, nct, typ or "?", title)))

    rec["findings"] = [f.as_dict() for f in fs]
    if not fs:
        rec["state"] = NA
        rec["detail"] = ("no refusal on this object turns on arm identity")
        return rec
    states = {f["state"] for f in rec["findings"]}
    rec["state"] = (FAIL if FAIL in states else
                    UNDET if UNDET in states else
                    PASS if PASS in states else NA)
    return rec


# --------------------------------------------------------------------------
# scope / reporting

def _is_canonical(rel):
    p = rel.split("/")
    return len(p) == 3 and p[0] == "ssot" and p[2] == p[1] + ".json"


def diff_objects(base, repo):
    r = subprocess.run(["git", "diff", "--name-only", "%s...HEAD" % base,
                        "--", "ssot/*.json"], cwd=repo, capture_output=True,
                       text=True, encoding="utf-8", errors="replace")
    if r.returncode != 0:
        return None, (r.stderr or "").strip()[:200]
    out = []
    for n in r.stdout.split("\n"):
        n = n.strip()
        p = os.path.join(repo, n.replace("/", os.sep))
        if n and _is_canonical(n) and os.path.exists(p):
            out.append(p)
    return out, None


def all_objects(repo):
    root = os.path.join(repo, "ssot")
    if not os.path.isdir(root):
        return []
    return [os.path.join(root, n, n + ".json") for n in sorted(os.listdir(root))
            if os.path.exists(os.path.join(root, n, n + ".json"))]


def report(records, n_in_scope, scope_note, wall, cpu, not_reached):
    fails = [r for r in records if r["state"] == FAIL]
    undet = [r for r in records if r["state"] in (UNDET, "NO_RECORD", "TIMED_OUT")]
    passes = [r for r in records if r["state"] == PASS]
    na = [r for r in records if r["state"] == NA]

    for r in fails:
        print("\nFAIL  %s" % r["object"])
        for f in [x for x in r["findings"] if x["state"] == FAIL]:
            print("      [%s] %s" % (f["rule"], f["where"]))
            print("      %s" % f["detail"])
    for r in undet:
        print("\n%-14s %s" % (r["state"], r["object"]))
        for f in [x for x in r["findings"] if x["state"] == UNDET][:3]:
            print("      [%s] %s" % (f["rule"], f["detail"]))

    reach = {}
    for r in records:
        for f in r["findings"]:
            d = reach.setdefault(f["rule"], {PASS: 0, FAIL: 0, UNDET: 0, NA: 0})
            d[f["state"]] += 1
    n_refusals = sum(r.get("refusals", 0) for r in records)

    print("\n" + "-" * 74)
    print("COVERAGE   %d of %d %s" % (len(records), n_in_scope, scope_note))
    print("           %d arm-identity refusal(s) found and judged across those "
          "object(s)" % n_refusals)
    print("           %d PASS, %d FAIL, %d could not be judged, %d carry no "
          "such refusal" % (len(passes), len(fails), len(undet), len(na)))
    print("PER RULE   (a rule that judged nothing reads NOT OBSERVED, not SAFE)")
    for rule in sorted(reach):
        d = reach[rule]
        judged = d[PASS] + d[FAIL] + d[UNDET]
        print("           %-42s %s"
              % (rule,
                 "NOT OBSERVED -- 0 judged" if judged == 0 else
                 "%d judged: %d pass, %d fail, %d undeterminable"
                 % (judged, d[PASS], d[FAIL], d[UNDET])))
    print("BLIND TO   refusals turning on anything but arm identity; whether the "
          "outcome-specific")
    print("           capture is itself right; refusal wording outside the "
          "marker lists. It")
    print("           judges which table was consulted, not whether the "
          "contrast should pool.")
    if n_refusals == 0:
        print("VERDICT    NOT OBSERVED -- no arm-identity refusal was in scope. "
              "That is not a")
        print("           statement that our refusals are sound.")
    if not_reached:
        print("           NOT REACHED: %d object(s)" % len(not_reached))
    print("COST       %.2fs wall, %.2fs CPU" % (wall, cpu))
    return (1 if fails else 0) + (2 if (undet or not_reached) else 0)


# --------------------------------------------------------------------------
# self-test

_SPIRE_TITLE = ("Percent Change From Baseline at Week 12 in Fasting Low Density "
                "Lipoprotein Cholesterol (LDL-C) Level for Bococizumab 150 mg "
                "Dose Group and Matched Placebo")


def _obj(claim, with_outcome_title=True, outcome_capture=True):
    trial = {"id": "spire-ai", "nct": "NCT02458287", "name": "SPIRE-AI",
             "arms": [{"label": "Bococizumab 150mg", "participants": 95},
                      {"label": "Bococizumab 75mg placebo", "participants": 50}]}
    if outcome_capture:
        trial["registration_other_outcome_counts"] = [
            {"title": (_SPIRE_TITLE if with_outcome_title else
                       "Percent Change From Baseline at Week 12 in Fasting LDL-C"),
             "type": "PRIMARY", "counts": [6.2, -57.2]}]
    return {"inputs": {"trials": [trial]},
            "results": {"by_outcome": {"o1": {"POOL_FINDINGS": {"a": claim}}}}}


def selftest():
    import shutil
    import tempfile

    root = tempfile.mkdtemp(prefix="refusalgate_")
    try:
        seq = [0]

        def run(label, obj, want, rule=None):
            seq[0] += 1
            d = os.path.join(root, "ssot", "__control_%02d" % seq[0])
            os.makedirs(d, exist_ok=True)
            p = os.path.join(d, "__control_%02d.json" % seq[0])
            with open(p, "w", encoding="utf-8") as fh:
                json.dump(obj, fh)
            r = judge_object(p, root)
            fired = {f["rule"] for f in r["findings"] if f["state"] == FAIL}
            good = r["state"] == want and (rule is None or rule in fired)
            print("  %-14s expected %-14s %-8s %s"
                  % (r["state"], want, "correct" if good else "WRONG", label))
            return good

        ok = True
        print("=== each plant must fire before its fix is allowed to pass ===")

        real = ("SPIRE-AI registers FOUR arms in a dose-matched double-dummy. "
                "THIS POOL'S SPIRE-AI ROW PAIRS THE 150 MG DOSE WITH THE 75 MG "
                "PLACEBO. Both are real registered arms and together they are "
                "not a registered contrast. Established from the registry's arm "
                "table.")
        ok &= run("PLANT: the bococizumab refusal, verbatim -- resolved from the "
                  "trial-level arm table", _obj(real), FAIL,
                  "REFUSAL_READ_THE_WRONG_TABLE")

        ok &= run("PLANT: the same object's outcome-specific title contradicts "
                  "it", _obj(real), FAIL,
                  "OUTCOME_GROUPS_CONTRADICT_THE_REFUSAL")

        ok &= run("PLANT: an arm-identity refusal naming no table at all",
                  _obj("SPIRE-AI's arm pair is not a registered contrast.",
                       with_outcome_title=False),
                  FAIL, "REFUSAL_NAMES_ITS_TABLE")

        # The corpus writes provenance into KEYS as well as sentences.
        keyed = {"inputs": {"trials": [
            {"id": "spire-ai", "nct": "NCT02458287", "name": "SPIRE-AI",
             "registration_other_outcome_counts": [
                 {"title": "Percent Change at Week 12", "type": "PRIMARY"}]}]},
            "risk_of_bias": {
                "IDENTITY_ESTABLISHED_FROM_THE_REGISTRY_ARM_TABLE":
                    "SPIRE-AI's arm pair is not a registered contrast."}}
        ok &= run("PLANT: the table is named in the FIELD NAME, not the prose",
                  keyed, FAIL, "REFUSAL_READ_THE_WRONG_TABLE")

        fixed = ("SPIRE-AI's recorded pair is not a registered contrast, "
                 "established from the outcome-specific group table for this "
                 "outcome (registration_primary_counts).")
        ok &= run("FIX of that plant: resolved from the outcome-specific group "
                  "table, whose entries name no contradicting comparator",
                  _obj(fixed, with_outcome_title=False), PASS)

        ok &= run("an object holding NO outcome-specific capture at all: "
                  "UNDETERMINABLE, because the only table that could settle it "
                  "was never read in",
                  _obj(fixed, outcome_capture=False), UNDET)

        ok &= run("a refusal on a trial whose outcome groups are not held: "
                  "UNDETERMINABLE, not a pass",
                  _obj("NCT09999999's arm pair is not a registered contrast, "
                       "read from the outcome-specific group table."),
                  UNDET)

        ok &= run("an object with no arm-identity refusal is NOT_APPLICABLE",
                  {"inputs": {"trials": []},
                   "results": {"by_outcome": {"o1": {"note": "nothing here"}}}},
                  NA)

        print("\nself-test %s" % ("PASSED" if ok else "FAILED"))
        return 0 if ok else 1
    finally:
        shutil.rmtree(root, ignore_errors=True)


# --------------------------------------------------------------------------

def run_controls():
    """Both controls, before any count is printed.

    THE CONTROLS ARE SYNTHETIC ON PURPOSE. A control anchored to a live corpus
    item retires itself the moment the defect is fixed: it then either fails and
    looks like a regression, or passes for the wrong reason. These are
    constructed, pinned in this file, and cannot drift. The negative side is not
    optional -- over-flagging is this gate's failure mode, and a false finding
    discredits the true ones.
    """
    import shutil
    import tempfile

    from instrument_controls import require_controls

    root = tempfile.mkdtemp(prefix="refusal_ctl_")
    try:
        def write(name, obj):
            d = os.path.join(root, "ssot", name)
            os.makedirs(d, exist_ok=True)
            p = os.path.join(d, name + ".json")
            with open(p, "w", encoding="utf-8") as fh:
                json.dump(obj, fh)
            return p

        p1 = write("__control_wrong_table", _obj(
            "SPIRE-AI registers FOUR arms in a dose-matched double-dummy. THIS "
            "POOL ROW PAIRS THE 150 MG DOSE WITH THE 75 MG PLACEBO. Both are "
            "real registered arms and together they are not a registered "
            "contrast. Established from the registry arm table."))
        p2 = write("__control_right_table", _obj(
            "SPIRE-AI recorded pair is not a registered contrast, established "
            "from the outcome-specific group table for this outcome "
            "(registration_primary_counts).", with_outcome_title=False))
        require_controls(
            "refusal_reads_outcome_groups_gate",
            positive=("a synthetic arm-identity refusal resolved from the "
                      "trial-level arm table",
                      judge_object(p1, root)["state"], FAIL),
            negative=("the same refusal resolved from the outcome-specific "
                      "group table", judge_object(p2, root)["state"], FAIL))
    finally:
        shutil.rmtree(root, ignore_errors=True)


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("objects", nargs="*")
    ap.add_argument("--selftest", action="store_true")
    ap.add_argument("--diff", metavar="BASE")
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--repo", default=REPO)
    ap.add_argument("--timeout-seconds", type=float, default=300.0)
    ap.add_argument("--json", metavar="PATH")
    a = ap.parse_args(argv)

    if a.selftest:
        return selftest()

    # NOTHING IS PRINTED BEFORE THE CONTROLS HOLD.
    run_controls()

    repo = os.path.abspath(a.repo)
    not_reached = []
    if a.objects:
        objs = [os.path.abspath(p) for p in a.objects]
        scope_note = "object(s) named on the command line"
    elif a.all:
        objs = all_objects(repo)
        scope_note = "canonical object(s) under ssot/"
    else:
        base = a.diff or "origin/main"
        objs, err = diff_objects(base, repo)
        if objs is None:
            print("INVALID: cannot compute the diff against %s: %s" % (base, err))
            return 2
        scope_note = "canonical object(s) changed against %s" % base

    t0, c0 = time.time(), time.process_time()
    deadline = t0 + a.timeout_seconds
    records = []
    for i, p in enumerate(objs):
        if time.time() > deadline:
            not_reached = objs[i:]
            print("TIMED_OUT after %.1fs: %d object(s) were not reached."
                  % (a.timeout_seconds, len(not_reached)))
            break
        records.append(judge_object(p, repo))
    wall, cpu = time.time() - t0, time.process_time() - c0

    rc = report(records, len(objs), scope_note, wall, cpu, not_reached)
    if a.json:
        with open(a.json, "w", encoding="utf-8") as fh:
            json.dump({"records": records, "scope": scope_note,
                       "n_in_scope": len(objs),
                       "not_reached": [os.path.basename(p) for p in not_reached],
                       "wall_seconds": wall, "cpu_seconds": cpu}, fh, indent=1)
    return rc


if __name__ == "__main__":
    raise SystemExit(main())
