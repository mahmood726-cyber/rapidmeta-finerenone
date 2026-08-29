"""One statistic, one value: a displayed number must match the output stored beside it.

AN EXTERNAL REVIEWER READ LEFAMULIN_CABP AND FOUND Q PRINTED TWICE, 0.7313 IN THE MAIN
RESULT AND 0.7316 IN THE GRADE REASONING. Both came from the same object. The metafor
output stored in that object -- the text R actually printed, kept unedited -- says
0.7316. So the headline heterogeneity statistic on the page disagreed with the
computation stored beside it, and a reader checking one against the other would find the
page contradicting itself with no way to tell which number the pooling used.

IT IS NOT ONE PAGE. `heterogeneity.q` is written by a dozen separate Python poolers in
this repository, each computing Q itself, while `r_output.verbatim` holds what metafor
computed. Two independent implementations of one statistic, stored in one object, both
rendered on one page. That is this project's oldest failure shape -- ONE FACT STORED
UNDER SEVERAL NAMES -- and it is why the disagreements sit in the fourth decimal, which
is exactly where review does not look. Twelve outcome blocks across ten objects.

AND THE FIRST VERSION OF THIS GATE OVERCOUNTED THEM BY EIGHT, IN BOTH DIRECTIONS OF
CARELESSNESS. It reported twenty. Seven of those were I^2 differences where the object
DECLARES Higgins (Q-df)/Q while metafor prints the REML form -- two different definitions
of I^2, and the objects carry the recomputation of both. TIGECYCLINE reads 7.2866 against
R's 1.16 for that reason, and the gate called it "the largest disagreement in the corpus",
which inverts a documented decision into an error and accuses the page that did the work.
The eighth was mine: R prints I^2 to two decimals, ARNI stores 32.8939087126, and
comparing a full-precision field against a rounded print manufactured a finding out of a
correct page.

WHY THIS IS A GATE AND NOT A ONE-OFF SWEEP. The sweep that found this was written, run
once, and called by nothing -- and gate 8 caught it in the same session, correctly, as a
check written and left inert. A class that can be reintroduced by the next pooling
script needs something that runs, not a report someone remembers.

RATCHETED, AND THE NOTE SAYS SO. Twelve disagreements exist today; two sit on pages that
are FROZEN and may not be rebuilt, so they cannot all be cleared by this gate's author. A PASS here means no NEW disagreement was introduced.
It does not mean the corpus is clean, and the note prints the frozen count every run so
the number is never read as one.
"""
from __future__ import annotations

import io
import json
import os
import subprocess
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _harness as H                                                        # noqa: E402

DETECTOR = os.path.join("scripts", "sweep_duplicate_statistics_2026_08_29.py")
RESULT = os.path.join("outputs", "duplicate_statistics_2026_08_29.json")
BACKLOG = "STATISTIC_DISAGREEMENT_BACKLOG.json"

# Named cases this gate must actually reach. If the gate passes without seeing these, it
# saw nothing and the pass is vacuous.
NAMED = {
    "LEFAMULIN_CABP": "the reported case: Q 0.7313 displayed against R's 0.7316",
    "TIGECYCLINE_CIAI": "Q 2.1572 against R's 2.1564 -- named because its I^2 looks like "
                        "a far larger disagreement and is NOT one",
}


def main(argv):
    gate = H.Gate("11 ONE STATISTIC, ONE VALUE",
                  "a displayed statistic disagrees with the R output stored beside it")
    for cid, desc in NAMED.items():
        gate.expect_case(cid, desc)
    gate.requires_control()

    repo = H.repo_root()
    path = os.path.join(repo, DETECTOR)
    if not os.path.exists(path):
        gate.broken("%s is absent; this gate RUNS the detector and will not substitute a "
                    "copy of its logic. A gate whose subject is missing is BROKEN, not "
                    "passing." % DETECTOR)
        gate.kinds({"detector present": 0, "detector absent": 1})
        return gate.report(denominator="0 objects -- the detector could not run")

    # THE CONTROL IS THE DETECTOR'S OWN PLANT, EXERCISED RATHER THAN ASSERTED. Four
    # constructed cases with known answers, including one that must NOT be flagged and
    # one where the authority is absent and must be reported as absent.
    plant = subprocess.run([sys.executable, path, "--plant"], cwd=repo, capture_output=True)
    pout = plant.stdout.decode("utf-8", "replace")
    held = plant.returncode == 0 and pout.count("[PASS]") == 4
    if held:
        gate.control(4, 0, [], accuses=True)
    else:
        gate.control(4, 4, ["the detector's own plant did not hold"], accuses=True)
        gate.broken("the detector's plant did not pass 4/4, so its findings are not "
                    "usable. stdout: %s" % pout[-300:].replace(chr(10), " "))

    proc = subprocess.run([sys.executable, path], cwd=repo, capture_output=True)
    if proc.returncode == 2:
        gate.broken("the detector REFUSED its own extractor controls: %s"
                    % proc.stdout.decode("utf-8", "replace")[-300:].replace(chr(10), " "))
        gate.kinds({"objects reached": 0})
        return gate.report(denominator="the detector refused rather than reporting a pass")

    try:
        doc = json.load(io.open(os.path.join(repo, RESULT), encoding="utf-8"))
    except Exception as e:
        gate.broken("the detector ran but its result could not be read: %s" % e)
        gate.kinds({"result file readable": 0})
        return gate.report(denominator="no result to ratchet")

    rows = doc.get("leg_a_disagreements") or []
    no_auth = doc.get("leg_a_no_authority") or []

    for r in rows:
        for cid in NAMED:
            if r["page"].startswith(cid):
                gate.saw(cid)

    found = ["%s|%s|%s" % (r["page"], r["outcome"], r["field"]) for r in rows]
    if "--plant" in argv:
        found.append("__control_planted_page.html|primary|q")
        gate.note("PLANTED: a new object whose stored field disagrees with its R output")

    new = H.ratchet(gate, BACKLOG, found,
                    "outcome blocks whose structured heterogeneity field disagrees with "
                    "the metafor output stored in the same object.")

    gate.kinds({
        "objects read": doc.get("n_objects", 0),
        "outcome blocks with NO stored R authority": len(no_auth),
        "blocks where field and R disagree": len(rows),
        "of those, NEW since the freeze": len(new),
    })
    gate.note("the blocks with no stored R output are NOT a pass. They are %d cases this "
              "gate cannot see, because nothing authoritative is stored to compare against."
              % len(no_auth))
    gate.note("WHAT THE DIFFERENCE ACTUALLY IS, established by recomputation rather than "
              "assumed: the stored field is Q computed from the per-trial log-effects and "
              "standard errors the object holds, which are rounded to six decimals and are "
              "what the page SHOWS. R computed Q from the raw counts at full precision. "
              "Recomputing from the object's own per-trial rows reproduces the STORED value "
              "exactly on both cases where those rows carry usable effects -- LEFAMULIN "
              "0.7313 and GEPOTIDACIN 3.3855. So the stored field is not a wrong number. It "
              "is the number a reader can check against the table above it, and R's is the "
              "more accurate one. Neither is a defect; PRINTING BOTH WITHOUT SAYING SO IS.")
    gate.note("that recomputation reached 2 of the 8 Q cases. The other six store no "
              "per-trial effect and standard error under any name this check knows, so they "
              "are UNRESOLVED, not agreed. Reach is not coverage.")
    gate.note("%d further i2 differences are DEFINITIONAL and are not counted as findings: "
              "those objects declare Higgins (Q-df)/Q while metafor prints the REML form. "
              "TIGECYCLINE's i2 reads 7.2866 against R's 1.16 for that reason, and its "
              "object carries the recomputation of BOTH definitions. An earlier version of "
              "this gate called that the corpus's largest error, which inverted a "
              "documented decision into a defect."
              % len(doc.get("leg_a_definitional_not_errors") or []))
    gate.note("this gate compares against the precision R ACTUALLY PRINTED -- two decimals "
              "for i2, four for tau2 and Q. Comparing a stored full-precision field against "
              "a rounded print manufactured a 13th finding out of a correct page.")

    for f in new:
        page, _, rest = f.partition("|")
        outcome, _, field = rest.partition("|")
        row = next((r for r in rows if r["page"] == page and r["outcome"] == outcome
                    and r["field"] == field), None)
        detail = ("%s %s/%s displays %s where the stored metafor output says %s. BOTH were "
                  "computed; they differ because they were computed from inputs at "
                  "different precision. State which the page is showing, or show one."
                  % (page, outcome, field, row["stored_field"], row["r_authority"])
                  ) if row else f
        gate.finding("STATISTIC-DISAGREES-WITH-STORED-R", detail,
                     numerator=len(new), denominator=len(rows))

    return gate.report(denominator="%d outcome blocks compared against a stored R output, "
                                   "%d frozen" % (len(rows) + 0, len(found) - len(new)))


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
