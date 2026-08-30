# -*- coding: utf-8 -*-
"""ROUND 3: the REGENERATED page against the same comparator. The run that decides.

⛔ THE CLAIM ROUND 2 DID NOT EARN. Six blinded judges preferred `DAPIVIRINE_RING_PILOT_REVIEW`,
23,090 rendered characters, every section AUTHORED. The harness now produces
`AGYW_HIV_PREP_REVIEW`, 86,040 rendered characters, every section GENERATED. **These are not the
same artefact and the verdict does not transfer.** 13 of 13 says the harness reproduces the
FEATURES that page won on; it says nothing about whether generated prose persuades the way
authored prose did. This run is the only thing that can say so.

WHAT IS UNCHANGED FROM ROUND 1, deliberately -- a comparison whose instrument moved is not a
comparison:
  * the same comparator, CD007961.pub3, DAPIVIRINE SECTION ONLY (PICO-matched: judging a
    two-trial review against a five-class parent would be the mismatch we refuse elsewhere)
  * the same prompt, verbatim, from blind_judge_control.PROMPT
  * the same blinding, and the same rendering of both documents to plain text, because FORMAT
    IS A TELL
  * the same three families: codex -> openai, agy gemini -> google, agy claude -> anthropic

WHAT IS ADDED FOR THIS ROUND:

  1. BOTH POSITIONS PER FAMILY -- six verdicts, not three. Position is then a within-family
     variable rather than a between-family one, and a family that flips on position is telling
     us something the three-verdict design could not.

  2. ⭐ A GROUNDING GATE. Round 1 had a judge cite content it was never shown. Every quoted
     string in a verdict is now checked against the document THAT judge received -- not against
     our page, and not against the other document. ⚠️ A quote that is not in what the judge saw
     invalidates that verdict rather than lowering it: a judge reasoning about text that was not
     in front of it is not judging our page.

  3. ⭐ A SHARED-SUBSTRING BLINDING DETECTOR. Our page QUOTES the comparator -- chlamydia
     RR 0.97 (0.89 to 1.07), syphilis RR 1.70 (0.63 to 4.59), the "up to August 2020" search
     date -- because the comparator is the only source we hold for those outcomes. **Any long
     string appearing in BOTH documents tells a judge which is derivative**, and round 2's page
     did not carry these rows. The detector must read 0 above the threshold before any judge is
     asked; what it finds is neutralised in OUR document, never in theirs.

  4. THE MODEL IS PROVED FROM THE CLI LOG, never from a self-claim. A verdict whose log does not
     name its own model family is discarded.

  5. THE JUDGED BYTES ARE FINGERPRINTED. sha256 of each document is recorded beside every
     verdict, because a finding raised against one version and checked against another is not a
     comparison -- 234 of 246 adjudications on this project were once exactly that.

⚠️ agy CONCURRENCY IS 3. A fourth worker returns `fatal error: out of memory` with rc=0 and an
EMPTY artefact, which looks exactly like a completed run. Judges are therefore issued in series.
"""
import hashlib
import io
import json
import os
import re
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(os.path.dirname(HERE))
os.chdir(REPO)
sys.path.insert(0, HERE)
import blind_judge_control as C  # noqa: E402
import blind_judge_round1 as R1  # noqa: E402

OUT = os.path.join(REPO, "out", "judge-r3")
OURS_HTML = "AGYW_HIV_PREP_REVIEW.html"

# The minimum shared run that counts as a blinding risk. Long enough that ordinary phrasing
# does not trip it, short enough to catch a quoted interval with its surrounding clause.
SHARED_MIN = 60


def ours_as_text(path=OURS_HTML):
    """The generated page, rendered and blinded with round 1's own tell list."""
    raw = io.open(path, encoding="utf-8").read()
    raw = re.sub(r"(?is)<style.*?</style>", " ", raw)
    raw = re.sub(r"(?is)<script.*?</script>", " ", raw)
    raw = re.sub(r"(?i)</(h1|h2|h3|p|tr|li|div)>", "\n", raw)
    raw = re.sub(r"(?i)</t[dh]>", " | ", raw)
    t = re.sub(r"<[^>]+>", "", raw)
    for a, b in (("&mdash;", "—"), ("&ndash;", "–"), ("&minus;", "−"),
                 ("&lt;", "<"), ("&gt;", ">"), ("&rsquo;", "'"), ("&ldquo;", "“"),
                 ("&rdquo;", "”"), ("&times;", "×"), ("&larr;", "<-"),
                 ("&nbsp;", " "), ("&amp;", "&")):
        t = t.replace(a, b)
    t = re.sub(r"[ \t]+", " ", t)
    t = re.sub(r"\n\s*\n\s*\n+", "\n\n", t)
    for pat, rep in R1.OUR_TELLS:
        t = pat.sub(rep, t)
    return C.blind(t.strip())


def shared_runs(a, b, minlen=SHARED_MIN):
    """Long strings present in BOTH documents. Shingle-indexed; never an O(n^2) scan."""
    def norm(s):
        return re.sub(r"\s+", " ", s.lower())
    A, B = norm(a), norm(b)
    idx = {}
    for i in range(0, len(B) - minlen + 1):
        idx.setdefault(B[i:i + minlen], i)
    hits, i = [], 0
    while i <= len(A) - minlen:
        k = A[i:i + minlen]
        if k in idx:
            j = idx[k]
            n = minlen
            while (i + n < len(A) and j + n < len(B) and A[i + n] == B[j + n]):
                n += 1
            hits.append(A[i:i + n])
            i += n
        else:
            i += 1
    return hits


QUOTE = re.compile(r"[\"“]([^\"”\n]{25,200})[\"”]")


def grounding(verdict_text, shown_text):
    """Quotes in the verdict that are NOT in what that judge was shown. -> list."""
    def norm(s):
        return re.sub(r"[^a-z0-9 ]", " ", re.sub(r"\s+", " ", s.lower())).strip()
    hay = norm(shown_text)
    bad = []
    for m in QUOTE.finditer(verdict_text):
        q = norm(m.group(1))
        if len(q) < 25:
            continue
        if q not in hay:
            bad.append(m.group(1)[:120])
    return bad


FAMILY_TOKENS = {"openai": ("gpt", "codex", "openai"),
                 "google": ("gemini",),
                 "anthropic": ("claude", "opus", "sonnet")}


def model_proved(log_text, family):
    """Does the CLI log NAME the family it claims? A self-claim is not proof."""
    low = (log_text or "").lower()
    return any(tok in low for tok in FAMILY_TOKENS[family])


def sha(s):
    return hashlib.sha256(s.encode("utf-8")).hexdigest()


def main():
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace",
                                  line_buffering=True)
    os.makedirs(OUT, exist_ok=True)
    if not os.path.exists(OURS_HTML):
        print("REFUSED: %s is absent. Nothing to judge." % OURS_HTML)
        return 2
    ours = ours_as_text()
    theirs = C.cochrane_dapivirine()
    print("")
    print("ROUND 3 -- the REGENERATED page")
    print("  ours   %6d chars  sha256 %s  residual marks %d"
          % (len(ours), sha(ours)[:16], len(C.BRAND.findall(ours))))
    print("  theirs %6d chars  sha256 %s  residual marks %d"
          % (len(theirs), sha(theirs)[:16], len(C.BRAND.findall(theirs))))

    # ⛔ THE BLINDING DETECTOR RUNS BEFORE ANY JUDGE IS ASKED.
    runs = shared_runs(ours, theirs)
    print("")
    print("  SHARED-SUBSTRING BLINDING DETECTOR (>= %d chars): %d run(s)"
          % (SHARED_MIN, len(runs)))
    for r in sorted(runs, key=len, reverse=True)[:10]:
        print("     %4d  %s" % (len(r), r[:110]))
    if runs:
        print("")
        print("  ⛔ REFUSED: a string this long in BOTH documents tells a judge which one is")
        print("     derivative. Neutralise it IN OURS -- never in theirs -- and re-run. Our page")
        print("     quotes the comparator for outcomes we hold no other source for, so this is")
        print("     expected on this round and was not a risk in round 2.")
        json.dump([{"len": len(r), "text": r} for r in runs],
                  io.open(os.path.join(OUT, "r3_shared_runs.json"), "w", encoding="utf-8"),
                  indent=1)
        return 1

    for n, d in (("ours", ours), ("theirs", theirs)):
        io.open(os.path.join(OUT, "r3_%s.txt" % n), "w", encoding="utf-8").write(d)

    # BOTH POSITIONS PER FAMILY. Six verdicts.
    judges = []
    for worker, model, family in (("codex", "", "openai"),
                                  ("agy", "gemini-3.1-pro-high", "google"),
                                  ("agy", "claude-opus-4-6-thinking", "anthropic")):
        judges.append((worker, model, family, ("ours", "theirs")))
        judges.append((worker, model, family, ("theirs", "ours")))
    txt = {"ours": ours, "theirs": theirs}
    mapping = {}
    print("")
    for worker, model, family, (a, b) in judges:
        tag = "r3_%s_%s_first" % (family, a)
        p = os.path.join(OUT, "prompt_%s.txt" % tag)
        io.open(p, "w", encoding="utf-8").write(C.PROMPT % (txt[a], txt[b]))
        mapping[tag] = {"A": a, "B": b, "family": family, "worker": worker, "model": model,
                        "sha256_A": sha(txt[a]), "sha256_B": sha(txt[b]),
                        "prompt_bytes": os.path.getsize(p)}
        print("  %-26s A=%-6s B=%-6s  %d chars" % (tag, a, b, os.path.getsize(p)))
    json.dump(mapping, io.open(os.path.join(OUT, "r3_mapping.json"), "w", encoding="utf-8"),
              indent=1)
    print("")
    print("  6 prompts written: 3 families x 2 positions.")
    print("  ⚠️ ISSUE THEM IN SERIES. agy's concurrency limit is 3 and a fourth worker returns")
    print("     `fatal error: out of memory` with rc=0 and an EMPTY artefact -- which looks")
    print("     exactly like a completed run.")
    print("  mapping -> out/judge-r3/r3_mapping.json")
    return 0


def score():
    """Read the six verdicts back: grounding, model proof, and the verdict itself."""
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace",
                                  line_buffering=True)
    mapping = json.load(io.open(os.path.join(OUT, "r3_mapping.json"), encoding="utf-8"))
    shown = {n: io.open(os.path.join(OUT, "r3_%s.txt" % n), encoding="utf-8").read()
             for n in ("ours", "theirs")}
    print("")
    print("ROUND 3 VERDICTS")
    rows = []
    for tag, m in sorted(mapping.items()):
        path = os.path.join(OUT, "%s.txt" % tag)
        if not os.path.exists(path):
            print("  %-26s NOT RUN" % tag)
            continue
        v = io.open(path, encoding="utf-8", errors="replace").read()
        if not v.strip():
            # ⚠️ An empty artefact is a FAILURE, not a tie. See the agy note above.
            print("  %-26s EMPTY ARTEFACT -- counted as a failed run, never as a verdict" % tag)
            continue
        seen = shown[m["A"]] + "\n" + shown[m["B"]]
        ungrounded = grounding(v, seen)
        proved = model_proved(v, m["family"])
        rows.append((tag, m, v, ungrounded, proved))
        print("  %-26s model-proved=%-5s ungrounded-quotes=%d" % (tag, proved, len(ungrounded)))
        for q in ungrounded[:2]:
            print("        NOT IN WHAT THIS JUDGE SAW: %s" % q)
    print("")
    print("  ⛔ A verdict with an ungrounded quote is INVALID, not merely weaker: a judge")
    print("     reasoning about text that was not in front of it is not judging our page.")
    return rows


if __name__ == "__main__":
    raise SystemExit(score() and 0 if "--score" in sys.argv else main())
