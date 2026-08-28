"""Build the READY keep-list POSITIVELY, and write it to every discovery surface.

MAHMOOD, TWICE: "the site seems full of estimand-withdrawn and retired reviews. it is hard to
find the working ones." Nothing is deleted and no link breaks. Every page keeps serving at its
URL. What changes is DISCOVERY: the indexes list only reviews that carry a result.

A KEEP LIST, NEVER A REMOVE LIST. An absence-based selector -- "pages with no interval in
their text" -- came within one commit of retiring 758 pages that hold results, because the
regex demanded a shape the corpus does not write. A whitelist cannot make that error. Its
failure mode is leaving a dead page listed, which costs a reader ten seconds, and that is the
right direction to be wrong in.

FOUR POSITIVE PROPERTIES, ALL REQUIRED, each read from source at the moment of use:

    1. the page has a store object in PAGE_MAP, and that file opens
    2. some outcome carries pooled.point that is not None AND per_trial rows behind it
    3. the object does not carry a refusal or withdrawal on that outcome
    4. the stamped build CONTAINS every required generator commit as an ancestor --
       not merely that a stamp is present, which is what the first version checked

Property 2 is stated as "a number AND evidence behind it" on purpose. This project has
conflated "has a point" with "has a pool" before, and a point with no per-trial rows is the
uncheckable-outcome class.

NEVER FROM A SERIALISED ARTEFACT. Building a working set by reading back my own JSON returned
232 pages instead of 763, because that JSON capped its member lists at 400 -- silently, an
hour after I wrote the cap. Recompute from source.

ONE PAGE IS EXCLUDED BY NAME. `gepotidacin` has three open findings and unverified trial
labels. It is excluded explicitly and reported as excluded, so that a later run cannot re-add
it as an oversight and call it a qualification.
"""
import io
import json
import os
import re
import subprocess
import sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(REPO, "scripts"))
OUT = os.path.join(REPO, "outputs", "ready_index_2026_08_28.json")
KEEP = os.path.join(REPO, "outputs", "_ready_keep.txt")

# Matched as a SUBSTRING of the page name, not as an exact filename. The first version of
# this named "GEPOTIDACIN_UTI_AUTO_FULL_REVIEW.html", which is not what the page is called --
# so the exclusion matched nothing, excluded nothing, and reported nothing. A silent no-op
# exclusion is worse than no exclusion: it reads as a decision that was applied.
EXCLUDED_SUBSTRINGS = {
    "GEPOTIDACIN":
        "three open findings and unverified trial labels -- held out deliberately, not a "
        "failure to qualify",
    # HFREF_NMA WAS HERE AND THE RULING SUPERSEDED IT. It was excluded on 2026-08-28 for
    # publishing an omnibus RR 0.86 with an NNT, a ranking, a patient-facing summary and
    # integrity 100/100 over placeholder risk-of-bias. Every one of those has since been
    # stripped from the served bytes and 0.8619 carries its true ACEI-versus-Placebo label,
    # so the ground for exclusion is gone. Mahmood ruled it back in; it now appears in
    # ADMITTED_BY_RULING with the leg it still fails (no store object) stated there.
    # Leaving it in BOTH lists would have printed a page as excluded and indexed it.
}


# ADMITTED BY RULING, each with the leg it fails and why the ruling stands anyway. A page
# admitted without its failure named would read as one that passed.
ADMITTED_BY_RULING = {
    "ARNI_HF_REVIEW.html": (
        "leg 4: stamp fa7ef6686 predates all seven required generator commits",
        "Mahmood: ARNI is a flagship. It is the corpus's ONLY hand-authored manuscript and it "
        "CANNOT be rebuilt to pass honestly -- measured, a rebuild reproduces just 10.5% of "
        "the served text and would replace 89.6% with projection. Indexed as-is, with the "
        "older build stated on the card rather than concealed."),
    "HFREF_NMA_AUTO_FULL_REVIEW.html": (
        "leg 1: no store object in PAGE_MAP",
        "Mahmood: index it now that the patient-facing claims, the NNT, the ranking and the "
        "integrity score are stripped and 0.8619 carries its true ACEI-versus-Placebo label."),
}


def excluded_reason(page):
    for frag, why in EXCLUDED_SUBSTRINGS.items():
        if frag in page.upper():
            return why
    return None

STAMP = re.compile(r"Generator build</th><td><code>([0-9a-f]{7,40})</code>")
REFUSAL = ("withdrawn_reason", "withdrawn_note", "not_poolable_reason", "absent_reason")


def current_stamp():
    return subprocess.run(["git", "rev-parse", "HEAD"], capture_output=True,
                          cwd=REPO).stdout.decode().strip()


def missing_ancestors(stamp):
    """Which REQUIRED generator commits the stamped build does NOT contain.

    LEG 4 WAS A STRING CHECK AND THAT IS NOT THE PROPERTY. The first version of this file
    accepted any page carrying `Generator build</th><td><code>...`, which is a claim that a
    stamp EXISTS, not a claim that the code which built the page contains the fixes we
    require. ARNI_HF_REVIEW passed it while stamped fa7ef6686 -- a commit that contains NONE
    of the seven required generator commits. A stamp naming the wrong commit passes a string
    check and fails the property the check exists to establish.
    """
    sys.path.insert(0, os.path.join(REPO, "ssot"))
    import do_not_rebuild
    out = []
    for sha in sorted(do_not_rebuild.REQUIRED_GENERATOR_COMMITS):
        r = subprocess.run(["git", "merge-base", "--is-ancestor", sha, stamp],
                           capture_output=True, cwd=REPO)
        if r.returncode != 0:
            out.append(sha)
    return out


def outcome_is_live(blk):
    """A pooled point AND per-trial rows behind it AND no refusal recorded on it."""
    if not isinstance(blk, dict):
        return False
    pooled = blk.get("pooled")
    if not isinstance(pooled, dict) or pooled.get("point") is None:
        return False
    if not (blk.get("per_trial") or []):
        return False
    if any(blk.get(f) for f in REFUSAL):
        return False
    return True


def run_controls():
    from instrument_controls import require_controls
    live = {"pooled": {"point": 0.81}, "per_trial": [{"t": 1}, {"t": 2}]}
    pointless = {"pooled": {"point": None}, "per_trial": [{"t": 1}]}
    norows = {"pooled": {"point": 0.81}, "per_trial": []}
    withdrawn = {"pooled": {"point": 0.81}, "per_trial": [{"t": 1}],
                 "withdrawn_reason": "endpoints differ"}
    assert outcome_is_live(norows) is False, "a point with no rows must not qualify"
    assert outcome_is_live(pointless) is False, "no point must not qualify"
    assert outcome_is_live(withdrawn) is False, "a withdrawn outcome must not qualify"
    require_controls(
        "ready_keep_list",
        ("an outcome with a point AND rows AND no refusal qualifies",
         outcome_is_live(live), True),
        ("a withdrawn outcome qualifies", outcome_is_live(withdrawn), True))


def main():
    run_controls()
    raw = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace",
                           write_through=True)

    def say(s):
        raw.write(s + chr(10))
        raw.flush()

    head = current_stamp()
    pm = json.load(io.open(os.path.join(REPO, "ssot", "PAGE_MAP.json"), encoding="utf-8"))
    say("HEAD %s" % head[:12])
    say("pages in PAGE_MAP: %d" % len(pm))
    say("")

    keep, rejected, excluded, excluded_not_in_pagemap = [], [], [], []
    admitted = []

    def admit(page):
        """A ruling admits a page; it does not make the page pass."""
        fails, why = ADMITTED_BY_RULING[page]
        served = os.path.join(REPO, page)
        if not os.path.exists(served):
            return None
        body = io.open(served, encoding="utf-8", errors="replace").read()
        m = STAMP.search(body)
        rel = pm.get(page)
        obj = None
        if rel and os.path.exists(os.path.join(REPO, rel)):
            obj = json.load(io.open(os.path.join(REPO, rel), encoding="utf-8"))
        live = []
        if obj:
            by = (obj.get("results") or {}).get("by_outcome") or {}
            live = [oid for oid, blk in by.items() if outcome_is_live(blk)]
        admitted.append({"page": page, "fails": fails, "ruling": why})
        return {"page": page, "object": rel, "outcomes": live,
                "stamp": m.group(1) if m else "none",
                "title": title_of(body) or page,
                "admitted_by_ruling": why, "fails": fails}
    for page, rel in sorted(pm.items()):
        why_excl = excluded_reason(page)
        if why_excl:
            excluded.append(page)
            rejected.append((page, "EXCLUDED BY NAME: " + why_excl))
            continue
        objpath = os.path.join(REPO, rel)
        if not os.path.exists(objpath):
            rejected.append((page, "1. no store object on disk"))
            continue
        try:
            obj = json.load(io.open(objpath, encoding="utf-8"))
        except ValueError:
            rejected.append((page, "1. store object does not parse"))
            continue
        by = (obj.get("results") or {}).get("by_outcome") or {}
        live = [oid for oid, blk in by.items() if outcome_is_live(blk)]
        if not live:
            rejected.append((page, "2. no outcome with a pooled point AND per-trial rows"))
            continue
        served = os.path.join(REPO, page)
        if not os.path.exists(served):
            rejected.append((page, "3. page does not build / is not served"))
            continue
        body = io.open(served, encoding="utf-8", errors="replace").read()
        m = STAMP.search(body)
        if not m:
            rejected.append((page, "4. no generator stamp on the served page"))
            continue
        missing = missing_ancestors(m.group(1))
        if missing:
            rejected.append((page, "4. stamp %s is missing %d required generator commit(s): "
                                   "%s" % (m.group(1), len(missing),
                                           ",".join(x[:9] for x in missing))))
            continue
        keep.append({"page": page, "object": rel, "outcomes": live,
                     "stamp": m.group(1), "title": title_of(body) or page})

    for page in ADMITTED_BY_RULING:
        rec = admit(page)
        if rec is None:
            say("REFUSED: %r is admitted by ruling but is not served on disk." % page)
            return 2
        keep.append(rec)

    # ONE REVIEW, ONE CARD. PAGE_MAP maps several page names onto the SAME object file, so
    # the index listed one review twice: ROTAVIRUS_VACCINE_AFRICA_REVIEW and
    # ROTAVIRUS_VACCINE_AUTO_FULL_REVIEW resolve to the identical object (same sha256, same
    # three NCTs) and therefore carried identical numbers to four decimals -- which a reader
    # can only read as two studies agreeing exactly. Deduplicated by OBJECT, not by page
    # name, keeping the page whose name matches the object's own slug. Both keep serving.
    by_object = {}
    for rec in keep:
        by_object.setdefault(rec.get("object"), []).append(rec)
    deduped, dropped = [], []
    for objpath, recs in by_object.items():
        if objpath is None or len(recs) == 1:
            deduped.extend(recs)
            continue
        slug = os.path.basename(os.path.dirname(objpath)).replace("-", "").lower()
        recs.sort(key=lambda r: (0 if r["page"].replace("_", "").replace(".html", "").lower()
                                 .startswith(slug[:18]) else 1, len(r["page"])))
        deduped.append(recs[0])
        for r in recs[1:]:
            dropped.append({"page": r["page"], "duplicate_of": recs[0]["page"],
                            "object": objpath})
    keep = deduped

    # A by-name exclusion that matches nothing is a no-op wearing the clothes of a decision.
    # It is checked against pages that EXIST ON DISK, not against PAGE_MAP: a page can be
    # ineligible for two independent reasons at once, and a page held out by name for a
    # safety reason must still be named even when it also lacks a store object. HFREF_NMA
    # is exactly that case -- it has no store, so it could never reach KEEP, and it is
    # still recorded as deliberately excluded so nobody reads its absence as an oversight.
    on_disk = set(p.upper() for p in os.listdir(REPO) if p.endswith(".html"))
    for frag in EXCLUDED_SUBSTRINGS:
        hits = [p for p in on_disk if frag in p]
        if not hits:
            say("REFUSED: the exclusion %r matched NO page on disk. Either the page is gone "
                "or the name is wrong; both need a person." % frag)
            return 2
        if not any(frag in p.upper() for p in excluded):
            excluded_not_in_pagemap.append((frag, sorted(hits)[0]))

    if dropped:
        say("DEDUPLICATED BY OBJECT -- same object, two page names")
        for d in dropped:
            say("   %-44s duplicate of %s" % (d["page"][:44], d["duplicate_of"]))
        say("")
    say("ADMITTED BY RULING -- these do NOT pass, they are ruled in")
    for a in admitted:
        say("   %-44s fails %s" % (a["page"][:44], a["fails"]))
    say("")
    say("KEEP  %d" % len(keep))
    say("held  %d" % len(rejected))
    say("")
    for k in keep:
        say("  %-52s %-9s %s" % (k["page"][:52], k["stamp"][:9], ", ".join(k["outcomes"])[:40]))
    say("")
    for page, why in rejected:
        if why.startswith("EXCLUDED BY NAME"):
            say("  EXCLUDED  %-44s %s" % (page[:44], why[18:]))
    for frag, page in excluded_not_in_pagemap:
        say("  EXCLUDED  %-44s by name AND has no store object -- ineligible twice"
            % page[:44])
    say("")
    say("LEG 4 REJECTIONS (stamp does not contain the required generator commits)")
    for page, why in rejected:
        if why.startswith("4. stamp"):
            say("  %-46s %s" % (page[:46], why[3:]))

    io.open(KEEP, "w", encoding="utf-8").write(
        "".join(k["page"] + chr(10) for k in keep))
    json.dump({"head": head, "keep": keep, "n_keep": len(keep),
               "excluded_by_name": {p: excluded_reason(p) for p in excluded},
               "excluded_by_name_no_store": dict(excluded_not_in_pagemap),
               "admitted_by_ruling": admitted,
               "deduplicated_by_object": dropped,
               "held": [{"page": p, "why": w} for p, w in rejected],
               "selector": "POSITIVE keep-list: store object + pooled.point with per_trial "
                           "rows + no refusal + a generator stamp on the served page"},
              io.open(OUT, "w", encoding="utf-8"), indent=1)
    say("")
    say("wrote %s and %s" % (os.path.relpath(KEEP, REPO), os.path.relpath(OUT, REPO)))
    return 0


def title_of(body):
    m = re.search(r"<title>(.*?)</title>", body, re.S | re.I)
    if not m:
        return None
    return re.sub(r"\s+", " ", re.sub(r"<[^>]+>", "", m.group(1))).strip()[:140]


if __name__ == "__main__":
    sys.exit(main())
