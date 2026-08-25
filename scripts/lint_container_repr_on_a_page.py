"""A Python dict or list repr rendered onto a delivered page. Grep with a known answer.

THE INSTANCE. `paper_projector.py` built the GRADE table's "Rating steps" cell as
`"; ".join(str(x) for x in blk["steps"])`, and the steps are dicts. A reader who opened
`SGLT2_HF_REVIEW.html` and scrolled to Certainty of the evidence met, in a table cell:

    {'domain': 'risk_of_bias', 'levels': -1, 'from': 'HIGH', 'to': 'MODERATE',
     'reason': 'Rated down one level because unassessed is not low.'}

THAT IS WHAT "READS LIKE COMPUTER CODE" MEANS IN ITS MOST LITERAL POSSIBLE FORM. It is not
a register problem, a vocabulary problem or an ordering problem. It is a Python data
structure printed onto a page a reader opened, and it is the single most reader-visible
defect found on 2026-08-20.

WHY A SEPARATE INSTRUMENT. `str()` on a container is silent, total and always succeeds --
there is no failure to notice. `lint_paper_reads_as_prose.py` scored the cell as one
machine sentence among twenty-five, which is true and badly understates it: a `{'domain':`
is not the same order of defect as an unglossed I-squared, and a count that treats them
alike cannot say so.

TWO SEARCHES, and the second is why this file exists rather than a one-off grep:

    SOURCE   `str(x)`-shaped calls in the projectors where the value can be a container.
             Reported as CANDIDATES -- static analysis cannot know a value's type, and
             saying it can would be the accusing-direction error.
    DELIVERED The actual bytes. `{'` and `[{'` and `': '` in rendered text is not a
             candidate, it is an instance. THIS IS THE SIDE THAT DECIDES.

The delivered search is the finding; the source search only says where to look.
"""
import io
import os
import re
import sys
import glob

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from instrument_controls import require_controls

# A dict or list repr as it lands in HTML. Deliberately narrow: a quoted key followed by a
# colon inside braces is not something English produces.
REPR_IN_TEXT = re.compile(
    r"\{&#x27;|\{'|&#x27;: &#x27;|': '|\[\{|&quot;: &quot;|\{&quot;\w+&quot;: "
    # A PLAIN LIST OF STRINGS WAS NOT IN THE LIST OF MARKERS.
    #
    # Everything above enumerates DICT reprs, plus `[{` for a list of dicts. A list of plain
    # strings -- `['harmonised_cvdeath_or_hhf', 'threecomp_cvdeath_hhf_urgent']` -- matches
    # none of them, and an overnight adversarial hunt found exactly that in reader prose on
    # SGLT2_HF_REVIEW while this lint returned [] for the page.
    #
    # That is this lint committing the failure it exists to catch. Its docstring says "a
    # Python data structure rendered onto a delivered page"; its implementation was a list of
    # the four shapes somebody had happened to see. A vocabulary, not a property -- the same
    # error as a hollow-prose gate resting on seven literal phrases, and the same reason a
    # 20-page defect sat behind that one all day.
    #
    # The property is: a BRACKETED SEQUENCE OF QUOTED STRINGS. Two or more, so an ordinary
    # sentence quoting one term in brackets is not accused.
    r"|\[(?:&#x27;|&quot;|')[^\]]{0,400}?,\s*(?:&#x27;|&quot;|')")
# ...but a JSON block inside <script>, <pre class="json"> or a code sample is legitimate.
STRIP = (re.compile(r"(?is)<script.*?</script>"),
         re.compile(r"(?is)<style.*?</style>"),
         re.compile(r"(?is)<pre[^>]*>.*?</pre>"),
         re.compile(r"(?is)<code[^>]*>.*?</code>"))

SOURCE_CALL = re.compile(r"str\(\s*(?:x|v|val|value|blk\[|row\[|step|item)")


def rendered_text(raw):
    t = raw
    for r in STRIP:
        t = r.sub(" ", t)
    t = re.sub(r"<[^>]+>", " ", t)
    return t


def scan_delivered(paths):
    hits = []
    for p in paths:
        try:
            raw = io.open(p, encoding="utf-8", errors="replace").read()
        except Exception:
            continue
        t = rendered_text(raw)
        found = [m.group(0) for m in REPR_IN_TEXT.finditer(t)]
        if found:
            i = REPR_IN_TEXT.search(t).start()
            hits.append((os.path.basename(p), len(found),
                         " ".join(t[max(0, i - 60):i + 160].split())))
    return hits


def scan_source():
    out = []
    for p in sorted(glob.glob(os.path.join(REPO, "ssot", "*.py"))
                    + glob.glob(os.path.join(REPO, "scripts", "*.py"))):
        src = io.open(p, encoding="utf-8", errors="replace").read()
        for i, line in enumerate(src.split("\n")):
            if SOURCE_CALL.search(line) and ("join(" in line or "append(" in line
                                             or "add(" in line or "%" in line):
                out.append((os.path.relpath(p, REPO).replace("\\", "/"), i + 1,
                            line.strip()[:96]))
    return out


def main():
    pages = sorted(glob.glob(os.path.join(REPO, "*_REVIEW.html")))
    hits = scan_delivered(pages)

    # CONTROLS. The positive is a constructed instance -- the exact cell the GRADE table
    # produced before it was worded -- because once the defect is fixed no delivered page
    # carries it, and a check whose positive control is "the corpus is dirty" stops working
    # the moment the corpus is clean. The negative is a sentence with a colon and a quote
    # in ordinary English, which must NOT match.
    fixture = ("<p>Rating steps: {'domain': 'risk_of_bias', 'levels': -1, 'from': 'HIGH'}"
               "</p>")
    clean = ("<p>The trial's own registry description says: 'no statistical comparison was "
             "planned', which is a fact about the protocol.</p>")
    require_controls(
        "lint_container_repr_on_a_page",
        positive=("the GRADE cell as it was delivered on 2026-08-20",
                  bool(REPR_IN_TEXT.search(rendered_text(fixture))), True),
        negative=("an ordinary English sentence carrying a colon and a quotation",
                  bool(REPR_IN_TEXT.search(rendered_text(clean))), True))

    print("")
    print("DELIVERED PAGES CARRYING A CONTAINER REPR: %d of %d" % (len(hits), len(pages)))
    for name, n, ctx in hits[:25]:
        print("    %-52s %d occurrence(s)" % (name, n))
        print("        ...%s..." % ctx[:150])
    if len(hits) > 25:
        print("    ... +%d more" % (len(hits) - 25))

    src = scan_source()
    print("")
    print("SOURCE CANDIDATES -- str() on a value that MAY be a container: %d" % len(src))
    print("CANDIDATES, NOT FINDINGS. Static analysis cannot know a value's type; the")
    print("delivered side above is what decides.")
    for rel, ln, txt in src[:20]:
        print("    %s:%d" % (rel, ln))
        print("        %s" % txt)
    if len(src) > 20:
        print("    ... +%d more" % (len(src) - 20))

    if hits:
        print("")
        print("REFUSED: a Python data structure is rendered onto a delivered page.")
        sys.exit(1)


if __name__ == "__main__":
    main()
