"""Changed page filenames -> the SSOT objects they were built from.

The mapping is EXPLICIT (ssot/PAGE_MAP.json), not inferred from the filename.
"arni-hfref" and "ARNI_HF_REVIEW.html" do not transform into one another by any
rule, and a heuristic that appeared to work on six names and quietly missed the
seventh would hand the harness gate an empty list -- which, before the
zero-execution guard, read as PASS.

Pages with no mapped object are printed to stderr so the caller can say so out
loud. A page silently absent from a gate's input is the difference between
"checked and clean" and "never looked at", and this repo has spent a day on that
distinction.
"""
import json, os, sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MAP = os.path.join(REPO, "ssot", "PAGE_MAP.json")


def main():
    try:
        with open(MAP, encoding="utf-8") as fh:
            m = json.load(fh)
    except Exception as ex:                                  # noqa: BLE001
        print("objects_for_pages: cannot read %s (%s)" % (MAP, ex), file=sys.stderr)
        return 2
    mapped, unmapped, retired = [], [], []
    for p in sys.argv[1:]:
        b = os.path.basename(p)
        if b not in m:
            unmapped.append(b)
            continue
        rel = m[b]
        # A RETIRED TOMBSTONE IS NOT AN OBJECT THE DETECTORS CAN READ, and it must not enter
        # the harness gate's input at all.
        #
        # The gate's contract is "every artefact I was told about must exist", and it is a good
        # contract -- it is what stops a silently-missing export reading as a pass. A tombstone
        # exports nothing by design, so naming it here makes the gate look for a file that will
        # never be written and refuse the push. The fix belongs HERE, at the point that decides
        # what the gate is told about, not in the gate, whose strictness is the whole point.
        #
        # RETIRED, UNMAPPED and PRESENT are three states and are reported as three.
        try:
            with open(os.path.join(REPO, rel.replace("/", os.sep)), encoding="utf-8") as fh:
                o = json.load(fh)
        except Exception:                                    # noqa: BLE001
            mapped.append(rel)
            continue
        if str(o.get("state") or "").upper() == "RETIRED" and o.get("absorbed_by"):
            retired.append("%s -> absorbed by %s" % (b, o["absorbed_by"]))
            continue
        mapped.append(rel)
    for u in unmapped:
        print("UNMAPPED %s" % u, file=sys.stderr)
    for r in retired:
        print("RETIRED (no artefact by design) %s" % r, file=sys.stderr)
    print(" ".join(mapped))
    return 0


if __name__ == "__main__":
    sys.exit(main())
