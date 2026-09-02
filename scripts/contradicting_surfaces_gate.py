"""CONTRADICTING SURFACES GATE -- two of our own surfaces asserting different
values for the same quantity.

WHY THIS CLASS IS CHEAP AND POWERFUL. A contradiction needs no ground truth to
interpret. Nobody has to know the topic, read the trial, or agree about the
right answer: if one surface says a trial is excluded and another pools it, the
page is wrong whichever surface is right, and it is wrong in a way the reader can
see. That is the cheapest true finding available to us and this repository keeps
producing it.

WHAT WAS FOUND, ALL OF IT ON PAGES WE SERVE

    A trial displayed as EXCLUDED while its data is in the pooled estimate.
    ARNI's page prints "ANSWER-HF NCT04853758 ... excluded" and "This review's
    decision: excluded", and pools ANSWER-HF at k=4 on the same page.

    GRADE reading both "pending -- not rated" and "low" for one outcome.
    "No systematic search was performed" beside a 22-record search.
    "Twenty-two records undetermined" while decisions are shown for all 22.
    A discrepancy marked both resolved and unresolved.

THE FOUR RULES

    EXCLUDED_YET_POOLED
        A trial in inputs.trials that also carries an exclusion record in the
        screening block. Set intersection on registry identifiers; no topic
        knowledge. A DECLARED, DATED supersession exempts the record -- a
        reversal that says so is honest bookkeeping, a silent one is a
        contradiction. ARNI's `screening.excluded` entry is properly marked
        `SUPERSEDED_2026_08_18` and is exempt; its `screening.records` entry
        carries no marker and is not.

    CERTAINTY_ASSERTED_TWICE
        One outcome carrying both a certainty rating and a not-rated marker, in
        the object or on the page. "pending", "not rated", "not assessed" and a
        grade are mutually exclusive answers to one question.

    SEARCH_DENIED_YET_PRESENT
        A surface saying no search was performed while the object holds executed
        queries or a retrieved corpus.

    RESOLVED_AND_UNRESOLVED
        One item appearing in both a resolved and an unresolved list of the same
        reconciliation block.

WHAT IT CANNOT SEE -- printed with every verdict

    * Contradictions between two pieces of prose that share no identifier. The
      rules key on registry ids, outcome ids and list membership.
    * A contradiction where BOTH surfaces are wrong in the same direction. This
      gate compares surfaces; it never establishes truth.
    * Objects with no screening block at all: 93 of the 155 canonical objects
      carry none, so EXCLUDED_YET_POOLED is NOT_APPLICABLE to those and its zero
      there means NOT OBSERVED, not SAFE.
    * The k-versus-k contradiction, which is `k_consistency_gate.py`'s and is
      deliberately not duplicated here.
    * Phrasings outside the marker lists below.

USAGE

    python scripts/contradicting_surfaces_gate.py --selftest
    python scripts/contradicting_surfaces_gate.py ssot/<app>/<app>.json ...
    python scripts/contradicting_surfaces_gate.py --diff origin/main   # DEFAULT
    python scripts/contradicting_surfaces_gate.py --all
    ... optionally with --page <served.html> to check the page's own surfaces

Exit code: +1 if anything FAILED, +2 if anything could not be judged.
"""
from __future__ import annotations

import argparse
import html as _html
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

_NCT = re.compile(r"NCT\d{8}")

# A record is an exclusion when it says so. Two vocabularies are in use across
# the corpus and both are listed rather than guessed at.
_EXCLUSION_MARKS = ("exclud", "not eligible", "ineligible", "fails ", "screened, not")

# A supersession must be DECLARED to exempt a record. Anything matching this is
# a dated, readable reversal; anything not matching is a silent contradiction.
_SUPERSEDED_KEY = re.compile(r"(?i)supersed")

_NOT_RATED = ("pending", "not rated", "not yet rated", "not assessed",
              "no rating", "unrated", "not graded")
_GRADES = ("high", "moderate", "low", "very low")

_NO_SEARCH = (
    "no systematic search was performed",
    "no systematic search has been performed",
    "no search was performed",
    "no search was run",
    "no systematic search was run",
)


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


# --------------------------------------------------------------------------

_INLINE = ("a|abbr|b|bdi|bdo|big|cite|code|del|dfn|em|font|i|ins|kbd|label|mark|"
           "output|q|rp|rt|ruby|s|samp|small|span|strike|strong|sub|sup|time|tt|"
           "u|var|wbr")
_INLINE_RE = re.compile(r"(?i)</?(?:%s)\b[^>]*>" % _INLINE)


def rendered_text(html):
    txt = re.sub(r"(?is)<(script|style)\b.*?</\1>", " ", html)
    txt = _INLINE_RE.sub("", txt)
    txt = re.sub(r"<[^>]+>", " ", txt)
    return re.sub(r"\s+", " ", _html.unescape(txt))


def _is_exclusion(rec):
    if not isinstance(rec, dict):
        return False
    if rec.get("criteria_failed"):
        return True
    blob = " ".join(str(rec.get(k, "")) for k in
                    ("disposition", "reason", "decision", "verdict")).lower()
    return any(m in blob for m in _EXCLUSION_MARKS)


def _declared_superseded(rec):
    if not isinstance(rec, dict):
        return None
    for k, v in rec.items():
        if _SUPERSEDED_KEY.search(str(k)) or (
                k in ("status", "note") and _SUPERSEDED_KEY.search(str(v))):
            return str(k)
    return None


# --------------------------------------------------------------------------
# the rules

def rule_excluded_yet_pooled(obj):
    trials = as_list((obj.get("inputs") or {}).get("trials"))
    pooled = {}
    for t in trials:
        if not isinstance(t, dict):
            continue
        for nct in _NCT.findall(json.dumps(t.get("nct") or "")):
            pooled[nct] = t.get("name") or t.get("id") or nct
    scr = obj.get("screening") or {}
    if not scr:
        return [Finding("EXCLUDED_YET_POOLED", "screening", NA,
                        "this object carries no screening block, so no "
                        "exclusion decision exists to contradict")]
    if not pooled:
        return [Finding("EXCLUDED_YET_POOLED", "inputs.trials", UNDET,
                        "a screening block is present but no pooled trial "
                        "carries a registry identifier to match it against")]

    out, checked = [], 0
    for key in ("records", "excluded", "screened"):
        for i, rec in enumerate(as_list(scr.get(key))):
            if not isinstance(rec, dict):
                continue
            checked += 1
            if not _is_exclusion(rec):
                continue
            marker = _declared_superseded(rec)
            ids = set(_NCT.findall(json.dumps(rec, ensure_ascii=False)))
            hit = ids & set(pooled)
            if not hit:
                continue
            if marker:
                continue    # a declared, dated reversal is honest bookkeeping
            for nct in sorted(hit):
                out.append(Finding(
                    "EXCLUDED_YET_POOLED", "screening.%s[%d]" % (key, i), FAIL,
                    "%s (%s) is recorded as an exclusion here and is also in "
                    "inputs.trials, contributing to the pooled estimate. No "
                    "supersession is declared on the record, so the object "
                    "asserts both at once."
                    % (pooled[nct], nct)))
    if not out:
        out.append(Finding("EXCLUDED_YET_POOLED", "screening", PASS,
                           "%d screening record(s) read against %d pooled "
                           "trial(s); no pooled trial is also excluded"
                           % (checked, len(pooled))))
    return out


def rule_certainty_asserted_twice(obj):
    by_outcome = ((obj.get("results") or {}).get("by_outcome") or {})
    if not by_outcome:
        return [Finding("CERTAINTY_ASSERTED_TWICE", "results", NA,
                        "no results.by_outcome on this object")]
    out, judged = [], 0
    for oid, o in by_outcome.items():
        if not isinstance(o, dict):
            continue
        grade = o.get("grade")
        if not isinstance(grade, dict):
            continue
        judged += 1
        cert = str(grade.get("certainty") or "").strip().lower()
        blob = json.dumps(grade, ensure_ascii=False).lower()
        rated = cert in _GRADES
        not_rated_here = [m for m in _NOT_RATED
                          if re.search(r"\b%s\b" % re.escape(m), cert)]
        if not rated and not not_rated_here:
            out.append(Finding("CERTAINTY_ASSERTED_TWICE", oid, UNDET,
                               "grade.certainty is %r, which is neither a "
                               "rating nor a declared not-rated state"
                               % grade.get("certainty")))
            continue
        # the contradiction: a rating AND a not-rated marker asserted for the
        # same outcome, in a field that answers the same question
        others = []
        for k, v in grade.items():
            if k == "certainty" or not isinstance(v, str):
                continue
            if k.endswith("_note") or k.endswith("_because") or "derivation" in k:
                continue
            vl = v.strip().lower()
            if rated and any(vl == m or vl.startswith(m + " ") for m in _NOT_RATED):
                others.append((k, v))
            if (not rated) and vl in _GRADES:
                others.append((k, v))
        if others:
            out.append(Finding(
                "CERTAINTY_ASSERTED_TWICE", oid, FAIL,
                "grade.certainty is %r while %s. One outcome cannot be both "
                "rated and not rated."
                % (grade.get("certainty"),
                   "; ".join("grade.%s is %r" % kv for kv in others))))
        else:
            out.append(Finding("CERTAINTY_ASSERTED_TWICE", oid, PASS,
                               "one certainty state on this outcome: %r"
                               % grade.get("certainty")))
    if not judged:
        out.append(Finding("CERTAINTY_ASSERTED_TWICE", "results", NA,
                           "no outcome on this object carries a grade block"))
    return out


def rule_search_denied_yet_present(obj, page_text=None):
    search = obj.get("search") or {}
    scr = obj.get("screening") or {}
    dbs = as_list(search.get("databases"))
    corpus = as_list(scr.get("corpus"))
    has_search = bool(dbs) or bool(corpus)

    surfaces = []
    for blob, where in ((json.dumps(obj, ensure_ascii=False), "the object"),
                        (page_text or "", "the page")):
        if not blob:
            continue
        low = blob.lower()
        for phrase in _NO_SEARCH:
            if phrase in low:
                surfaces.append((where, phrase))
    if not surfaces:
        return [Finding("SEARCH_DENIED_YET_PRESENT", "search",
                        PASS if has_search else NA,
                        "no surface denies that a search was run; %d database "
                        "record(s) and %d corpus record(s) are held"
                        % (len(dbs), len(corpus))
                        if has_search else
                        "no search is claimed and none is denied; nothing to "
                        "contradict")]
    if not has_search:
        return [Finding("SEARCH_DENIED_YET_PRESENT", "search", PASS,
                        "a surface says no search was performed and the object "
                        "holds none: the two agree")]
    return [Finding(
        "SEARCH_DENIED_YET_PRESENT", where, FAIL,
        "%s says %r, while the object holds %d executed database record(s) and "
        "a corpus of %d record(s)." % (where, phrase, len(dbs), len(corpus)))
        for where, phrase in surfaces]


def rule_resolved_and_unresolved(obj):
    rec = obj.get("reconciliation")
    if not isinstance(rec, dict):
        return [Finding("RESOLVED_AND_UNRESOLVED", "reconciliation", NA,
                        "no reconciliation block on this object")]
    resolved_keys = ("matches", "corrections", "resolved")
    unresolved_keys = ("unresolved", "outstanding", "open")

    def ids_of(keys):
        got = {}
        for k in keys:
            for i, item in enumerate(as_list(rec.get(k))):
                blob = json.dumps(item, ensure_ascii=False)
                for nct in _NCT.findall(blob):
                    got.setdefault(nct, []).append("%s[%d]" % (k, i))
        return got

    res, unres = ids_of(resolved_keys), ids_of(unresolved_keys)
    both = sorted(set(res) & set(unres))
    if both:
        return [Finding(
            "RESOLVED_AND_UNRESOLVED", "reconciliation", FAIL,
            "%s appears in %s and in %s at once."
            % (nct, "/".join(res[nct]), "/".join(unres[nct]))) for nct in both]
    if not res and not unres:
        return [Finding("RESOLVED_AND_UNRESOLVED", "reconciliation", NA,
                        "the reconciliation block names no identifier on either "
                        "side, so nothing can be compared")]
    return [Finding("RESOLVED_AND_UNRESOLVED", "reconciliation", PASS,
                    "%d resolved and %d unresolved identifier(s), disjoint"
                    % (len(res), len(unres)))]


# --------------------------------------------------------------------------

def judge_object(path, repo, page_path=None):
    rec = {"object": os.path.relpath(path, repo).replace(os.sep, "/"),
           "page": None, "state": None, "detail": "", "findings": []}
    try:
        with open(path, "rb") as fh:
            obj = json.loads(fh.read().decode("utf-8", "replace"))
    except Exception as exc:
        rec["state"] = "NO_RECORD"
        rec["detail"] = "object unreadable: %s" % exc
        return rec

    page_text = None
    if page_path and os.path.exists(page_path):
        with open(page_path, "rb") as fh:
            page_text = rendered_text(fh.read().decode("utf-8", "replace"))
        rec["page"] = os.path.relpath(page_path, repo).replace(os.sep, "/")

    fs = []
    fs += rule_excluded_yet_pooled(obj)
    fs += rule_certainty_asserted_twice(obj)
    fs += rule_search_denied_yet_present(obj, page_text)
    fs += rule_resolved_and_unresolved(obj)
    rec["findings"] = [f.as_dict() for f in fs]

    states = {f["state"] for f in rec["findings"]}
    rec["state"] = (FAIL if FAIL in states else
                    UNDET if UNDET in states else
                    PASS if PASS in states else NA)
    return rec


# --------------------------------------------------------------------------
# scope

def _is_canonical(rel):
    parts = rel.split("/")
    return (len(parts) == 3 and parts[0] == "ssot"
            and parts[2] == parts[1] + ".json")


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
    out = []
    for name in sorted(os.listdir(root)):
        p = os.path.join(root, name, name + ".json")
        if os.path.exists(p):
            out.append(p)
    return out


# --------------------------------------------------------------------------

def report(records, n_in_scope, scope_note, wall, cpu, not_reached):
    fails = [r for r in records if r["state"] == FAIL]
    undet = [r for r in records if r["state"] in (UNDET, "NO_RECORD", "TIMED_OUT")]
    passes = [r for r in records if r["state"] == PASS]
    na = [r for r in records if r["state"] == NA]

    for r in fails:
        print("\nFAIL  %s%s" % (r["object"],
                                "  (page %s)" % r["page"] if r["page"] else ""))
        for f in [x for x in r["findings"] if x["state"] == FAIL]:
            print("      [%s] %s" % (f["rule"], f["where"]))
            print("      %s" % f["detail"])
    for r in undet:
        print("\n%-14s %s -- %s" % (r["state"], r["object"], r["detail"][:120]))
        for f in [x for x in r["findings"] if x["state"] == UNDET][:4]:
            print("      [%s] %s" % (f["rule"], f["detail"]))

    reach = {}
    for r in records:
        for f in r["findings"]:
            d = reach.setdefault(f["rule"], {PASS: 0, FAIL: 0, UNDET: 0, NA: 0})
            d[f["state"]] += 1

    print("\n" + "-" * 74)
    print("COVERAGE   %d of %d %s" % (len(records), n_in_scope, scope_note))
    print("           %d PASS, %d FAIL, %d could not be judged, %d not "
          "applicable" % (len(passes), len(fails), len(undet), len(na)))
    print("PER RULE   (a rule that judged nothing reads NOT OBSERVED, not SAFE)")
    for rule in sorted(reach):
        d = reach[rule]
        judged = d[PASS] + d[FAIL] + d[UNDET]
        print("           %-34s %s"
              % (rule,
                 "NOT OBSERVED -- 0 judged, %d not applicable" % d[NA]
                 if judged == 0 else
                 "%d judged: %d pass, %d fail, %d undeterminable (%d n/a)"
                 % (judged, d[PASS], d[FAIL], d[UNDET], d[NA])))
    n_paged = sum(1 for r in records if r["page"])
    print("BLIND TO   prose contradictions sharing no identifier; a page not "
          "supplied (%d of %d" % (n_paged, len(records)))
    print("           record(s) had one); k-versus-k, which is "
          "k_consistency_gate.py's;")
    print("           and any case where both surfaces are wrong the same way.")
    if not_reached:
        print("           NOT REACHED: %d object(s)" % len(not_reached))
    print("COST       %.2fs wall, %.2fs CPU" % (wall, cpu))
    if not records:
        print("VERDICT    NOT OBSERVED -- nothing in scope carried an object.")
    return (1 if fails else 0) + (2 if (undet or not_reached) else 0)


# --------------------------------------------------------------------------
# self-test

def _base():
    return {
        "inputs": {"trials": [
            {"id": "t1", "nct": "NCT00000001", "name": "TRIAL-ONE"},
            {"id": "t2", "nct": "NCT00000002", "name": "TRIAL-TWO"}]},
        "screening": {"records": [
            {"trial": "OTHER", "nct": "NCT00000009",
             "criteria_failed": ["population"], "reason": "excluded"}],
            "corpus": [{"pmid": "1"}, {"pmid": "2"}]},
        "search": {"databases": [{"database": "PubMed"}]},
        "results": {"by_outcome": {"o1": {
            "k": 2, "grade": {"certainty": "low",
                              "certainty_derivation": "start high; -1, -1"}}}},
        "reconciliation": {"matches": [{"nct": "NCT00000001"}],
                           "unresolved": [{"nct": "NCT00000003"}]},
    }


def selftest():
    import copy
    import shutil
    import tempfile

    root = tempfile.mkdtemp(prefix="contradictgate_")
    try:
        def write(name, obj):
            d = os.path.join(root, "ssot", name)
            os.makedirs(d, exist_ok=True)
            p = os.path.join(d, name + ".json")
            with open(p, "w", encoding="utf-8") as fh:
                json.dump(obj, fh)
            return p

        ok = True
        seq = [0]
        print("=== each plant must fire before its fix is allowed to pass ===")

        def case(label, obj, want, rule=None, page=None):
            # A COUNTER, not hash(label): PYTHONHASHSEED is randomised per
            # process, so hash-derived names differ between runs. That is the
            # very class lint_unordered_iteration.py exists to catch, and a
            # self-test is a bad place to demonstrate it.
            nonlocal ok
            seq[0] += 1
            pth = write("__control_%02d" % seq[0], obj)
            pg = None
            if page is not None:
                pg = os.path.join(root, "p%02d.html" % seq[0])
                with open(pg, "w", encoding="utf-8") as fh:
                    fh.write(page)
            r = judge_object(pth, root, pg)
            fired = {f["rule"] for f in r["findings"] if f["state"] == FAIL}
            good = r["state"] == want and (rule is None or rule in fired)
            ok = ok and good
            print("  %-14s expected %-14s %-8s %s"
                  % (r["state"], want, "correct" if good else "WRONG", label))

        case("clean object: nothing contradicts", _base(), PASS)

        o = copy.deepcopy(_base())
        o["screening"]["records"].append(
            {"trial": "TRIAL-ONE", "nct": "NCT00000001",
             "criteria_failed": ["measure"], "reason": "excluded: fails measure"})
        case("PLANT: a pooled trial also recorded as excluded",
             o, FAIL, "EXCLUDED_YET_POOLED")

        o2 = copy.deepcopy(o)
        o2["screening"]["records"][-1]["SUPERSEDED_2026_09_02"] = (
            "SUPERSEDED. The measure question was resolved against the source "
            "and TRIAL-ONE is in the pool.")
        case("FIX of that plant: the reversal is declared and dated",
             o2, PASS)

        o3 = copy.deepcopy(_base())
        o3["results"]["by_outcome"]["o1"]["grade"]["status"] = "pending"
        case("PLANT: one outcome both rated 'low' and 'pending'",
             o3, FAIL, "CERTAINTY_ASSERTED_TWICE")

        o4 = copy.deepcopy(_base())
        o4["screening"]["note"] = "No systematic search was performed."
        case("PLANT: a search denied by the object that the object holds",
             o4, FAIL, "SEARCH_DENIED_YET_PRESENT")

        case("PLANT: the same denial on the PAGE instead of the object",
             _base(), FAIL, "SEARCH_DENIED_YET_PRESENT",
             page="<html><body><p>No systematic search was "
                  "perf<em>ormed</em>.</p></body></html>")

        o5 = copy.deepcopy(_base())
        o5["reconciliation"]["unresolved"].append({"nct": "NCT00000001"})
        case("PLANT: one identifier both resolved and unresolved",
             o5, FAIL, "RESOLVED_AND_UNRESOLVED")

        o6 = copy.deepcopy(_base())
        del o6["screening"]
        r = judge_object(write("__control_noscreen", o6), root)
        rules = {f["rule"]: f["state"] for f in r["findings"]}
        good = rules.get("EXCLUDED_YET_POOLED") == NA
        ok = ok and good
        print("  %-14s expected %-14s %-8s %s"
              % (rules.get("EXCLUDED_YET_POOLED"), NA,
                 "correct" if good else "WRONG",
                 "no screening block: NOT_APPLICABLE, never a pass"))

        o7 = copy.deepcopy(_base())
        o7["inputs"]["trials"] = [{"id": "t1", "name": "no registry id"}]
        r = judge_object(write("__control_noids", o7), root)
        rules = {f["rule"]: f["state"] for f in r["findings"]}
        good = rules.get("EXCLUDED_YET_POOLED") == UNDET
        ok = ok and good
        print("  %-14s expected %-14s %-8s %s"
              % (rules.get("EXCLUDED_YET_POOLED"), UNDET,
                 "correct" if good else "WRONG",
                 "screening present but no identifier to match on"))

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
    import copy
    import shutil
    import tempfile

    from instrument_controls import require_controls

    root = tempfile.mkdtemp(prefix="contradict_ctl_")
    try:
        def write(name, obj):
            d = os.path.join(root, "ssot", name)
            os.makedirs(d, exist_ok=True)
            p = os.path.join(d, name + ".json")
            with open(p, "w", encoding="utf-8") as fh:
                json.dump(obj, fh)
            return p

        planted = copy.deepcopy(_base())
        planted["screening"]["records"].append(
            {"trial": "TRIAL-ONE", "nct": "NCT00000001",
             "criteria_failed": ["measure"],
             "reason": "excluded: fails measure"})
        p1 = write("__control_contradiction", planted)
        p2 = write("__control_clean", _base())
        require_controls(
            "contradicting_surfaces_gate",
            positive=("a synthetic object pooling a trial it also records as "
                      "excluded", judge_object(p1, root)["state"], FAIL),
            negative=("the same object with no such record",
                      judge_object(p2, root)["state"], FAIL))
    finally:
        shutil.rmtree(root, ignore_errors=True)


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("objects", nargs="*")
    ap.add_argument("--selftest", action="store_true")
    ap.add_argument("--page", help="served page to read alongside the object")
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
        records.append(judge_object(p, repo, a.page if len(objs) == 1 else None))
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
