#!/usr/bin/env python3
"""Objects that NAME a repository path — does the thing at the end of it exist, and is it used?

STANDING ORDER 9a's COMPANION: "when a fix touches a path, ENUMERATE THE TARGET". The 10-page
placeholder leak was a path INTO protocols/; the path was fixed as a string and nobody asked
what it pointed at. 92 pages then denied protocols that were sitting in the repository.

FOUND AGAIN, 2026-08-28, by following one finding rather than filing it:
    colchicine-pericarditis names sources.literature_extraction =
    evidence/2026-08-19-batch1/pericarditis_publication_extraction.json
    That file EXISTS -- 11,158 bytes, four trials, each with acronym, PMID, DOI, citation and
    VERBATIM QUOTES for population and primary outcome. The object holds ZERO per_trial rows.
    The finding was filed as evidence-blocked. The evidence was in the repository.

THREE STATES, because "the path is dead" and "the path is live but unused" are different facts
and only the second is recoverable work:
    TARGET_MISSING   the object names a path that does not exist
    TARGET_UNUSED    the target exists and the object does not carry what it holds
    TARGET_USED      the target exists and its content is reflected in the object

LAYER: store objects, plus the filesystem the object points into. Not served bytes -- this is
about what the object could show and does not.

WHAT THIS CANNOT DO, stated: "used" is judged by whether identifiers found in the target also
appear in the object. A target whose value is prose rather than identifiers cannot be judged
that way and is reported NOT_ASSESSABLE rather than counted as unused.
"""
import io
import json
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
OUT = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
PATHLIKE = re.compile(r"(?<![\w/])((?:evidence|outputs|sources|figs|protocols|scripts|data)"
                      r"/[\w./-]+\.(?:json|jsonl|csv|txt|md))")
NCT = re.compile(r"NCT\d{8}")


def say(s=""):
    OUT.write(s + "\n")
    OUT.flush()


def walk(o, p=""):
    if isinstance(o, dict):
        for k, v in o.items():
            yield from walk(v, p + "/" + str(k))
    elif isinstance(o, list):
        for i, v in enumerate(o):
            yield from walk(v, p + "/%d" % i)
    else:
        yield p, o


def main():
    rows = []
    objects = 0
    skipped_not_dir = 0
    skipped_no_object = 0
    for topic in sorted(os.listdir(os.path.join(ROOT, "ssot"))):
        d = os.path.join(ROOT, "ssot", topic)
        # POSITIVE FORM: name the property an entry must HOLD to be read, and count what is
        # declined. `if not X: continue` in a corpus loop reads as an absence in the world
        # rather than as an item the sweep never opened.
        if os.path.isdir(d):
            p = os.path.join(d, topic + ".json")
        else:
            skipped_not_dir += 1
            continue
        if os.path.exists(p):
            pass
        else:
            skipped_no_object += 1
            continue
        try:
            obj = json.load(io.open(p, encoding="utf-8"))
        except Exception:
            continue
        objects += 1
        blob = json.dumps(obj, ensure_ascii=False)
        obj_ncts = set(NCT.findall(blob))
        seen = set()
        for key, val in walk(obj):
            if isinstance(val, str):
                pass
            else:
                continue
            for m in PATHLIKE.finditer(val):
                rel = m.group(1)
                if rel in seen:
                    continue
                seen.add(rel)
                full = os.path.join(ROOT, rel)
                if os.path.exists(full):
                    pass
                else:
                    rows.append(dict(topic=topic, field=key, path=rel,
                                     state="TARGET_MISSING",
                                     why="the object names this path and nothing is there"))
                    continue
                try:
                    payload = io.open(full, encoding="utf-8", errors="replace").read()
                except Exception:
                    continue
                tgt_ncts = set(NCT.findall(payload))
                if tgt_ncts:
                    pass
                else:
                    rows.append(dict(topic=topic, field=key, path=rel, bytes=len(payload),
                                     state="NOT_ASSESSABLE",
                                     why="the target carries no identifiers, so whether the "
                                         "object uses it cannot be judged this way"))
                    continue
                unused = tgt_ncts - obj_ncts
                if unused == tgt_ncts:
                    rows.append(dict(topic=topic, field=key, path=rel, bytes=len(payload),
                                     state="TARGET_UNUSED",
                                     why="the target holds %d identifier(s), NONE of which "
                                         "appear in the object: %s"
                                         % (len(tgt_ncts), ", ".join(sorted(tgt_ncts)[:5]))))
                elif unused:
                    rows.append(dict(topic=topic, field=key, path=rel, bytes=len(payload),
                                     state="TARGET_PARTLY_USED",
                                     why="%d of %d identifier(s) in the target are absent from "
                                         "the object: %s"
                                         % (len(unused), len(tgt_ncts),
                                            ", ".join(sorted(unused)[:5]))))
                else:
                    rows.append(dict(topic=topic, field=key, path=rel, bytes=len(payload),
                                     state="TARGET_USED",
                                     why="every identifier in the target also appears in the "
                                         "object"))

    counts = {}
    for r in rows:
        counts[r["state"]] = counts.get(r["state"], 0) + 1
    say("*** COUNTS WITHHELD -- THIS INSTRUMENT DOES NOT MEASURE WHAT IT WAS WRITTEN FOR. ***")
    say("Validated against the case that motivated it and it FAILED IN BOTH DIRECTIONS:")
    say("  MISSED IT: colchicine-pericarditis names a topic-scoped extraction holding four")
    say("    trials with verbatim population and primary-outcome quotes. The object carries")
    say("    ZERO per_trial rows and does not use that content -- yet this reports TARGET_USED,")
    say("    because the four NCT ids happen to appear in inputs.trials. IDENTIFIER PRESENCE IS")
    say("    NOT CONTENT USE, and the whole point was the content.")
    say("  FLAGGED THE WRONG THING: 26 of the flagged targets hold 101+ identifiers. Those are")
    say("    corpus-wide CANDIDATE POOLS -- a screening cascade of 357 NCTs, a reconcile file of")
    say("    486. An object is SUPPOSED to carry almost none of them; absence is the filter")
    say("    working. Counting that as evidence-ignored is the candidate-pool-as-denominator")
    say("    error again.")
    say("The one real finding here was reached by following a finding by hand, not by this")
    say("sweep, and it stands on its own evidence. The rows are kept for diagnosis; the counts")
    say("are not a defect count and must not be quoted as one.")
    say("")
    say("LAYER: store objects + the filesystem they point into.")
    say("objects read: %d | path references found: %d" % (objects, len(rows)))
    say("")
    say("%-22s %s" % ("STATE", "n"))
    for k in ("TARGET_USED", "TARGET_PARTLY_USED", "TARGET_UNUSED", "TARGET_MISSING",
              "NOT_ASSESSABLE"):
        say("%-22s %d" % (k, counts.get(k, 0)))
    say("")
    for state in ("TARGET_UNUSED", "TARGET_PARTLY_USED"):
        hits = [r for r in rows if r["state"] == state]
        if not hits:
            continue
        say("%s -- evidence in the repository the object does not carry:" % state)
        for r in hits[:15]:
            say("   %-30s %s" % (r["topic"][:30], r["path"][:70]))
            say("        %s" % r["why"][:130])
        if len(hits) > 15:
            say("   ... +%d more" % (len(hits) - 15))
        say("")
    with io.open(os.path.join(ROOT, "out", "named_paths_sweep.json"), "w",
                 encoding="utf-8", newline="\n") as fh:
        json.dump({"objects": objects, "counts": counts, "rows": rows},
                  fh, indent=1, ensure_ascii=False)
    say("declined to open, counted rather than dropped: %d non-directory entries, %d topic "
        "dirs with no canonical object" % (skipped_not_dir, skipped_no_object))
    say("wrote out/named_paths_sweep.json")
    return 0


if __name__ == "__main__":
    sys.exit(main())
