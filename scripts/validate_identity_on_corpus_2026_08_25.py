"""Run the trial-identity rule over the whole corpus, on registry arm structures.

This is the validation the nine hand-checked cases could not provide, and it is possible only
because the arm structures were fetched from ClinicalTrials.gov API v2 -- AACT is behind a
login and is not needed.

THE ROLES ARE RE-DERIVED, NOT READ. Mahmood made this a hard condition and RAMBLE is why: the
sweep labelled apixaban the COMPARATOR on a trial whose registration shows two
ACTIVE_COMPARATOR arms with apixaban as the hypothesised better one. Writing remedies from
those labels would put the error on the page, where it stops being ours and becomes the
reader's. So every role here comes from the fetched arm structure, and the sweep is shown
only as a column to be disagreed with.

DRUG PATTERNS COME FROM THE MATCHER'S OWN TOPIC LIST. `add_topic_autodiscover.py` cannot be
imported -- it reads an AACT snapshot at module scope and there is none -- so TOPICS is
extracted by parsing the file's AST without executing it. Patterns taken from anywhere else
would test the rule against inputs production never sees, which is how the last attempt at
this ended up measuring its own harness.

THREE OUTCOMES PER TRIAL, and the third is not a pass:
  STUDIED        the drug is the randomised contrast, or one side of a head-to-head
  NOT STUDIED    background in every arm, comparator-only, placebo-only, or a combination
                 that merely contains the drug
  UNJUDGED       the arm structure could not be fetched, or the trial registers no arms.
                 Never counted as either. A fetch failure is not an absence.
"""
import ast
import io
import json
import os
import re
import sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(REPO, "ssot"))
sys.path.insert(0, os.path.join(REPO, "scripts"))
import trial_identity as T
import instrument_controls

CACHE = os.path.join(REPO, "outputs", "arm_structures_cache.jsonl")
SWEEP = os.path.join(REPO, "outputs", "trial_identity_sweep_2026_08_25.jsonl")
OUT = os.path.join(REPO, "outputs", "identity_roles_rederived_2026_08_25.json")


def topics_from_source():
    """(stem, name, drug_patterns) parsed from the matcher WITHOUT executing it."""
    src = io.open(os.path.join(REPO, "scripts", "add_topic_autodiscover.py"),
                  encoding="utf-8", errors="replace").read()
    tree = ast.parse(src)
    for node in tree.body:
        if not isinstance(node, ast.Assign):
            continue
        if not any(getattr(t, "id", None) == "TOPICS" for t in node.targets):
            continue
        out = []
        for el in node.value.elts:
            try:
                vals = ast.literal_eval(el)
            except Exception:
                continue
            if len(vals) >= 3 and isinstance(vals[2], (list, tuple)):
                out.append((str(vals[0]), str(vals[1]), [str(x) for x in vals[2]]))
        return out
    return []


def load_arms():
    """nct -> record. Last write wins, so a later successful retry supersedes an error."""
    arms = {}
    if os.path.exists(CACHE):
        for line in io.open(CACHE, encoding="utf-8"):
            try:
                d = json.loads(line)
            except ValueError:
                continue
            if d.get("nct"):
                arms[d["nct"]] = d
    return arms


def patterns_for(page, obj, topics):
    """(patterns, source). Topic list first; object title only as a labelled fallback."""
    stem = re.sub(r"\.html$", "", page).upper()
    best = None
    for tstem, _name, pats in topics:
        ts = tstem.upper()
        if ts and (ts in stem or stem.startswith(ts.split("_")[0])):
            if best is None or len(ts) > len(best[0]):
                best = (ts, pats)
    if best:
        return best[1], "TOPICS"
    title = str(obj.get("title") or "").strip()
    toks = [t.lower() for t in re.split(r"[^A-Za-z0-9]+", title) if len(t) >= 6]
    return (toks[:1], "title-fallback") if toks else ([], "none")


def main():
    if not os.path.exists(CACHE):
        print("REFUSED: no arm-structure cache. Run fetch_arm_structures first. "
              "NO COUNT IS PRINTED.")
        return 2
    arms = load_arms()
    topics = topics_from_source()
    print("topics parsed from the matcher source : %d" % len(topics))
    print("arm records cached                    : %d  (ok %d, error %d)"
          % (len(arms), sum(1 for v in arms.values() if v.get("status") == "ok"),
             sum(1 for v in arms.values() if v.get("status") != "ok")))

    # CONTROL: the rule must still separate the two cases whose registrations we read by hand.
    ram = arms.get("NCT02829957")
    twi = arms.get("NCT02270242")
    if not (ram and twi and ram.get("status") == "ok" and twi.get("status") == "ok"):
        print("REFUSED: the two hand-read control registrations are not in the cache, so the "
              "rule could not be checked against known answers. NO COUNT IS PRINTED.")
        return 2
    instrument_controls.require_controls(
        "identity-on-corpus",
        ("RAMBLE head-to-head: apixaban IS studied (two ACTIVE_COMPARATOR arms)",
         T.studies_subject(["apixaban"], ram["armGroups"])[0], True),
        ("TWILIGHT: ticagrelor is background in every arm and must NOT count as studied",
         T.studies_subject(["ticagrelor"], twi["armGroups"])[0], True))

    pmap = json.load(io.open(os.path.join(REPO, "ssot", "PAGE_MAP.json"), encoding="utf-8"))
    sweep = {}
    if os.path.exists(SWEEP):
        for line in io.open(SWEEP, encoding="utf-8"):
            try:
                d = json.loads(line)
            except ValueError:
                continue
            if d.get("status") == "ok":
                for t in d.get("trials", []):
                    sweep[(d["page"], t.get("nct"))] = t

    rows, unjudged, no_patterns = [], 0, 0
    for page, rel in sorted(pmap.items()):
        path = os.path.join(REPO, rel)
        if not os.path.exists(path):
            continue
        try:
            obj = json.load(io.open(path, encoding="utf-8"))
        except Exception:
            continue
        trials = [t for t in ((obj.get("inputs") or {}).get("trials") or [])
                  if isinstance(t, dict)]
        if not trials:
            continue
        pats, psrc = patterns_for(page, obj, topics)
        if not pats:
            no_patterns += len(trials)
            continue
        for t in trials:
            nct = t.get("nct") or t.get("trial_id")
            if not nct:
                continue
            rec = arms.get(nct)
            if not rec or rec.get("status") != "ok":
                unjudged += 1
                rows.append({"page": page, "nct": nct, "verdict": "UNJUDGED",
                             "why": "arm structure not fetched (%s)"
                                    % (rec or {}).get("error", "absent"),
                             "patterns": pats, "pattern_source": psrc})
                continue
            if not rec.get("armGroups"):
                unjudged += 1
                rows.append({"page": page, "nct": nct, "verdict": "UNJUDGED",
                             "why": "the registration declares no arm groups",
                             "patterns": pats, "pattern_source": psrc})
                continue
            ok, why = T.studies_subject(pats, rec["armGroups"])
            rows.append({"page": page, "nct": nct,
                         "verdict": "STUDIED" if ok else "NOT STUDIED", "why": why,
                         "patterns": pats, "pattern_source": psrc,
                         "sweep_said": (sweep.get((page, nct)) or {}).get("studies_subject"),
                         "sweep_role": (sweep.get((page, nct)) or {}).get("role")})

    studied = [r for r in rows if r["verdict"] == "STUDIED"]
    notstud = [r for r in rows if r["verdict"] == "NOT STUDIED"]
    pages_bad = sorted({r["page"] for r in notstud})
    print()
    print("trial records examined            : %d" % len(rows))
    print("  STUDIED                         : %d" % len(studied))
    print("  NOT STUDIED                     : %d   on %d page(s)"
          % (len(notstud), len(pages_bad)))
    print("  UNJUDGED (no arm data)          : %d   <- never counted as either" % unjudged)
    print("  skipped, no drug pattern derivable: %d" % no_patterns)
    print()
    byreason = {}
    for r in notstud:
        key = r["why"].split("(")[0].strip()
        byreason[key] = byreason.get(key, 0) + 1
    print("WHY, re-derived from arm structure:")
    for k, v in sorted(byreason.items(), key=lambda x: -x[1]):
        print("   %-64s %d" % (k[:64], v))
    print()
    dis = [r for r in rows if r.get("sweep_said") and
           ((r["verdict"] == "STUDIED") != (r["sweep_said"] == "YES"))]
    print("WHERE THE SWEEP'S LABEL DISAGREES WITH THE REGISTRATION: %d" % len(dis))
    print("(the registration is the standard; the sweep is the thing being audited)")
    for r in dis[:15]:
        print("   %-40s %-12s registry=%-12s sweep=%-4s role=%s"
              % (r["page"][:38], r["nct"], r["verdict"], r["sweep_said"], r["sweep_role"]))
    json.dump({"rows": rows, "pages_with_not_studied": pages_bad},
              io.open(OUT, "w", encoding="utf-8"), indent=1)
    print()
    print("written: %s" % os.path.relpath(OUT, REPO))
    return 0


if __name__ == "__main__":
    sys.exit(main())
