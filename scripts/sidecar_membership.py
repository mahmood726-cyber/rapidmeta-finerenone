"""Does a sidecar pool trials that belong to the review whose stem it carries?

A sidecar that pools trials absent from its own review is not a second opinion
about the same question -- it is an answer to a different one. So it is never
authoritative over the review, and a k disagreement between them is a MEMBERSHIP
dispute, not a counting error.

THE TRAP THIS AVOIDS. Several sidecars record trial LABELS and no NCT ids at
all. A disjointness test keyed on ids would then find "no shared ids" for every
one of them and accuse them all -- an instrument that can only reject. So the
identifier arm returns NOT_ASSESSABLE when either side has no ids, and the name
arm is used only when a label is specific enough to be searched for.

FOUR STATES, and only one of them is an accusation:

    SHARES            at least one pooled trial is identifiably on the page
    EXCLUDED_BY_REVIEW  a pooled trial appears on the page INSIDE the review's
                      excluded-records list. Stronger than absence: the review
                      considered it and said no, and the pool took it anyway.
    DISJOINT          every pooled trial is checkable and none is on the page
    STUB_NO_TRIALS_NAMED  the REVIEW PAGE names no trial at all -- no NCT id and no
                      trial-shaped label anywhere in its bytes. Such a page cannot
                      DISAGREE with its sidecar; it can only fail to confirm it.
                      Counting it as DISJOINT would manufacture a defect out of
                      emptiness. This is a limit of the page-derived route -- OURS,
                      not a property of the sidecar -- and it is subtracted from the
                      denominator rather than counted either way.
    NOT_ASSESSABLE    neither ids nor searchable labels on the SIDECAR side -- never
                      an accusation

Measured 2026-09-01 on the two sidecars this surface actually reads.
"""
import os
import re

# A label is searchable if it looks like a trial name rather than prose: at least
# one uppercase run of 3+ characters, or a recognised NCT id. "HPTN 082" and
# "FACTS-001" qualify; "oral PrEP (open label)" does not.
_SEARCHABLE = re.compile(r"[A-Z][A-Z0-9]{2,}")
_NCT = re.compile(r"NCT\d{8}")
# A trial-shaped token: an uppercase run of 3+, optionally hyphenated, standing
# as a word. Anchored on word boundaries the artefact already has.
_TRIALNAME = re.compile(r"\b[A-Z][A-Z0-9]{2,}(?:-[A-Z0-9]+)*\b")

# Phrases the review uses when it is listing a record it EXCLUDED. Anchored on
# wording the artefact already contains, never on an assumed quote style or tag.
_EXCLUSION_MARKERS = (
    "it is not a report of",
    "neither dapivirine nor any development code appears",
    "excluded",
    "does not appear in the title or the abstract",
)


def _visible(html_text):
    t = re.sub(r"(?is)<script.*?</script>", " ", html_text)
    t = re.sub(r"(?is)<style.*?</style>", " ", t)
    t = re.sub(r"<[^>]+>", " ", t)
    return re.sub(r"\s+", " ", t)


def trial_labels(sidecar):
    """[(label, nct_or_None)] from a sidecar object, in its own order."""
    trials = (sidecar.get("inputs") or {}).get("trials") or sidecar.get("trials") or []
    out = []
    for t in trials:
        if not isinstance(t, dict):
            continue
        label = (t.get("label") or t.get("name") or t.get("trial")
                 or t.get("study") or "").strip()
        out.append((label, t.get("nct")))
    return out


def _first_token(label):
    """The searchable head of a label: 'HPTN 082 (oral PrEP arm)' -> 'HPTN 082'."""
    if not label:
        return None
    head = label.split("(")[0].strip().rstrip(",;:")
    if not _SEARCHABLE.search(head):
        return None
    # keep at most the first three words -- longer is prose, not a name
    return " ".join(head.split()[:3]) or None


def classify(sidecar, page_html):
    """(state, evidence) for one sidecar against its own review page."""
    labels = trial_labels(sidecar)
    if not labels:
        return "NOT_ASSESSABLE", {"why": "the sidecar records no trials"}
    text = _visible(page_html)
    page_ncts = set(_NCT.findall(page_html))

    # A PAGE THAT NAMES NOTHING CANNOT DISAGREE. Measured 2026-09-02: 12 of 83
    # rows in the DISJOINT class were pages like OMECAMTIV_HF_AUTO_FULL_REVIEW.html
    # -- 2,746 bytes, zero NCT ids, zero trial labels. Reporting those as "this
    # pool's trials are not in this review" tells a reader the review disagrees,
    # when the review says nothing at all.
    if not page_ncts and not _TRIALNAME.search(text):
        return "STUB_NO_TRIALS_NAMED", {
            "pooled": [l or "(unnamed)" for l, _ in labels],
            "why": ("the review page names no trial at all -- no registration id and "
                    "no trial-shaped label. It cannot confirm or contradict this pool, "
                    "so nothing is asserted about the pool either way."),
            "page_bytes": len(page_html)}

    found, absent, excluded, unsearchable = [], [], [], []
    for label, nct in labels:
        if nct:
            if nct in page_ncts:
                found.append(label or nct)
                continue
            absent.append(label or nct)
            continue
        token = _first_token(label)
        if not token:
            unsearchable.append(label or "(unnamed)")
            continue
        hits = [m.start() for m in re.finditer(re.escape(token), text, re.I)]
        if not hits:
            absent.append(label)
            continue
        # present -- but is EVERY mention inside an exclusion context?
        ctx_excluded = 0
        for i in hits:
            window = text[max(0, i - 260):i + 260].lower()
            if any(mk in window for mk in _EXCLUSION_MARKERS):
                ctx_excluded += 1
        if ctx_excluded == len(hits):
            excluded.append(label)
        else:
            found.append(label)

    ev = {"pooled": [l or "(unnamed)" for l, _ in labels],
          "on_the_page": found, "absent_from_the_page": absent,
          "present_only_as_an_excluded_record": excluded,
          "not_searchable": unsearchable}
    if unsearchable and not (found or absent or excluded):
        return "NOT_ASSESSABLE", ev
    if excluded:
        return "EXCLUDED_BY_REVIEW", ev
    if found:
        return "SHARES", ev
    if absent:
        return "DISJOINT", ev
    return "NOT_ASSESSABLE", ev


# --- CONTROLS. Synthetic pages and sidecars, so they cannot retire.
_PAGE_WITH = "<p>The ASPIRE trial and the Ring Study both enrolled women.</p>"
_PAGE_EXCL = ("<p>Excluded records: Lessons learned from HPTN 082. "
              "Neither dapivirine nor any development code appears in the title "
              "or the abstract, so it is not a report of a dapivirine study.</p>")
_PAGE_NONE = "<p>This review includes ASPIRE only.</p>"

CONTROLS = [
    ({"trials": [{"label": "ASPIRE"}]}, _PAGE_WITH, "SHARES",
     "a pooled trial named on the page is not an accusation"),
    ({"trials": [{"label": "HPTN 082"}]}, _PAGE_EXCL, "EXCLUDED_BY_REVIEW",
     "present ONLY inside the excluded-records list is its own state"),
    ({"trials": [{"label": "FACTS-001"}]}, _PAGE_NONE, "DISJOINT",
     "a searchable name absent from the page is genuinely disjoint"),
    ({"trials": [{"label": "the open label extension"}]}, _PAGE_NONE, "NOT_ASSESSABLE",
     "an unsearchable label must NEVER be reported as disjoint"),
    ({"trials": [{"label": "X", "nct": "NCT01617096"}]},
     "<p>NCT01617096 ASPIRE</p>", "SHARES", "an id present on the page shares"),
    ({"trials": []}, _PAGE_WITH, "NOT_ASSESSABLE", "no trials recorded -- nothing to say"),
    ({"trials": [{"label": "GALACTIC-HF"}]},
     "<p>This review is pending. No trials are listed yet.</p>",
     "STUB_NO_TRIALS_NAMED",
     "a page naming NO trial cannot disagree -- it must never be called DISJOINT"),
    ({"trials": [{"label": "FACTS-001"}]}, _PAGE_NONE, "DISJOINT",
     "a page that DOES name a trial, just not this one, is genuinely disjoint"),
]


def run_controls(say=print):
    bad = 0
    for sc, page, want, why in CONTROLS:
        got, _ = classify(sc, page)
        ok = got == want
        bad += (not ok)
        say("   %-5s got %-20s expected %-20s %s"
            % ("PASS" if ok else "FAIL", got, want, why))
    return bad == 0


if __name__ == "__main__":
    import sys
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    print("scripts/sidecar_membership.py -- CONTROLS")
    ok = run_controls()
    print("\n   %s" % ("all controls held" if ok else "A CONTROL FAILED -- do not use"))
    sys.exit(0 if ok else 1)
