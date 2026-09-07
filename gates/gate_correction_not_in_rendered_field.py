"""A withdrawn or superseded claim must not stay live in a rendered field.

DEFECT, 2026-09-07. A correction was recorded beside the live text while the
field a page renders still asserted the old claim. Regeneration then reads the
rendered field, not the note, and publishes the retracted claim again.
"""
from __future__ import annotations

import glob
import html
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _harness as H                                                        # noqa: E402

MIN_WORDS = 6
MARKER_WINDOW = 120
WORD = re.compile(r"[a-z0-9]+", re.I)
WS = re.compile(r"\s+")
RETRACTION = re.compile(r"\b(withdrawn|superseded|retracted|no longer)\b", re.I)
CLAIM_FIELD = re.compile(r"^CLAIM_WITHDRAWN_", re.I)
SUPERSEDED_FIELD = re.compile(r"(^|_)superseded(_|$)", re.I)

STOP = set("""
a about above after again against all also an and any are as at be because been
before being beside between both but by can cannot could did do does each either
for from has have here in into is it its itself not of on one or other over own
rather same see so than that the their them then there these they this those to
under was were what when where which while who whose why with without would
""".split())

CLAIM_CUES = [
    re.compile(r"\basserted\s+that\s+(.+?)(?:[.;]|$)", re.I),
    re.compile(r"\bclaimed\s+that\s+(.+?)(?:[.;]|$)", re.I),
    re.compile(r"\bclaim\s+that\s+(.+?)(?:[.;]|$)", re.I),
    re.compile(r"\b(?:previously|earlier)\s+(?:read|said|stated|asserted|claimed)\s+"
               r"['\"]?(.+?)(?:['\"]|[.;]|$)", re.I),
    re.compile(r"\b(?:what it said|withdrawn text)\s*[:\-]\s*['\"]?(.+?)"
               r"(?:['\"]|[.;]|$)", re.I),
]


def norm(text):
    text = html.unescape(str(text)).lower()
    text = text.replace("'", " ")
    text = re.sub(r"[^a-z0-9]+", " ", text)
    text = re.sub(r"\bthis review s\b", "these", text)
    return WS.sub(" ", text).strip()


def words(text):
    return WORD.findall(html.unescape(str(text)).lower())


def distinctive(tokens):
    return len([w for w in tokens if w not in STOP and len(w) >= 4]) >= 3


def best_phrase(fragment):
    toks = words(fragment)
    if len(toks) < MIN_WORDS:
        return None
    if any(w in ("withdrawn", "superseded", "retracted") for w in toks):
        return None
    if "no" in toks and "longer" in toks:
        return None

    if len(toks) <= 14 and distinctive(toks):
        return " ".join(toks)

    if any(any(ch.isdigit() for ch in w) for w in toks):
        for width in range(min(12, len(toks)), MIN_WORDS - 1, -1):
            for i in range(0, len(toks) - width + 1):
                cand = toks[i:i + width]
                if any(any(ch.isdigit() for ch in w) for w in cand) and distinctive(cand):
                    return " ".join(cand)

    best = None
    best_score = -1
    for width in range(12, MIN_WORDS - 1, -1):
        for i in range(0, len(toks) - width + 1):
            cand = toks[i:i + width]
            if not distinctive(cand):
                continue
            score = sum(1 for w in cand if w not in STOP and len(w) >= 4)
            score += sum(1 for w in cand if len(w) >= 8)
            if score > best_score:
                best = cand
                best_score = score
    return " ".join(best) if best else None


def sentence_fragments(text):
    text = WS.sub(" ", html.unescape(str(text))).strip()
    if not text:
        return []
    out = []
    for cue in CLAIM_CUES:
        out.extend(m.group(1).strip(" '\"") for m in cue.finditer(text))
    if out:
        return out
    return [s.strip(" '\"") for s in re.split(r"(?<=[.!?])\s+", text) if s.strip()]


def claim_phrase(text):
    for frag in sentence_fragments(text):
        phrase = best_phrase(frag)
        if phrase:
            return phrase
    return None


def collect_strings(node, path):
    if isinstance(node, str):
        yield path, node
    elif isinstance(node, dict):
        for k, v in node.items():
            child = "%s.%s" % (path, k) if path else str(k)
            for item in collect_strings(v, child):
                yield item
    elif isinstance(node, list):
        for i, v in enumerate(node):
            child = "%s[%d]" % (path, i)
            for item in collect_strings(v, child):
                yield item


def correction_sources(doc):
    sources = []

    def visit(node, path):
        if not isinstance(node, dict):
            return
        for k, v in node.items():
            child = "%s.%s" % (path, k) if path else str(k)
            is_claim = CLAIM_FIELD.search(str(k)) is not None
            is_superseded = SUPERSEDED_FIELD.search(str(k)) is not None
            if is_claim or is_superseded:
                phrases = []
                for spath, text in collect_strings(v, child):
                    phrase = claim_phrase(text)
                    if phrase and phrase not in phrases:
                        phrases.append(phrase)
                if phrases:
                    sources.append({
                        "path": child,
                        "kind": "CLAIM_WITHDRAWN" if is_claim else "SUPERSEDED",
                        "phrases": phrases,
                    })
            visit(v, child)

    visit(doc, "")
    return sources


def rendered_fields(doc):
    fields = []
    pc = doc.get("published_comparison") if isinstance(doc, dict) else None
    if isinstance(pc, dict) and isinstance(pc.get("_why"), str):
        fields.append(("published_comparison._why", pc["_why"]))

    results = doc.get("results") if isinstance(doc, dict) else None
    by_outcome = results.get("by_outcome") if isinstance(results, dict) else None
    if isinstance(by_outcome, dict):
        for outcome, block in sorted(by_outcome.items()):
            if not isinstance(block, dict):
                continue
            for leaf in ("heterogeneity_status", "interpretation_caveat"):
                if isinstance(block.get(leaf), str):
                    fields.append(("results.by_outcome.%s.%s" % (outcome, leaf),
                                   block[leaf]))

    grade = doc.get("grade") if isinstance(doc, dict) else None
    if isinstance(grade, dict):
        for path, node in H.walk(grade):
            if path.endswith(".summary") and isinstance(node, str):
                fields.append(("grade%s" % path, node))
    return fields


def has_nearby_retraction_marker(haystack, start, end):
    left = max(0, start - MARKER_WINDOW)
    right = min(len(haystack), end + MARKER_WINDOW)
    return RETRACTION.search(haystack[left:right]) is not None


def scan_object(object_id, doc):
    firings = []
    sources = correction_sources(doc)
    rendered = rendered_fields(doc)
    for source in sources:
        for rpath, text in rendered:
            hay = norm(text)
            if not hay:
                continue
            for phrase in source["phrases"]:
                needle = norm(phrase)
                if len(needle.split()) < MIN_WORDS:
                    continue
                pos = hay.find(needle)
                if pos < 0:
                    continue
                if has_nearby_retraction_marker(hay, pos, pos + len(needle)):
                    continue
                firings.append({
                    "object": object_id,
                    "correction_path": source["path"],
                    "rendered_path": rpath,
                    "phrase": phrase,
                })
                break
    return firings


def control_docs():
    withdrawn = ("A CLAIM ON THIS OBJECT IS WITHDRAWN AS FALSE. It asserted that "
                 "no published synthesis pools these two trials.")
    positive = {
        "CLAIM_WITHDRAWN_2026_09_07": withdrawn,
        "published_comparison": {
            "_why": ("No published synthesis pools these two trials, so this review "
                     "has no exact comparator.")
        },
    }
    negative = {
        "CLAIM_WITHDRAWN_2026_09_07": withdrawn,
        "published_comparison": {
            "_why": ("The earlier claim that no published synthesis pools these two "
                     "trials was withdrawn as false on 2026-09-07.")
        },
    }
    return positive, negative


def main(argv):
    gate = H.Gate("CORRECTION NOT IN RENDERED FIELD",
                  "a withdrawn or superseded claim must not remain live in rendered text")
    gate.expect_case("PINNED_RETRACTED_CLAIM_LIVE",
                     "withdrawal names 'no published synthesis pools these two trials' "
                     "and published_comparison._why still asserts it plainly")
    gate.requires_control()

    pos_doc, neg_doc = control_docs()
    pos = scan_object("__positive_control__", pos_doc)
    neg = scan_object("__negative_control__", neg_doc)
    if len(pos) == 1:
        gate.saw("PINNED_RETRACTED_CLAIM_LIVE")
    else:
        gate.broken("positive control fired %d time(s), expected exactly 1" % len(pos))
    gate.control(1, len(neg),
                 ["negative control fired at %s via %r"
                  % (f["rendered_path"], f["phrase"]) for f in neg],
                 accuses=True)

    repo = H.repo_root()
    paths = sorted(glob.glob(os.path.join(repo, "ssot", "*", "*.json")))
    if not paths:
        gate.broken("no JSON objects matched ssot/*/*.json from %s" % repo)
        gate.kinds({"json objects scanned from ssot/*/*.json": 0})
        gate.coverage(0, 0, "no corpus objects were reachable")
        return gate.report(denominator="0 ssot/*/*.json objects")

    findings = []
    n_objects = 0
    n_load_failed = 0
    n_claim_objects = 0
    n_superseded_objects = 0
    n_source_objects = 0
    rendered_total = 0
    rendered_checked = 0

    for path in paths:
        try:
            doc = H.load(path)
        except Exception as e:
            n_load_failed += 1
            gate.broken("%s could not be parsed as JSON: %s"
                        % (os.path.relpath(path, repo), e))
            continue
        if not isinstance(doc, dict):
            continue
        n_objects += 1
        object_id = H.topic_id(path)
        fields = rendered_fields(doc)
        sources = correction_sources(doc)
        rendered_total += len(fields)
        if any(s["kind"] == "CLAIM_WITHDRAWN" for s in sources):
            n_claim_objects += 1
        if any(s["kind"] == "SUPERSEDED" for s in sources):
            n_superseded_objects += 1
        if sources:
            n_source_objects += 1
            rendered_checked += len(fields)
        findings.extend(scan_object(object_id, doc))

    if n_objects == 0:
        gate.broken("ssot/*/*.json matched files, but none loaded to a JSON object")

    gate.kinds({
        "json objects scanned from ssot/*/*.json": n_objects,
        "json files that failed to load": n_load_failed,
        "objects with CLAIM_WITHDRAWN_* phrases": n_claim_objects,
        "objects with *_superseded* phrases": n_superseded_objects,
        "objects with any extracted correction phrase": n_source_objects,
        "rendered fields found": rendered_total,
        "rendered fields compared with correction phrases": rendered_checked,
        "correction-source/rendered-field firings": len(findings),
    })
    gate.coverage(rendered_checked, rendered_total,
                  "rendered fields in objects with no extracted CLAIM_WITHDRAWN_* or "
                  "*_superseded* phrase to compare")

    for f in findings:
        gate.finding("CORRECTION-NOT-IN-RENDERED-FIELD",
                     "%s: %s repeats phrase from %s without a nearby retraction "
                     "marker: %r"
                     % (f["object"], f["rendered_path"], f["correction_path"],
                        f["phrase"]))

    gate.note("pinned negative held when the same phrase was followed by 'withdrawn "
              "as false' inside the rendered field")
    return gate.report(denominator="%d ssot/*/*.json objects; %d firings = %d findings"
                       % (n_objects, len(findings), len(findings)))


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
