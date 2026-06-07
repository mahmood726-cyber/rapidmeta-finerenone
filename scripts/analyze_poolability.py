"""Poolability analysis for generated meta apps (READ-ONLY).

A meta-analysis needs >=2 trials measuring the SAME outcome with the SAME
effect type. AUTO apps tag every trial's outcome "MACE", so the engine pools
heterogeneous endpoints. This script reconstructs the real per-trial outcomes
from realData, fuzzy-clusters them, and classifies each app:

  poolable      >=1 cluster (same normalized endpoint + same effect class)
                spanning >=2 distinct trials
  non-poolable  no such cluster — either a single trial, or every trial
                measures a different endpoint (fuzzy matching can't help)

Outputs counts at several similarity thresholds (sensitivity) + a JSON list
of remove-candidates. Writes nothing else. Run --selftest to validate the
clustering on known cases first.
"""
from __future__ import annotations
import glob, io, json, os, re, sys

if hasattr(sys.stdout, "buffer") and getattr(sys.stdout, "encoding", "").lower() != "utf-8":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

STOP = set("the of in a an and or to for with at from by on as is was were be been "
           "after before during per change baseline week weeks day days month months "
           "year years number percent participants patients subjects time score mean "
           "rate ratio total least dose last".split())

# Canonicalize common endpoint phrases to a single token so spelled-out and
# abbreviated forms match (e.g. "American College of Rheumatology" vs "ACR 20").
SYNONYMS = {
    "american college of rheumatology": " acr ",
    "progression free survival": " pfs ",
    "progression-free survival": " pfs ",
    "overall survival": " os ",
    "forced expiratory volume in one second": " fev1 ",
    "forced expiratory volume in 1 second": " fev1 ",
    "forced expiratory volume": " fev1 ",
    "estimated glomerular filtration rate": " egfr ",
    "glycated hemoglobin": " hba1c ",
    "glycosylated hemoglobin": " hba1c ",
    "hemoglobin a1c": " hba1c ",
    "psoriasis area and severity index": " pasi ",
    "eczema area and severity index": " easi ",
    "disease activity score": " das28 ",
    "major adverse cardiovascular events": " mace ",
    "major adverse cardiac events": " mace ",
    "lean body mass": " leanbodymass ",
    "bone mineral density": " bmd ",
    "american college of cardiology": " acc ",
    "investigator-assessed": " ",
    "investigator assessed": " ",
}
_ACRO_RE = re.compile(r"\(([A-Za-z]{2,6}\s?\d{0,3})\)")


def _acronyms(title):
    out = set()
    for m in _ACRO_RE.finditer(title):
        a = re.sub(r"\s+", "", m.group(1)).lower()
        if a and not a.isdigit():
            out.add(a)
    return out


def normalize_tokens(title):
    t = re.sub(r"\(primary\)\s*$", "", title.lower())
    for phrase, repl in SYNONYMS.items():
        t = t.replace(phrase, repl)
    acro = _acronyms(title)
    t = re.sub(r"[^a-z0-9\s]", " ", t)
    toks = set(acro)
    for w in t.split():
        if w in STOP or w.isdigit() or len(w) <= 2:
            continue
        toks.add(w)
    return toks


def effect_class(o):
    et = (o.get("estimandType") or "").upper()
    if et == "MD" or ("md" in o and "effect" not in o):
        return "continuous"
    return "binary"


def jaccard(a, b):
    if not a or not b:
        return 0.0
    return len(a & b) / len(a | b)


# Distinctive endpoint identifiers: sharing one is strong evidence of the same
# endpoint even when surrounding wording differs (spelled-out vs abbreviated).
CANON = {"acr", "pfs", "os", "fev1", "egfr", "hba1c", "pasi", "easi",
         "das28", "mace", "bmd", "leanbodymass", "acc"}


def salient_tokens(title):
    return _acronyms(title) | (normalize_tokens(title) & CANON)


def cluster_outcomes(outcomes, thresh):
    """Greedy union-find: group outcomes with the same effect class when their
    token-Jaccard >= thresh OR they share a distinctive endpoint acronym."""
    n = len(outcomes)
    parent = list(range(n))

    def find(x):
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    def union(x, y):
        parent[find(x)] = find(y)

    toks = [normalize_tokens(o["title"]) for o in outcomes]
    sal = [salient_tokens(o["title"]) for o in outcomes]
    cls = [effect_class(o) for o in outcomes]
    for i in range(n):
        for j in range(i + 1, n):
            if cls[i] != cls[j]:
                continue
            if jaccard(toks[i], toks[j]) >= thresh or (sal[i] & sal[j]):
                union(i, j)
    groups = {}
    for i in range(n):
        groups.setdefault(find(i), []).append(i)
    return list(groups.values())


# Quoted-string body that tolerates the OTHER quote, apostrophes, and escapes
# (lessons.md: "Alzheimer's"/"Crohn's" inside a double-quoted title must not
# truncate the match).
_OUTCOME_RE = re.compile(
    r"\{\s*shortLabel:\s*(['\"])(?:\\.|(?!\1).)*\1\s*,\s*title:\s*(['\"])"
    r"(?P<title>(?:\\.|(?!\2).)*)\2(?P<rest>(?:\\.|[^}])*)\}")

_NCT_RE = re.compile(r"(?<![\w'\"])(NCT\d+)\s*:\s*\{")


def _parse_outcome(m):
    rest = m.group("rest")
    o = {"title": m.group("title")}
    et = re.search(r"estimandType:\s*(['\"])([^'\"]*)\1", rest)
    if et:
        o["estimandType"] = et.group(2)
    if re.search(r"\bmd:", rest):
        o["md"] = True
    if re.search(r"\beffect:", rest):
        o["effect"] = True
    return o


def extract_trial_outcomes(html):
    """Return list of (trial_id, outcome_dict). Each outcome is associated with
    the nearest preceding NCT trial key so a cluster can require >=2 DISTINCT
    trials (never pool one trial's own multiple outcomes)."""
    ncts = [(m.start(), m.group(1)) for m in _NCT_RE.finditer(html)]
    nct_pos = [p for p, _ in ncts]
    import bisect
    pairs = []
    for m in _OUTCOME_RE.finditer(html):
        i = bisect.bisect_right(nct_pos, m.start()) - 1
        tid = ncts[i][1] if i >= 0 else f"_pos{m.start()}"
        pairs.append((tid, _parse_outcome(m)))
    return pairs


def extract_app_outcomes(html):
    return [o for _, o in extract_trial_outcomes(html)]


def count_trials(html):
    return len(_NCT_RE.findall(html))


def classify(html, thresh):
    pairs = extract_trial_outcomes(html)
    outs = [o for _, o in pairs]
    tids = [t for t, _ in pairs]
    ntrials = len(set(tids))
    if ntrials < 2:
        return {"poolable": False, "reason": "single-trial/k<2",
                "n_outcomes": len(outs), "n_trials": ntrials, "max_cluster_trials": ntrials}
    clusters = cluster_outcomes(outs, thresh)
    # a cluster pools only if it spans >=2 DISTINCT trials
    max_trials = max((len({tids[i] for i in c}) for c in clusters), default=0)
    return {"poolable": max_trials >= 2,
            "reason": "has poolable cluster" if max_trials >= 2 else "all endpoints distinct",
            "n_outcomes": len(outs), "n_trials": ntrials, "max_cluster_trials": max_trials,
            "n_clusters": len(clusters)}


def selftest():
    cases = {
        "OMALIZUMAB (4 distinct)": [
            {"title": "Tolerance of 2000 mg 6 Weeks After Last Dose (primary)", "estimandType": "OR"},
            {"title": "Change in Allergen-specific Serum IgG4 and IgE (primary)", "estimandType": "OR"},
            {"title": "Decrease in Pn-BHR AUC of > 80% (primary)", "estimandType": "OR"},
            {"title": "Number of Participants With Anaphylaxis (primary)", "estimandType": "OR"},
        ],
        "Shared PFS x3 (poolable)": [
            {"title": "Investigator-assessed Progression Free Survival (primary)", "estimandType": "HR"},
            {"title": "Progression Free Survival by investigator (primary)", "estimandType": "HR"},
            {"title": "Progression-Free Survival (primary)", "estimandType": "HR"},
        ],
        "Mixed type same words (not poolable - type differs)": [
            {"title": "Fracture incidence (primary)", "estimandType": "OR"},
            {"title": "Fracture incidence change (primary)", "estimandType": "MD", "md": True},
        ],
        "ACR spelled-out vs abbreviated (poolable via synonym)": [
            {"title": "Percentage of Participants Achieving an American College of Rheumatology 20 response (primary)", "estimandType": "OR"},
            {"title": "Number of American College of Rheumatology 20 (ACR 20) Responders (primary)", "estimandType": "OR"},
        ],
    }
    print("=== selftest (thresh=0.5) ===")
    ok = True
    expect = {"OMALIZUMAB (4 distinct)": False, "Shared PFS x3 (poolable)": True,
              "Mixed type same words (not poolable - type differs)": False,
              "ACR spelled-out vs abbreviated (poolable via synonym)": True}
    for name, outs in cases.items():
        cl = cluster_outcomes(outs, 0.5)
        biggest = max(len(c) for c in cl)
        got = biggest >= 2
        flag = "OK" if got == expect[name] else "FAIL"
        if got != expect[name]:
            ok = False
        print(f"  [{flag}] {name}: max_cluster={biggest} poolable={got} (expect {expect[name]})")
    print("selftest", "PASSED" if ok else "FAILED")
    return ok


def main():
    if "--selftest" in sys.argv:
        sys.exit(0 if selftest() else 1)
    pattern = "*_AUTO*_FULL_REVIEW.html"
    files = sorted(glob.glob(os.path.join(HERE, pattern)))
    thresholds = [0.4, 0.5, 0.6]
    print(f"AUTO_FULL_REVIEW apps: {len(files)}  (pattern {pattern})\n")
    per_thresh = {}
    detail = {}
    for th in thresholds:
        keep = remove = 0
        removes = []
        for p in files:
            html = io.open(p, encoding="utf-8", errors="replace").read()
            r = classify(html, th)
            if r["poolable"]:
                keep += 1
            else:
                remove += 1
                removes.append({"name": os.path.basename(p), **r})
            if th == 0.5:
                detail[os.path.basename(p)] = r
        per_thresh[th] = (keep, remove)
        print(f"thresh={th}: KEEP(poolable)={keep}  REMOVE(non-poolable)={remove}")
        if th == 0.5:
            out = os.path.join(HERE, "outputs", "poolability_remove_candidates.json")
            json.dump(removes, io.open(out, "w", encoding="utf-8"), indent=1, ensure_ascii=False)
            print(f"  remove-candidates (thresh 0.5) -> {out}")
    # reason breakdown at 0.5
    from collections import Counter
    rc = Counter(d["reason"] for d in detail.values() if not d["poolable"])
    print("\nnon-poolable reason breakdown (thresh 0.5):", dict(rc))
    tc = Counter(min(d["n_trials"], 5) for d in detail.values())
    print("trial-count distribution (capped 5):", dict(sorted(tc.items())))


if __name__ == "__main__":
    main()
