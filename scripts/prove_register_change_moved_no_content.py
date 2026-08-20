"""Before/after on the delivered bytes: did the register change, and ONLY the register?

THE FAILURE MODE THIS EXISTS TO CATCH is a fix that reads as a reformatting and is actually
a paraphrase. A page whose numbers move has not been reformatted, and the whole claim about
this pass -- that it changes how the manuscript reads and not what it says -- would be
false.

FOUR INVARIANTS, taken from the DELIVERED BYTES of both versions and compared as multisets
so a value moving between sections is not a change and a value LOST is:

    ESTIMATES        every number in the Paper panel at 1-4 decimal places, including the
                     interval bounds. A dropped bound and a rounded point both show here.
    REGISTRATION IDS every NCT string on the whole page.
    OUTCOME TEXT     every registered outcome name the object holds, checked for presence
                     in the panel. Registered text is quoted, never paraphrased.
    VERBATIM R       the `quoted verbatim` sections, compared as exact strings. P46's
                     fourth criterion requires the model output verbatim; a reader checking
                     the arithmetic needs exactly those characters.

AND ONE THING THAT MUST CHANGE, or the pass did nothing: the count of field paths standing
inside the sentence flow.

THE ESTIMATE INVARIANT IS DELIBERATELY ONE-SIDED. A number PRESENT BEFORE and absent after
is a failure. A number present after and absent before is NOT -- the glossed heterogeneity
sentence and the cascade table print the same values in more places, and forbidding that
would forbid the fix.
"""
import io
import os
import re
import sys
import json
import html as htmllib

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lint_paper_reads_as_prose import panel_text, FIELD_PATH

NUM = re.compile(r"(?<![\w.])\d+\.\d{1,4}(?![\w])")
NCT = re.compile(r"\bNCT\d{8}\b")
R_OUTPUT = re.compile(r"\[R version|Random-Effects Model|\brma\(")


def panel_raw(raw):
    i = raw.find('id="paper"')
    if i < 0:
        return ""
    start = raw.rfind("<", 0, i)
    rest = raw[start:]
    for m in re.finditer(r'id="(?:pn-)?(?:analysis|extract|dm|data|home|dash|method)"',
                         rest[10:]):
        return rest[:10 + m.start()]
    return rest


def verbatim_blocks(raw):
    """Exact text of every `quoted verbatim` section, keyed by heading.

    THE PROVENANCE MARKER IS STRIPPED BEFORE COMPARING, and that is only legitimate because
    the marker was also MOVED OUT of the block. The first build appended it, so the R model
    results read "0.7636 0.7062 0.8258 0.7062 0.8258 2" -- A SIXTH COLUMN A READER COULD
    TAKE FOR DATA, introduced by the fix for readability. This check refused that build.
    Preformatted blocks now carry the marker in front; stripping it here compares the R
    output to the R output. Had the marker stayed inside the block, stripping it here would
    have hidden exactly the defect the check had just caught.
    """
    raw = re.sub(r"(?is)<sup class=.prov-ref.[^>]*>.*?</sup>", "", raw)
    # A REFUSAL IS NOT R OUTPUT, AND COMPARING IT AS THOUGH IT WERE FAILED SIX PAGES.
    # On a topic with no stored model output the `quoted verbatim` section holds a REFUSAL,
    # and that refusal legitimately changed in this pass: it used to end "-- no field:
    # results.by_outcome.*.r_output.verbatim" inline, and the field moved to the provenance
    # list. The check called that a changed verbatim block and restored six pages that were
    # fine. Refusal blocks are removed, and only sections that actually contain R output
    # are compared -- a section with none has nothing to compare, which is different from a
    # section that matches.
    raw = re.sub(r"(?is)<div class=.absent-state.[^>]*>.*?</div>", " ", raw)
    secs, _a = panel_text(raw)
    if secs is None:
        return {}
    out = {}
    for h, t in secs:
        if "quoted verbatim" not in h.lower():
            continue
        if not re.search(R_OUTPUT, t):
            continue
        out[h] = t
    return out


def flow_paths(raw):
    """Field paths standing INSIDE the sentence flow (not in a provenance list)."""
    p = panel_raw(raw)
    # Remove the provenance block, which is where they are supposed to be now.
    p = re.sub(r"(?is)<div class='prov-block'>.*?</div>", " ", p)
    p = re.sub(r"(?is)<small[^>]*>\s*(?:&larr;|←).*?</small>", "@@ARROW@@", p)
    txt = htmllib.unescape(re.sub(r"<[^>]+>", " ", p))
    return len(FIELD_PATH.findall(txt)) + txt.count("@@ARROW@@")


def bag(pattern, text):
    from collections import Counter
    return Counter(pattern.findall(text))


def main():
    if len(sys.argv) < 3:
        sys.exit("usage: prove_register_change_moved_no_content.py BEFORE.html AFTER.html "
                 "[object.json]")
    before = io.open(sys.argv[1], encoding="utf-8", errors="replace").read()
    after = io.open(sys.argv[2], encoding="utf-8", errors="replace").read()
    obj = None
    if len(sys.argv) > 3 and os.path.exists(sys.argv[3]):
        obj = json.load(io.open(sys.argv[3], encoding="utf-8"))

    pb = htmllib.unescape(re.sub(r"<[^>]+>", " ", panel_raw(before)))
    pa = htmllib.unescape(re.sub(r"<[^>]+>", " ", panel_raw(after)))

    failures = []

    lost_n = bag(NUM, pb) - bag(NUM, pa)
    gained_n = bag(NUM, pa) - bag(NUM, pb)
    print("ESTIMATES  present before and NOT after: %d distinct" % len(lost_n))
    for v, n in sorted(lost_n.items())[:20]:
        print("    LOST  %s x%d" % (v, n))
    if lost_n:
        failures.append("%d numeric value(s) present before are absent after" % len(lost_n))
    print("           present after and not before: %d distinct (allowed -- the gloss and "
          "the cascade table print the same values in more places)" % len(gained_n))

    lost_ids = bag(NCT, before) - bag(NCT, after)
    print("")
    print("REGISTRATION IDS lost from the whole page: %d" % len(lost_ids))
    for v, n in sorted(lost_ids.items()):
        print("    LOST  %s x%d" % (v, n))
    if lost_ids:
        failures.append("%d registration id(s) lost" % len(lost_ids))

    if obj is not None:
        missing = []
        for o in (obj.get("outcomes") or []):
            nm = (o or {}).get("name")
            if not nm:
                continue
            key = " ".join(str(nm).split())[:60].lower()
            if key and key in " ".join(pb.split()).lower() \
                    and key not in " ".join(pa.split()).lower():
                missing.append(nm)
        print("")
        print("REGISTERED OUTCOME TEXT present before and lost after: %d" % len(missing))
        for m in missing:
            print("    LOST  %s" % m[:90])
        if missing:
            failures.append("%d registered outcome name(s) lost" % len(missing))

    vb, va = verbatim_blocks(before), verbatim_blocks(after)
    print("")
    print("VERBATIM-R SECTIONS  before %d, after %d" % (len(vb), len(va)))
    changed = [h for h in vb if vb[h] != va.get(h)]
    for h in changed:
        print("    CHANGED  %s" % h[:80])
    if changed:
        failures.append("%d verbatim section(s) changed" % len(changed))
    if len(vb) != len(va):
        failures.append("the number of verbatim sections changed")

    fb, fa = flow_paths(before), flow_paths(after)
    print("")
    print("FIELD PATHS INSIDE THE SENTENCE FLOW  before %d, after %d" % (fb, fa))
    if fa >= fb:
        failures.append("field paths in the sentence flow did not fall (%d -> %d) -- the "
                        "pass did nothing" % (fb, fa))

    print("")
    if failures:
        print("REFUSED. This was supposed to be a register change and it moved content:")
        for f in failures:
            print("    %s" % f)
        sys.exit(1)
    print("PASSED. Every estimate, registration id, registered outcome name and verbatim R")
    print("block that was on the page before is on it after. The field paths moved out of")
    print("the sentence flow: %d -> %d." % (fb, fa))


if __name__ == "__main__":
    main()
