"""Record on each object what the trial-identity check could and could not decide.

MAHMOOD: "A page whose trials are undecidable should say so rather than implying they were
checked and passed. Undecidable is a third state on the page as well as in the code."

That is the whole point of this file. The check reached a verdict on 301 of 420 trial records
and could not decide 113 of them, because arm names are paraphrases -- NCT00643188 registers
"Procedure: Radiofrequency ablation" where the topic says "catheter ablation". A page that
stays silent about that is telling the reader its trials were verified. They were not.

THREE STATES, WRITTEN AS THREE STATES:

  studied       the registration shows the drug in the randomised contrast
  not_studied   the registration shows it in EVERY arm, so it is background therapy --
                the one class decidable without relying on the arm-type label, which lies
                (NCT00423319 labels the enoxaparin arm EXPERIMENTAL on an apixaban trial)
  undecidable   the arm names do not name the drug the way the topic does, or the drug sits
                in a non-experimental arm and the label is not trustworthy enough to call it

NOTHING IS INFERRED. The status is written only for trials whose arm structure was actually
fetched; a trial whose fetch failed gets no status at all rather than a reassuring one, for
the same reason a network error must not become `hasResults: false`.

Read from outputs/identity_roles_rederived_2026_08_25.json, which is produced by
validate_identity_on_corpus and carries its own controls.
"""
import io
import json
import os
import sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ROLES = os.path.join(REPO, "outputs", "identity_roles_rederived_2026_08_25.json")

_STATE = {"STUDIED": "studied", "NOT STUDIED": "not_studied",
          "UNDECIDABLE": "undecidable"}


def main():
    apply = "--apply" in sys.argv
    if not os.path.exists(ROLES):
        print("REFUSED: %s is not on disk. Nothing written."
              % os.path.relpath(ROLES, REPO))
        return 2
    rows = json.load(io.open(ROLES, encoding="utf-8"))["rows"]
    pmap = json.load(io.open(os.path.join(REPO, "ssot", "PAGE_MAP.json"), encoding="utf-8"))

    bypage = {}
    for r in rows:
        if r["verdict"] not in _STATE:
            continue          # UNJUDGED: no arm data, so no status is written at all
        bypage.setdefault(r["page"], []).append(r)

    written = 0
    counts = {"studied": 0, "not_studied": 0, "undecidable": 0}
    for page, rs in sorted(bypage.items()):
        rel = pmap.get(page)
        if not rel:
            continue
        path = os.path.join(REPO, rel)
        if not os.path.exists(path):
            continue
        obj = json.load(io.open(path, encoding="utf-8"))
        trials = {}
        for r in rs:
            trials[r["nct"]] = {"state": _STATE[r["verdict"]], "why": r["why"]}
            counts[_STATE[r["verdict"]]] += 1
        block = {
            "checked_utc": "2026-08-25",
            "source": "ClinicalTrials.gov API v2 armsInterventionsModule",
            "method": ("the drug pattern from the matcher's own TOPICS list, compared "
                       "against the registered arm structure"),
            "by_trial": trials,
            "n_studied": sum(1 for v in trials.values() if v["state"] == "studied"),
            "n_not_studied": sum(1 for v in trials.values() if v["state"] == "not_studied"),
            "n_undecidable": sum(1 for v in trials.values() if v["state"] == "undecidable"),
            "what_undecidable_means": (
                "The registered arm names do not name this intervention the way the review "
                "does, or the drug sits outside the experimental arm and registry arm-type "
                "labels are not reliable enough to judge on. It is NOT a pass and NOT a "
                "failure: this check could not decide, and no other check has looked."),
        }
        obj["trial_identity_check"] = block
        if apply:
            io.open(path, "w", encoding="utf-8").write(
                json.dumps(obj, ensure_ascii=False, indent=1))
        written += 1

    print("pages given a trial_identity_check block : %d" % written)
    print("  trial records: studied %d, not_studied %d, undecidable %d"
          % (counts["studied"], counts["not_studied"], counts["undecidable"]))
    print()
    if apply:
        print("WRITTEN.")
    else:
        print("DRY RUN. Re-run with --apply to write.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
