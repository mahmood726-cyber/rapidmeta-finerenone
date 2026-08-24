"""Repair the authored fields that make the delivered papers read terribly.

MAHMOOD READ `POSACONAZOLE_FUNGAL_AUTO_FULL_REVIEW.html` ON THE PUBLIC HOST AND SAID THE
PAPERS "STILL READ TERRIBLY", FOR AT LEAST THE SIXTH TIME. The served bytes were fetched
and hashed against a fresh build from the current generator: identical but for the
`Page generated` timestamp. So this was NEVER a stale deploy -- every previous lane that
reported it fixed was measuring something the reader does not meet.

WHY THE EXISTING INSTRUMENT DID NOT SEE IT. `lint_paper_reads_as_prose.py` counts MACHINE
VOCABULARY: field paths, snake_case, bare NCTs, raw statistics. It scores this page at 16%
and every sentence below passes it CLEAN, because every sentence below is well-formed
English. The defect is not that the prose is machine-shaped. It is that the prose is
EMPTY, CIRCULAR, OR ABOUT ANOTHER TOPIC. A lint that cannot express that difference will
keep certifying these pages, which is exactly what has been happening.

FIVE DEFECTS, ALL IN AUTHORED FIELDS ON THE OBJECTS. The generator is faithful; what it
was told is bad. Repairing the generator would be repairing the wrong layer.

  1  VERDICT IN THE TITLE SLOT (65 objects). `title` reads
     "Posaconazole Fungal: NOT POOLABLE -- no registration declares a clinical endpoint at
     any rank". That is an audit verdict, shouted, standing where a manuscript title goes
     -- and it is the first thing a reader meets, in the browser tab, the H1 and the
     "Title and review question" section. NOTHING IS LOST BY MOVING IT: the same verdict is
     already carried by `topic_state` and `which_limb_fails`, and is already rendered in
     the banner and in Results.

  2  THE QUESTION IS THE TITLE WITH A SUFFIX GLUED ON (61 objects). `question` is literally
     `title + " on " + outcome_name + "?"`, which yields
     "Posaconazole Fungal: NOT POOLABLE -- no registration declares a clinical endpoint at
     any rank on the clinical quantity this page pools?" -- a verdict, a preposition and a
     placeholder, punctuated as a question. It is not a review question and no reader can
     parse it.

  3  THE INTRODUCTION IS THREE FRAGMENTS CONCATENATED (140 objects). "This review asks:
     <the broken question>" then "It identifies no trial that can be pooled." then "The
     outcome sought is <the placeholder>." Repairing 2 repairs the first fragment; this
     rebuilds the lead sentence so the paragraph coheres.

  4  ONE TOPIC'S ILLUSTRATION EMITTED ONTO 123 UNRELATED PAGES. The `estimand_established`
     caution is general and correct, but it carries a worked example written about
     `attr-pn-review` -- patisiran against saline, vutrisiran against PATISIRAN,
     eplontersen against another trial's placebo cohort. A reader of the POSACONAZOLE page
     meets three transthyretin-amyloidosis drugs in the Summary of Findings. The CAUTION IS
     KEPT EVERYWHERE; the worked example is kept only on the topic it is about.

  5  A SELF-REFERENTIAL OUTCOME NAME (10 objects). `outcomes[].name` is "the clinical
     quantity this page pools", which the projector then splices into every slot that wants
     a noun phrase, producing "The outcome sought is the clinical quantity this page pools."
     -- a sentence that says the outcome is the outcome. NO NAME IS INVENTED HERE: these
     registrations declare no endpoint at any rank, so the object is right that it cannot
     name one. It is renamed to what it honestly is, by its ROLE in the review, which is
     the one thing the object does know.

WHAT THIS SCRIPT WILL NOT DO. It will not write a clinical title where the object holds
only a slug. "Amoxicillin Aom" becomes "Amoxicillin AOM" and stops there: expanding a
declared abbreviation is a substitution, but deciding that the topic is "amoxicillin for
acute otitis media in children" is authorship, and this project's whole contract is that
the renderer does not author. Those are REPORTED, by name, for Mahmood to write.

Idempotent: every repair is guarded on the defect still being present. `--apply` writes;
default is a dry run.
"""
import io
import json
import glob
import os
import re
import sys

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# The verdict shapes that occupy the title slot. Anchored after a colon so a legitimate
# title containing the word "not" is untouched.
VERDICT = re.compile(
    r"^(?P<topic>.+?):\s*(?P<verdict>(NOT POOLABLE|NOT ESTABLISHED|NOT ASSESSABLE|"
    r"NOT COMPARABLE)\b.*)$")

# Declared abbreviation expansions -- capitalisation only, never a new clinical claim.
# Same discipline as ssot/topic_identity.py's synonym sets: enumerate what is safe, and
# leave anything not enumerated exactly as it was rather than guess at it.
CAPS = {
    "aom": "AOM", "cdi": "CDI", "tb": "TB", "hiv": "HIV", "af": "AF", "vte": "VTE",
    "acs": "ACS", "pah": "PAH", "mrsa": "MRSA", "covid": "COVID", "covid19": "COVID-19",
    "hf": "HF", "hfref": "HFrEF", "hfpef": "HFpEF", "ckd": "CKD", "t2d": "T2D",
    "cll": "CLL", "nstemi": "NSTEMI", "pci": "PCI", "dapt": "DAPT", "sglt2": "SGLT2",
    "rsv": "RSV", "hbv": "HBV", "hcv": "HCV", "cmv": "CMV", "uti": "UTI",
    "copd": "COPD", "ra": "RA", "ms": "MS", "ibd": "IBD", "nash": "NASH",
    "pcsk9": "PCSK9", "arni": "ARNI", "attr": "ATTR", "prep": "PrEP", "dta": "DTA",
}

PLACEHOLDER_NAME = "the clinical quantity this page pools"
# Named by its ROLE, which is the one thing the object knows. Reads as a noun phrase in
# every slot the projector splices it into, and stays true in the Results sentence:
# "...register no clinical endpoint at any rank on the quantity this review was asked to
# pool" is coherent and non-circular, where the old name made it say nothing.
ROLE_NAME = "the quantity this review was asked to pool"

ATTRPN_EXAMPLE = re.compile(
    r"\s*On attr-pn-review the flag is TRUE and correct while the pool combines patisiran "
    r"against its own saline placebo, vutrisiran against PATISIRAN, and eplontersen "
    r"against the placebo cohort of a DIFFERENT TRIAL\.", re.I)
ATTRPN_TOPIC = "attr-pn-review"


def deslug(topic):
    """Title-case artefacts back to something a reader can read. Capitalisation only."""
    words = []
    for w in topic.split():
        low = w.lower().strip(",.")
        words.append(CAPS[low] if low in CAPS else w)
    return " ".join(words)


def repair(obj, slug):
    """Return (changes, clean_topic) for one object. Mutates `obj`."""
    changes = []

    # ---- 5. the self-referential outcome name (do this FIRST; 2 and 3 quote it) --------
    old_name = None
    for o in (obj.get("outcomes") or []):
        if (o.get("name") or "").strip() == PLACEHOLDER_NAME:
            old_name = o["name"]
            o["name"] = ROLE_NAME
            changes.append("outcome-name")

    # ---- 1. the verdict standing in the title slot -------------------------------------
    title = obj.get("title") or ""
    m = VERDICT.match(title)
    if m:
        clean_topic = deslug(m.group("topic").strip())
        obj["title"] = clean_topic
        # The verdict is not discarded -- it is already on the object twice. Recorded here
        # only if neither carrier holds it, so nothing this page said can go missing.
        if not (obj.get("topic_state") or obj.get("which_limb_fails")):
            obj["topic_state"] = m.group("verdict").strip()
        changes.append("title")
    else:
        clean_topic = deslug(title.strip()) if title else None

    # ---- 2. the question that is the title with a suffix -------------------------------
    q = obj.get("question") or ""
    if q and title and q.startswith(title.rstrip("?").rstrip()[:40]) and clean_topic:
        # Recover the outcome the old question was glued to, then pose a real question.
        tail = q[len(title):].strip()
        tail = re.sub(r"^on\s+", "", tail).rstrip("?").strip()
        if old_name and (tail == PLACEHOLDER_NAME or not tail):
            # No endpoint is declared anywhere on this topic, so the question a reader can
            # actually be asked is the one the object answers.
            obj["question"] = ("In %s, is there a registered clinical endpoint that the "
                               "contributing trials can be pooled on?" % clean_topic)
        elif tail:
            obj["question"] = "In %s, what is the effect on %s?" % (clean_topic, tail)
        else:
            obj["question"] = "In %s, what do the contributing trials show?" % clean_topic
        changes.append("question")

    # ---- 3. the introduction whose lead sentence quotes the broken question -------------
    man = obj.get("manuscript")
    if isinstance(man, dict):
        intro = man.get("introduction")
        if isinstance(intro, str) and intro.startswith("This review asks:") and obj.get("question"):
            parts = intro.split("\n")
            parts[0] = "This review asks: %s" % obj["question"]
            new = "\n".join(parts)
            if old_name:
                new = new.replace(PLACEHOLDER_NAME, ROLE_NAME)
            if new != intro:
                man["introduction"] = new
                changes.append("introduction")

    # ---- 4. one topic's worked example on every other topic's page ---------------------
    if slug != ATTRPN_TOPIC:
        for oc in ((obj.get("results") or {}).get("by_outcome") or {}).values():
            if not isinstance(oc, dict):
                continue
            for k, v in list(oc.items()):
                if isinstance(v, str) and ATTRPN_EXAMPLE.search(v):
                    oc[k] = ATTRPN_EXAMPLE.sub("", v)
                    changes.append("attrpn-example")

    return changes, clean_topic


def main():
    apply_ = "--apply" in sys.argv
    objs = sorted(glob.glob(os.path.join(REPO, "ssot", "*", "*.json")))
    touched, unwritable = [], []
    tally = {}
    for p in objs:
        slug = os.path.basename(os.path.dirname(p))
        try:
            obj = json.load(open(p, encoding="utf-8"))
        except Exception as exc:
            print("  SKIP unreadable %s: %s" % (slug, exc))
            continue
        changes, clean_topic = repair(obj, slug)
        if not changes:
            continue
        for c in changes:
            tally[c] = tally.get(c, 0) + 1
        touched.append((slug, sorted(set(changes)), obj.get("title")))
        # A title that is still a bare slug pair is reported, not invented.
        if clean_topic and len(clean_topic.split()) <= 3 and " for " not in clean_topic:
            unwritable.append((slug, clean_topic))
        if apply_:
            tmp = p + ".tmp"
            with io.open(tmp, "w", encoding="utf-8") as fh:
                json.dump(obj, fh, ensure_ascii=False, indent=2)
            os.replace(tmp, p)

    print("objects scanned: %d" % len(objs))
    print("objects repaired: %d   %s" % (len(touched), "(APPLIED)" if apply_ else "(dry run)"))
    for k in sorted(tally):
        print("    %-18s %d" % (k, tally[k]))
    print("\nTITLES THAT ARE STILL A SLUG AND NEED AN AUTHOR (%d):" % len(unwritable))
    for slug, t in unwritable[:200]:
        print("    %-46s %s" % (slug, t))
    with io.open(os.path.join(REPO, "outputs",
                              "paper_reads_terribly_repair_2026_08_24.json"),
                 "w", encoding="utf-8") as fh:
        json.dump({"scanned": len(objs), "repaired": len(touched), "tally": tally,
                   "titles_needing_an_author": unwritable,
                   "objects": [{"slug": s, "changes": c, "title": t} for s, c, t in touched]},
                  fh, ensure_ascii=False, indent=2)
    return 0


if __name__ == "__main__":
    sys.exit(main())
