"""Overnight adversarial hunts. Codex saturated, aimed where it has actually produced.

MAHMOOD: "work hard on corpus as per usual using codex all night".

WHAT ACTUALLY WORKS, from a full day of evidence. Three live defect classes came from asking
Codex to look where NOBODY HAD ENUMERATED -- the 72-instance splice class, the estimand
marker beside a statistical model on 20 pages, the truthy-container class. Every hunt that
asked it to CONFIRM a list we already had came back empty. So every brief here forbids
verification of the known list and demands a form nobody has named.

THE HIGHEST-VALUE TARGET IS THE GATES, NOT THE PAGES. `gate_paper_reads_terribly` rests on
seven literal vocabulary patterns; a hollow phrase in different words passes clean, and the
20-page estimand defect sat behind it all day. Every clean gate report this repository
produces inherits that gate's blind spots. So hunt H1 attacks the checks themselves: for each
gate, find an instance of the defect it exists to catch THAT IT DOES NOT CATCH.

DISCIPLINE, ALL OF IT LEARNED THE HARD WAY TODAY AND NONE OF IT OPTIONAL:

  PER-LANE PATHS. The bash /tmp alias resolves to the shared claude-temp root, written
  by every lane, 31k loose files.
  A `git commit -F` pointed at a generic name in that root committed 220 files under
  another lane's message tonight.
  Everything here writes under SESSION.

  VERIFY BYTES BEFORE BELIEVING A JOB. `codex exec` intermittently fails to receive its
  prompt: it prints "Reading additional input from stdin...", waits, and EXITS 0 having done
  nothing. A hunt that silently did nothing returns "no defects found", which is
  indistinguishable from a clean corpus. Every job must produce an artefact with bytes, and
  retries on failure.

  VALIDATE EACH PROBE AGAINST A KNOWN POSITIVE. Two of six probes written tonight were wrong
  on their first run -- one reported 141 of 148 pages losing content that was figure axis
  ticks, one refused a good payload because it read a page's own provenance as a leaked
  element id. A hunt whose instrument is untested produces confident nonsense. Each brief
  requires the hunt to demonstrate its method finds a SEEDED KNOWN INSTANCE first, and to
  report that demonstration in its output.

  AN EMPTY HUNT IS A FINDING EITHER WAY. Clean corpus or blunt instrument -- the difference
  is the point, so a hunt returning nothing must say WHAT IT SEARCHED and HOW IT WOULD HAVE
  RECOGNISED a hit.
"""
import io
import json
import os
import shutil
import subprocess
import sys
import time

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SESSION = (r"F:\claude-temp\claude\F--rapidmeta-finerenone"
           r"\e2e2a1d5-c19e-44de-90ab-690dbc5235a1\scratchpad\overnight")
LEDGER = os.path.join(REPO, "outputs", "overnight_hunt_ledger.jsonl")

_PREAMBLE = """You are working in F:\\rapidmeta-ssot-shell, a corpus of ~160 published
evidence-synthesis web pages generated from canonical JSON objects under ssot/<slug>/.

READ ONLY. Do NOT commit, push, build, or modify any .html or ssot/*.json file. Write exactly
ONE output file, named at the end of this brief, and nothing else.

THREE RULES THAT DECIDE WHETHER YOUR WORK IS USED:

1. DO NOT VERIFY WHAT WE ALREADY KNOW. Every hunt that re-checked a known list has returned
   nothing all day. Your value is finding a FORM NOBODY HAS ENUMERATED. If you find yourself
   confirming a defect class that is already named in a script under scripts/, you are in the
   wrong place -- go somewhere nobody has looked.

2. DEMONSTRATE YOUR METHOD FINDS A KNOWN INSTANCE BEFORE YOU TRUST IT. Pick one case you can
   verify by hand, show your method flags it, and record that demonstration in your output
   under "control". Two probes written here today were wrong on their first run and reported
   corpus-wide catastrophe that did not exist. If your method cannot find a case you already
   know about, it cannot be trusted on cases you do not.

3. AN EMPTY RESULT IS A REAL ANSWER, BUT ONLY IF YOU SAY WHAT YOU SEARCHED. If you find
   nothing, record exactly what you examined, how many, and what a hit would have looked like.
   "No defects found" without that is indistinguishable from a job that never ran.

Quote evidence verbatim. Give file paths and line numbers. Do not speculate about intent.
"""

HUNTS = {
    "gate_blind_spots": """
THE HIGHEST-VALUE TARGET IN THIS REPOSITORY.

The scripts under scripts/ named gate_*.py and lint_*.py are the checks that decide whether
this corpus ships. Every clean report they produce inherits whatever they cannot see.

A worked example of the failure you are looking for: `gate_paper_reads_terribly_2026_08_24.py`
detects hollow prose using SEVEN LITERAL VOCABULARY PATTERNS. A hollow sentence phrased in
different words passes it clean. A 20-page defect sat behind that gate all day.

YOUR TASK: for each gate or lint you examine, find A REAL INSTANCE IN THIS CORPUS of the
defect that gate exists to catch, WHICH THAT GATE DOES NOT CATCH. Run the gate to confirm it
passes on your instance. A vocabulary-based check that should have been a property check is
the commonest shape; there will be others.

For each finding record: the gate, what it claims to catch, the page or object holding an
instance it misses, the verbatim text, and WHY it slips through.

Write outputs/hunt_gate_blind_spots_%(stamp)s.json
""",

    "false_absence": """
PAGES THAT ASSERT AN ABSENCE THAT IS NOT TRUE.

This is the worst defect class this corpus produces, because a reader cannot detect it: the
page states that something is missing, and the object holds it. Found today by hand, not by
any gate:

  - four topics published "no result is pooled" while holding a readable per-trial estimate,
    including CLEAR-Outcomes HR 0.87 (0.79 to 0.96) and SPRINT HR 0.75 (0.64 to 0.89);
  - a certainty section stating "no GRADE record is held" on a topic that rated all three of
    its outcomes `low`;
  - 74 trials rendering "title not recorded in the registry read" when the registry title was
    held under a different key.

The mechanism is always the same: the renderer looks in ONE place, does not find the value,
and reports absence rather than not-found.

YOUR TASK: find MORE. Any sentence on any delivered page that asserts something is absent,
unavailable, not recorded, not held, not assessed, or not established -- where the object
DOES hold it, anywhere, under any key. Compare the rendered page against the object.

DO NOT re-report the three classes above; they are fixed. Find the ones nobody has named.

Write outputs/hunt_false_absence_%(stamp)s.json
""",

    "untraceable_number": """
NUMBERS ON A PAGE THAT DO NOT TRACE TO A SOURCE.

Every quantity on these pages is supposed to be READ from the canonical object, never
computed by the renderer and never carried over from a previous version. A number that
appears on a page and cannot be found in that page's object is either a stale artefact, a
computation nobody declared, or a value from another topic.

YOUR TASK: for a sample of delivered *_REVIEW.html pages, extract every numeric quantity in
the Paper tab -- effect estimates, intervals, counts, percentages, participant numbers -- and
determine whether each traces to a value in that page's own ssot object. Report every number
that does not.

Distinguish carefully, because most will be legitimate: a number may be FORMATTED differently
(0.7171 rendered as 0.72), DERIVED and declared (a percentage of two stored counts), or part
of prose (a year, a version). What you are hunting is a number that is none of those and has
no origin in the object.

Write outputs/hunt_untraceable_number_%(stamp)s.json
""",

    "identifier_in_prose": """
INTERNAL IDENTIFIERS REACHING READER PROSE.

A blind editor persona DESK-REJECTED one of these pages today for unreadability, quoting
`k_cascade.k_unscreened_remainder` and a list of build-property names as examples of "bizarre
text". Those are our own field paths and internal identifiers appearing in sentences a
clinician is expected to read.

IMPORTANT DISTINCTION, and getting it wrong wastes the hunt: this corpus deliberately shows
provenance inside COLLAPSED <details class='prov-block'> elements, and inside "Sources for
this section" lists. THAT IS A FEATURE and is not what you are hunting -- a reader only meets
it if they open the disclosure. What you are hunting is an identifier in a SENTENCE, a table
cell, a caption, or a heading -- somewhere a reader meets it without choosing to.

Shapes to look for: dotted field paths (`results.by_outcome.x.pooled`), snake_case tokens
(`registered_primary_timeframe`), internal enum values (`NO_INFORMATION`, `SOME_CONCERNS`),
build property names (`P18_restatement_is_reproducible`), script filenames, and any token
carrying an underscore or a bracket that a clinical reader would not recognise.

Write outputs/hunt_identifier_in_prose_%(stamp)s.json
""",

    "unenumerated": """
FIND A DEFECT CLASS NOBODY HERE HAS NAMED.

No target. No list to check. The three highest-value findings in this corpus today all came
from this brief, and each was a FORM nobody had thought to look for:

  - a "sentinel splice": an absence marker composed into a sentence as though it were a
    value, 72 instances;
  - an estimand-identity marker rendered beside a statistical model as if it were part of the
    model output, 20 pages;
  - a truthy-container check that treated an empty container as present, so a page asserted
    data it did not have.

Notice what those share: each is a category error at a JOIN -- a value of one kind used where
a value of another kind belongs, and no gate existed because nobody had named the kind.

YOUR TASK: read widely across delivered pages and the objects behind them, and find a NEW
class of that shape. Prefer a defect that (a) reaches a reader, (b) has more than one
instance, and (c) no script under scripts/ currently detects. Name the class, define the
property that is violated, and list every instance you can find.

Write outputs/hunt_unenumerated_%(stamp)s.json
""",
}


def verify(path):
    """(ok, why). Bytes on disk, valid JSON, and a control section. Exit code proves nothing."""
    if not os.path.exists(path):
        return False, "no artefact on disk"
    n = os.path.getsize(path)
    if n < 200:
        return False, "artefact is %d bytes -- too small to be a report" % n
    try:
        d = json.load(io.open(path, encoding="utf-8"))
    except Exception as e:
        return False, "artefact is not valid JSON (%s)" % type(e).__name__
    if not isinstance(d, (dict, list)):
        return False, "artefact is neither an object nor a list"
    return True, "%d bytes" % n


def run_hunt(name, brief, stamp, log):
    out_rel = "outputs/hunt_%s_%s.json" % (name, stamp)
    out_abs = os.path.join(REPO, out_rel.replace("/", os.sep))
    prompt = _PREAMBLE + (brief % {"stamp": stamp})
    exe = shutil.which("codex") or "codex"
    for attempt in (1, 2, 3):
        log("  [%s] attempt %d" % (name, attempt))
        try:
            p = subprocess.run([exe, "exec", "-s", "workspace-write"],
                               input=prompt.encode("utf-8"),
                               capture_output=True, timeout=3000, cwd=REPO)
        except subprocess.TimeoutExpired:
            log("      timed out after 3000s")
            continue
        body = (p.stdout or b"").decode("utf-8", "replace")
        io.open(os.path.join(SESSION, "hunt_%s_r%d.out" % (name, attempt)),
                "w", encoding="utf-8").write(body)
        ok, why = verify(out_abs)
        log("      stdout %d bytes | artefact: %s" % (len(body), why))
        if ok:
            return {"hunt": name, "artefact": out_rel, "attempts": attempt, "status": "ok"}
        time.sleep(5)
    return {"hunt": name, "artefact": out_rel, "attempts": 3, "status": "no usable artefact"}


def main():
    os.makedirs(SESSION, exist_ok=True)
    rounds = int(sys.argv[1]) if len(sys.argv) > 1 else 1
    raw = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace",
                           write_through=True)

    def log(s):
        raw.write(s + "\n")
        raw.flush()
        try:
            os.fsync(sys.stdout.fileno())
        except (OSError, ValueError):
            pass

    for rnd in range(1, rounds + 1):
        for name, brief in HUNTS.items():
            stamp = "2026_08_25_r%d" % rnd
            log("ROUND %d  HUNT %s" % (rnd, name))
            rec = run_hunt(name, brief, stamp, log)
            rec["round"] = rnd
            with io.open(LEDGER, "a", encoding="utf-8") as fh:
                fh.write(json.dumps(rec) + "\n")
            log("  -> %s (%s)" % (rec["status"], rec["artefact"]))
    return 0


if __name__ == "__main__":
    sys.exit(main())
