"""Where does a gate assert certainty about THE WORLD rather than about its own limits?

THE ORIGINATING CASE. CHK017 said "two distinct trials cannot agree to 16 significant
digits ... This is a PROOF, not an inference." Its own founding value was math.log(0.86).
THE WORD MARKED EXACTLY WHERE ITS AUTHOR STOPPED LOOKING FOR A COUNTEREXAMPLE -- writing
"proof" closed the question that writing "in the cases I have seen" would have left open.

That is a detector, not a style note. But the naive grep is useless: 226 hits across 76
files, and most are the OPPOSITE of over-claiming. "This check cannot discriminate here"
is a confession of limits, and confessions are what we want more of.

SO THE DETECTOR SPLITS ON WHAT THE SENTENCE IS ABOUT:

  LIMITATION   the subject is the instrument -- this check, the regex, the list -- and the
               verb is a seeing verb. "The pattern cannot see X." Refuting it would mean
               improving the tool. HARMLESS, AND USUALLY VIRTUOUS.

  CLAIM        the subject is the world -- trials, estimates, values, pages -- or the
               sentence asserts the check's conclusion is beyond doubt. "Two trials cannot
               agree." "This is a PROOF." REFUTABLE BY A COUNTEREXAMPLE, and therefore the
               place to go looking for one.

Only the second class is reported. Each hit is an invitation to spend five minutes trying
to break the sentence -- which is the five minutes CHK017 never got.
"""
from __future__ import annotations
import collections
import glob
import io
import os
import re
import sys

if __name__ == "__main__":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Certainty about the check's OWN CONCLUSION. No subject test needed: these words
# claim the verdict is beyond doubt whoever the subject is.
ABSOLUTE = re.compile(
    r"\b(is a PROOF|IS A PROOF|a PROOF, not|proves that|proven|"
    r"impossible|guarantee[sd]?|by definition|necessarily true|"
    r"beyond doubt|conclusively)\b")

# Certainty about the WORLD. "cannot" / "never" / "always" whose subject is not the
# instrument.
MODAL = re.compile(r"\b(cannot|can never|never|always)\b", re.I)

# The instrument, as a grammatical subject. If one of these governs the modal, the
# sentence is a confession of limits rather than a claim about reality.
INSTRUMENT = re.compile(
    r"\b(this check|the check|a check|checks|this gate|the gate|a gate|gates|"
    r"the list|the regex|the pattern|the sweep|the detector|a detector|detectors|"
    r"the harness|the adapter|the exporter|the projection|the rule|a rule|"
    r"the probe|the fixture|the mutator|the audit|it) ", re.I)
SEEING = re.compile(
    r"\b(see|tell|discriminate|recognis|recogniz|resolve|compute|detect|know|"
    r"distinguish|attribute|satisf|express|fire|run|survive|read|match|"
    r"observe|reach|inspect|adjudicat|decide|say)\w*\b", re.I)


def classify(line: str):
    a = ABSOLUTE.search(line)
    if a:
        return "CLAIM", a.group(0)
    m = MODAL.search(line)
    if not m:
        return None, None
    pre = line[:m.start()]
    post = line[m.end():m.end() + 60]
    if INSTRUMENT.search(pre[-46:]) and SEEING.search(post):
        return "LIMITATION", m.group(0)
    return "CLAIM", m.group(0)


def main() -> int:
    files = sorted(set(glob.glob(os.path.join(REPO, "scripts", "*gate*.py"))
                       + glob.glob(os.path.join(REPO, "scripts", "nafis_harness",
                                                "*.py"))))
    claims = collections.defaultdict(list)
    n_lim = 0
    for f in files:
        try:
            text = io.open(f, encoding="utf-8", errors="replace").read()
        except Exception:
            continue
        for i, line in enumerate(text.splitlines(), 1):
            kind, word = classify(line)
            if kind == "LIMITATION":
                n_lim += 1
            elif kind == "CLAIM":
                claims[f].append((i, word, line.strip()[:100]))

    tot = sum(len(v) for v in claims.values())
    print("=" * 92)
    print("OVER-CLAIM DETECTOR -- certainty about the world, not about the instrument")
    print("=" * 92)
    print("files scanned          : %d" % len(files))
    print("LIMITATION (harmless)  : %d   -- 'this check cannot see X', confessions of "
          "limits" % n_lim)
    print("CLAIM (go break these) : %d   -- assertions a counterexample could refute"
          % tot)
    print()
    for f, v in sorted(claims.items(), key=lambda kv: -len(kv[1])):
        print("== %-52s %d" % (os.path.basename(f), len(v)))
        for i, w, line in v[:6]:
            print("   %5d  %-14s %s" % (i, w, line))
        if len(v) > 6:
            print("   ...    %d more" % (len(v) - 6))
    print()
    print("=" * 92)
    print("EACH CLAIM IS AN INVITATION TO SPEND FIVE MINUTES TRYING TO BREAK IT.")
    print("That is the five minutes CHK017 never got: its author wrote 'PROOF' and the")
    print("question closed. The founding value was math.log(0.86) the whole time.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
