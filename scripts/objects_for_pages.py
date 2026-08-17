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
    mapped, unmapped = [], []
    for p in sys.argv[1:]:
        b = os.path.basename(p)
        (mapped if b in m else unmapped).append(m.get(b, b))
    for u in unmapped:
        print("UNMAPPED %s" % u, file=sys.stderr)
    print(" ".join(mapped))
    return 0


if __name__ == "__main__":
    sys.exit(main())
