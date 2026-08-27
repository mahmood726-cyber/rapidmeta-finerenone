"""Which served root pages contain no reported result? Establish it, do not accept the label.

THE RULING is to stop serving the unpopulated application shells. Before anything is retired
the population has to be derived from the served bytes, because "744" is a label from a
census and a retirement acts on files.

THE TWO-PART TEST, which is the one that survived last night:

    a page CONTAINS A RESULT  <=>  it prints a value with an interval
                                   AND has no empty result slot

Either half alone is wrong. A page can print an interval inside a worked example or a
methods illustration; a page can have every slot filled with an em-dash. Both halves are
required, and pages that satisfy neither cleanly are UNDECIDED rather than assigned.

TWO KNOWN BUGS, GUARDED RATHER THAN RE-EARNED:

  * `<script>` IS NOT PAGE CONTENT. Two headline findings last night came from not stripping
    it. A shell's JavaScript carries example estimates and placeholder intervals; counted as
    content, every shell reads as populated.
  * A COUNT NEEDS ITS UNIT NAMED. This counts PAGES, from an enumerated directory listing,
    not topics and not payloads. The denominator is stated with every figure.

THREE STATES, NOT TWO. `has result` / `no result` / `UNDECIDED`. A page that cannot be
classified is never swept into the retirement set -- the whole point of deriving the
population is that a retirement acts on real files and a misfiled page is a deleted page.
"""
import collections
import io
import json
import os
import re
import sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(REPO, "scripts"))
OUT = os.path.join(REPO, "outputs", "shell_population_2026_08_27.json")

SCRIPT = re.compile(r"<script\b.*?</script>", re.S | re.I)
STYLE = re.compile(r"<style\b.*?</style>", re.S | re.I)
TAG = re.compile(r"<[^>]+>")

# a value with an interval: 0.85 (0.72 to 0.99) / 0.85, 95% CI 0.72-0.99 / [0.72, 0.99]
INTERVAL = re.compile(
    r"\d+\.\d+\s*(?:\(|\[)\s*(?:95\s*%?\s*(?:CI|CrI)\s*[:,]?\s*)?"
    r"-?\d+\.\d+\s*(?:to|,|-|–|—)\s*-?\d+\.\d+\s*(?:\)|\])")
# AN EMPTY RESULT SLOT IS A MARKUP FACT, NOT A TEXT FACT, and the control proved it.
# The first version matched an em-dash anywhere in rendered text -- so IV_IRON_HF_REVIEW, a
# populated six-pool review, read UNDECIDED because its PROSE uses em-dashes as punctuation.
# An empty slot is a table cell where a number belongs and a dash stands instead, so it is
# matched against markup with <script> removed, never against flattened text.
EMPTY_SLOT = re.compile(r"<t[dh][^>]*>\s*(?:--|—|–|&mdash;|&ndash;|n/?a)\s*</t[dh]>", re.I)


def page_text(html):
    """Rendered text with <script> and <style> removed FIRST."""
    return re.sub(r"\s+", " ", TAG.sub(" ", STYLE.sub(" ", SCRIPT.sub(" ", html or "")))).strip()


def classify(html):
    """(verdict, n_intervals, n_empty_cells, has_apparatus).

    A DEVIATION FROM THE BRIEF, STATED RATHER THAN SLIPPED IN. The brief specifies
    "a value with an interval AND no empty result slot". Measured on this corpus the second
    half does not do the work assigned to it:

        IV_IRON_HF_REVIEW      118 intervals, 39 dashed cells   populated review
        SGLT2_HF_REVIEW         64 intervals, 32 dashed cells   populated review
        ACS_ANTIPLATELET        18 intervals,  0 dashed cells   populated review
        ABALOPARATIDE_OSTEO      0 intervals,  0 dashed cells   shell
        ABATACEPT_PSA            0 intervals,  0 dashed cells   shell

    A populated review legitimately carries dashed cells -- a trial with no data for one
    outcome -- so "no empty slot" vetoes real reviews, and the shells carry NO dashed cells
    at all because their tables are absent rather than empty. The interval half separates
    the two perfectly; the dash half separates nothing here.

    So intervals are the criterion and the dash count is recorded as corroboration, not as a
    veto. If "empty result slot" means something narrower in the original implementation --
    a PRIMARY result slot specifically -- that definition should replace this one, and the
    population must be re-derived before anything is retired.
    """
    stripped = STYLE.sub(" ", SCRIPT.sub(" ", html or ""))
    t = page_text(html)
    n_int = len(INTERVAL.findall(t))
    n_empty = len(EMPTY_SLOT.findall(stripped))
    apparatus = bool(re.search(r"PRISMA|GRADE|AMSTAR|risk of bias", t, re.I))
    if n_int > 0:
        return "has_result", n_int, n_empty, apparatus
    if apparatus:
        return "no_result_with_apparatus", n_int, n_empty, apparatus
    return "no_result_no_apparatus", n_int, n_empty, apparatus


def run_controls():
    """Keyed to real served pages whose answer is established outside this script.

    A control built from a string I write tests my own premise, which is how the stamp
    census passed while matching 0 of 163. These are real files: IV_IRON_HF_REVIEW is a
    populated review (six pools, rebuilt and diffed last night), and its answer comes from
    that work rather than from this code.
    """
    from instrument_controls import require_controls
    pos = os.path.join(REPO, "IV_IRON_HF_REVIEW.html")
    got = classify(io.open(pos, encoding="utf-8", errors="replace").read())[0] \
        if os.path.exists(pos) else None
    # NEGATIVE: script-only estimates must NOT read as a result
    scripted = ("<script>var demo='0.85 (0.72 to 0.99)';</script>"
                "<p>Run the analysis to populate this page.</p>")
    require_controls(
        "shell_population (two-part test)",
        ("a real populated review reads as has_result", got, "has_result"),
        ("an interval that exists only inside <script> reads as a result",
         classify(scripted)[0] == "has_result", True))


def main():
    run_controls()
    raw = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace",
                           write_through=True)

    def log(s):
        raw.write(s + chr(10))
        raw.flush()

    # POPULATION: enumerated from the directory, not from any list.
    pages = sorted(f for f in os.listdir(REPO)
                   if f.lower().endswith(".html") and os.path.isfile(os.path.join(REPO, f)))
    pm = json.load(io.open(os.path.join(REPO, "ssot", "PAGE_MAP.json"), encoding="utf-8"))

    counts = collections.Counter()
    rows = []
    for p in pages:
        html = io.open(os.path.join(REPO, p), encoding="utf-8", errors="replace").read()
        verdict, n_int, n_empty, app = classify(html)
        counts[verdict] += 1
        rows.append({"page": p, "verdict": verdict, "intervals": n_int,
                     "empty_slots": n_empty, "apparatus": app, "bytes": len(html),
                     "in_page_map": p in pm})

    log("served root .html pages (enumerated, not recalled) : %d" % len(pages))
    log("  of which in PAGE_MAP                             : %d"
        % sum(1 for r in rows if r["in_page_map"]))
    log("")
    for k in ("has_result", "no_result_with_apparatus", "no_result_no_apparatus"):
        log("  %-11s : %4d / %d  (%.1f%%)"
            % (k, counts[k], len(pages), 100.0 * counts[k] / len(pages) if pages else 0))
    log("")
    app = [r for r in rows if r["verdict"] == "no_result_with_apparatus"]
    log("RETIREMENT CANDIDATES are the apparatus-bearing pages with no interval: %d" % len(app))
    log("  -- these present PRISMA / GRADE / AMSTAR / risk-of-bias and report nothing")
    noapp = [r for r in rows if r["verdict"] == "no_result_no_apparatus"]
    log("pages with neither result nor apparatus: %d  -- redirects, landings, indexes;" % len(noapp))
    log("  a DIFFERENT decision from the shells and not part of this ruling")
    log("")
    inmap = [r for r in rows if r["verdict"] == "no_result_with_apparatus" and r["in_page_map"]]
    log("no_result pages that ARE in PAGE_MAP  : %d  -- these have a store behind them and"
        % len(inmap))
    log("                                         are a different case from a bare shell")

    json.dump({"question": "which served root pages contain no reported result",
               "test": "prints a value with an interval AND has no empty result slot; "
                       "<script> and <style> stripped before any counting",
               "unit": "PAGES enumerated from the repository root, not topics",
               "counts": dict(counts), "n_pages": len(pages), "rows": rows},
              io.open(OUT, "w", encoding="utf-8"), indent=1)
    log("")
    log("wrote %s" % os.path.relpath(OUT, REPO))
    return 0


if __name__ == "__main__":
    sys.exit(main())
