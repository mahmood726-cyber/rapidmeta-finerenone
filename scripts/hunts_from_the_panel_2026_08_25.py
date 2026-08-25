"""Open-brief hunts seeded by the panel -- pages nobody had ever read are a new hypothesis source.

MAHMOOD: keep the open-brief hunt running underneath, "particularly now that the panel is
reading pages nobody has ever read, which is itself a novel source of hypotheses."

That is the design of this round. Rounds 1-4 briefed a hunter against the CODE and the
OBJECTS. This one briefs it against what happened when 149 pages met two readers for the
first time, because the panel already produced one defect class no gate of ours could reach:
an agreement statistic contradicting a refusal two sections later. That defect lives BETWEEN
TWO SENTENCES, and every checker we own compares one sentence to one field.

So each brief below points at a relationship a field-by-field checker cannot see. None of
them names a defect to confirm -- naming one would just get it confirmed. They name a
PROPERTY and ask what violates it.

STANDING CONDITIONS. Verify the artefact on disk, not the exit code: `codex exec` returns 0
having produced nothing often enough that at this volume it is certain. Three attempts, then
recorded as producing no usable artefact -- never as a clean hunt.
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
           r"\e2e2a1d5-c19e-44de-90ab-690dbc5235a1\scratchpad\hunts_panel")
LEDGER = os.path.join(REPO, "outputs", "hunts_from_panel_2026_08_25.jsonl")

PREAMBLE = """You are hunting for defects in a systematic-review generator at F:/rapidmeta-ssot-shell.
It projects 149 HTML review pages from canonical JSON objects. Tab 7 of each page (id
"pn-paper") is the manuscript.

Ground rules, and they matter more than finding something:
- A defect you cannot demonstrate on a NAMED page or object is not a finding. Name it.
- Report the DENOMINATOR you searched, not just the hits. "3 pages" means nothing without
  "of how many examined".
- If you find nothing, say so. A hunt that reports nothing is a result. A hunt that invents
  something costs more review time than it saves.
- Do not report a defect that an existing script under scripts/ already detects. Check first.
- Over-flagging is not the safe direction. Four separate over-flags on 2026-08-25 each
  manufactured a defect class that did not exist, and each cost the same review time as a
  real one would have.

"""

HUNTS = {
    "between_two_sentences": """
THE PROPERTY: a manuscript must not assert in one section something it contradicts in
another.

Every checker in scripts/ compares ONE sentence to ONE field on the object. That is why the
corpus shipped 15 pages whose abstract reported the agreement between trials the body said
were not pooled -- on the object the number was genuinely stored, so every field-level check
passed. The contradiction lived between two sentences.

Find OTHER instances of that shape. Read the delivered HTML pages, not the object. For each
page, extract the claims the abstract makes, then check each against what later sections say.
Look especially at: counts of trials, counts of outcomes, certainty statements, statements
about what was searched, statements about what was assessed, and any sentence containing a
number that also appears elsewhere with a different value.

Write outputs/hunt_between_sentences_%(stamp)s.json with, for each finding: page, the two
quoted passages, and why they cannot both be true.
""",

    "denominator_unstated": """
THE PROPERTY: a count in a manuscript must be readable as a proportion of something the
reader can see.

"No risk-of-bias domain was rated high" was true of the THREE trials assessed, on a page
concluding "Across 4 randomised trials". A reader takes the first sentence as covering the
second. The sentence was not false; it was unreadable without a denominator the page never
gave.

Find every sentence in the delivered pages that states a count, a proportion, or an absence
("no", "none", "all", "each", "every") where the population it applies to is NOT stated in
the same sentence AND differs from the page's headline trial count. Check the object to
establish what the true denominator is.

Write outputs/hunt_denominator_%(stamp)s.json: page, quoted sentence, the denominator the
sentence implies, the denominator the object supports.
""",

    "what_the_short_pages_hide": """
THE PROPERTY: a page that declines to produce a result must decline for a reason the object
supports.

99 of the 149 pages are short notes, typically 1,100-1,400 characters, saying why no pooled
result was possible. Nobody has audited those reasons. They have been treated as
self-evidently correct because they are refusals, and a refusal feels safe.

For each SHORT page (paper panel under 3,000 characters), read the stated reason for not
pooling and check it against the object. Is the reason the object actually supports? A page
saying "one trial" when the object holds two, or "no shared outcome" when the object shows a
shared outcome, is a FALSE REFUSAL -- evidence suppressed by an incorrect rule application,
which is worse than a wrong pool because nobody looks at it.

Write outputs/hunt_false_refusal_%(stamp)s.json: page, the stated reason, what the object
shows, and whether the refusal is supported.
""",

    "identity_of_the_trials": """
THE PROPERTY: every trial named on a page must be a trial that studies the intervention the
page is about.

This repository has shipped a trial-identity defect before: HELIOS-B was keyed to a
hydrocephalus shunt trial, and a comparator sweep later found 107 genuine trial-identity
mismatches including transpositions. A reader of the panel flagged CEFEPIME_TAZ for
presenting two registered trials of which neither appears to study cefepime-tazobactam.

Take every page and every NCT id it names. Check that the registration's intervention matches
the page's subject drug or procedure, and that the registration's condition matches the page's
population. Report mismatches with the NCT id, what the page claims it is, and what the
registration says it is.

Write outputs/hunt_trial_identity_%(stamp)s.json. State how many NCT ids you checked.
""",
}


def verify(path):
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


def run(name, brief, stamp, log):
    out_rel = "outputs/hunt_%s_%s.json" % (name, stamp)
    out_abs = os.path.join(REPO, out_rel.replace("/", os.sep))
    prompt = PREAMBLE + (brief % {"stamp": stamp})
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
        io.open(os.path.join(SESSION, "%s_r%d.out" % (name, attempt)),
                "w", encoding="utf-8").write(body)
        ok, why = verify(out_abs)
        log("      stdout %d bytes | artefact: %s" % (len(body), why))
        if ok:
            return {"hunt": name, "artefact": out_rel, "attempts": attempt, "status": "ok"}
        time.sleep(5)
    return {"hunt": name, "artefact": out_rel, "attempts": 3,
            "status": "no usable artefact"}


def main():
    os.makedirs(SESSION, exist_ok=True)
    rounds = int(sys.argv[1]) if len(sys.argv) > 1 else 1
    raw = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace",
                           write_through=True)

    def log(s):
        raw.write(s + "\n")
        raw.flush()

    for r in range(1, rounds + 1):
        for name, brief in HUNTS.items():
            stamp = "r%d" % r
            log("round %d :: %s" % (r, name))
            rec = run(name, brief, stamp, log)
            rec["round"] = r
            with io.open(LEDGER, "a", encoding="utf-8") as fh:
                fh.write(json.dumps(rec, ensure_ascii=False) + "\n")
            log("  -> %s (%d attempt(s))" % (rec["status"], rec["attempts"]))
    return 0


if __name__ == "__main__":
    sys.exit(main())
