"""A planned duration displayed as an observed one: sweep the dapivirine class.

AN EXTERNAL REVIEWER READ THE DAPIVIRINE PAGE AND FOUND ASPIRE'S FOLLOW-UP GIVEN AS
12-14 MONTHS. That is the figure in the trial's registration -- what the investigators
INTENDED to observe. The publication reports what they actually observed: a median of
1.6 years, a maximum of 2.6, across 4,280 person-years. The page presented the first
number in a field a reader reads as the second.

THE TWO NUMBERS ARE NOT VERSIONS OF ONE FACT. A planned duration is a design parameter,
fixed before anyone was enrolled. An observed duration is a result, and on this trial it
is more than a third longer than the plan. Substituting one for the other understates
exposure time, and on a time-to-event outcome exposure time is the denominator.

WHY A REGISTRY FIELD IS THE EASY ONE TO REACH FOR. The registered timeframe is present
for 182 outcomes in this corpus because it can be fetched. The observed follow-up is
stored for a couple of dozen, because it has to be read out of a paper. When a builder
needs a duration and only one is at hand, the available number gets used and the label
does not change to match. That is the same shape as this project's oldest failure --
ABSENCE READ AS A NEGATIVE -- with a substitution on top.

WHAT THIS DETECTS, STATED NARROWLY. An object that stores BOTH a registered timeframe
and an observed follow-up, where the observed value is the registered one. That is the
dapivirine shape and it is decidable. It does NOT detect a page that displays a planned
figure while storing no observed value at all, because there is nothing to compare
against -- those are counted and reported as UNCHECKABLE, never as passes. A sweep that
called them clean would be reporting its own reach as coverage.
"""
import io
import json
import os
import re
import sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(REPO, "outputs", "planned_as_observed_2026_08_29.json")

PLANNED_KEYS = ("registered_primary_timeframe", "registered_primary_time_frame",
                "time_frame")
OBSERVED_KEYS = ("follow_up", "follow_up_months", "follow_up_length",
                 "follow_up_verbatim", "median_follow_up")


def norm(v):
    """Compare durations by meaning, not by spelling.

    '12 months', '12 Months', 'up to 12 months' and '12-month' are one value. Without
    this the sweep would miss every real instance and report a clean corpus, which is the
    most dangerous thing a sweep can do.
    """
    if v is None:
        return None
    s = str(v).strip().lower()
    if not s:
        return None
    s = re.sub(r"\b(up to|approximately|approx\.?|about|median|maximum|max)\b", " ", s)
    s = re.sub(r"[^a-z0-9.]+", " ", s).strip()
    s = re.sub(r"\bmonth s?\b|\bmonths\b|\bmonth\b", "month", s)
    s = re.sub(r"\byear s?\b|\byears\b|\byear\b", "year", s)
    s = re.sub(r"\bweek s?\b|\bweeks\b|\bweek\b", "week", s)
    return re.sub(r"\s+", " ", s).strip()


def collect(obj):
    """page -> {planned: [(path, value)], observed: [(path, value)]}"""
    planned, observed = [], []

    def w(x, p):
        if isinstance(x, dict):
            for k, v in x.items():
                if k in PLANNED_KEYS and not isinstance(v, (dict, list)) and v is not None:
                    planned.append((p + "." + k, v))
                if k in OBSERVED_KEYS and not isinstance(v, (dict, list)) and v is not None:
                    observed.append((p + "." + k, v))
                w(v, p + "." + k)
        elif isinstance(x, list):
            for i, v in enumerate(x):
                w(v, p + "[%d]" % i)
    w(obj, "")
    return planned, observed


# PRECISION KNOWN_NEGATIVE_CONTROLS. Constructed, so they cannot retire themselves when the corpus is
# repaired. Each is (planned, observed, must_flag, why).
KNOWN_NEGATIVE_CONTROLS = [
    ("12-14 months", "12-14 months", True, "the dapivirine shape: identical strings"),
    ("12 months", "Up to 12 Months", True, "identical once spelling is normalised"),
    ("12-14 months", "median 1.6 years", False, "a genuinely observed value must not flag"),
    ("52 weeks", "52 weeks from randomisation", False,
     "a longer observed string that merely CONTAINS the planned one is not the same "
     "value, and treating it as one would accuse a correct page"),
    ("7 years", "", False, "an empty observed value is uncheckable, not a hit"),
]


def measure_precision(say):
    bad = 0
    for pl, ob, must, why in KNOWN_NEGATIVE_CONTROLS:
        got = norm(pl) is not None and norm(pl) == norm(ob)
        if got != must:
            bad += 1
            say("   CONTROL FAILED  planned=%r observed=%r expected %s -- %s"
                % (pl, ob, must, why))
    rate = 100.0 * bad / len(KNOWN_NEGATIVE_CONTROLS)
    say("   comparator controls: %d/%d wrong (measured error rate %.1f%%)"
        % (bad, len(KNOWN_NEGATIVE_CONTROLS), rate))
    return bad


def main():
    raw = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace",
                           write_through=True)

    def say(s):
        raw.write(s + chr(10))
        raw.flush()

    say("PLANNED-AS-OBSERVED SWEEP")
    say("")
    say("COMPARATOR PRECISION, measured before any count is reported:")
    if measure_precision(say):
        say("")
        say("REFUSED: the comparator failed its own controls. Any count would be a "
            "statement about the matcher, not about the corpus.")
        return 2
    if "--plant" in sys.argv:
        say("")
        say("PLANT -- constructed cases with known answers")
        ok = sum(1 for pl, ob, must, _ in KNOWN_NEGATIVE_CONTROLS
                 if (norm(pl) is not None and norm(pl) == norm(ob)) == must)
        for pl, ob, must, why in KNOWN_NEGATIVE_CONTROLS:
            got = norm(pl) is not None and norm(pl) == norm(ob)
            say("   [%s] %s" % ("PASS" if got == must else "FAIL", why))
        say("   plant: %d/%d" % (ok, len(KNOWN_NEGATIVE_CONTROLS)))
        return 0 if ok == len(KNOWN_NEGATIVE_CONTROLS) else 2
    say("")

    pm = json.load(io.open(os.path.join(REPO, "ssot", "PAGE_MAP.json"), encoding="utf-8"))
    hits, uncheckable, both, neither = [], [], 0, 0

    for page, objpath in sorted(pm.items()):
        full = os.path.join(REPO, objpath)
        if not os.path.exists(full):
            continue
        try:
            obj = json.load(io.open(full, encoding="utf-8"))
        except ValueError:
            continue
        planned, observed = collect(obj)
        pn = set(x for x in (norm(v) for _, v in planned) if x)
        on = [(p, v, norm(v)) for p, v in observed if norm(v)]
        if not on:
            if pn:
                uncheckable.append({"page": page, "n_planned": len(pn)})
            else:
                neither += 1
            continue
        both += 1
        for opath, ovalue, onorm in on:
            if onorm in pn:
                src = next((p for p, v in planned if norm(v) == onorm), "")
                hits.append({"page": page, "observed_field": opath,
                             "observed_value": ovalue, "planned_field": src,
                             "normalised": onorm})

    say("KINDS IN THE POPULATION -- the denominator before the count")
    say("   objects storing BOTH a registered timeframe and an observed follow-up: %d" % both)
    say("   objects storing a registered timeframe and NO observed value:          %d"
        % len(uncheckable))
    say("   objects storing neither:                                               %d" % neither)
    say("")
    say("   the %d uncheckable objects are NOT passes. They are objects where the only "
        "duration stored is the planned one, so if a page displays it as observed there "
        "is nothing here to catch it." % len(uncheckable))
    say("")
    say("FINDINGS -- an observed follow-up field holding the registered planned value: %d"
        % len(hits))
    for h in hits[:40]:
        say("      %-50s %-26s = %r" % (h["page"][:50], h["observed_field"][-26:],
                                        str(h["observed_value"])[:40]))

    # ------------------------------------------------------------------
    # LEG B -- THE PAGE, BECAUSE LEG A REACHES ALMOST NOTHING.
    #
    # Leg A could compare only 4 objects of 163. Seventy-nine store the planned duration
    # and no observed one, which is exactly the condition under which the substitution
    # happens -- so the leg with the clean method is blind to the population where the
    # defect lives. Reporting its zero as a result would be reporting reach as coverage.
    #
    # The reviewer did not read an object. They read a page and saw a duration sitting
    # under a follow-up label. So this leg reads the rendered text, finds durations that
    # a reader would take as observed, and asks whether that number is the registered
    # planned one.
    #
    # A PAGE THAT SAYS WHICH IT IS MUST NOT BE FLAGGED. Dapivirine now prints the planned
    # figure and labels it planned, beside the observed one. That is the CORRECT handling
    # and a sweep that accused it would be arguing for the defect it exists to find.
    OBSERVED_LABEL = re.compile(
        r"(?i)(median follow[- ]?up|followed (?:up )?for|duration of follow[- ]?up|"
        r"follow[- ]?up (?:was|of|:)|over a median of)")
    DURATION = re.compile(r"(?i)(\d+(?:[.–-]\d+)?)\s*(month|months|year|years|week|weeks)")
    DISCLOSES = re.compile(
        r"(?i)(planned|registered|intended|protocol[- ]specified|per protocol|"
        r"as registered|design(?:ed)? (?:duration|follow))")

    # MEASURED ON LIVE DATA, NOT ASSUMED. The first version of this leg returned exactly
    # one hit and it was WRONG: on LENACAPAVIR_PREP_SSOT the phrase "duration of
    # follow-up" sits inside a registry outcome-measure DEFINITION -- "sum of all
    # duration of follow-up time in years, while at risk of HIV-1 infection" -- and the
    # "Up to 149 weeks" that followed it is the registered timeframe, printed correctly
    # as one. The page was quoting a registry field, not claiming an observed duration,
    # and the 150-character window swept straight across the quotation.
    #
    # So the leg's measured false-positive rate on its first live run was 1 of 1. Two
    # discriminators, both from that case: a label inside a COMPUTATION DEFINITION is not
    # a claim about what happened, and a duration more than 80 characters away is not the
    # value that label refers to.
    DEFINITIONAL = re.compile(
        r"(?i)(sum of all|total of|calculated as|divided by|defined as|is computed)")

    leg_b, leg_b_clean, leg_b_suppressed = [], 0, 0
    for page, objpath in sorted(pm.items()):
        full = os.path.join(REPO, objpath)
        pagefile = os.path.join(REPO, page)
        if not (os.path.exists(full) and os.path.exists(pagefile)):
            continue
        try:
            obj = json.load(io.open(full, encoding="utf-8"))
        except ValueError:
            continue
        planned, _ = collect(obj)
        pn = set(x for x in (norm(v) for _, v in planned) if x)
        if not pn:
            continue
        html = io.open(pagefile, encoding="utf-8", errors="replace").read()
        text = re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", html))
        flagged = False
        for m in OBSERVED_LABEL.finditer(text):
            if DEFINITIONAL.search(text[max(0, m.start() - 70):m.start()]):
                leg_b_suppressed += 1
                continue
            window = text[m.start():m.start() + 80]
            d = DURATION.search(window)
            if not d:
                continue
            if norm(d.group(0)) not in pn:
                continue
            # The number under an observed label IS the registered planned one. Only a
            # finding if the page does not say so within reading distance.
            context = text[max(0, m.start() - 260):m.start() + 320]
            if DISCLOSES.search(context):
                continue
            leg_b.append({"page": page, "label": m.group(0),
                          "duration": d.group(0), "context": context[:260]})
            flagged = True
            break
        if not flagged:
            leg_b_clean += 1

    say("")
    say("LEG B -- the rendered page, which is what the reviewer read")
    say("   pages with a registered timeframe to compare against: %d"
        % (leg_b_clean + len(leg_b)))
    say("   label occurrences suppressed as computation DEFINITIONS, not claims: %d"
        % leg_b_suppressed)
    say("   pages showing the PLANNED duration under an observed label, undisclosed: %d"
        % len(leg_b))
    for h in leg_b[:40]:
        say("      %-50s %-22s %s" % (h["page"][:50], h["label"][:22], h["duration"]))

    json.dump({"n_both": both, "n_uncheckable": len(uncheckable), "n_neither": neither,
               "uncheckable": uncheckable, "findings": hits,
               "leg_b_pages_checked": leg_b_clean + len(leg_b), "leg_b_findings": leg_b},
              io.open(OUT, "w", encoding="utf-8"), indent=1)
    say("")
    say("wrote %s" % os.path.relpath(OUT, REPO))
    return 0


if __name__ == "__main__":
    sys.exit(main())
