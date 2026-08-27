"""Render a topic's trials as material for an author, DERIVED FROM THE SCHEMA.

WHY THIS REPLACED A HAND-LISTED SET OF FIELD NAMES. Twice in one batch a disagreement
between two authoring families turned out to be caused by this extractor rather than by
the families:

  round 1  emitted only outcome KEYS          -> one family refused for want of a named
                                                 quantity, the other supplied one from
                                                 its own knowledge
  round 2  added `registered_primaries`       -> THE SAME TWO FAMILIES SWAPPED SIDES
  round 3  added `registered_secondaries`     -> both authored, neither refused

Same models, same topic, opposite answers, only the material changed. So an agreement
rate computed over round 1 would have been a statement about this file wearing the
clothes of a statement about models.

A hand-listed set of field names is the vocabulary problem this project has now met in a
regex, a path list, a label matcher, a proxy join and an estimand check. The fix is the
same every time: DERIVE THE VOCABULARY FROM THE DATA. The schema here is the union of
keys actually present on trial records across the whole corpus; every key a trial has is
emitted, so forgetting one is not possible.

AND THE MATERIAL DECLARES ITS OWN COMPLETENESS. The standing rule is that no agreement or
disagreement rate may be quoted unless both families received the same COMPLETE material
and the material was sufficient to answer. Nothing in a two-family protocol checks that,
so the material states, in its own text: which schema keys this trial carries, which it
does not, and every value that was truncated. An author that refuses can then say whether
it refused for want of evidence or for want of a coherent question, and the two are
different findings.
"""
import io
import json
import os
import sys
from collections import Counter

# GUARDED. A module-level stdout reassignment closes the CALLER's stdout when this
# file is imported -- documented in this project's own register, and it bit here
# within an hour of the extractor being written. A module that is imported must not
# reach into the interpreter's I/O.
if __name__ == "__main__":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8",
                                  errors="replace")

S = r"F:\claude-temp\claude\C--Users-mahmo\f842b4e4-f3de-4ce2-83d8-0adf7aa7cfb1\scratchpad"
SSOT = os.path.join(S, "main-wt", "ssot")

# Keys whose CONTENT is provenance rather than evidence about the trial. Emitting them
# would bury the material without adding anything an author can reason from. They are
# named here and REPORTED as omitted, not silently dropped -- a filter that removes
# candidates before counting is the likeliest place to lose the population.
PROVENANCE_KEYS = {
    "provenance", "source_quotes", "quote_note", "all_ranks_read_utc",
    "registration_counts_read_utc", "registration_contrasts_read_utc",
    "registration_read_utc", "label_source", "cascade",
}
VALUE_CAP = 400


def corpus_schema():
    """The union of keys present on trial records across the corpus. This IS the schema."""
    keys, nested = Counter(), Counter()
    # Written as the POSITIVE property -- "is a topic store" -- rather than a negative
    # guard that `continue`s past everything else. A negative guard inside a corpus loop
    # decides what a sweep reaches, and this loop defines the SCHEMA: a store skipped
    # here is a set of field names that never enters the vocabulary, which is precisely
    # the failure this file was written to end.
    unreadable = []
    for topic in sorted(os.listdir(SSOT)):
        f = os.path.join(SSOT, topic, topic + ".json")
        if os.path.isfile(f):
            try:
                obj = json.load(open(f, encoding="utf-8"))
            except Exception as exc:
                # Counted and named, never silently dropped: a store this cannot parse
                # is a hole in the derived schema and the caller should know its size.
                unreadable.append(topic + " (" + type(exc).__name__ + ")")
                obj = None
            if obj is not None:
                for t in ((obj.get("inputs") or {}).get("trials") or []):
                    if isinstance(t, dict):
                        for k in t:
                            keys[k] += 1
                        for blk in (t.get("by_outcome") or {}).values():
                            if isinstance(blk, dict):
                                for k in blk:
                                    nested[k] += 1
    if unreadable:
        keys["__UNREADABLE_STORES__"] = len(unreadable)
    return keys, nested


def _render(value, cap=VALUE_CAP):
    s = value if isinstance(value, str) else json.dumps(value, ensure_ascii=False)
    if len(s) > cap:
        return s[:cap], len(s)
    return s, 0


def render_trial(trial, schema_keys, nested_keys, truncated):
    out, present = [], set()
    for k in sorted(trial):
        if k in PROVENANCE_KEYS:
            continue
        present.add(k)
        if k == "by_outcome":
            for okey, blk in (trial[k] or {}).items():
                out.append("      outcome '" + okey + "':")
                if isinstance(blk, dict):
                    for nk in sorted(blk):
                        if nk in PROVENANCE_KEYS:
                            continue
                        txt, full = _render(blk[nk])
                        if full:
                            truncated.append(okey + "." + nk + " (%d chars)" % full)
                        out.append("          " + nk + ": " + txt)
            continue
        # A LIST IS RENDERED PER ITEM, NOT DUMPED AND CUT. json.dumps of a list
        # followed by a character cap severs it mid-item, and the item lost is as
        # likely to be the decisive one as any other: `registered_secondaries` is
        # where ATTRibute-CM records that its mortality endpoint bundles heart
        # transplant and mechanical assist, which is the fact that decides whether
        # this topic is poolable on mortality at all.
        v = trial[k]
        if isinstance(v, list) and v:
            out.append("      " + k + ":")
            for item in v:
                txt, full = _render(item)
                if full:
                    truncated.append(k + "[] item (%d chars)" % full)
                out.append("          - " + txt)
        else:
            txt, full = _render(v)
            if full:
                truncated.append(k + " (%d chars)" % full)
            out.append("      " + k + ": " + txt)
    missing = sorted(set(schema_keys) - present - PROVENANCE_KEYS)
    return out, present, missing


def material(topic):
    """Return (text, completeness) for one topic."""
    schema_keys, nested_keys = corpus_schema()
    obj = json.load(open(os.path.join(SSOT, topic, topic + ".json"), encoding="utf-8"))
    trials = ((obj.get("inputs") or {}).get("trials") or [])
    truncated, all_missing = [], {}
    lines = ["TOPIC TITLE: " + str(obj.get("title") or "<none>"), "",
             "THE TRIALS THIS REVIEW HOLDS (%d):" % len(trials)]
    for t in trials:
        if not isinstance(t, dict):
            continue
        name = t.get("name") or t.get("acronym") or t.get("id") or "<unnamed>"
        lines.append("  --- " + str(name))
        body, present, missing = render_trial(t, schema_keys, nested_keys, truncated)
        lines.extend(body)
        all_missing[str(name)] = missing

    lines += ["", "COMPLETENESS OF THIS MATERIAL -- stated so that a refusal can be read",
              "correctly. An author refusing for want of EVIDENCE and an author refusing",
              "for want of a coherent QUESTION are different findings.",
              "  schema: %d distinct keys are used on trial records across this corpus."
              % len(schema_keys)]
    for name, missing in all_missing.items():
        lines.append("  %s: carries %d of them; DOES NOT CARRY: %s"
                     % (name, len(schema_keys) - len(missing),
                        ", ".join(missing[:14]) if missing else "none"))
    lines.append("  values truncated at %d chars: %s"
                 % (VALUE_CAP, ", ".join(truncated) if truncated else "none"))
    lines.append("  provenance keys omitted by design: " + ", ".join(sorted(PROVENANCE_KEYS)))
    lines.append("If a field you need is listed as NOT CARRIED or truncated, say so in "
                 "CONCERNS rather than supplying the value from your own knowledge.")
    return "\n".join(lines), {"truncated": truncated, "missing": all_missing,
                              "schema_size": len(schema_keys)}


if __name__ == "__main__":
    keys, nested = corpus_schema()
    print("TRIAL-RECORD SCHEMA, derived from the corpus (not hand-listed)")
    print("  %d distinct keys on trial records; %d on by_outcome blocks\n"
          % (len(keys), len(nested)))
    for k, v in keys.most_common():
        mark = "  (provenance, omitted)" if k in PROVENANCE_KEYS else ""
        print("    x%-5d %s%s" % (v, k, mark))
    if len(sys.argv) > 1:
        text, comp = material(sys.argv[1])
        print("\n" + "=" * 70)
        print(text)
