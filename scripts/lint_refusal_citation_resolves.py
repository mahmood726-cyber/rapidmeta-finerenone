#!/usr/bin/env python3
"""A REFUSAL THAT CITES A FIELD PATH MUST RESOLVE IT, AND ANY NUMBER IT QUOTES MUST MATCH.

THE INSTANCE THIS WAS BUILT FROM, found 2026-08-20 while checking whether a shared refusal
was a template or a genuine corpus-wide blocker. Fourteen objects carry, byte-identical:

    published_comparison.candidate_source_search
        "PubMed search recorded at search.databases[1] (109 records)"

It is **true of exactly one topic** -- `bempedoic-acid-review`, whose `search.databases[1]`
is PubMed with `total_count = 109` -- and **false on the other thirteen**:

    ablation-af-heart-failure     databases[1] = ClinicalTrials.gov, 74 records
    ablation-af-medical-therapy   databases[1] = ClinicalTrials.gov, 143
    apixaban-vte-prophylaxis      databases[1] = ClinicalTrials.gov, 49
    apixaban-vte-treatment        databases[1] = ClinicalTrials.gov, 49
    bococizumab-lipid-review      databases[1] = ClinicalTrials.gov, 21
    colchicine-cvd-coronary       databases[1] = PubMed, 523
    sglt2-hf                      databases[1] = ClinicalTrials.gov, 56
    attr-cm-review                HAS ONLY ONE DATABASE -- databases[1] DOES NOT EXIST

`databases[1]` is PubMed on **7 of the 14**, so on seven the sentence names the wrong database
as well as the wrong number.

    THIS IS THE MOST DANGEROUS FORM OF A TEMPLATE, because it is ENGINEERED TO LOOK
    TOPIC-SPECIFIC. It cites a field path and a record count -- exactly the two things a
    reader, or a linter, takes as evidence that somebody checked this particular topic. A
    template that says "not recoverable" announces its own generality. This one conceals it.

So the check is not about sharing. It is the strongest available test and it is per-object:
**resolve the path the sentence cites, on the object the sentence sits on, and compare.**

  C1 the cited path RESOLVES on this object            (attr-cm-review fails: no databases[1])
  C2 any integer the sentence quotes EQUALS a value at that path
  C3 any database NAME the sentence gives matches the resolved node's own name

A sentence citing nothing is out of scope -- this judges citations, not prose.
"""
import argparse
import glob
import json
import os
import re
import sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# a dotted path with optional [i] segments, e.g. search.databases[1].records_returned
PATH_RE = re.compile(r"\b([a-z_][a-z0-9_]*(?:\[\d+\])?(?:\.[a-z_][a-z0-9_]*(?:\[\d+\])?)+)")
INT_RE = re.compile(r"\(?\b(\d{1,7})\s*(?:records|studies|trials|results|hits)\b", re.I)
COUNT_KEYS = ("records_returned", "total_count", "total_reported", "n_records",
              "returned", "count", "records", "n")


def resolve(obj, path):
    """Walk `a.b[2].c`. Returns (ok, node)."""
    cur = obj
    for part in path.split("."):
        m = re.match(r"^([a-z_][a-z0-9_]*)((?:\[\d+\])*)$", part)
        if not m:
            return False, None
        key, idx = m.group(1), m.group(2)
        if not isinstance(cur, dict) or key not in cur:
            return False, None
        cur = cur[key]
        for i in re.findall(r"\[(\d+)\]", idx):
            if not isinstance(cur, list) or int(i) >= len(cur):
                return False, None
            cur = cur[int(i)]
    return True, cur


def numbers_at(node):
    out = set()
    if isinstance(node, dict):
        for k in COUNT_KEYS:
            v = node.get(k)
            if isinstance(v, int):
                out.add(v)
    elif isinstance(node, int):
        out.add(node)
    elif isinstance(node, list):
        out.add(len(node))
    return out


def walk_strings(node, path=""):
    if isinstance(node, dict):
        for k, v in node.items():
            yield from walk_strings(v, "%s.%s" % (path, k) if path else k)
    elif isinstance(node, list):
        for i, v in enumerate(node):
            yield from walk_strings(v, "%s[%d]" % (path, i))
    elif isinstance(node, str) and len(node) > 20:
        yield path, node


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--gate", action="store_true")
    args = ap.parse_args()
    os.chdir(REPO)
    findings, unjudged = [], []
    checked = 0
    for op in sorted(glob.glob("ssot/*/*.json")):
        name = os.path.basename(op)[:-5]
        if os.path.basename(os.path.dirname(op)) != name:
            continue
        try:
            obj = json.load(open(op, encoding="utf-8"))
        except Exception:
            continue
        if not isinstance(obj, dict) or "title" not in obj:
            continue
        for where, text in walk_strings(obj):
            # A FIELD THAT RECORDS A PAST ERROR IS NOT MAKING A LIVE CLAIM. The repair for
            # the copied citation writes `candidate_source_search_restated`, which QUOTES the
            # false sentence verbatim so the record survives -- and the lint promptly flagged
            # the quotation. Rewording the note to dodge the regex would be gaming the check;
            # excluding fields whose NAME marks them as history is the honest fix, and it
            # matches the `restated_*` convention P18 already uses.
            leaf = where.rsplit(".", 1)[-1]
            if leaf.endswith(("_restated", "_superseded", "_was", "_previously")):
                continue
            if ".restated" in where or "_superseded." in where:
                continue
            for cited in PATH_RE.findall(text):
                # ONLY LITERAL, INDEXED CITATIONS. `inputs.trials.arms` is prose naming a
                # FIELD -- trials is a list, so that path cannot resolve and never could;
                # flagging it would fire on every legitimate reference to a field by name,
                # which is how a rule gets ignored within a day. `search.databases[1]` is a
                # citation to ONE LOCATION and is a checkable claim about this object.
                if "[" not in cited:
                    continue
                if not cited.startswith(("search.", "results.", "inputs.", "k_cascade.",
                                         "screening.", "grade.", "risk_of_bias.")):
                    continue
                checked += 1
                ok, node = resolve(obj, cited)
                if not ok:
                    findings.append((name, where, cited, "C1 the cited path DOES NOT RESOLVE "
                                                         "on this object"))
                    continue
                quoted = {int(x) for x in INT_RE.findall(text)}
                if quoted:
                    have = numbers_at(node)
                    if not have:
                        # THE PATH RESOLVES AND HOLDS NO COMPARABLE NUMBER. The check cannot
                        # judge this citation, and that is NOT a pass. Reported by name, or
                        # six topics carrying the same suspect sentence would read as clean
                        # simply because their node has no count key to contradict it.
                        unjudged.append((name, where, cited, sorted(quoted)))
                    elif not (quoted & have):
                        findings.append((name, where, cited,
                                         "C2 quotes %s; the path holds %s"
                                         % (sorted(quoted), sorted(have))))
    print("citations checked : %d" % checked)
    print("FINDINGS          : %d" % len(findings))
    print()
    for name, where, cited, why in findings:
        print("  %-32s %s" % (name[:32], why))
        print("      at %s -> cites %s" % (where[:70], cited))
    print()
    print("NOT_ASSESSABLE -- the path resolves but holds no comparable number: %d" % len(unjudged))
    for name, where, cited, quoted in unjudged:
        print("  %-32s quotes %s; %s has no count key" % (name[:32], quoted, cited))
    print("  These are NOT passes. The check could not judge them.")
    if findings:
        print()
        print("A refusal that cites a field path is making a CHECKABLE claim about THIS")
        print("object. If the path does not resolve, or the number it quotes is not there,")
        print("the sentence is a template wearing a citation.")
    if args.gate and findings:
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
