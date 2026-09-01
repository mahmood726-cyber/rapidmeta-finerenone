# -*- coding: utf-8 -*-
"""GAP 1 -- SENTENCE-LEVEL PROVENANCE FOR RISK OF BIAS, mechanical and measured.

WHAT THIS IS
  Given a trial report's sentences and a Cochrane RoB-1 domain, return the sentences that
  a RoB judgement in that domain would rest on. The page can then show the judgement WITH
  the sentence it came from, which is the gap.

WHY IT IS MECHANICAL AND NOT A MODEL
  It is a deterministic lexicon scorer. It makes no judgement -- it does not say low/high/
  unclear -- it only CITES. So it is not covered by the RAISE declaration rule, which binds
  anything that makes or suggests a judgement. It also never touches a number.

GROUND TRUTH
  RoBBR SSR_Cochrane_test (Lou, Tao et al., EMNLP 2025, arXiv:2411.18831), CC-BY-NC-4.0.
  Each record gives the paper's sentences, the ASPECTS a judgement must rest on, and the
  sentence indices supporting each aspect. Published metric: aspect coverage of a k-sentence
  selection, with the dataset carrying its own optimal-k.

THREE CONTROLS SHIP WITH IT, because a detector that has only ever returned negatives is
indistinguishable from a broken one:
  MUST-FIRE   an unmistakable allocation sentence must be selected for its own domain.
  MUST-NOT    an unrelated sentence must not outrank it.
  RANDOM      a random-selection baseline, so a good-looking score can be compared to chance.
"""
import io, json, os, random, re, sys

# GUARDED. An unguarded module-level reassignment closes the caller's stdout wrapper on
# plain import -- it broke the very next script that imported this one. Only reconfigure
# when run as a script.
if __name__ == "__main__":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace",
                                  line_buffering=True)

ROBBR_DIR = os.environ.get("ROBBR_DIR", "robbr")
SSR = os.path.join(ROBBR_DIR, "SSR_Cochrane_test.json")

# ---------------------------------------------------------------- domain cue lexicon
# Keyed on the RoB-1 domain, which the Handbook fixes -- NOT on the clinical topic. The
# same lexicon serves cardiology, HIV and malaria without being redone, which is the bar.
DOMAIN_CUES = {
    "random_sequence": (
        r"random(?:is|iz)ation|random(?:ly)? (?:assigned|allocated|generated)|"
        r"random number|computer[- ]generated|permuted block|block random|"
        r"stratified random|coin toss|random sequence|randomisation schedule|"
        r"randomization schedule|simple randomi"),
    "allocation_concealment": (
        r"allocation concealment|concealed allocation|sealed (?:opaque )?envelope|"
        r"opaque envelope|central(?:ised|ized)? (?:randomi|allocation)|"
        r"pharmacy[- ]controlled|sequentially numbered|allocation (?:was )?conceal|"
        r"web[- ]based (?:computer )?system|interactive voice response|telephone randomi"),
    "blinding_participants": (
        r"double[- ]blind|single[- ]blind|triple[- ]blind|"
        r"participants? (?:and|,)? ?(?:personnel|investigators?|clinicians?)? ?(?:were |was )?blind|"
        r"blinded to (?:the )?(?:treatment|allocation|intervention|group)|"
        r"placebo[- ]controlled|identical (?:in )?appearance|matching placebo|"
        r"masked|open[- ]label|unblinded"),
    "blinding_outcome": (
        r"outcome assessors?|assessors? (?:were |was )?blind|blinded (?:outcome )?assessment|"
        r"blinded to (?:group|allocation|treatment) assignment|independent (?:review|adjudicat)|"
        r"adjudicat(?:ion|ed) committee|end ?point committee|central(?:ly)? adjudicat|"
        r"statistician (?:was )?blind|radiologist (?:was )?blind"),
    "incomplete_outcome": (
        r"intention[- ]to[- ]treat|\bITT\b|per[- ]protocol|lost to follow[- ]?up|"
        r"withdraw|drop[- ]?out|discontinu|missing data|attrition|"
        r"imputation|last observation carried forward|\bLOCF\b|"
        r"completed the (?:study|trial)|available for analysis|analysed"),
    "selective_reporting": (
        r"(?:pre)?(?:-)?specified (?:primary |secondary )?outcome|protocol|"
        r"registered|registration|trial registry|clinicaltrials\.gov|ISRCTN|"
        r"primary (?:end ?point|outcome)|secondary (?:end ?point|outcome)|"
        r"outcomes? (?:were )?reported"),
}
# Generic methods-section cues -- weak signal, present in every domain.
GENERIC = re.compile(r"\bmethods?\b|\btrial\b|\bstudy\b|\bgroup(?:s)?\b|\ballocat|\bassign",
                     re.I)

COMPILED = {k: re.compile(v, re.I) for k, v in DOMAIN_CUES.items()}


def domain_key(bias_string):
    """Map a RoBBR bias label onto a lexicon key. Returns None when unmapped -- and an
    unmapped domain is REPORTED, never silently scored as zero."""
    b = (bias_string or "").lower()
    if "random sequence" in b:
        return "random_sequence"
    if "allocation concealment" in b:
        return "allocation_concealment"
    if "blinding of outcome" in b or "detection bias" in b:
        return "blinding_outcome"
    if "blinding of participants" in b or "performance bias" in b:
        return "blinding_participants"
    if "incomplete outcome" in b or "attrition" in b:
        return "incomplete_outcome"
    if "selective report" in b or "reporting bias" in b:
        return "selective_reporting"
    return None


def score_sentences(sentences, key, cues=None):
    """Deterministic score per sentence. cues param exists so the defect can be PLANTED."""
    table = cues if cues is not None else COMPILED
    pat = table.get(key)
    out = []
    for i, s in enumerate(sentences):
        if not isinstance(s, str):
            out.append((i, 0.0))
            continue
        strong = len(pat.findall(s)) if pat else 0
        weak = len(GENERIC.findall(s))
        # length normalisation keeps a long paragraph from winning on volume alone
        n = max(20.0, len(s)) ** 0.5
        out.append((i, (3.0 * strong + 0.25 * weak) / n))
    return out


def select(sentences, key, k=3, cues=None):
    sc = score_sentences(sentences, key, cues)
    sc.sort(key=lambda t: (-t[1], t[0]))          # deterministic tie-break on index
    return [i for i, v in sc[:k] if v > 0]


# ---------------------------------------------------------------- evaluation
def coverage(selected, aspect2idx):
    """Published metric shape: fraction of ASPECTS with >=1 supporting sentence selected."""
    if not aspect2idx:
        return None
    sel = set(selected)
    hit = sum(1 for a, idxs in aspect2idx.items() if sel & set(idxs))
    return hit / float(len(aspect2idx))


def evaluate(records, k=3, cues=None, seed=None):
    rnd = random.Random(seed)
    covs, rands, opts, unmapped = [], [], [], 0
    for r in records:
        pool = r.get("paper_as_candidate_pool") or []
        a2i = {a: list(v) for a, v in (r.get("aspect2sentence_indices") or {}).items()}
        if not pool or not a2i:
            continue
        key = domain_key(r.get("bias"))
        if key is None:
            unmapped += 1
            continue
        c = coverage(select(pool, key, k, cues), a2i)
        if c is None:
            continue
        covs.append(c)
        if seed is not None:
            rands.append(coverage(rnd.sample(range(len(pool)), min(k, len(pool))), a2i))
        o = (r.get("bias_retrieval_at_optimal_evaluation") or {}).get("optimal")
        if isinstance(o, int):
            opts.append(o)
    return {
        "n": len(covs),
        "coverage_at_k": sum(covs) / len(covs) if covs else 0.0,
        "full_coverage_rate": sum(1 for c in covs if c >= 1.0) / float(len(covs)) if covs else 0.0,
        "random_baseline": (sum(rands) / len(rands)) if rands else None,
        "median_optimal_k": sorted(opts)[len(opts) // 2] if opts else None,
        "unmapped_domains": unmapped,
    }


def main():
    recs = list(json.load(io.open(SSR, encoding="utf-8")).values())
    print("MEASURED  SSR_Cochrane_test records: %d" % len(recs))
    print("          cmd: python rob_provenance.py")
    doms = {}
    for r in recs:
        doms[domain_key(r.get("bias"))] = doms.get(domain_key(r.get("bias")), 0) + 1
    print("MEASURED  domain coverage of the lexicon: %s" % doms)
    print("")

    # ---------- CONTROL 1: MUST-FIRE ----------
    print("CONTROL 1  MUST-FIRE -- an unmistakable sentence must be selected for its domain")
    probe = [
        "Patients presented to the clinic between January and March.",
        "The primary endpoint was death from any cause at 12 months.",
        "Randomisation was performed using a computer-generated random number sequence.",
        "Baseline characteristics were similar between the two groups.",
    ]
    got = select(probe, "random_sequence", k=1)
    ok1 = got == [2]
    print("          selected index %s, expected [2] -- %s" % (got, "PASS" if ok1 else "FAIL"))

    print("CONTROL 2  MUST-NOT -- allocation concealment must pick the envelope sentence")
    probe2 = [
        "The trial was funded by a university grant.",
        "Allocation was concealed using sequentially numbered, sealed opaque envelopes.",
        "Mean age was 61 years.",
    ]
    got2 = select(probe2, "allocation_concealment", k=1)
    ok2 = got2 == [1]
    print("          selected index %s, expected [1] -- %s" % (got2, "PASS" if ok2 else "FAIL"))
    print("")

    # ---------- the real measurement ----------
    print("MEASURED  scoring against the benchmark, k=3, with a random baseline")
    res = evaluate(recs, k=3, seed=20260901)
    print("          records scored          : %d" % res["n"])
    print("          unmapped domains        : %d" % res["unmapped_domains"])
    print("          median optimal k        : %s" % res["median_optimal_k"])
    print("          ASPECT COVERAGE @3      : %.3f" % res["coverage_at_k"])
    print("          random baseline @3      : %.3f" % (res["random_baseline"] or 0))
    print("          all-aspects-covered rate: %.3f" % res["full_coverage_rate"])
    lift = res["coverage_at_k"] - (res["random_baseline"] or 0)
    print("          LIFT OVER CHANCE        : %+.3f" % lift)
    print("")

    # ---------- CONTROL 3: PLANT THE DEFECT ----------
    print("CONTROL 3  PLANT THE DEFECT -- empty the lexicon; the score MUST collapse to chance")
    broken = {k: re.compile(r"(?!x)x") for k in COMPILED}          # matches nothing
    bres = evaluate(recs, k=3, cues=broken, seed=20260901)
    print("          coverage with lexicon destroyed: %.3f (was %.3f)"
          % (bres["coverage_at_k"], res["coverage_at_k"]))
    collapsed = bres["coverage_at_k"] < res["coverage_at_k"] - 0.05
    print("          collapse observed: %s" % ("YES" if collapsed else "NO -- CHECK IS INERT"))

    print("           RESTORE and assert the original score returns")
    rres = evaluate(recs, k=3, seed=20260901)
    restored = abs(rres["coverage_at_k"] - res["coverage_at_k"]) < 1e-9
    print("          restored coverage: %.3f -- %s"
          % (rres["coverage_at_k"], "PASS" if restored else "FAIL"))
    print("")

    allok = ok1 and ok2 and collapsed and restored
    print("VERDICT   controls %s" % ("ALL PASS" if allok else "FAILED -- do not trust the number"))
    json.dump({"k3": res, "planted": bres, "controls_pass": bool(allok)},
              io.open("rob_provenance_result.json", "w", encoding="utf-8"), indent=1)
    return 0 if allok else 1


if __name__ == "__main__":
    raise SystemExit(main())
