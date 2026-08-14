"""Every included study keyed to a registration ID found IN its source document.

WHY. A file arrived labelled `ANSWERHF-fulltext.txt`. Its covering message said
"this is answer HF full text". It contained NCT04023227 twice, NCT04853758 never,
"PARACHUTE" nineteen times and "ANSWER-HF" not once. It was a different trial,
and it cost hours and produced a reject-level finding against a pooled input that
turned out to be correct.

A trial name is a label someone applied. A citation string is a label someone
typed. Neither is evidence about which study a document reports. The registration
number is, because it is printed in the document by the people who ran the trial.

THE INVARIANT: for every pooled row, the registration ID recorded in the object
must appear in the text of the document that row is sourced from. Not in the
filename, not in our note about the file -- in the document.

This is the most productive detector in the set, and we found it by failing it.

Usage:
  python identity_gate.py <object.json> [--sources <dir>] [--file <doc> --expect <NCT>]
  python identity_gate.py --selftest
"""
import io
import json
import os
import re
import sys

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from verdict import Verdict, PASS, FAIL, INVALID, summarise  # noqa: E402

REG = re.compile(r"\b(NCT\d{8}|ISRCTN\d{8}|ACTRN\d{14}|ChiCTR[A-Za-z0-9-]{6,}|"
                 r"EUCTR\d{4}-\d{6}-\d{2}|jRCT[a-zA-Z0-9]{10,})\b")


def ids_in(text):
    return set(REG.findall(text or ""))


def check_document(path, expect):
    """Does the document itself carry the registration we filed it under?"""
    if not os.path.exists(path):
        return Verdict("source document present: %s" % os.path.basename(path),
                       INVALID, detail="file not found, so nothing can be read "
                                       "from it either way")
    try:
        txt = open(path, encoding="utf-8", errors="replace").read()
    except Exception as e:                                # noqa: BLE001
        return Verdict("readable: %s" % os.path.basename(path), INVALID,
                       detail=str(e)[:120])
    if not txt.strip():
        return Verdict("non-empty: %s" % os.path.basename(path), INVALID,
                       detail="file is empty; an empty file cannot disagree "
                              "with a label, which is exactly why it must not "
                              "be scored as agreeing")
    found = ids_in(txt)
    name = "%s carries %s" % (os.path.basename(path), expect)
    if expect in found:
        return Verdict(name, PASS,
                       witness="found %s in the document text (%d bytes, "
                               "registration IDs present: %s)"
                               % (expect, len(txt), ", ".join(sorted(found))),
                       failure_would_be="the filed registration absent from the "
                                        "document's own text")
    return Verdict(name, FAIL,
                   detail="%s NOT in this document. IDs actually present: %s. "
                          "The file is labelled for a study it does not report."
                          % (expect, ", ".join(sorted(found)) or "none"),
                   failure_would_be="")


def check_object(obj_path, sources_dir=None):
    d = json.load(open(obj_path, encoding="utf-8"))
    out = []
    trials = (d.get("inputs") or {}).get("trials") or []
    if not trials:
        return [Verdict("object has pooled trials", INVALID,
                        detail="no inputs.trials to key")]
    seen = {}
    for t in trials:
        nct = t.get("nct")
        nm = t.get("name") or t.get("id")
        if not nct:
            out.append(Verdict("%s has a registration id" % nm, FAIL,
                               detail="no registry identifier recorded; the row "
                                      "is keyed only by name"))
            continue
        if nct in seen:
            out.append(Verdict("%s registration is unique" % nm, FAIL,
                               detail="%s is also used by %s -- one trial has "
                                      "entered the pool twice"
                                      % (nct, seen[nct])))
            continue
        seen[nct] = nm
        out.append(Verdict("%s keyed to %s" % (nm, nct), PASS,
                           witness="registration recorded on the trial row and "
                                   "unique across the %d pooled trials"
                                   % len(trials),
                           failure_would_be="a row with no registration, or two "
                                            "rows sharing one"))
    if sources_dir and os.path.isdir(sources_dir):
        files = [f for f in os.listdir(sources_dir)
                 if f.lower().endswith((".txt", ".html", ".json"))]
        corpus = " ".join(files)
        for nct, nm in seen.items():
            hits = [f for f in files
                    if nct in open(os.path.join(sources_dir, f), encoding="utf-8",
                                   errors="replace").read()]
            if hits:
                out.append(Verdict("%s: a staged source carries %s" % (nm, nct),
                                   PASS,
                                   witness="found in %s" % ", ".join(hits[:3]),
                                   failure_would_be="no staged document "
                                                    "containing the trial's own "
                                                    "registration"))
            else:
                out.append(Verdict("%s: a staged source carries %s" % (nm, nct),
                                   INVALID,
                                   detail="no staged document in %s contains "
                                          "this registration, so the row's "
                                          "identity cannot be confirmed from "
                                          "the bundle. Not a FAIL: the trial may "
                                          "be correct and simply unstaged."
                                          % os.path.basename(sources_dir)))
    return out


def selftest():
    import tempfile
    print("=== the identity gate ===")
    cases = []
    d1 = tempfile.mkdtemp()
    good = os.path.join(d1, "trial.txt")
    open(good, "w", encoding="utf-8").write(
        "Primary Results ... Trial Registration: ClinicalTrials.gov Identifier: "
        "NCT04853758 ... 190 patients randomized")
    cases.append(("document carries the registration it is filed under",
                  check_document(good, "NCT04853758"), PASS))
    # THE REAL ONE: the mislabelled file, reconstructed.
    bad = os.path.join(d1, "ANSWERHF-fulltext.txt")
    open(bad, "w", encoding="utf-8").write(
        "this is answer HF full text. hopefully we can exclude based on this "
        "JAMA ... PARACHUTE-HF ... NCT04023227 ... 462 patients")
    cases.append(("THE MISLABELLED FILE: filed as ANSWER-HF, reports PARACHUTE",
                  check_document(bad, "NCT04853758"), FAIL))
    empty = os.path.join(d1, "empty.txt")
    open(empty, "w", encoding="utf-8").write("")
    cases.append(("an empty file is INVALID, never a pass",
                  check_document(empty, "NCT04853758"), INVALID))
    cases.append(("a missing file is INVALID, never a pass",
                  check_document(os.path.join(d1, "nope.txt"), "NCT1"), INVALID))
    ok = True
    for name, v, want in cases:
        good_ = v.state == want
        ok &= good_
        print("  %-58s %-8s expected=%-8s %s"
              % (name[:58], v.state, want, "correct" if good_ else "WRONG"))
    print("\nidentity gate correct on every case:", ok)
    return 0 if ok else 1


if __name__ == "__main__":
    if "--selftest" in sys.argv:
        raise SystemExit(selftest())
    a = [x for x in sys.argv[1:] if not x.startswith("--")]
    if "--file" in sys.argv:
        i = sys.argv.index("--file")
        j = sys.argv.index("--expect")
        raise SystemExit(summarise([check_document(sys.argv[i + 1],
                                                   sys.argv[j + 1])]))
    src = None
    if "--sources" in sys.argv:
        src = sys.argv[sys.argv.index("--sources") + 1]
    raise SystemExit(summarise(check_object(a[0], src), "identity:"))
