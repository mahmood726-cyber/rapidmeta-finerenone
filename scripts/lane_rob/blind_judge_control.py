# -*- coding: utf-8 -*-
"""CONTROL RUN: can three AI judges discriminate between two PUBLISHED reviews at all?

WHY THIS RUNS BEFORE ANY VERDICT ON OUR OWN PAGE. If the judges call two published reviews of
the same question a tie, or split by model family rather than by document, then a later verdict
about our review measures the instrument and not the work -- and we would spend several
iterations optimising against noise. This is the known-negative for the whole exercise, and it
costs one run.

⚠️ PICO MATCHING IS ENFORCED, NOT ASSUMED. The Cochrane document is a review of FIVE microbicide
classes; only its DAPIVIRINE section is extracted. Judging our two-trial dapivirine review
against a five-class parent review would be the PICO-mismatch error this project refuted on
nirsevimab, arriving from the other side.

⛔ BLIND MEANS BLIND, AND POSITION IS RANDOMISED. Journal names, collaboration names, author
names, copyright lines and running heads are stripped. Each judge sees the two documents in a
different A/B order, because otherwise position becomes a variable and any later optimisation
would be partly against position.

⭐ THE JUDGE NAMES ITS AXES AND WEIGHTS BEFORE ITS VERDICT. A verdict without a reason cannot be
improved against, and "what would change your mind" is the next iteration's work list.

THREE FAMILIES, RECORDED PER JUDGE. codex -> openai, agy pinned to gemini-3.1-pro-high ->
google, agy claude-opus-4-6-thinking -> anthropic. If the split is consistently by FAMILY
rather than by DOCUMENT we are measuring dispositions, which this project has already been
caught by once when a third family abstained on 90.3% of cells.
"""
import io
import json
import os
import re
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(os.path.dirname(HERE))
os.chdir(REPO)
OUT = r"F:\claude-temp\pend\out\judge"
COCHRANE = r"F:\claude-temp\pend\cochrane_cd007961.txt"
JAIDS = r"F:\claude-temp\pend\rev\PMC11458098.xml"

# Identifying marks. Blinding fails on a single running head, so this is deliberately blunt.
BRAND = re.compile(
    r"cochrane|wiley|john wiley|the cochrane collaboration|cochrane library|CDSR|"
    r"CD007961|copyright \(c\) \d{4}|Obiero|Ogongo|Mwethera|Wiysonge|"
    r"J Acquir Immune Defic Syndr|JAIDS|Lippincott|Wolters Kluwer|doi:\s*10\.\d+/\S+|"
    r"Trusted evidence|Informed decisions|Better health", re.I)


def rendered_xml(path):
    raw = io.open(path, encoding="utf-8", errors="replace").read()
    t = re.sub(r"(?is)<(script|style).*?</\1>", " ", raw)
    return re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", t)).strip()


def blind(text):
    text = BRAND.sub("[REDACTED]", text)
    # collapse the redaction runs so the density of marks is not itself a tell
    return re.sub(r"(\[REDACTED\]\s*){2,}", "[REDACTED] ", text)


def cochrane_dapivirine():
    """The DAPIVIRINE section only: its summary of findings, its risk-of-bias reasoning,
    and its dapivirine results paragraphs. Not the parent five-class review."""
    lines = io.open(COCHRANE, encoding="utf-8", errors="replace").read().split("\n")
    take = []
    take.append("SUMMARY OF FINDINGS")
    # ⚠️ STOP AT THE NEXT INTERVENTION'S TABLE. The first extraction ran to a fixed line and
    # spilled into "Summary of findings 2. Tenofovir", carrying cellulose sulphate, PRO 2000
    # and SAVVY material with it. Two of three judges then scored the comparator DOWN for lack
    # of focus on dapivirine -- an axis it lost because of MY extraction, not its own writing.
    # That is a PICO mismatch in our own favour, which is the mirror of the error this project
    # refuses elsewhere, and it made part of round 1 unusable.
    OTHER = re.compile(r"tenofovir|cellulose sulphate|PRO 2000|SAVVY|BufferGel|Carraguard",
                       re.I)
    take += lines[182:281]          # ends immediately before "Summary of findings 2."
    take.append("\nRISK OF BIAS ASSESSMENT")
    # Their risk-of-bias narrative genuinely covers all twelve trials and names these two among
    # them. That is the comparator's own writing and is left exactly as it stands.
    take += lines[1044:1096]
    take.append("\nRESULTS AND CONCLUSIONS FOR THIS INTERVENTION")
    res = []
    for ln in lines[1203:1260]:
        if OTHER.search(ln):
            break
        if ln.strip():
            res.append(ln)
    take += res
    take.append("\nSEARCH")
    take += [l for l in lines[725:750] if l.strip()]
    return blind("\n".join(take))


def jaids_dapivirine():
    t = rendered_xml(JAIDS)
    # keep the portion about the ring's efficacy and evidence assessment
    i = t.lower().find("dapivirine")
    return blind(t[max(0, i - 500):i + 22000])


PROMPT = """You are assessing two documents, A and B. Both address the SAME question:

  In women, does a dapivirine vaginal ring reduce HIV-1 acquisition compared with placebo?

Both are evidence syntheses of the same two randomised trials. Assess ONLY the dapivirine
content; ignore any material about other interventions.

Answer in this order and do NOT reorder:

1. AXES. Before reading for a verdict, list the 4-7 axes on which an evidence synthesis of
   this kind should be judged. Give each a weight as a percentage; the weights must total 100.
2. PER-AXIS. For each axis, say which document is better (A, B, or TIE) and give a one-sentence
   reason citing something concrete from the document.
3. VERDICT. Which document is better OVERALL, and by how much: DECISIVELY, MODERATELY, or
   MARGINALLY. If they are equivalent say TIE.
4. WHAT WOULD CHANGE YOUR MIND. Name the two specific changes that would most improve the
   LOSING document.

Be concise. Do not speculate about who wrote either document.

=== DOCUMENT A ===
%s

=== DOCUMENT B ===
%s
"""


def ask(worker, model, prompt_path, tag):
    if worker == "codex":
        cmd = ["codex", "exec", "-c", "model_reasoning_effort=medium",
               "Read the file %s and follow the instructions inside it." % prompt_path]
    else:
        cmd = ["agy", "--model", model, "--print",
               "Read the file %s and follow the instructions inside it." % prompt_path]
    r = subprocess.run(cmd, capture_output=True, timeout=1800)
    out = r.stdout.decode("utf-8", "replace")
    io.open(os.path.join(OUT, "%s.txt" % tag), "w", encoding="utf-8").write(out)
    return out


def main():
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace",
                                  line_buffering=True)
    os.makedirs(OUT, exist_ok=True)
    doc_c, doc_j = cochrane_dapivirine(), jaids_dapivirine()
    print("document 1 (published review 1): %d chars" % len(doc_c))
    print("document 2 (published review 2): %d chars" % len(doc_j))
    for name, d in (("doc1", doc_c), ("doc2", doc_j)):
        leaks = BRAND.findall(d)
        print("  %s residual identifying marks: %d %s" % (name, len(leaks), leaks[:3]))
        io.open(os.path.join(OUT, name + ".txt"), "w", encoding="utf-8").write(d)

    # POSITION IS RANDOMISED BY JUDGE, and the mapping is recorded so a later verdict can be
    # read back to a document rather than to a letter.
    judges = [("codex", "", "openai", ("doc1", "doc2")),
              ("agy", "gemini-3.1-pro-high", "google", ("doc2", "doc1")),
              ("agy", "claude-opus-4-6-thinking", "anthropic", ("doc1", "doc2"))]
    mapping = {}
    for worker, model, family, (a, b) in judges:
        tag = "control_%s" % family
        txt = {"doc1": doc_c, "doc2": doc_j}
        p = os.path.join(OUT, "prompt_%s.txt" % tag)
        io.open(p, "w", encoding="utf-8").write(PROMPT % (txt[a], txt[b]))
        mapping[tag] = {"A": a, "B": b, "family": family, "worker": worker, "model": model}
        print("  %s: A=%s B=%s  prompt %d chars" % (tag, a, b, os.path.getsize(p)))
    json.dump(mapping, io.open(os.path.join(OUT, "control_mapping.json"), "w",
                               encoding="utf-8"), indent=1)
    print("")
    print("prompts written. doc1 = published review 1, doc2 = published review 2.")
    print("mapping -> control_mapping.json")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
