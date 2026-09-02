# -*- coding: utf-8 -*-
r"""CORPUS SWEEP v2 -- trials sitting in the LOCAL snapshot, never screened, per topic.

Supersedes aact_sweep.py. Incorporates the AACT lane's postmortem in full.

WHAT CHANGED AND WHY
  1. TOKENS, NOT WHOLE STRINGS. v1 derived the entire registered name
     ('dapivirine vaginal ring'), so a trial registering 'Dapivirine' alone never matched --
     the AACT lane's defect 1 ('inclisiran sodium' vs 'Inclisiran'). Distinctiveness is now
     decided MECHANICALLY by document frequency across every intervention name in the
     registry: a token in more than DF_MAX NCTs is generic vocabulary ('ring', 'sodium',
     'injection'), a rarer one identifies a drug. No hand list of generic words.
  2. WORD-BOUNDARY MATCHING, so 'iron' cannot match 'environment'.
  3. STOPLIST widened to multi-word vehicles ('saline solution' was the lane's defect 2;
     'sterile water' and 'dextrose 5%' were gaps in mine).
  4. THE SYNONYMY CEILING IS MEASURED, NOT JUST DECLARED. Condition derivation fixes hand
     listing; it does NOT bridge synonymy -- 'Acute Coronary Syndrome' shares no token with
     'ASCVD' though one is a subset of the other. So every topic reports
     drug_matched_condition_refused: the size of its own blind spot.
  5. ORION-8 as a MUST-NOT-FIRE control: NCT03814187 is allocation=NA, SINGLE_GROUP,
     n=3275. Refusing it is CORRECT. An unfiltered hand-off would have put a single-arm
     extension into a pool of randomised effects -- the fix is a FILTERED adapter, not a
     faster pipe, and both halves must be reported together.

SNAPSHOT F:\AACT-storage\AACT\2026-08-30 -- DATA DATE 2026-08-27. Never blended with
2026-04-12 (data date 2026-04-08). NO PHASE FILTER.
"""
import io, json, os, re, sys, glob, collections

if __name__ == "__main__":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace",
                                  line_buffering=True)

AACT = os.environ.get("AACT_DIR", r"F:\AACT-storage\AACT\2026-08-30")
DATA_DATE = "2026-08-27"
REPO = os.environ.get("SSOT_REPO", r"F:\claude-temp\wt\rob-lane")
DF_LOW = int(os.environ.get("DF_LOW", "200"))    # token this rare = a drug identity
DF_MAX = int(os.environ.get("DF_MAX", "1500"))   # token in more NCTs than this = generic
CDF_MAX = int(os.environ.get("CDF_MAX", "20000"))  # MeSH term on more NCTs than this = an
                                                   # ancestor too broad to name a population

NOT_A_DRUG = re.compile(
    r"^(placebos?|standard (of )?care|usual care|control|no intervention|saline|"
    r"normal saline|saline solution|sham|best supportive care|observation|questionnaire|"
    r"education|exercise|diet|counsel|routine|blood draw|matching placebo|vehicle|"
    r"sterile water|water for injection|dextrose|glucose solution|comparator|"
    r"conventional therapy|standard therapy)\b", re.I)
DOSE = re.compile(r"\b\d+(\.\d+)?\s*(mg|mcg|µg|ug|g|ml|%|iu|units?)\b", re.I)
PAREN = re.compile(r"\s*\([^)]*\)")
TOKEN = re.compile(r"[a-z][a-z0-9\-]{2,}")
# junk that survives frequency filtering because it is genuinely rare but identifies nothing
JUNK_TOKENS = {"factor", "risk", "group", "arm", "dose", "high", "low", "study", "trial",
               "therapy", "treatment", "product", "device", "solution", "injection", "oral",
               "intravenous", "infusion", "tablet", "capsule", "ring", "gel", "film", "patch"}


def hdr_idx(path, names):
    with io.open(path, encoding="utf-8", errors="replace") as f:
        h = f.readline().rstrip("\n").split("|")
    return [h.index(n) if n in h else None for n in names]


def norm_type(ty):
    """AACT uses UNDERSCORES: COMBINATION_PRODUCT, ACTIVE_COMPARATOR, NO_INTERVENTION.
    Comparing those to spaced strings is a false absence, not a filter."""
    return (ty or "").replace("_", " ").strip().lower()


def load_all():
    ip = os.path.join(AACT, "interventions.txt")
    i = hdr_idx(ip, ["nct_id", "name", "intervention_type"])
    by_nct = collections.defaultdict(list)
    df = collections.Counter()
    iv_type = {}
    with io.open(ip, encoding="utf-8", errors="replace") as f:
        f.readline()
        for line in f:
            c = line.rstrip("\n").split("|")
            if len(c) <= max(x for x in i if x is not None):
                continue
            n, nm = c[i[0]], c[i[1]]
            by_nct[n].append((nm, c[i[2]]))
            iv_type[n] = c[i[2]]
    # THE BRAND -> GENERIC BRIDGE, and it is already in the snapshot. v2 read only
    # interventions.name and so saw "AMR101" but never "VASCEPA (icosapent ethyl)", which is
    # what reaches the other 16 icosapent trials. This table is the route from brand code to
    # INN that needed no external mapping -- found by the AACT lane's member-level calibration.
    op = os.path.join(AACT, "intervention_other_names.txt")
    if os.path.exists(op):
        o = hdr_idx(op, ["nct_id", "name"])
        with io.open(op, encoding="utf-8", errors="replace") as f:
            f.readline()
            for line in f:
                c = line.rstrip("\n").split("|")
                if len(c) > max(o) and c[o[0]]:
                    by_nct[c[o[0]]].append((c[o[1]], iv_type.get(c[o[0]], "DRUG")))
    # document frequency of each token, counted ONCE per NCT
    for n, ivs in by_nct.items():
        toks = set()
        for nm, _ in ivs:
            toks.update(TOKEN.findall(nm.lower()))
        for t in toks:
            df[t] += 1

    sp = os.path.join(AACT, "studies.txt")
    j = hdr_idx(sp, ["nct_id", "study_type", "phase", "overall_status", "enrollment"])
    st = {}
    with io.open(sp, encoding="utf-8", errors="replace") as f:
        f.readline()
        for line in f:
            c = line.rstrip("\n").split("|")
            if len(c) > max(x for x in j if x is not None):
                st[c[j[0]]] = (c[j[1]], c[j[2]], c[j[3]], c[j[4]])

    dp = os.path.join(AACT, "designs.txt")
    k = hdr_idx(dp, ["nct_id", "allocation", "intervention_model"])
    rnd, model = set(), {}
    with io.open(dp, encoding="utf-8", errors="replace") as f:
        f.readline()
        for line in f:
            c = line.rstrip("\n").split("|")
            if len(c) > max(x for x in k if x is not None):
                model[c[k[0]]] = c[k[2]]
                if "random" in c[k[1]].lower():
                    rnd.add(c[k[0]])

    # CONDITIONS VIA MeSH, not raw free text. Raw text cannot bridge synonymy: V-INCEPTION
    # registers only "Acute Coronary Syndrome", which shares no token with ASCVD though one
    # is clinically a subset of the other. AACT ships its own MeSH mapping (direct terms and
    # ancestors) and that DOES bridge it -- V-INCEPTION carries hypercholesterolemia,
    # dyslipidemias and atherosclerosis under MeSH. This uses the registry's own controlled
    # vocabulary rather than a hand-built thesaurus.
    # ⛔ mesh-list ONLY, NEVER mesh-ancestor. The ancestor rows are where the known failure
    # lives: ORION-9/10/11 carry `mesh-ancestor | Metabolic Diseases`, the exact term that
    # once merged hereditary amyloidosis with type-2 diabetes. Filtering on mesh_type
    # excludes that class BY CONSTRUCTION rather than by a frequency threshold I chose.
    # Confirmed independently by the AACT lane: mesh-list admitted 2 of 30 inclisiran
    # candidates, both correct, zero junk. 837,326 mesh-list rows vs 3,519,470 ancestors.
    cp = os.path.join(AACT, "browse_conditions.txt")
    m = hdr_idx(cp, ["nct_id", "downcase_mesh_term", "mesh_type"])
    cond = collections.defaultdict(set)
    with io.open(cp, encoding="utf-8", errors="replace") as f:
        f.readline()
        for line in f:
            c = line.rstrip("\n").split("|")
            if len(c) > max(x for x in m if x is not None) and c[m[2]] == "mesh-list":
                cond[c[m[0]]].add(c[m[1]])
    # Fall back to raw conditions ONLY for trials with no MeSH mapping at all, so a missing
    # mapping is a fallback rather than a silent exclusion.
    rp = os.path.join(AACT, "conditions.txt")
    r = hdr_idx(rp, ["nct_id", "downcase_name"])
    with io.open(rp, encoding="utf-8", errors="replace") as f:
        f.readline()
        for line in f:
            c = line.rstrip("\n").split("|")
            if len(c) > max(r) and c[r[0]] not in cond:
                cond[c[r[0]]].add(c[r[1]])
    cond_df = collections.Counter()
    for n, cs in cond.items():
        for c in cs:
            cond_df[c.strip().lower()] += 1
    return by_nct, df, st, rnd, model, cond, cond_df


ALLOWED = {"drug", "biological", "combination product", "dietary supplement", "device", "other"}


def drug_tokens(ingested, by_nct, df):
    """Distinctive TOKENS from the topic's own registered intervention names.
    Distinctive == rare in the registry. Mechanical, no hand list of generic words."""
    toks = collections.Counter()
    for n in ingested:
        for nm, ty in by_nct.get(n, []):
            if norm_type(ty) not in ALLOWED:
                continue
            # ⛔ PARENTHESES ARE NO LONGER STRIPPED BEFORE TOKENISING. v2 ran
            # PAREN.sub() first, which deleted "(ethyl icosapentate)" from
            # "AMR101 (ethyl icosapentate) - 4 g/day" -- discarding the exact token that
            # reaches 16 further trials. The generic name very often lives in the bracket.
            s = DOSE.sub(" ", nm).strip()
            if NOT_A_DRUG.match(PAREN.sub(" ", s).strip(" .,-/")):
                continue
            cands = [t for t in set(TOKEN.findall(s.lower()))
                     if t not in JUNK_TOKENS and df.get(t, 0) > 0]
            if not cands:
                continue
            # UNION OF TWO CLAUSES, because NEITHER ALONE COVERS BOTH TOPICS -- established
            # by member-level calibration with the AACT lane, not by argument:
            #   (a) RAREST TOKEN PER NAME keeps 'iron' (df 743), which IS the intervention
            #       for iv-iron-hf and which any df threshold low enough to catch generics
            #       would discard.
            #   (b) EVERY TOKEN BELOW DF_LOW keeps 'icosapentate' (5), 'vascepa' (22),
            #       'icosapent' (29) alongside 'amr101' (7) -- which clause (a) throws away
            #       because only one survives per name.
            # (b) also kills the 'placebos' (592) leak on FREQUENCY rather than on a plural
            # regex I have to get right, which is the more robust way to lose it.
            best = min(cands, key=lambda t: df.get(t, 0))
            if df.get(best, 0) <= DF_MAX:
                toks[best] += 1
            for t in cands:
                if df.get(t, 0) < DF_LOW:
                    toks[t] += 1
    return set(toks)


def condition_tokens(ingested, cond, cond_df=None, cdf_max=None):
    """WHOLE MeSH TERMS, never tokens.

    Tokenising a controlled vocabulary destroys the normalisation that makes it useful:
    splitting 'cardiovascular diseases' yielded the token 'diseases', which matched a breast
    neoplasms trial for a heart-failure topic. Only 15% of that run's hits carried any
    heart-failure term. MeSH terms are the atoms -- compare them whole.

    Broad ANCESTOR terms are then dropped by document frequency, the same mechanical rule
    used for drug tokens: 'cardiovascular diseases' sits on a large fraction of the registry
    and identifies no population, while 'heart failure' does."""
    cnt = collections.Counter()
    for n in ingested:
        for c in cond.get(n, ()):
            c = c.strip().lower()
            if len(c) >= 4:
                cnt[c] += 1
    need = max(1, (len(ingested) + 1) // 2)
    terms = {t for t, k in cnt.items() if k >= need}
    if cond_df and cdf_max:
        specific = {t for t in terms if cond_df.get(t, 0) <= cdf_max}
        # keep the most specific available rather than emptying the set
        if specific:
            terms = specific
    return terms


def main():
    print("MEASURED  AACT %s  (DATA DATE %s) -- never blended with 2026-04-12"
          % (AACT, DATA_DATE))
    print("          cmd: python aact_sweep2.py [topics...]   DF_MAX=%d" % DF_MAX)
    print("")
    by_nct, df, st, rnd, model, cond, cond_df = load_all()
    print("MEASURED  %d NCTs with interventions | %d studies | %d randomised | %d token types"
          % (len(by_nct), len(st), len(rnd), len(df)))

    # ---- MUST-NOT-FIRE control, adopted from the AACT lane ----
    o8 = "NCT03814187"
    ok_o8 = o8 not in rnd
    print("")
    print("CONTROL   MUST-NOT-FIRE  ORION-8 %s: allocation=%s model=%s n=%s"
          % (o8, "randomised" if o8 in rnd else "NOT randomised",
             model.get(o8, "?"), (st.get(o8) or ("", "", "", "?"))[3]))
    print("          refusing it is CORRECT -- a single-arm extension must not enter a pool")
    print("          of randomised effects. %s" % ("PASS" if ok_o8 else "FAIL"))

    topics = sys.argv[1:]
    if not topics:
        topics = sorted(os.path.basename(d) for d in glob.glob(os.path.join(REPO, "ssot", "*"))
                        if os.path.isdir(d) and glob.glob(os.path.join(d, "*.json")))
    print("MEASURED  topics to score: %d" % len(topics))
    print("")

    rows, skipped = [], []
    for t in topics:
        cands = [c for c in glob.glob(os.path.join(REPO, "ssot", t, "*.json"))
                 if not c.endswith(".striptest")]
        if not cands:
            skipped.append((t, "no object")); continue
        try:
            d = json.load(io.open(cands[0], encoding="utf-8"))
        except Exception as e:
            skipped.append((t, "unreadable: %s" % type(e).__name__)); continue
        ing = [x.get("nct") for x in ((d.get("inputs") or {}).get("trials") or []) if x.get("nct")]
        if not ing:
            skipped.append((t, "no ingested NCTs")); continue
        dt = drug_tokens(set(ing), by_nct, df)
        if not dt:
            skipped.append((t, "no distinctive drug token derivable")); continue
        ct = condition_tokens(set(ing), cond, cond_df, CDF_MAX)
        if not ct:
            skipped.append((t, "no shared registered condition")); continue
        drx = re.compile(r"\b(?:%s)\b" % "|".join(re.escape(x) for x in sorted(dt)), re.I)
        drug_hit = {n for n, ivs in by_nct.items() if any(drx.search(nm) for nm, _ in ivs)}
        ctset = set(ct)
        # OR across MeSH terms = the UPPER bound. For a topic whose population is an
        # INTERSECTION -- iron deficiency AND heart failure -- OR over-counts, because a
        # trial carrying only 'iron deficiencies' qualifies. The registry does not encode
        # that the topic wants both, so we report a BRACKET rather than a false-precision
        # single number: OR is the ceiling, AND-of-all-terms is the floor.
        cond_ok = {n for n in drug_hit
                   if ctset & {c.strip().lower() for c in cond.get(n, ())}}
        cond_strict = {n for n in drug_hit
                       if ctset <= {c.strip().lower() for c in cond.get(n, ())}}
        refused = drug_hit - cond_ok                      # the synonymy blind spot, measured
        interv = {n for n in cond_ok if (st.get(n) or ("",))[0].lower().startswith("interventional")}
        avail = interv & rnd
        miss = avail - set(ing)
        interv_s = {n for n in cond_strict if (st.get(n) or ("",))[0].lower().startswith("interventional")}
        miss_strict = (interv_s & rnd) - set(ing)
        p3 = [n for n in miss if (st.get(n) or ("", "", ""))[1] == "PHASE3"
              and (st.get(n) or ("", "", ""))[2] == "COMPLETED"]
        rows.append({"topic": t, "available": len(avail), "ingested": len(ing),
                     "never_screened": len(miss), "never_screened_strict": len(miss_strict),
                     "completed_p3_unseen": len(p3),
                     "drug_tokens": sorted(dt), "condition_tokens": sorted(ct),
                     "drug_matched_condition_refused": len(refused),
                     "missed": sorted(miss), "p3": sorted(p3),
                     "available_ncts": sorted(avail)})

    rows.sort(key=lambda r: -r["never_screened"])
    print("=== RANKED BY ABSOLUTE TRIALS NEVER SCREENED ===")
    print("%-34s %5s %5s %8s %8s %5s %7s"
          % ("topic", "avail", "ingst", "NEVER-hi", "NEVER-lo", "cP3", "condref"))
    for r in rows[:60]:
        print("%-34s %5d %5d %8d %8d %5d %7d"
              % (r["topic"][:34], r["available"], r["ingested"], r["never_screened"],
                 r["never_screened_strict"], r["completed_p3_unseen"],
                 r["drug_matched_condition_refused"]))
    tot = sum(r["never_screened"] for r in rows)
    print("")
    print("MEASURED  topics scored %d | skipped-and-named %d" % (len(rows), len(skipped)))
    print("MEASURED  TOTAL NEVER SCREENED: %d (OR-bound, ceiling) .. %d (AND-bound, floor)"
          % (tot, sum(r["never_screened_strict"] for r in rows)))
    print("MEASURED  total completed phase-3 never screened: %d"
          % sum(r["completed_p3_unseen"] for r in rows))
    print("MEASURED  total drug-matched-but-condition-refused (SYNONYMY BLIND SPOT): %d"
          % sum(r["drug_matched_condition_refused"] for r in rows))
    print("")
    print("SKIPPED, named not scored as zero:")
    for t, why in skipped[:25]:
        print("   %-34s %s" % (t[:34], why))
    json.dump({"data_date": DATA_DATE, "df_max": DF_MAX, "df_low": DF_LOW, "rows": rows,
               "skipped": skipped, "orion8_refused": ok_o8},
              io.open("aact_sweep2_result.json", "w", encoding="utf-8"), indent=1)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
