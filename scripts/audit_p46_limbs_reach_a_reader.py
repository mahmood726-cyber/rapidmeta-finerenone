"""For every limb P46 scores, does the thing it scores REACH A READER?

THE GENERAL FORM OF CLASS 83, WHICH WAS FOUND THREE TIMES IN ONE NIGHT IN THREE DIFFERENT
VOCABULARIES BEFORE ANYBODY ASKED THE GENERAL QUESTION:

    limb 3   applier wrote `title`/`agreement`     projector read `citation`/`how_it_differs`
             -> 16 rows across 13 topics rendered a PMID and four blank cells
    limb 4   applier wrote `model_output.verbatim` projector read `by_outcome.*.r_output`
             -> the manuscript refused "no analysis output is stored on this object"
    limb 4   applier wrote `model_output.verbatim` SCORER read `by_outcome.*.r_output`
             -> p46_queue returned ABSENT and two topics were REPORTED AS 4 OF 4 AT 3 OF 4

`p46_queue.score()` reads the OBJECT. It answers "does this topic possess the limb". It has
never answered "can a reader open a page and find it", and every P46 count reported so far
has meant the first while being heard as the second. THAT IS THE PRECISE DEFINITION OF
"objects built is not topics a reader can open", committed by the people who wrote it down.

HOW THIS DECIDES "RENDERS", AND WHY IT IS THE ONLY TEST THAT CANNOT BE FOOLED. It takes a
PROBE STRING OUT OF THE STORED LIMB ITSELF -- never typed here -- and looks for it in the
DELIVERED BYTES of the topic's page. Not in the object. Not in the projector's source. Not in
a list of section names. If the sentence the object stores is not in the file a reader
downloads, the limb does not reach a reader, whatever anything else says.

    probe = the longest run of HTML-safe characters in the stored limb, >= 40 chars

Quotes, ampersands and angle brackets are escaped on the way out, so a probe containing them
would report a false absence. The probe is chosen to avoid them rather than the comparison
being loosened -- a check that can only report "renders" is not a check.

SCORES ARE NEVER INVENTED HERE. `held` comes from importing p46_queue.score, so there is ONE
definition of held in the repo and this file cannot drift from it.

FOUR STATES PER LIMB:
    HELD+RENDERS   the object carries it and a reader can find it
    HELD ONLY      the object carries it and the delivered page does not show it  <- class 83
    NO PAGE        the topic has no page in PAGE_MAP, so nothing can be delivered
    not held       p46_queue says REFUSED or ABSENT; delivery is not asked
"""
import glob
import importlib.util
import io
import json
import os
import re
import sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from instrument_controls import require_controls          # noqa: E402

_spec = importlib.util.spec_from_file_location(
    "p46_queue", os.path.join(REPO, "scripts", "p46_queue.py"))
p46 = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(p46)

LIMBS = ["rob_per_result", "grade_per_pool", "comparison_denominator",
         "model_output_verbatim"]

# THE MANUSCRIPT SECTION EACH LIMB IS PROJECTED INTO, by its rendered heading. Used ONLY for
# refused limbs: the projector generates its own refusal wording rather than projecting the
# object's, so a probe taken from the object cannot match, and the testable property is
# narrower -- IS THE REFUSAL NAMED IN THIS LIMB'S OWN SECTION. Reported as REFUSED+NAMED, a
# deliberately weaker claim than HELD+RENDERS.
SECTION_HEADING = {
    "rob_per_result": "Risk of bias in the included results",
    "grade_per_pool": "Certainty of the evidence",
    "comparison_denominator": "Comparison with published syntheses",
    "model_output_verbatim": "Statistical output, quoted verbatim",
}


def refusal_named_in_section(page_text, heading):
    """Does a `Refused:` block appear inside this section on the delivered page?

    The section runs from the LAST occurrence of its heading (the first is the in-page
    navigation strip) to the next heading-like marker after it.
    """
    hits = [m.end() for m in re.finditer(re.escape(heading), page_text)]
    if not hits:
        return False, "the section heading is not on the page at all"
    start = hits[-1]
    nxt = page_text.find("<h3", start)
    span = page_text[start:nxt if nxt > start else start + 6000]
    return ("Refused:" in span), ("a refusal is named in this section" if "Refused:" in span
                                  else "the section renders with no refusal in it")


def probe_is_distinctive(probe, page, other_pages):
    """A probe found on OTHER topics' pages is boilerplate and proves nothing here.

    THE SECOND STATED LIMIT, CLOSED. A short or generic stored sentence can be shared across
    objects -- house-rule wording, a ceiling statement, a standard refusal. Finding it in
    this page would then say nothing about THIS limb reaching a reader. A probe that appears
    on a page belonging to a different topic is reported WEAK rather than counted.
    """
    for p in other_pages:
        if probe in p:
            return False
    return True

# Characters the renderer escapes on the way out. A probe containing one of these would be
# looked for in a form the page never carries, and would report a false ABSENT.
UNSAFE = re.compile(r"[<>&\"'‘’“”]")


def probe_from(text, minimum=40):
    """The longest HTML-safe run in `text`, or None if nothing long enough survives."""
    if not isinstance(text, str):
        return None
    runs = [r.strip() for r in UNSAFE.split(text)]
    runs = [r for r in runs if len(r) >= minimum]
    return max(runs, key=len) if runs else None


def strings_under(node, depth=0):
    """Every string leaf under `node`, longest first, skipping bookkeeping keys."""
    out = []
    if isinstance(node, str):
        out.append(node)
    elif isinstance(node, dict):
        for k, v in node.items():
            if str(k).startswith("_") or str(k).upper().startswith("SUPERSEDED"):
                continue
            out.extend(strings_under(v, depth + 1))
    elif isinstance(node, list):
        for v in node:
            out.extend(strings_under(v, depth + 1))
    return out


def limb_probe(obj, limb):
    """A string the renderer should emit for this limb, taken out of the object."""
    if limb == "rob_per_result":
        node = (obj.get("risk_of_bias") or {}).get("by_outcome")
    elif limb == "grade_per_pool":
        node = (obj.get("grade") or {}).get("by_outcome")
        if not node:
            node = [blk.get("grade") for _, blk in p46.pooled_outcomes(obj)]
    elif limb == "comparison_denominator":
        node = obj.get("published_comparison")
    else:
        # PROBE THE VERBATIM, WHICH IS THE THING THE LIMB SCORES.
        #
        # The first version of this function EXCLUDED `verbatim` and probed the prose fields
        # around it -- what_it_is, interval_method, reproduction_of_the_previous_value -- on
        # the reasoning that machine output is full of quotes. It reported HELD ONLY for
        # eleven topics INCLUDING one whose R output I had confirmed on the public host an
        # hour earlier. The prose fields genuinely do not render (the projector emits only
        # environment, call and verbatim), but that is a different finding, and reporting it
        # as "limb 4 reaches no reader" would have been false.
        #
        # A probe must come from the thing the limb scores. `p46_queue` scores
        # `r_output.verbatim`; so does this. Class 77 in my own instrument, again.
        node = [str((blk.get("r_output") or {}).get("verbatim") or "")
                for _, blk in p46.pooled_outcomes(obj)]
        node = [s for s in node if s] or None
    if not node:
        return None
    for s in sorted(strings_under(node), key=len, reverse=True):
        p = probe_from(s)
        if p:
            return p
    return None


def page_map():
    m = json.load(io.open(os.path.join(REPO, "ssot", "PAGE_MAP.json"), encoding="utf-8"))
    rev = {}
    for page, objpath in m.items():
        rev.setdefault(os.path.basename(os.path.dirname(objpath)), []).append(page)
    return rev


# Pages from OTHER topics, used to test that a probe is distinctive rather than boilerplate.
# Chosen to span builders and eras: an authored docmodel, an antibiotic pool, a lipid pool.
CONTROL_PAGES = ["ARNI_HF_REVIEW.html", "LEFAMULIN_CABP_AUTO_FULL_REVIEW.html",
                 "INCLISIRAN_LIPID_KIDNEY_AUTO_FULL_REVIEW.html", "ATTR_CM_REVIEW.html"]


def main():
    rev = page_map()
    cache = {}

    def delivered(page):
        if page not in cache:
            p = os.path.join(REPO, page)
            cache[page] = io.open(p, encoding="utf-8", errors="replace").read() \
                if os.path.isfile(p) else None
        return cache[page]

    # ---- CONTROLS. The positive is a limb VERIFIED ON THE PUBLIC HOST earlier tonight; the
    # negative is a sentence of the right shape that is in no object at all.
    cab = json.load(io.open(os.path.join(
        REPO, "ssot", "cab-prep-hiv-review", "cab-prep-hiv-review.json"), encoding="utf-8"))
    pos_probe = limb_probe(cab, "comparison_denominator")
    pos_page = delivered("CAB_PREP_HIV_REVIEW.html") or ""
    require_controls(
        "audit_p46_limbs_reach_a_reader",
        positive=("cab-prep-hiv-review's comparison probe, confirmed on the public host at "
                  "2026-08-21, is found in the delivered bytes",
                  bool(pos_probe) and pos_probe in pos_page, True),
        negative=("a sentence of the right shape that no object contains is reported as "
                  "rendering",
                  "THIS SENTENCE IS IN NO OBJECT AND MUST NOT BE FOUND ANYWHERE" in pos_page,
                  True))

    rows = []
    for p in sorted(glob.glob(os.path.join(REPO, "ssot", "*", "*.json"))):
        topic = os.path.basename(os.path.dirname(p))
        if os.path.basename(p) != topic + ".json":
            continue
        try:
            obj = json.load(io.open(p, encoding="utf-8"))
        except ValueError:
            continue
        if not p46.pooled_outcomes(obj):
            continue
        sc = p46.score(obj)
        pages = rev.get(topic) or []
        row = {"topic": topic, "pages": pages, "limbs": {}}
        for limb in LIMBS:
            state = sc.get(limb, ("ABSENT", ""))[0]
            if state == "ABSENT":
                row["limbs"][limb] = ("not held", state)
                continue
            if not pages:
                row["limbs"][limb] = ("NO PAGE", "topic absent from PAGE_MAP")
                continue

            # A REFUSED LIMB IS A COMPLETED OUTCOME UNDER P46 AND ITS DELIVERY IS ASKED TOO.
            # The claim is narrower and labelled as such: the projector generates its own
            # refusal wording, so what can be tested is that the refusal is NAMED IN THIS
            # LIMB'S OWN SECTION, not that the object's reason was projected.
            if state == "REFUSED":
                named, why = False, "no section mapped for this limb"
                for pg in pages:
                    named, why = refusal_named_in_section(delivered(pg) or "",
                                                          SECTION_HEADING[limb])
                    if named:
                        break
                row["limbs"][limb] = (("REFUSED+NAMED", why) if named
                                      else ("REFUSED, NOT NAMED", why))
                continue

            pr = limb_probe(obj, limb)
            if not pr:
                row["limbs"][limb] = ("UNPROBEABLE", "no HTML-safe run of 40+ chars stored")
                continue
            hit = [pg for pg in pages if pr in (delivered(pg) or "")]
            if not hit:
                row["limbs"][limb] = ("HELD ONLY", "not in %s" % ", ".join(pages))
                continue
            others = [delivered(pg) or "" for pg in CONTROL_PAGES if pg not in pages]
            if not probe_is_distinctive(pr, delivered(hit[0]) or "", others):
                row["limbs"][limb] = ("WEAK PROBE", "the probe also appears on another "
                                                    "topic's page, so it is boilerplate and "
                                                    "proves nothing about this limb")
                continue
            row["limbs"][limb] = ("HELD+RENDERS", hit[0])
        rows.append(row)

    print("")
    print("TOPICS WITH AT LEAST ONE POOLED OUTCOME: %d" % len(rows))
    print("")
    hdr = ("topic", "RoB", "GRADE", "compare", "output")
    print("%-42s %-13s %-13s %-13s %-13s" % hdr)
    tally = dict((s, 0) for s in
                 ("HELD+RENDERS", "HELD ONLY", "REFUSED+NAMED", "REFUSED, NOT NAMED",
                  "NO PAGE", "UNPROBEABLE", "WEAK PROBE", "not held"))
    both = held_only_topics = []
    both, held_only_topics = [], []
    for r in sorted(rows, key=lambda x: x["topic"]):
        cells = []
        for limb in LIMBS:
            st = r["limbs"][limb][0]
            tally[st] += 1
            cells.append({"HELD+RENDERS": "renders", "HELD ONLY": "HELD-ONLY",
                          "REFUSED+NAMED": "refusal shown",
                          "REFUSED, NOT NAMED": "REFUSAL LOST",
                          "NO PAGE": "no page", "UNPROBEABLE": "unprobeable",
                          "WEAK PROBE": "WEAK PROBE", "not held": "-"}[st])
        states = [r["limbs"][l][0] for l in LIMBS]
        # DELIVERED means every limb reached a reader in the state P46 scored it: a held limb
        # found in the bytes, or a refusal named in its own section.
        if all(s in ("HELD+RENDERS", "REFUSED+NAMED") for s in states):
            both.append(r["topic"])
        if any(s == "HELD ONLY" for s in states):
            held_only_topics.append(r["topic"])
        if set(states) != {"not held"}:
            print("%-42s %-13s %-13s %-13s %-13s" % tuple([r["topic"][:42]] + cells))

    print("")
    print("LIMB-INSTANCES, over %d topics x 4 limbs = %d:" % (len(rows), len(rows) * 4))
    for k in ("HELD+RENDERS", "HELD ONLY", "REFUSED+NAMED", "REFUSED, NOT NAMED",
              "NO PAGE", "UNPROBEABLE", "WEAK PROBE", "not held"):
        print("   %-14s %d" % (k, tally[k]))
    print("")
    print("TOPICS WHERE ALL FOUR LIMBS BOTH HOLD AND RENDER: %d" % len(both))
    for t in both:
        print("   %s" % t)
    print("")
    print("TOPICS CARRYING AT LEAST ONE LIMB THAT IS HELD AND DOES NOT RENDER: %d"
          % len(held_only_topics))
    for t in held_only_topics:
        print("   %s" % t)
    print("")
    print("A LIMB THAT DOES NOT REACH A READER IS NOT A DELIVERED LIMB. p46_queue scores "
          "POSSESSION;\nthis file scores DELIVERY, and the second number is the one a reader "
          "experiences.")


if __name__ == "__main__":
    main()
