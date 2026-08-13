"""D-33: an identifier that is well-formed once a prefix or suffix is stripped is
a BROKEN JOIN, not an absent identifier.

THE CLASS. Every identifier-keyed check in this programme matched a clean pattern
-- `^NCT\\d{8}$` or similar -- and treated anything else as "no identifier here".
That is the wrong default. `NULLED:NCT03657017` is ADVOR. `LEGACY-ISRCTN-35739639-PREDIMED`
is PREDIMED with its real ISRCTN. `NCT04381936c` is a legitimate RECOVERY sub-arm.
In all three the identifier is present and usable; only the KEY FORM differs, and
a strict matcher reports the row as unidentified rather than as unjoinable.

WHY THAT IS WORSE THAN A MISS. An absent identifier is visible: it shows up as a
gap and someone goes and finds it. A masked identifier is invisible -- it passes
every check by not matching them, and the coverage figure the audit reports counts
it as out of scope. The provenance lane measured its own coverage at 86% and did
not know why. This detector is what closes that gap.

WHAT IT DOES NOT DO. It does not strip anything. Three of these classes mean three
different things -- a reversed adjudication, a non-ClinicalTrials.gov registry, and
a deliberate sub-arm convention -- and only a human should decide which applies.
It reports the row as JOINABLE-BUT-NOT-JOINED and names the class.
"""
import collections
import glob
import io
import json
import os
import re
import sys

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

CLEAN = re.compile(r"^NCT\d{8}$")
# Each pattern: name, regex over the KEY, and how to recover a joinable id.
CLASSES = (
    ("PREFIXED", re.compile(r"^([A-Z_]+):(NCT\d{8})$"),
     lambda m: m.group(2),
     "A prefix was prepended by a pipeline step. The registry id is intact and "
     "the row is joinable once the prefix is removed. Removing it may reverse an "
     "adjudication, so it needs evidence, not a string operation."),
    ("SUFFIXED", re.compile(r"^(NCT\d{8})([a-z]|_[A-Z0-9]+)$"),
     lambda m: m.group(1),
     "A sub-arm or sub-study suffix. Usually a deliberate convention for "
     "multi-arm platform trials, NOT a defect. Joins must strip the suffix to "
     "reach the parent registration rather than fail."),
    ("OTHER_REGISTRY", re.compile(
        r"^(?:LEGACY-)?(ISRCTN[- ]?\d+|ACTRN\d+|UMIN\d+|EUCTR[\d-]+|JPRN-[\w-]+)"
        r"(?:-[A-Za-z0-9]+)?$"),
     lambda m: m.group(1).replace(" ", "").replace("ISRCTN-", "ISRCTN"),
     "A registration in a registry that is not ClinicalTrials.gov -- ISRCTN, "
     "ANZCTR, UMIN, EudraCT, jRCT. These are REAL registrations and are "
     "checkable against their own registry. Reporting them as unidentified "
     "because they are not NCTs is a limitation of the matcher, not of the row."),
)


def scan(root="."):
    key_pat = re.compile(r'["\']([A-Za-z0-9_:.\-]{6,60})["\']\s*:\s*\{')
    found = collections.defaultdict(list)
    counts = collections.Counter()
    files = sorted(glob.glob(os.path.join(root, "*_REVIEW.html")))
    for f in files:
        try:
            s = open(f, encoding="utf-8", errors="replace").read()
        except Exception:                                    # noqa: BLE001
            continue
        for m in key_pat.finditer(s):
            k = m.group(1)
            if CLEAN.match(k):
                counts["clean"] += 1
                continue
            for name, pat, rec, why in CLASSES:
                mm = pat.match(k)
                if mm:
                    counts[name] += 1
                    found[name].append({"app": os.path.basename(f), "key": k,
                                        "joinable_as": rec(mm)})
                    break
    return files, counts, found


def main():
    files, counts, found = scan()
    clean = counts.get("clean", 0)
    masked = sum(v for k, v in counts.items() if k != "clean")
    total = clean + masked
    print("D-33 masked identifiers")
    print("  review files scanned            : %d" % len(files))
    print("  clean NCT keys                  : %d" % clean)
    print("  MASKED but joinable             : %d" % masked)
    if total:
        print("  share of keys a strict matcher")
        print("  would have reported as absent   : %.2f%% (%d/%d)"
              % (100.0 * masked / total, masked, total))
    print()
    for name, _pat, _rec, why in CLASSES:
        rows = found.get(name, [])
        if not rows:
            continue
        apps = len({r["app"] for r in rows})
        ids = len({r["key"] for r in rows})
        print("  %-15s %5d keys | %4d distinct | %3d apps"
              % (name, len(rows), ids, apps))
        print("      %s" % why)
        for r in rows[:3]:
            print("      e.g. %-34s -> joins as %s" % (r["key"], r["joinable_as"]))
        print()
    out = os.path.join("outputs", "masked_identifiers.json")
    os.makedirs("outputs", exist_ok=True)
    json.dump({"files_scanned": len(files), "clean_keys": clean,
               "masked_keys": masked,
               "masked_share_pct": round(100.0 * masked / total, 3) if total else None,
               "denominator": "all object keys that look like an identifier, "
                              "clean plus masked -- not corpus rows",
               "classes": {k: v for k, v in found.items()}},
              open(out, "w", encoding="utf-8"), indent=1, ensure_ascii=False)
    print("wrote %s" % out)
    # A masked identifier is a finding, not an error: exit 0, report loudly.
    return 0


if __name__ == "__main__":
    sys.exit(main())
