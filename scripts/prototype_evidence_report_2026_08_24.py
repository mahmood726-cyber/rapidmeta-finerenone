"""The EVIDENCE REPORT form, v2 -- projecting what the object HOLDS, after a blind panel.

WHY v2 EXISTS. Five reviewers across two families judged v1 on its own terms. Four of five
preferred this form to a review article. Every one of them then named the same gaps, and
when those were measured against the object THREE OF THE BIGGEST WERE NOT GAPS AT ALL --
they were projection failures in v1:

  "you completely forgot the patients"     -> population IS held, per result, on 48% of the
                                              A/B topics. v1 never read it.
  "Where is the data for the one trial?
   ... That is absurd."                    -> the estimate IS held: HR 0.84 (0.72-0.99).
                                              v1 printed the reason and withheld the number.
  "No certainty rating is held"            -> FALSE AS WRITTEN. grade lives on the OUTCOME
                                              BLOCK, not the object. v1 probed obj["grade"],
                                              found nothing, and told the reader nothing was
                                              rated when all three outcomes are rated `low`
                                              with a recorded derivation.

That last one is the serious one: v1 did not merely omit, it ASSERTED AN ABSENCE THAT WAS NOT
TRUE, because the probe guessed a key name instead of reading the schema. Same error class as
`label` vs `name` an hour earlier in this same file. Hence: every field here is read from a key
observed in the corpus, never from a key I expected to exist.

WHAT IS GENUINELY ABSENT, corpus-wide over the 50 A/B topics, and so is declared rather than
implied: arm-level event counts (0/50 under any standard name), baseline risk (0/50), absolute
effect or NNT (0/50), follow-up duration (0/50), harms (0/50). A report of benefits with no
harms and no absolute numbers must say so where a reader cannot miss it.
"""
import collections
import io
import json

REPO = r"F:\rapidmeta-ssot-shell"
SLUG = "sotagliflozin-hf"
OUT = (r"F:\claude-temp\claude\F--rapidmeta-finerenone"
       r"\e2e2a1d5-c19e-44de-90ab-690dbc5235a1\scratchpad\report_sota.txt")


def num(v):
    """Two decimals, the precision the trials themselves report.

    The pooled figures are stored at four (0.7171) and the per-trial ones at two (0.67),
    so an unformatted projection prints both side by side and invites a reader to think
    the pooled estimate is the more precise of the two. It is not; it is the same
    quantity carried at more digits than its own inputs justify.
    """
    try:
        return "%.2f" % float(v)
    except (TypeError, ValueError):
        return str(v)


def fmt(p):
    """An estimate with its interval, or None. Never computed, only read."""
    pt, lo, hi = p.get("point"), p.get("ci_low"), p.get("ci_high")
    if pt is None:
        return None
    m = p.get("measure") or ""
    if lo is None or hi is None:
        return ("%s %s" % (m, num(pt))).strip()
    return ("%s %s (%s%% CI %s to %s)"
            % (m, num(pt), p.get("ci_level") or 95, num(lo), num(hi))).strip()


# GRADE derivations are stored as the working: "start high; risk_of_bias serious (-1),
# imprecision serious (-1); total -2 -> low". That is the arithmetic of the rating, in
# field names, with an ASCII arrow. A reader needs the two REASONS, in their own words.
_DOWNGRADE = (
    ("risk_of_bias", "risk of bias in the underlying results"),
    ("risk of bias", "risk of bias in the underlying results"),
    # "imprecision -- the intervals remain wide" was MY gloss, not the data's. Three of five
    # reviewers disputed it against HR 0.72 (0.62 to 0.82) and they were right: a report that
    # says it does not interpret must not characterise its own intervals. The stored rating
    # says imprecision, so imprecision is what gets printed.
    ("imprecision", "imprecision"),
    ("inconsistency", "inconsistency between the trials"),
    ("indirectness", "indirectness -- the trials do not answer this question directly"),
    ("publication_bias", "possible publication bias"),
    ("publication bias", "possible publication bias"),
)


def why_certainty(text):
    """The reasons a rating was downgraded, in English, or None."""
    t = str(text or "").lower()
    hits = []
    for key, english in _DOWNGRADE:
        if key in t and english not in hits:
            hits.append(english)
    if not hits:
        return None
    if len(hits) == 1:
        return "Rated down for " + hits[0] + "."
    return "Rated down for " + ", ".join(hits[:-1]) + " and " + hits[-1] + "."


def dedup(seq):
    out = []
    for s in seq:
        s = " ".join(str(s or "").split())
        if s and s not in out:
            out.append(s)
    return out


def main():
    obj = json.load(open("%s\\ssot\\%s\\%s.json" % (REPO, SLUG, SLUG), encoding="utf-8"))
    L = []
    w = L.append

    trials = [t for t in (obj.get("inputs") or {}).get("trials") or [] if isinstance(t, dict)]
    by = (obj.get("results") or {}).get("by_outcome") or {}
    blocks = [(k, b) for k, b in by.items() if isinstance(b, dict)]
    names = {o.get("id"): (o.get("name") or "").strip()
             for o in (obj.get("outcomes") or []) if isinstance(o, dict)}
    rows = [r for _k, b in blocks for r in (b.get("per_trial") or []) if isinstance(r, dict)]
    _rob = obj.get("risk_of_bias")
    robs = (_rob.get("by_outcome") or {}) if isinstance(_rob, dict) else {}

    w("EVIDENCE REPORT")
    w("")
    # v1 SAID "the two phase 3 trials that supported its approval". Four of five reviewers
    # called that a regulatory claim -- which regulator, which indication -- and the object
    # holds no approval record to cite. A claim we cannot source does not go in.
    # v1 also promised "three" questions after naming two. They are now named as three.
    w("Sotagliflozin compared with placebo in two phase 3 trials. Three questions, each")
    w("answered on its own and never combined with the others:")
    w("   1. all occurrences of cardiovascular death, heart failure hospitalisation or")
    w("      urgent heart failure visit, counting repeat events;")
    w("   2. the time to the FIRST such event;")
    w("   3. the time to the first cardiovascular death, non-fatal myocardial infarction")
    w("      or non-fatal stroke.")
    w("")

    # WHO WAS STUDIED -- the single most-cited omission in the blind panel.
    w("WHO WAS STUDIED")
    pops = dedup(r.get("population") for r in rows) or dedup(t.get("population") for t in trials)
    for p in pops:
        w("   " + p)
    if not pops:
        w("   The populations are not recorded with these results.")
    w("")

    w("WHICH TRIALS")
    for t in trials:
        n = t.get("enrolled") or t.get("registration_enrolment")
        tail = []
        if n:
            tail.append("%s randomised" % n)
        if t.get("design"):
            tail.append(str(t.get("design")))
        if t.get("year"):
            tail.append(str(t.get("year")))
        w("   %-13s %-14s %s" % (str(t.get("nct") or "?"),
                                 (t.get("name") or "").strip(), "; ".join(tail)))
    dates = sorted({str(t.get("all_ranks_read_utc") or t.get("registration_read_utc") or "")[:10]
                    for t in trials} - {""})
    if dates:
        w("   Each trial's registry entry was read in full on %s, including its primary,"
          % dates[-1])
        w("   secondary and other registered outcomes, not only the outcomes used here.")
    w("")

    w("WHAT THE TRIALS REPORT")
    for oid, b in blocks:
        nm = names.get(oid, oid)
        pooled = b.get("pooled") or {}
        per = [r for r in (b.get("per_trial") or []) if isinstance(r, dict)]
        k = b.get("k")
        w(nm)
        s = fmt(pooled)
        if s and not pooled.get("withdrawn"):
            w("   Combined across %s trials: %s" % (k, s))
            het = b.get("heterogeneity") or {}
            if het.get("i2") is not None:
                w("   Between-trial variation: I-squared %s%%. With only %s trials this"
                  % (het.get("i2"), k))
                w("   statistic is very imprecise, and should not be read as evidence that")
                w("   the trials agree.")
        else:
            # v1 PRINTED THE REASON AND WITHHELD THE NUMBER. Both families called that out.
            w("   Not combined: only one of the two trials reports this endpoint.")
        for r in per:
            e = fmt(r)
            if e:
                w("      %s   %s" % (r.get("nct", "?"), e))
        g = b.get("grade") or {}
        if g.get("certainty"):
            why = why_certainty(g.get("certainty_derivation"))
            w("   Certainty in this result: %s. %s"
              % (str(g.get("certainty")).upper(), why or ""))
            # A CERTAINTY RATING THAT CITES AN ASSESSMENT NOBODY MADE FOR THIS RESULT.
            # mace3_first is rated down for risk of bias, and no risk-of-bias assessment
            # exists for mace3_first. 1 of 11 GRADE-rated outcomes corpus-wide. The report
            # cannot silently pass that on, and it is not the report's job to fix it.
            if "risk_of_bias" in str(g.get("certainty_derivation")) and oid not in robs:
                w("   Note: that downgrade cites risk of bias, but no risk-of-bias")
                w("   assessment was carried out for this particular result. The rating")
                w("   should be read as unsupported on that point until one is.")
        w("")

    w("HOW FAR THESE RESULTS CAN BE TRUSTED")
    rob = obj.get("risk_of_bias") or {}
    if robs:
        w("Risk of bias was assessed with RoB 2 separately for each reported result, rather")
        w("than once for each trial, because the same trial can be at different risk of bias")
        w("for different endpoints.")
        w("")
        # SHOW THE JUDGEMENTS, DO NOT ASSERT THEM. Every reviewer asked for this. What the
        # showing reveals is that most domains are NO INFORMATION -- the protocols were
        # never retrieved -- which is a far more useful thing for a reader to know than a
        # sentence claiming the assessment was done.
        counts = collections.Counter()
        for oid2, per_nct in robs.items():
            if not isinstance(per_nct, dict):
                continue
            for _nct, rec in per_nct.items():
                for dname, dom in ((rec or {}).get("domains") or {}).items():
                    if isinstance(dom, dict) and dom.get("judgement"):
                        counts[(dname, str(dom["judgement"]))] += 1
        seen_domains = sorted({d for d, _j in counts})
        for d in seen_domains:
            js = ", ".join("%s in %d" % (j.replace("_", " ").lower(), n)
                           for (dd, j), n in sorted(counts.items()) if dd == d)
            w("   %-34s %s" % (d.split("_", 1)[-1].replace("_", " "), js))
        nis = sum(n for (_d, j), n in counts.items() if j.upper() == "NO_INFORMATION")
        tot = sum(counts.values())
        if tot and nis:
            w("")
            w("   %d of the %d domain judgements are NO INFORMATION. That is not a finding"
              % (nis, tot))
            w("   that the trials were well or badly run: it records that neither trial's")
            w("   protocol or statistical analysis plan was obtained, so those domains")
            w("   could not be judged at all.")
    else:
        w("No risk-of-bias assessment was carried out for these results.")
    # The stored derivation reads "the printed hazard ratio, stored on the log scale with
    # the standard error its printed interval implies". Both families called that a
    # statistician's codebook note. Same fact, in a clinician's words:
    if dedup(r.get("derivation") for r in rows):
        w("")
        w("The hazard ratios above are the ones the trials themselves published. Where a")
        w("standard error was needed to combine them, it was calculated back from the")
        w("published confidence interval; no estimate here was recomputed from raw data.")
    w("")

    w("WHAT THIS REPORT DOES NOT CONTAIN")
    w("It reports relative effects only. It holds no arm-level event counts and no")
    w("control-arm event rate, and therefore no absolute risk reduction and no number")
    w("needed to treat. A hazard ratio of 0.72 cannot be turned into a benefit for a")
    w("particular patient without those figures, and they are not here.")
    w("It contains no safety or adverse-event data of any kind. Nothing here should be read")
    w("as showing that the benefits outweigh the harms, because the harms were not")
    w("collected for this report.")
    w("It does not record how long the trials followed participants.")
    w("No bibliographic database search was run. The trials were identified from named")
    w("registrations, so an eligible trial that nobody named would not appear here, and")
    w("this is not a systematic review.")
    w("No protocol was registered in advance for this report.")
    w("It reports what these two trials measured. It does not interpret those measurements,")
    w("recommend practice, or place them beside the other SGLT2 inhibitor trials.")

    out = "\n".join(L)
    io.open(OUT, "w", encoding="utf-8").write(out)
    print("words:", len(out.split()))


main()
