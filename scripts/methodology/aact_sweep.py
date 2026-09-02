# -*- coding: utf-8 -*-
r"""CORPUS SWEEP: how many randomised trials sit in the LOCAL snapshot, unscreened, per topic.

⛔ THE DRUG EXPRESSION IS DERIVED FROM THE TOPIC'S OWN REGISTERED INTERVENTION NAMES,
   NEVER FROM ITS TITLE. For each ingested NCT we read what that trial actually registered in
   AACT `interventions.name`, and build the match from those strings. A title-derived term is
   a guess about identity; a registered name is the registry's own word for the thing.
   The matched names are PRINTED PER TOPIC so the expression can be audited by eye --
   a plausible large number is this project's commonest failure mode.

Snapshot default F:\AACT-storage\AACT\2026-08-30 -- DATA DATE 2026-08-27. Cite the data
date, never the folder date. NO PHASE FILTER (NCT01539226 is registered phase=NA).
"""
import io, json, os, re, sys, glob, collections

if __name__ == "__main__":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace",
                                  line_buffering=True)

AACT = os.environ.get("AACT_DIR", r"F:\AACT-storage\AACT\2026-08-30")
DATA_DATE = "2026-08-27"
# THE REPO THIS SCRIPT LIVES IN, not an absolute path into another lane working copy.
# The default was a scratch path under another lane worktree -- a DIFFERENT lane checkout, measured at
# 103 commits behind main with 23 uncommitted files. It happened to be equivalent for
# every field this sweep reads and would not have stayed so; a fresh clone could not
# run this at all; and on this machine it read another lane tree in the shared scratch
# root, which is what gate9 refuses. SSOT_REPO is kept, so anyone setting it is
# unaffected.
REPO = os.environ.get("SSOT_REPO", os.path.abspath(
    os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..")))

# Names that identify no drug. Matching on these would pull in the whole registry.
NOT_A_DRUG = re.compile(
    r"^(placebo|standard (of )?care|usual care|control|no intervention|saline|"
    r"normal saline|sham|best supportive care|observation|questionnaire|education|"
    r"exercise|diet|counsel|routine|blood draw|matching placebo|vehicle)\b", re.I)
# Strip dose/formulation noise so "empagliflozin 10 mg" and "Empagliflozin" unify.
DOSE = re.compile(r"\b\d+(\.\d+)?\s*(mg|mcg|µg|ug|g|ml|%|iu|units?)\b.*$", re.I)
PAREN = re.compile(r"\s*\([^)]*\)")


def hdr_idx(path, names):
    with io.open(path, encoding="utf-8", errors="replace") as f:
        h = f.readline().rstrip("\n").split("|")
    return [h.index(n) if n in h else None for n in names]


def load_interventions():
    p = os.path.join(AACT, "interventions.txt")
    inct, iname, itype = hdr_idx(p, ["nct_id", "name", "intervention_type"])
    by_nct = collections.defaultdict(list)
    rows = []
    with io.open(p, encoding="utf-8", errors="replace") as f:
        f.readline()
        for line in f:
            c = line.rstrip("\n").split("|")
            if len(c) <= max(inct, iname):
                continue
            n, nm = c[inct], c[iname]
            ty = c[itype] if itype is not None and len(c) > itype else ""
            by_nct[n].append((nm, ty))
            rows.append((n, nm))
    return by_nct, rows


def load_studies():
    p = os.path.join(AACT, "studies.txt")
    i = hdr_idx(p, ["nct_id", "study_type", "phase", "overall_status", "enrollment"])
    out = {}
    with io.open(p, encoding="utf-8", errors="replace") as f:
        f.readline()
        for line in f:
            c = line.rstrip("\n").split("|")
            if len(c) <= max(x for x in i if x is not None):
                continue
            out[c[i[0]]] = (c[i[1]], c[i[2]], c[i[3]], c[i[4]])
    return out


def load_randomised():
    p = os.path.join(AACT, "designs.txt")
    i = hdr_idx(p, ["nct_id", "allocation"])
    s = set()
    with io.open(p, encoding="utf-8", errors="replace") as f:
        f.readline()
        for line in f:
            c = line.rstrip("\n").split("|")
            if len(c) > max(i) and "random" in c[i[1]].lower():
                s.add(c[i[0]])
    return s


ALLOWED_TYPES = {"drug", "biological", "combination product", "dietary supplement", "device"}


def norm_type(ty):
    """AACT writes COMBINATION_PRODUCT with an UNDERSCORE. Comparing against
    'combination product' with a space rejected every dapivirine intervention and scored a
    working topic as unmeasurable. Normalise before comparing -- a format mismatch is not
    an absence."""
    return (ty or "").replace("_", " ").strip().lower()


def load_conditions():
    p = os.path.join(AACT, "conditions.txt")
    i = hdr_idx(p, ["nct_id", "downcase_name"])
    by = collections.defaultdict(set)
    with io.open(p, encoding="utf-8", errors="replace") as f:
        f.readline()
        for line in f:
            c = line.rstrip("\n").split("|")
            if len(c) > max(i):
                by[c[i[0]]].add(c[i[1]])
    return by


def condition_terms(ingested, by_cond):
    """The population, derived from the registry the same way the drug is.

    A term must be registered by a MAJORITY of the topic's own trials. Majority not
    intersection: one trial labelling itself idiosyncratically must not empty the set, and
    one trial's stray condition must not widen it to the whole registry."""
    cnt = collections.Counter()
    for n in ingested:
        for c in by_cond.get(n, ()):
            c = PAREN.sub("", c).strip(" .,-")
            if len(c) >= 3:
                cnt[c] += 1
    need = max(1, (len(ingested) + 1) // 2)
    terms = {c for c, k in cnt.items() if k >= need}
    keep = set()
    for t in sorted(terms, key=len):
        if not any(k in t for k in keep):
            keep.add(t)
    return keep


def drug_terms(ingested, by_nct):
    """The registered intervention names of the trials WE ingested -> the match expression."""
    terms = set()
    seen_raw = []
    for n in ingested:
        for nm, ty in by_nct.get(n, []):
            seen_raw.append((n, nm, ty))
            if norm_type(ty) not in ALLOWED_TYPES:
                continue
            s = PAREN.sub("", DOSE.sub("", nm)).strip(" .,-/")
            if not s or NOT_A_DRUG.match(s) or len(s) < 4:
                continue
            # keep the head token when the name is a phrase like "Ferric carboxymaltose injection"
            terms.add(s.lower())
    # collapse terms that contain one another (keep the shortest distinctive form)
    keep = set()
    for t in sorted(terms, key=len):
        if not any(k in t for k in keep):
            keep.add(t)
    return keep, seen_raw



def topic_object(repo, t):
    """The topic object BY NAME, never whichever file glob yielded first.

    Extracted so a plant can EXERCISE THIS CODE rather than reimplement it: an inline
    expression cannot have a control, and a control that re-derives the defect tests
    only its own copy. A THING WITH A NAME CAN HAVE A PLANT.

    Four topic dirs hold several JSONs. For empagliflozin-hf-auto-full-review the first
    was ADJUDICATION-RECORD.json, which has no inputs.trials, so a NON-EMPTY topic was
    skipped as "no ingested NCTs" and its trials left the corpus silently. The other
    three survived by ALPHABETICAL LUCK. sorted(cands)[0] would be deterministic and
    would CEMENT the wrong file: A DETERMINISM FIX CAN MAKE A WRONG ANSWER REPRODUCIBLE.
    """
    cands = [c for c in glob.glob(os.path.join(repo, "ssot", t, "*.json"))
             if not c.endswith(".striptest")]
    if not cands:
        return None
    named = os.path.join(repo, "ssot", t, t + ".json")
    return named if named in cands else sorted(cands)[0]

def main():
    topics = sys.argv[1:] or ["agyw-hiv-prep-review", "sglt2-hf", "iv-iron-hf"]
    print("MEASURED  AACT %s  (DATA DATE %s)" % (AACT, DATA_DATE))
    print("          cmd: python aact_sweep.py %s" % " ".join(topics))
    print("          NO phase filter. Drug expression derived from REGISTERED names only.")
    print("")
    by_nct, _ = load_interventions()
    st = load_studies()
    rnd = load_randomised()
    by_cond = load_conditions()
    print("MEASURED  AACT rows loaded: %d NCTs with interventions, %d studies, %d randomised"
          % (len(by_nct), len(st), len(rnd)))
    print("")

    results = []
    for t in topics:
        cand = glob.glob(os.path.join(REPO, "ssot", t, "*.json"))
        cand = [c for c in cand if not c.endswith(".striptest")]
        if not cand:
            print("  %-26s NO OBJECT FOUND -- skipped and reported, not scored 0" % t)
            continue
        _pick = topic_object(REPO, t)
        d = json.load(io.open(_pick, encoding="utf-8"))
        ing = [x.get("nct") for x in ((d.get("inputs") or {}).get("trials") or []) if x.get("nct")]
        if not ing:
            print("  %-26s NO INGESTED NCTs -- skipped and reported" % t)
            continue
        terms, raw = drug_terms(set(ing), by_nct)
        if not terms:
            print("  %-26s NO DRUG-TYPE INTERVENTION NAMES on its own trials -- cannot derive"
                  " an expression; reported, not scored" % t)
            continue
        conds = condition_terms(set(ing), by_cond)
        if not conds:
            print("  %-26s NO SHARED REGISTERED CONDITION across its own trials -- the"
                  " population cannot be defined; reported, not scored" % t)
            continue
        rx = re.compile("|".join(re.escape(x) for x in sorted(terms)), re.I)
        crx = re.compile("|".join(re.escape(x) for x in sorted(conds)), re.I)
        matched = {n for n, ivs in by_nct.items() if any(rx.search(nm) for nm, _ in ivs)}
        # ⛔ CONDITION RESTRICTION. Without it this counted every dapagliflozin trial in
        # diabetes and CKD as an unscreened HEART FAILURE trial -- 846 of them. The drug
        # alone is not the population when a drug has several indications.
        matched = {n for n in matched if any(crx.search(c) for c in by_cond.get(n, ()))}
        interv = {n for n in matched if (st.get(n) or ("",))[0].lower().startswith("interventional")}
        available = interv & rnd
        missed = available - set(ing)
        results.append((len(missed), t, ing, terms, conds, available, missed))

    results.sort(reverse=True)
    print("=== RANKED BY ABSOLUTE TRIALS NEVER SCREENED ===")
    print("")
    for nmiss, t, ing, terms, conds, available, missed in results:
        print("  %-26s available %3d | ingested %2d | NEVER SCREENED %3d | ingestion recall %.3f"
              % (t, len(available), len(ing), nmiss, len(set(ing) & available) / float(max(1, len(available)))))
        print("      drug terms   (registered): %s" % ", ".join(sorted(terms))[:130])
        print("      condition    (registered): %s" % ", ".join(sorted(conds))[:130])
        p3 = [n for n in missed if (st.get(n) or ("", "", "", ""))[1] == "PHASE3"
              and (st.get(n) or ("", "", "", ""))[2] == "COMPLETED"]
        print("      completed PHASE3 never screened: %d %s"
              % (len(p3), sorted(p3)[:6] if p3 else ""))
        print("")
    json.dump([{"topic": t, "available": sorted(a), "ingested": sorted(i),
                "missed": sorted(m), "drug_terms": sorted(x), "condition_terms": sorted(cc)}
               for _, t, i, x, cc, a, m in results],
              io.open("aact_sweep_result.json", "w", encoding="utf-8"), indent=1)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
