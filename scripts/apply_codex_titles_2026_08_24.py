"""Apply the Codex-derived titles, after re-verifying every evidence string myself.

WHERE THESE CAME FROM. `codex exec -s workspace-write` (gpt-5.5) read all 58 objects whose
title was still a bare slug after the reads-terribly repair and proposed a title for each,
recording for every substantive noun the field path and the verbatim source string it came
from. Round 1 proposed 8 and nulled 50 -- because MY field list was wrong, not because the
evidence was absent: I told it to read `inputs.trials[].name`, which is null on most of
these objects, when the trial title actually lives in `inputs.trials[].label`. Round 2, with
the corrected field list, proposed 39 and nulled 19.

WHY THE PROPOSALS ARE NOT TAKEN ON TRUST. Round 1 put three registry ARM LABELS into titles
-- "Dabigatran dose 1", "Malaria Vaccine 257049", "Tecovirimat Oral Capsule". The evidence
was honest; the SOURCE was contaminated, because the `question` field those came from is
itself built from arm labels. That is the label-keying defect `ssot/topic_identity.py` was
written about, surfacing in the reader-facing question. Round 2 was given the rule
explicitly and stripped all three.

THIS SCRIPT RE-VERIFIES RATHER THAN RELAYING. Every evidence string is checked to appear
literally in its own object before that row's title is applied; a row with any unverifiable
string is DROPPED WHOLE, not partially applied. A delegated step that silently did nothing
-- or did something plausible and wrong -- is worse than not delegating, so the check is
here and not in the delegation.

THE QUESTION MOVES WITH THE TITLE. The reads-terribly repair rewrote `question` as
"In <title>, ...". Changing the title and leaving the question would put two different names
for the same review on one page, which is the defect class this whole pass exists to end.

`--apply` writes; default is a dry run.
"""
import io
import json
import os
import re
import sys

if __name__ == "__main__":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
EVIDENCE = os.path.join(REPO, "outputs", "codex_title_evidence_round2_2026_08_24.json")

# The arm-label vocabulary Codex was told to strip. Checked again here, because a rule
# stated in a prompt is not a rule enforced on the output.
ARM_LABEL = re.compile(
    r"\b(dose\s*\d+|arm\s*[A-Z0-9]\b|group\s*[A-Z0-9]\b|oral capsule|oral tablet|"
    r"placebo comparator|active comparator|experimental arm)\b", re.I)


def main():
    apply_ = "--apply" in sys.argv
    rows = json.load(open(EVIDENCE, encoding="utf-8"))["rows"]
    applied, dropped, skipped = [], [], 0

    for r in rows:
        title = (r.get("proposed_title") or "").strip()
        if not title:
            skipped += 1
            continue
        slug = r["slug"]
        path = os.path.join(REPO, "ssot", slug, slug + ".json")
        if not os.path.exists(path):
            dropped.append((slug, "object missing"))
            continue
        obj = json.load(open(path, encoding="utf-8"))
        raw = json.dumps(obj, ensure_ascii=False)

        # RE-VERIFY. Any evidence string that is not literally in the object drops the row.
        missing = [e.get("verbatim", "")[:60] for e in r.get("evidence", [])
                   if e.get("verbatim", "")[:60] not in raw]
        if missing:
            dropped.append((slug, "evidence not in object: %s" % missing[0][:50]))
            continue
        m = ARM_LABEL.search(title)
        if m:
            dropped.append((slug, "arm label survived in title: %r" % m.group(0)))
            continue

        old_title = obj.get("title") or ""
        obj["title"] = title
        # Carry the question with the title so one review does not carry two names.
        q = obj.get("question") or ""
        if old_title and q.startswith("In %s," % old_title):
            obj["question"] = "In %s,%s" % (title, q[len("In %s," % old_title):])
        applied.append((slug, old_title, title))
        if apply_:
            tmp = path + ".tmp"
            with io.open(tmp, "w", encoding="utf-8") as fh:
                json.dump(obj, fh, ensure_ascii=False, indent=1)
            os.replace(tmp, path)

    print("proposals read      : %d" % len(rows))
    print("nulled by codex     : %d" % skipped)
    print("APPLIED             : %d   %s" % (len(applied), "(written)" if apply_ else "(dry run)"))
    print("DROPPED on re-verify: %d" % len(dropped))
    for slug, why in dropped:
        print("    %-40s %s" % (slug, why))
    for slug, old, new in applied[:60]:
        print("    %-38s %-26s -> %s" % (slug, old[:26], new))
    with io.open(os.path.join(REPO, "outputs",
                              "codex_titles_applied_2026_08_24.json"), "w",
                 encoding="utf-8") as fh:
        json.dump({"applied": [{"slug": s, "from": o, "to": n} for s, o, n in applied],
                   "dropped": [{"slug": s, "why": w} for s, w in dropped],
                   "nulled_by_codex": skipped}, fh, ensure_ascii=False, indent=2)
    return 0


if __name__ == "__main__":
    sys.exit(main())
