"""Does every trial a page names actually study the drug the page is about?

THE CLASS MAHMOOD CARES MOST ABOUT, because he found it himself in his own flagship: HELIOS-B
keyed to a hydrocephalus shunt trial, and a later comparator sweep found 107 trial-identity
mismatches including transpositions.

The panel found another. CEFEPIME_TAZ_AUTO_FULL_REVIEW is about cefepime-TAZOBACTAM and names
two trials:

    NCT02497781  ceftazidime-avibactam compared with cefepime in children -- cefepime is the
                 COMPARATOR arm, and the subject drug is a different combination entirely
    NCT03840148  cefepime/VNRX-5133, which is TANIBORBACTAM, not tazobactam

Neither studies the subject drug, and the page says "What was found. 2 registered trials".
The correct trial exists: NCT03630081, WCK 4282 (FEP-TAZ), Wockhardt, n=1004, cefepime-
tazobactam versus meropenem in complicated UTI. So this is a MATCHING failure, not an absence
of evidence -- the page had a real trial available and named two wrong ones instead.

SWEEP THE CLASS, NOT THE INSTANCE. If two got through, more will have. 422 trial records
across 349 distinct NCT ids, and each record carries `label` -- the ClinicalTrials.gov
officialTitle -- so most of this is answerable without a single API call.

WHAT THIS DOES AND DOES NOT CLAIM. It produces CANDIDATES, not findings. A page-trial pair is
a candidate when the subject drug's name appears in NONE of the trial's official title, its
arms, or its registered conditions. That is a strong hint and a weak proof: drugs carry code
names (WCK 4282), brand names, and salt forms, and a trial can name its drug only in a field
this object does not store. Every candidate is adjudicated against the registration before it
is called a defect. Six instruments over-flagged on 2026-08-25 alone; this one is built
assuming it will too.

CLASS TOPICS ARE EXCLUDED BY DESIGN. SGLT2, DOAC, PCSK9 and the like name a drug CLASS, and
their trials correctly study members whose names share nothing with the class label. Including
them would generate a flood of false candidates and drown the real ones.
"""
import io
import json
import os
import re
import sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(REPO, "scripts"))
import instrument_controls

# Topics naming a drug CLASS or a procedure rather than one molecule. A trial of
# dapagliflozin correctly shares no token with "SGLT2", so these cannot be checked this way.
CLASS_TOPICS = re.compile(
    r"sglt2|doac|pcsk9|arni|nma|antiplatelet|anticoagul|vaccine|ablation|statin|"
    r"incretin|antiviral|antigen|prep\b|dapt|iron|rhythm|intensive|bp\b|"
    r"colchicine_(cvd|periprocedural|stroke|pad)|covid19|umbrella", re.I)

STOP = {"auto", "full", "review", "ssot", "html", "the", "and", "vs", "versus", "in",
        "for", "of", "cv", "hf", "hfref", "hfpef", "ckd", "af", "vte", "acs", "taz",
        "lipid", "kidney", "extended", "prophylaxis", "treatment", "infection", "infect",
        "cabp", "cap", "cdi", "cdiff", "ciai", "urinary", "tract", "pah", "children",
        "adults", "mixed", "dyslipidemia", "hypertension", "htn", "ocular", "auto2"}


def subject_tokens(page):
    """Drug-name tokens from the page name. Short and junk tokens are dropped."""
    base = re.sub(r"\.html$", "", page)
    parts = [p.lower() for p in re.split(r"[_\-]", base)]
    return [p for p in parts if len(p) >= 5 and p not in STOP]


def trial_haystack(t):
    """Everything the object records that could name the trial's intervention."""
    bits = [str(t.get("label") or ""), str(t.get("name") or "")]
    for k in ("arms", "registered_conditions", "interventions"):
        v = t.get(k)
        if isinstance(v, (list, tuple)):
            bits.extend(str(x) for x in v)
        elif v:
            bits.append(str(v))
    return " ".join(bits).lower()


def examine_pair(page, trial):
    """(is_candidate, subject_token_that_is_absent, what the trial says).

    Only meaningful where the object records SOMETHING about the trial's identity. A trial
    record with no label, no arms and no conditions cannot be checked, and is reported as
    UNCHECKABLE rather than as clean -- an absence of evidence is not evidence of a match.
    """
    hay = trial_haystack(trial)
    if len(hay.strip()) < 20:
        return None, "", ""
    toks = subject_tokens(page)
    if not toks:
        return None, "", ""
    for tok in toks:
        # a 5+ char drug token appearing nowhere in title, arms or conditions
        if tok[:6] not in hay:
            return True, tok, hay[:150]
    return False, "", ""


def control():
    """Positive: the adjudicated CEFEPIME pair. Negative: a page whose trials do match."""
    pmap = json.load(io.open(os.path.join(REPO, "ssot", "PAGE_MAP.json"), encoding="utf-8"))
    pos_page = "CEFEPIME_TAZ_AUTO_FULL_REVIEW.html"
    o = json.load(io.open(os.path.join(REPO, pmap[pos_page]), encoding="utf-8"))
    trials = (o.get("inputs") or {}).get("trials") or []
    pos = any(examine_pair(pos_page, t)[0] for t in trials)

    # A trial that plainly names its drug in the title must NOT be flagged.
    neg_ok = examine_pair(
        "TIGECYCLINE_CIAI_SSOT.html",
        {"label": "A Study of Tigecycline Versus Imipenem in Complicated Intra-Abdominal "
                  "Infection", "registered_conditions": ["Intraabdominal Infections"]})[0]

    instrument_controls.require_controls(
        "trial-identity-mismatch",
        ("CEFEPIME_TAZ, whose two trials study ceftazidime-avibactam and cefepime/"
         "VNRX-5133 -- adjudicated CONFIRMED/HIGH against the registrations", pos, True),
        ("a tigecycline trial whose official title names tigecycline", neg_ok, True))
    return True


def main():
    control()
    pmap = json.load(io.open(os.path.join(REPO, "ssot", "PAGE_MAP.json"), encoding="utf-8"))
    cands, checked, uncheckable, skipped_class, pages = [], 0, 0, 0, 0
    for page in sorted(pmap):
        path = os.path.join(REPO, pmap[page])
        if not os.path.exists(path):
            continue
        if CLASS_TOPICS.search(page):
            skipped_class += 1
            continue
        try:
            o = json.load(io.open(path, encoding="utf-8"))
        except Exception:
            continue
        trials = (o.get("inputs") or {}).get("trials") or []
        if not trials:
            continue
        pages += 1
        for t in trials:
            if not isinstance(t, dict):
                continue
            bad, tok, hay = examine_pair(page, t)
            if bad is None:
                uncheckable += 1
                continue
            checked += 1
            if bad:
                cands.append({"page": page, "nct": t.get("nct") or t.get("trial_id"),
                              "subject_token_absent": tok,
                              "trial_says": hay})

    print()
    print("pages checked (drug-named topics only) : %d   (%d class/procedure topics skipped)"
          % (pages, skipped_class))
    print("trial records comparable               : %d" % checked)
    print("trial records with nothing to compare  : %d   <- UNCHECKABLE, not clean"
          % uncheckable)
    print("CANDIDATE mismatches                   : %d   on %d page(s)"
          % (len(cands), len(set(c["page"] for c in cands))))
    print()
    for c in cands:
        print("  %-40s %s   subject token %r absent"
              % (c["page"][:38], c["nct"], c["subject_token_absent"]))
        print("       trial says: %s" % c["trial_says"][:120])
    out = os.path.join(REPO, "outputs", "trial_identity_candidates_2026_08_25.json")
    json.dump({"pages_checked": pages, "records_comparable": checked,
               "records_uncheckable": uncheckable, "candidates": cands},
              io.open(out, "w", encoding="utf-8"), indent=1)
    print()
    print("written: %s" % os.path.relpath(out, REPO))
    print("These are CANDIDATES. Each is adjudicated against the registration before it is "
          "called a defect.")
    return 1 if cands else 0


if __name__ == "__main__":
    sys.exit(main())
