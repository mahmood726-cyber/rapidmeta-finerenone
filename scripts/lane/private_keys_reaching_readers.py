#!/usr/bin/env python3
"""Which "private" keys in the store actually reach a reader? LAYERS: store objects + served bytes.

THERE IS NO PRIVATE KEY IN A RENDERED STORE. The generator renders unknown keys generically, so
any field added to an object is a field a reader may be shown. This was learned by doing it: a
fix on 2026-08-28 preserved a superseded sentence in `subject_scope_flag_was` to keep the
record, and the "fixed" page printed that stale sentence straight back to the reader. Git holds
history; an object does not.

TWO LAYERS, BECAUSE THE COUNT THAT MATTERS IS THE SECOND. Counting keys in the store measures
housekeeping. Counting the ones whose VALUES appear in the served bytes measures what a reader
is actually shown, and only that second number is a defect count. Both are printed, and they
are not summed.

It is a sweep, not a gate: it returns counts and never a verdict, so it must not carry a name
that promises a block.

WHAT IT CANNOT DO, named rather than implied: a short value ("none", a date) may coincide with
unrelated page text, so a match on a value under ~25 characters is reported separately as
UNRELIABLE rather than counted. And it reads the page as rendered text with scripts stripped --
markup a reader never sees is not page content.
"""
import io
import json
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
OUT = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
TAG = re.compile(r"<[^>]+>")
WS = re.compile(r"\s+")
SCRIPT = re.compile(r"(?is)<(script|style)\b.*?</\1>")

# Names that announce "this is not for the reader". Deliberately a NAMED list rather than a
# guess: each has been seen on this project, and the list is printed so it can be argued with.
PRIVATE = re.compile(r"(?i)(^|_)(was|old|previous|prior|superseded|internal|note|notes|"
                     r"debug|tmp|temp|scratch|todo|fixme)$")


def say(s=""):
    OUT.write(s + "\n")
    OUT.flush()


def rendered(html):
    return WS.sub(" ", TAG.sub(" ", SCRIPT.sub(" ", html))).strip()


def walk(o, path=""):
    if isinstance(o, dict):
        for k, v in o.items():
            yield from walk(v, path + "/" + str(k))
    elif isinstance(o, list):
        for i, v in enumerate(o):
            yield from walk(v, path + "/%d" % i)
    else:
        yield path, o


def main():
    pm = json.load(io.open(os.path.join(ROOT, "ssot", "PAGE_MAP.json"), encoding="utf-8"))
    obj2page = {v.replace("\\", "/"): k for k, v in pm.items()}

    objects = 0
    with_private = 0
    key_hits = []
    reaching = []
    unreliable = 0

    # POSITIVE FORM THROUGHOUT. `if not X: continue` in a corpus loop is the shape that lets a
    # sweep report compliance it never measured -- the skip reads as an absence in the world
    # rather than as an item the sweep declined to open. Each condition below names the property
    # an item must HOLD, and everything that fails one is COUNTED rather than silently dropped.
    skipped_not_a_topic_dir = 0
    skipped_no_canonical_object = 0
    skipped_unparseable = 0
    no_served_page = 0

    for topic in sorted(os.listdir(os.path.join(ROOT, "ssot"))):
        d = os.path.join(ROOT, "ssot", topic)
        if os.path.isdir(d):
            p = os.path.join(d, topic + ".json")
        else:
            skipped_not_a_topic_dir += 1
            continue
        if os.path.exists(p):
            try:
                obj = json.load(io.open(p, encoding="utf-8"))
            except Exception:
                skipped_unparseable += 1
                continue
        else:
            skipped_no_canonical_object += 1
            continue
        objects += 1
        rel = "ssot/%s/%s.json" % (topic, topic)
        page = obj2page.get(rel)
        text = None
        if page:
            fp = os.path.join(ROOT, page)
            if os.path.exists(fp):
                text = rendered(io.open(fp, encoding="utf-8", errors="replace").read())

        found = []
        for path, val in walk(obj):
            leaf = path.rsplit("/", 1)[-1]
            # POSITIVE: the field must BE private-named AND carry testable text.
            if PRIVATE.search(leaf) and isinstance(val, str) and val.strip():
                found.append((path, val))
        if found:
            with_private += 1
        else:
            continue
        for path, val in found:
            key_hits.append((topic, path, len(val)))
            if text is not None:
                pass
            else:
                no_served_page += 1
                continue
            probe = WS.sub(" ", val).strip()
            if len(probe) < 25:
                unreliable += 1
                continue
            # a distinctive slice, long enough that coincidence is implausible
            slice_ = probe[:120]
            if slice_ in text:
                reaching.append((topic, page, path, slice_[:90]))

    say("LAYERS: store objects, then served bytes. The second count is the defect count.")
    say("")
    say("STORE")
    say("  objects read                       : %d" % objects)
    say("  carrying at least one private key   : %d" % with_private)
    say("  private-key fields in total         : %d" % len(key_hits))
    say("")
    say("SERVED BYTES -- the number that matters")
    say("  private-key VALUES found on the page: %d" % len(reaching))
    say("  fields with no served page to test  : %d" % no_served_page)
    say("  values too short to test (<25 chars): %d  -- reported, not counted, because a short"
        % unreliable)
    say("                                          value can coincide with unrelated prose")
    say("")
    if reaching:
        say("REACHING A READER:")
        for topic, page, path, s in reaching[:25]:
            say("   %-34s %-46s" % (topic[:34], path[:46]))
            say("        %s..." % s)
        if len(reaching) > 25:
            say("   ... +%d more" % (len(reaching) - 25))
    else:
        say("No private-key value was found in any served page.")

    with io.open(os.path.join(ROOT, "out", "private_keys_sweep.json"), "w",
                 encoding="utf-8", newline="\n") as fh:
        json.dump({"objects": objects, "objects_with_private_key": with_private,
                   "private_key_fields": len(key_hits),
                   "values_reaching_a_reader": len(reaching),
                   "too_short_to_test": unreliable,
                   "reaching": [{"topic": t, "page": p, "path": k, "sample": s}
                                for t, p, k, s in reaching],
                   "fields": [{"topic": t, "path": k, "len": n} for t, k, n in key_hits]},
                  fh, indent=1, ensure_ascii=False)
    say("")
    say("")
    say("WHAT THE SWEEP DECLINED TO OPEN, counted rather than dropped:")
    say("  entries in ssot/ that are not topic directories : %d" % skipped_not_a_topic_dir)
    say("  topic dirs with no canonical <topic>.json       : %d" % skipped_no_canonical_object)
    say("  objects that would not parse                    : %d" % skipped_unparseable)
    say("wrote out/private_keys_sweep.json")
    return 0


if __name__ == "__main__":
    sys.exit(main())
