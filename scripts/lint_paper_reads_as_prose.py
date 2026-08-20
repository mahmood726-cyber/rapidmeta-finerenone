"""How much of the Paper panel is machine vocabulary a reader has no way to parse?

MAHMOOD READ `SGLT2_HF_REVIEW.html#paper` ON THE PUBLIC HOST AND CALLED IT "COMPUTER CODE".
He is the second reader tonight to reach that manuscript and bounce off it, AFTER the
`#paper` anchor was created and the section order was fixed. So the ordering was necessary
and was not what either of them met.

THIS COUNTS SENTENCES, NOT SECTIONS. A sentence reads as code if it contains any of:

    FIELD PATH      a dotted path into the object -- `results.by_outcome.x.heterogeneity.i2`,
                    `screening.eligibility_provenance`, `protocol.rationale`
    SNAKE/CAMEL     an identifier in the prose -- `cvdeath_or_whf_first`,
                    `harmonised_cvdeath_or_hhf`, `k_unscreened_remainder`
    BARE NCT        a registration id inline in a sentence rather than in a table or a
                    provenance line
    STORAGE DIGITS  a number carried at more decimal places than the estimate supports --
                    `0.7576` where the page renders 0.76, `tau-squared 0.0012`
    RAW STATS       machine statistics with no gloss -- `tau^2`, `I^2`, `zval`, `pval`,
                    `ci.lb`, `se`, `Q(df = 2)`

AND SEPARATELY, THE PROVENANCE ARROW. Every projected paragraph on every page ends with
`<small class='muted'>&larr; <field path></small>`. That is not one topic's prose; it is
`ssot/paper_projector.py` appending the source field to each paragraph it writes. IT IS
CORRECT AND IT IS THE SINGLE LARGEST SOURCE OF FIELD NAMES IN THE READER'S EYE. Counted on
its own line here because the fix for it is a projector change that reaches 141 pages, not a
rewrite of one topic.

WHAT THIS DOES NOT MEASURE, AND WILL NOT. The `Statistical output, quoted verbatim` section
is R console output ON PURPOSE -- P46's fourth criterion requires the model output quoted
verbatim, and a reader who wants to check the arithmetic needs exactly those characters. It
is machine vocabulary that BELONGS. It is excluded by name, and excluding it is the
difference between measuring a defect and measuring the standard.

THREE STATES. A page with no Paper panel is NOT_ASSESSABLE, not clean.
"""
import io
import os
import re
import sys
import glob
import html as htmllib

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from instrument_controls import require_controls

# Sections that are machine vocabulary BY DESIGN and are excluded from the count.
# "quoted verbatim" as a substring, because the heading is not stable across generators:
# the delivered SGLT2 page says "Statistical output, quoted verbatim" and an older build
# says "Analysis output - <estimand> (quoted verbatim)". Matching the stable phrase rather
# than one generator's wording is the difference between excluding the R output and
# counting it as a defect.
BY_DESIGN = ("quoted verbatim", "software availability", "data availability",
             "references", "submission conformance")

READER_FACING = ("abstract", "introduction", "discussion", "conclusions")

FIELD_PATH = re.compile(
    r"\b(?:results|screening|protocol|search|config|outcomes|risk_of_bias|grade|inputs|"
    r"k_cascade|prisma_flow|manuscript|methodological_authority|withholding_question)"
    r"[\.\[][\w\.\[\]=\-]+")
SNAKE = re.compile(r"\b[a-z][a-z0-9]*(?:_[a-z0-9]+){1,}\b")
CAMEL = re.compile(r"\b[a-z]+[A-Z][a-zA-Z]*\b")
NCT = re.compile(r"\bNCT\d{8}\b")
RAW_STATS = re.compile(
    r"tau\^2|I\^2|H\^2|\bzval\b|\bpval\b|\bci\.(?:lb|ub)\b|\bpi\.(?:lb|ub)\b|"
    r"\bQ\(df\s*=|\byi\s*=|\bsei\s*=|\brma\(|\bqnorm\(|\bp-val\b|\btau-squared\b|"
    r"\bI-squared\b|degrees of freedom")
# Four or more decimal places is beyond what any effect estimate on these pages supports.
STORAGE_DIGITS = re.compile(r"\d\.\d{4,}")

SENT = re.compile(r"(?<=[.!?])\s+(?=[A-Z←])|\n+")


def panel_text(raw):
    """(sections, arrows) from the delivered bytes. sections = [(heading, text)]."""
    i = raw.find('id="paper"')
    if i < 0:
        return None, 0
    start = raw.rfind("<", 0, i)
    rest = raw[start:]
    nxt = None
    for m in re.finditer(r'id="(?:pn-)?(?:analysis|extract|dm|data|home|dash|method)"',
                         rest[10:]):
        nxt = 10 + m.start()
        break
    panel = rest[:nxt] if nxt else rest

    arrows = panel.count("&larr;") + panel.count("←")

    t = re.sub(r"(?is)<script.*?</script>", " ", panel)
    t = re.sub(r"(?is)<style.*?</style>", " ", t)
    # The provenance arrow is its own element and is counted separately, not as prose.
    t = re.sub(r"(?is)<small[^>]*>\s*(?:&larr;|←).*?</small>", " ", t)
    t = re.sub(r"(?i)<h[1-6][^>]*>", "\n@@@", t)
    t = re.sub(r"(?i)</h[1-6]>", "\n", t)
    t = re.sub(r"(?i)<(p|div|li|tr|br)[^>]*>", "\n", t)
    t = re.sub(r"<[^>]+>", " ", t)
    t = htmllib.unescape(t)
    t = re.sub(r"[ \t]+", " ", t)

    sections, head, buf = [], "(preamble)", []
    for line in t.split("\n"):
        if line.startswith("@@@"):
            sections.append((head, "\n".join(buf)))
            head, buf = line[3:].strip(), []
        else:
            if line.strip():
                buf.append(line.strip())
    sections.append((head, "\n".join(buf)))
    return sections, arrows


def score(text):
    """-> (sentences, machine_sentences, reasons Counter-ish dict)."""
    sents = [s.strip() for s in SENT.split(text) if len(s.strip()) > 25]
    bad, why = 0, {}
    for s in sents:
        hits = []
        if FIELD_PATH.search(s):
            hits.append("field path")
        if RAW_STATS.search(s):
            hits.append("raw stats")
        if NCT.search(s):
            hits.append("bare NCT")
        if STORAGE_DIGITS.search(s):
            hits.append("storage digits")
        # snake/camel, after field paths so a path is not double-counted
        if not hits or "field path" not in hits:
            if SNAKE.search(s) or CAMEL.search(s):
                hits.append("identifier")
        if hits:
            bad += 1
            for h in hits:
                why[h] = why.get(h, 0) + 1
    return len(sents), bad, why


def measure(path):
    raw = io.open(path, encoding="utf-8", errors="replace").read()
    sections, arrows = panel_text(raw)
    if sections is None:
        return None
    tot = mach = 0
    rf_tot = rf_mach = 0
    why = {}
    worst = []
    for head, text in sections:
        h = head.lower().strip()
        if any(b in h for b in BY_DESIGN):
            continue
        n, b, w = score(text)
        tot += n
        mach += b
        for k, v in w.items():
            why[k] = why.get(k, 0) + v
        if any(r in h for r in READER_FACING):
            rf_tot += n
            rf_mach += b
        if b:
            worst.append((b, n, head))
    worst.sort(reverse=True)
    return {"sentences": tot, "machine": mach, "arrows": arrows, "why": why,
            "reader_facing": (rf_mach, rf_tot), "worst": worst}


def main():
    target = None
    for a in sys.argv[1:]:
        if not a.startswith("--"):
            target = a
    figs = REPO   # delivered pages live at the repo root, not in figs/
    paths = ([target] if target
             else sorted(glob.glob(os.path.join(figs, "*_REVIEW.html"))))

    # CONTROLS. The positive is the page Mahmood read; its Paper panel demonstrably
    # contains field paths, because they are visible in the delivered bytes. The negative
    # is the verbatim-R section, which is machine vocabulary BY DESIGN -- if the check
    # counts that, it is measuring the standard rather than a defect.
    probe = os.path.join(figs, "SGLT2_HF_REVIEW.html")
    if os.path.exists(probe):
        m = measure(probe)
        raw = io.open(probe, encoding="utf-8", errors="replace").read()
        secs, _a = panel_text(raw)
        verbatim_counted = any(
            "statistical output" in h.lower() for h, _t in secs
            if any(b in h.lower() for b in BY_DESIGN)) is False
        require_controls(
            "lint_paper_reads_as_prose",
            positive=("SGLT2_HF_REVIEW's Paper panel, which a reader called computer code",
                      m is not None and m["machine"] > 0, True),
            negative=("the verbatim-R section, machine vocabulary BY DESIGN",
                      verbatim_counted, True))

    print("")
    rows = []
    for p in paths:
        m = measure(p)
        name = os.path.basename(p)
        if m is None:
            rows.append((name, None))
            continue
        rows.append((name, m))

    assessable = [(n, m) for n, m in rows if m]
    print("PAPER PANELS MEASURED: %d; NOT_ASSESSABLE (no Paper panel): %d"
          % (len(assessable), len(rows) - len(assessable)))
    print("NOT_ASSESSABLE MEANS NO PANEL WAS FOUND, NOT THAT THE PROSE IS CLEAN.")

    if target or len(assessable) == 1:
        for name, m in assessable:
            pct = 100.0 * m["machine"] / m["sentences"] if m["sentences"] else 0
            rf_m, rf_t = m["reader_facing"]
            print("")
            print("%s" % name)
            print("    sentences in the Paper panel (verbatim-R and references excluded) %4d"
                  % m["sentences"])
            print("    sentences carrying machine vocabulary                            %4d"
                  " (%.0f%%)" % (m["machine"], pct))
            print("    of those, in the four READER-FACING sections                     %4d"
                  " of %d" % (rf_m, rf_t))
            print("    provenance arrows appended by the projector                      %4d"
                  % m["arrows"])
            for k in sorted(m["why"], key=lambda k: -m["why"][k]):
                print("        %-16s %4d" % (k, m["why"][k]))
            print("    heaviest sections:")
            for b, n, head in m["worst"][:8]:
                print("        %3d/%-3d  %s" % (b, n, head))
        return

    tot_s = sum(m["sentences"] for _n, m in assessable)
    tot_m = sum(m["machine"] for _n, m in assessable)
    tot_a = sum(m["arrows"] for _n, m in assessable)
    print("")
    print("ACROSS THE CORPUS")
    print("    sentences                    %6d" % tot_s)
    print("    carrying machine vocabulary  %6d  (%.0f%%)"
          % (tot_m, 100.0 * tot_m / tot_s if tot_s else 0))
    print("    provenance arrows            %6d" % tot_a)
    print("")
    print("WORST PAGES BY PROPORTION:")
    ranked = sorted(((100.0 * m["machine"] / m["sentences"] if m["sentences"] else 0,
                      m["machine"], m["sentences"], n) for n, m in assessable),
                    reverse=True)
    for pct, b, n_, name in ranked[:12]:
        print("    %5.0f%%  %4d/%-4d  %s" % (pct, b, n_, name))


if __name__ == "__main__":
    main()
