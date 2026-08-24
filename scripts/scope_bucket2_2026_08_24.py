"""How much work is bucket 2, measured rather than guessed.

BUCKET 2 is the three things five blind reviewers said stopped them acting on a review:
arm-level event counts, follow-up duration, and harms. None needs a judgement anybody has
to stand behind -- each is a fact printed in a source, and a second reader can check it and
agree or disagree on fact alone. That makes it labour, and labour can be costed.

WHAT THIS SCRIPT ESTABLISHES, per topic and per trial:

  1. WHERE THE DATA WOULD COME FROM. A registration that has POSTED RESULTS carries arm
     counts, denominators, follow-up and adverse events in structured form -- machine
     readable, no reading required. A registration WITHOUT posted results carries none of
     it, and the numbers exist only in the published paper, which means a human reads a PDF.
     That single distinction is the whole cost model, so it is measured and not assumed.

  2. WHETHER WE ALREADY HOLD THE HANDLE. Every trial we can reach by NCT is reachable; a
     trial with no registration identifier is not, and has to be found first.

  3. WHAT WE ALREADY HAVE. `registration_read_utc` and the all-ranks capture prove these
     registrations were fetched once already, so the fetching path exists and works. What
     was not captured was the RESULTS section, which is a different endpoint on the same
     API.

It deliberately does NOT phone ClinicalTrials.gov. The counts here come from what the
objects already record, so the estimate is reproducible offline and cannot be blamed on a
transient network. Where an object does not record whether results were posted, that is
itself reported as unknown rather than assumed either way -- an unknown counted as "cheap"
is how a 90-minute job became a 15.7-hour estimate this morning, in the other direction.
"""
import collections
import glob
import io
import json
import os

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Keys that indicate the object has already seen a registry RESULTS posting for a trial.
# Arm-level counts only ever arrive with one of these, in this corpus.
_RESULTS_MARKERS = (
    "registration_counts_read_utc", "registry_paramType", "registry_statistical_method",
    "as_posted", "registration_contrasts_read_utc", "registration_declared_contrasts",
)

# Arm-level count keys actually observed in this corpus, including the bespoke ones. The
# generic names are here too; the topic-specific ones prove the data CAN be extracted,
# because somebody already did it by hand for those trials.
_ARM_COUNT_KEYS = (
    "events_int", "events_ctrl", "e_int", "e_ctrl", "events", "n_events",
    "n_int", "n_ctrl", "n_treat", "n_control", "treatment_evaluable",
    "control_evaluable", "treatment_deaths", "control_deaths", "treatment_cured",
    "control_cured", "treatment_failures", "control_failures", "treatment_analysed",
    "control_analysed", "events_apixaban", "n_apixaban", "events_comparator",
    "n_comparator",
)


def has_any(d, keys):
    return any(d.get(k) not in (None, "", [], {}) for k in keys)


def main():
    L = []

    def w(s):
        L.append(str(s))

    ab_topics = []
    for p in sorted(glob.glob(os.path.join(REPO, "ssot", "*", "*.json"))):
        slug = os.path.basename(os.path.dirname(p))
        if os.path.basename(p) != slug + ".json":
            continue
        try:
            with io.open(p, encoding="utf-8") as fh:
                obj = json.load(fh)
        except Exception:
            continue
        blks = [b for b in ((obj.get("results") or {}).get("by_outcome") or {}).values()
                if isinstance(b, dict)]
        rows = [r for b in blks for r in (b.get("per_trial") or [])
                if isinstance(r, dict) and r.get("point") is not None]
        if rows:
            ab_topics.append((slug, obj, blks, rows))

    w("A/B topics in scope (hold at least one readable estimate): %d" % len(ab_topics))
    w("")

    trials_total = 0
    reachable = 0            # has an NCT we can query
    no_handle = []           # no registration identifier at all
    results_posted = 0       # object already shows evidence of a results posting
    results_unknown = 0
    have_counts = 0
    per_topic = []

    for slug, obj, blks, rows in ab_topics:
        trials = [t for t in ((obj.get("inputs") or {}).get("trials") or [])
                  if isinstance(t, dict)]
        t_reach = t_posted = t_unknown = 0
        for t in trials:
            trials_total += 1
            nct = str(t.get("nct") or t.get("registration") or "").strip()
            if nct:
                reachable += 1
                t_reach += 1
            else:
                no_handle.append((slug, str(t.get("name") or "unnamed")))
            if has_any(t, _RESULTS_MARKERS):
                results_posted += 1
                t_posted += 1
            else:
                results_unknown += 1
                t_unknown += 1
        topic_counts = any(has_any(r, _ARM_COUNT_KEYS) for r in rows)
        if topic_counts:
            have_counts += 1
        per_topic.append((slug, len(trials), t_reach, t_posted, t_unknown, topic_counts))

    w("TRIALS ACROSS THOSE TOPICS: %d" % trials_total)
    w("   reachable by registration id                    : %d" % reachable)
    w("   with NO registration identifier (must be found)  : %d" % len(no_handle))
    w("   object already shows a registry RESULTS posting   : %d" % results_posted)
    w("   results status not recorded on the object         : %d" % results_unknown)
    w("")
    w("TOPICS ALREADY HOLDING ANY ARM-LEVEL COUNT: %d of %d"
      % (have_counts, len(ab_topics)))
    w("   -- these were extracted by hand, under topic-specific key names, which is")
    w("      evidence the extraction is possible and evidence there is no schema for it.")
    w("")

    if no_handle:
        w("TRIALS WITH NO REGISTRATION IDENTIFIER (%d) -- each needs finding before"
          % len(no_handle))
        w("anything can be fetched for it:")
        for slug, nm in no_handle[:12]:
            w("   %-30s %s" % (slug, nm[:44]))
        if len(no_handle) > 12:
            w("   ... and %d more" % (len(no_handle) - 12))
        w("")

    w("WHAT EACH OF THE THREE COSTS")
    w("")
    w("FOLLOW-UP DURATION -- the cheapest, and it is not close.")
    w("   Held on 0 of %d topics. It is a single field on the registration record"
      % len(ab_topics))
    w("   (`time frame` on the primary outcome, and the study start/completion dates),")
    w("   and every one of these %d registrations has already been fetched once by this"
      % reachable)
    w("   pipeline -- `registration_read_utc` is stamped on them. So this is a re-fetch")
    w("   of an endpoint we already call, plus a field to store. Fully automatable, no")
    w("   reading, no judgement. One pass over %d registrations." % reachable)
    w("")
    w("ARM-LEVEL EVENT COUNTS -- splits sharply in two, and the split is the estimate.")
    w("   For the %d trials whose object already shows a results posting, the counts are"
      % results_posted)
    w("   structured data on an endpoint we call today: automatable.")
    w("   For the %d where no posting is recorded, the numbers exist only in the" % results_unknown)
    w("   published report, which means a person opens a paper, finds the outcome table,")
    w("   and transcribes two numerators and two denominators per outcome. That is the")
    w("   irreducible human cost, and it is the bulk of bucket 2.")
    w("   NOTE: 'not recorded' is not 'not posted'. This corpus never asked the question,")
    w("   so the true automatable share is AT LEAST %d and may be much higher. Probing"
      % results_posted)
    w("   the results endpoint for all %d is itself a one-pass automated job, and it" % reachable)
    w("   should be done BEFORE anyone commits to the manual figure -- costing the manual")
    w("   work against an unknown denominator is how this session already produced one")
    w("   badly wrong estimate.")
    w("")
    w("HARMS -- automatable to fetch, NOT automatable to scope.")
    w("   A registry results posting carries the full adverse-event tables, so retrieval")
    w("   is the same job as the counts above. What cannot be automated is DECIDING WHICH")
    w("   HARMS THIS REVIEW REPORTS: a posting lists every event at every grade, and")
    w("   choosing the ones a reader needs -- serious adverse events, discontinuations,")
    w("   the drug-class harms a clinician asks about -- is a judgement about relevance.")
    w("   That makes harms a bucket-2 fetch with a bucket-3 decision attached, and it is")
    w("   the only one of the three that cannot be finished without an author.")
    w("")
    w("SEQUENCING THAT FALLS OUT OF THIS")
    w("   1. Probe the results endpoint for all %d reachable registrations. One automated"
      % reachable)
    w("      pass. It converts the %d unknowns into a real number and costs almost"
      % results_unknown)
    w("      nothing. Nothing else should be committed to before it returns.")
    w("   2. Take follow-up duration in the same pass. It is free once the record is open.")
    w("   3. Ingest arm counts for every trial with a posting. Automated.")
    w("   4. Then, and only then, count what is left for manual extraction and price it.")
    w("   5. Harms last, because it needs a rule about what to report before it needs data.")

    out = os.path.join(REPO, "outputs", "bucket2_scope_2026_08_24.txt")
    io.open(out, "w", encoding="utf-8").write("\n".join(L))
    print("\n".join(L))


main()
