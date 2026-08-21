"""Class 83: sixteen comparison rows were reaching readers as a PMID and four blank cells.

WHAT A READER MET. Under the headers "Citation / PMID / Their k / Scope / How it differs
from ours", one identifier and FOUR EMPTY CELLS. Not a refusal -- a table asserting that a
comparison had been made, with nothing behind it. Strictly worse than the refusal the same
section emits when no comparison exists, because a refusal at least tells the truth.

THE CAUSE IS TWO VOCABULARIES AND ONE READER. paper_projector asks each record for
`citation`, `their_k`, `scope` and `how_it_differs_from_ours`. Every applier written during
this run stored `title`, `journal`, `year`, `outcome_pooled` and `agreement` instead. The
older records use the projector's names and render correctly; the sixteen new ones do not.
NOBODY OPENED THE RENDERED TABLE, so limb 3 was counted as held on thirteen topics while
being delivered to nobody -- the same mechanism as class 65, on the limb we spent the run
writing.

    22 rows in the projector's vocabulary   render
    16 rows in the appliers' vocabulary     rendered a PMID and four blanks

THIS SCRIPT IS THE OBJECT HALF OF THE FIX and it only ever ADDS. `citation` is composed
from title, journal and year; `scope` copies `outcome_pooled`; `how_it_differs_from_ours`
copies `agreement` or `why_not_comparable`. Nothing is renamed, nothing is deleted, and a
record that already carries the projector's key is left alone.

THEIR TRIAL COUNT IS WRITTEN BY HAND, NOT PARSED. Where the trial set is a list of named
trials the projector can count it. Where the count is a WORD inside a sentinel string --
"NOT NAMED -- fifteen studies", "six RCTs", "twelve trials" -- no instrument here reads it,
and until now `audit_our_k_against_theirs.py` recorded those topics as THEIR COUNT NOT
STATED. That is the third instance of the same shape: a number written as a word is
invisible to a check that looks for a number. Each of the six is read off the stored
sentence below, transcribed once, and carries the sentence it came from.
"""
import io
import json
import os
import sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(REPO, "ssot"))
import atomic_write

TODAY = "2026-08-21"

# Their k where the count is stated as a WORD inside the trial-set sentinel and no list can
# be counted. Keyed by PMID. Each carries the stored sentence it was read from, so the
# transcription can be checked against the object without leaving the object.
THEIR_K_FROM_PROSE = {
    "39286810": (10, "ten studies"),
    "37498645": (12, "twelve trials, of which seven are prevention trials"),
    "41906074": (4, "four trials, n = 4,149"),
    "41314935": (6, "six RCTs, n = 12,086"),
    "34231123": (10, "ten CVOTs"),
    "31577763": (15, "fifteen studies, 6,745 participants"),
}


def topic_objects():
    root = os.path.join(REPO, "ssot")
    for name in sorted(os.listdir(root)):
        p = os.path.join(root, name, name + ".json")
        if os.path.isfile(p):
            yield name, p


def main():
    dry = "--apply" not in sys.argv
    repaired = touched = k_written = already = 0
    seen_prose = set()

    for topic, path in topic_objects():
        obj = json.load(io.open(path, encoding="utf-8"))
        pc = obj.get("published_comparison")
        if not isinstance(pc, dict):
            continue
        revs = pc.get("reviews")
        if not isinstance(revs, list) or not revs:
            continue

        changed = []
        for r in revs:
            if not isinstance(r, dict):
                continue
            has = [k for k in ("citation", "scope", "how_it_differs_from_ours")
                   if str(r.get(k) or "").strip()]
            if len(has) == 3:
                already += 1
                continue

            if not str(r.get("citation") or "").strip():
                bits = [str(r.get(k) or "").strip()
                        for k in ("title", "journal", "year")]
                bits = [b for b in bits if b]
                if bits:
                    r["citation"] = ". ".join(bits)
                    changed.append("citation")
            if not str(r.get("scope") or "").strip():
                t = str(r.get("outcome_pooled") or "").strip()
                if t:
                    r["scope"] = t
                    changed.append("scope")
            if not str(r.get("how_it_differs_from_ours") or "").strip():
                t = (str(r.get("agreement") or "").strip()
                     or str(r.get("why_not_comparable") or "").strip())
                if t:
                    r["how_it_differs_from_ours"] = t
                    changed.append("how_it_differs_from_ours")

            pmid = str(r.get("pmid") or "")
            if pmid in THEIR_K_FROM_PROSE and not r.get("their_k"):
                k, quote = THEIR_K_FROM_PROSE[pmid]
                ts = r.get("trial_set")
                joined = " ".join(str(x) for x in ts) if isinstance(ts, list) else str(ts)
                if quote.split(",")[0] not in joined:
                    sys.exit("REFUSED: PMID %s on %s does not carry the sentence this count "
                             "was transcribed from (%r). Transcribing a number from a "
                             "sentence that is no longer there is how a count becomes "
                             "detached from its source.\n  found: %r"
                             % (pmid, topic, quote, joined[:200]))
                r["their_k"] = k
                r["their_k_basis"] = (
                    "TRANSCRIBED FROM THIS RECORD'S OWN STORED SENTENCE, %r, which states "
                    "the count as a WORD. No included-study list was read, so this is a "
                    "COUNT AND NOT AN IDENTIFICATION -- which trials they carry remains "
                    "unestablished. Written by hand rather than parsed, because a number "
                    "spelled out is exactly what an automated count misses." % quote)
                changed.append("their_k")
                k_written += 1
                seen_prose.add(pmid)
            repaired += 1

        if changed:
            touched += 1
            obj.setdefault("display_change_announced", []).append({
                "date": TODAY,
                "change": "the published-comparison table rendered blank cells; repaired",
                "values_moved": "NONE",
                "what_changed": ("added %s to the comparison record(s); nothing renamed, "
                                 "nothing removed" % ", ".join(sorted(set(changed)))),
                "why": ("The projector reads `citation`/`their_k`/`scope`/"
                        "`how_it_differs_from_ours`; these records stored `title`/"
                        "`journal`/`outcome_pooled`/`agreement`. A reader met a PMID and "
                        "four empty cells. Registry class 83."),
            })
            print("%-44s + %s" % (topic[:44], ", ".join(sorted(set(changed)))))
            if not dry:
                atomic_write.write_json(path, obj, indent=1)

    missing = sorted(set(THEIR_K_FROM_PROSE) - seen_prose)
    print("\n%d record(s) repaired across %d topic(s); %d already carried the projector's "
          "keys; %d trial counts transcribed from prose."
          % (repaired, touched, already, k_written))
    if missing and not dry:
        sys.exit("PROOF FAILED: %d prose count(s) were declared here and never applied to "
                 "any record -- %s. A table of hand-written values that silently matches "
                 "nothing is the failure this exit exists to prevent."
                 % (len(missing), ", ".join(missing)))
    if dry:
        print("DRY RUN -- pass --apply to write")


if __name__ == "__main__":
    main()
