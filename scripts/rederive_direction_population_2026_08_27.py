"""Which pages actually assert a direction the object never recorded?

WHY RE-DERIVE RATHER THAN RE-CHECK. Nine served pages were hand-edited on 2026-08-26 to
replace a direction-of-benefit label with a refusal, on the stated grounds that "the object
never recorded" it. That population was derived from `results.by_outcome[].
direction_of_benefit`, which is empty for every object in the corpus:

    recorded in outcomes[] ONLY   78
    recorded in BOTH               0
    recorded in by_outcome ONLY    0
    recorded in NEITHER           90

Zero agreement cases, because the two fields never co-occur. A check reading `by_outcome`
concludes "never recorded" for all 78 -- so the population was wrong by construction, and at
least one member of it has already turned out to be a false refusal: FINERENONE_CV_REVIEW's
outcome records `direction_of_benefit: 'lower'` in outcomes[] for a composite of CV death,
non-fatal MI, non-fatal stroke and HF hospitalisation, where lower plainly is better.

THE FAULT WAS THE FIELD, NOT THE JUDGEMENT. So this re-derives the population from the
canonical field instead of re-adjudicating the nine verdicts. A verdict re-checked against
the same wrong field would come back the same.

WHAT COUNTS AS AN ASSERTION. The served page states a direction in words -- "lower is
better", "higher is better", "Favours" with a polarity. What counts as RECORDED is
`outcomes[].direction_of_benefit` being present and non-empty for that outcome id.

  page asserts + object records        -> supported
  page asserts + object does NOT       -> MANUFACTURED, the real population
  page refuses + object records        -> FALSE REFUSAL, the hand-edit's own error class
  page refuses + object does not       -> correct

The third row is the one the hand-edits created and nobody was looking for. It is reported
beside the second, because a night spent removing manufactured claims can install refusals
that are equally unsupported in the other direction.
"""
import io
import json
import os
import re
import sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(REPO, "scripts"))
OUT = os.path.join(REPO, "outputs", "direction_population_2026_08_27.json")

TAG = re.compile(r"<[^>]+>")
SCRIPT = re.compile(r"<script\b.*?</script>", re.S | re.I)
ASSERT_RE = re.compile(r"(lower is better|higher is better)", re.I)
REFUSE_RE = re.compile(r"direction of benefit not recorded", re.I)


def text(html):
    """Rendered text. A <script> block is not page content -- two headline findings last
    night came from not stripping it, so it goes first."""
    return re.sub(r"\s+", " ", TAG.sub(" ", SCRIPT.sub(" ", html or ""))).strip()


def run_controls():
    from instrument_controls import require_controls
    good = text("<p>Favours the intervention (lower is better)</p>")
    inscript = text("<script>var s='lower is better';</script><p>nothing</p>")
    require_controls(
        "direction_population (assertion)",
        ("an assertion in page text is seen", bool(ASSERT_RE.search(good)), True),
        ("an assertion inside a <script> block is counted as page content",
         bool(ASSERT_RE.search(inscript)), True))


def main():
    run_controls()
    raw = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace",
                           write_through=True)

    def log(s):
        raw.write(s + chr(10))
        raw.flush()

    pm = json.load(io.open(os.path.join(REPO, "ssot", "PAGE_MAP.json"), encoding="utf-8"))
    rows = []
    counts = {"supported": 0, "manufactured": 0, "false_refusal": 0, "correct_refusal": 0,
              "silent": 0, "no_served_file": 0}
    for page, path in sorted(pm.items()):
        served = os.path.join(REPO, page)
        if not os.path.exists(served):
            counts["no_served_file"] += 1
            continue
        obj = json.load(io.open(os.path.join(REPO, path), encoding="utf-8"))
        recorded = {}
        for oc in (obj.get("outcomes") or []):
            v = oc.get("direction_of_benefit")
            recorded[oc.get("id")] = bool(v and str(v).strip())
        any_recorded = any(recorded.values())
        t = text(io.open(served, encoding="utf-8", errors="replace").read())
        asserts = bool(ASSERT_RE.search(t))
        refuses = bool(REFUSE_RE.search(t))

        if asserts and any_recorded:
            k = "supported"
        elif asserts and not any_recorded:
            k = "manufactured"
        elif refuses and any_recorded:
            k = "false_refusal"
        elif refuses and not any_recorded:
            k = "correct_refusal"
        else:
            k = "silent"
        counts[k] += 1
        rows.append({"page": page, "object": path, "verdict": k,
                     "asserts": asserts, "refuses": refuses,
                     "outcomes_recorded": sum(1 for v in recorded.values() if v),
                     "outcomes_total": len(recorded)})

    n = sum(v for k, v in counts.items() if k != "no_served_file")
    log("pages with a served file : %d   (no served file: %d)" % (n, counts["no_served_file"]))
    log("")
    log("  page asserts, object records        supported      : %d" % counts["supported"])
    log("  page asserts, object does NOT       MANUFACTURED   : %d" % counts["manufactured"])
    log("  page refuses, object records        FALSE REFUSAL  : %d" % counts["false_refusal"])
    log("  page refuses, object does not       correct refusal: %d" % counts["correct_refusal"])
    log("  page says neither                   silent         : %d" % counts["silent"])
    log("")
    for k, label in (("manufactured", "MANUFACTURED"), ("false_refusal", "FALSE REFUSAL")):
        named = [r["page"] for r in rows if r["verdict"] == k]
        if named:
            log("%s (%d):" % (label, len(named)))
            for p in named[:12]:
                log("    %s" % p)
            if len(named) > 12:
                log("    ... and %d more" % (len(named) - 12))
            log("")
    log("The hand-edits' population was derived from results.by_outcome, which is empty for")
    log("every object, so it could only ever have produced false refusals. This population")
    log("comes from outcomes[], which is where the corpus actually records the field.")

    json.dump({"question": "which pages assert or refuse a direction the object does or does "
                           "not record",
               "canonical_field": "outcomes[].direction_of_benefit; results.by_outcome[]."
                                  "direction_of_benefit is empty corpus-wide and is not a "
                                  "second source of truth",
               "counts": counts, "rows": rows},
              io.open(OUT, "w", encoding="utf-8"), indent=1)
    log("wrote %s" % os.path.relpath(OUT, REPO))
    return 0


if __name__ == "__main__":
    sys.exit(main())
