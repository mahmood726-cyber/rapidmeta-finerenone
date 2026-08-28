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
    4. the served page carries the CURRENT generator stamp

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

    keep, rejected, excluded = [], [], []
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
        keep.append({"page": page, "object": rel, "outcomes": live,
                     "stamp": m.group(1), "title": title_of(body) or page})

    # A by-name exclusion that matches nothing is a no-op wearing the clothes of a decision.
    for frag in EXCLUDED_SUBSTRINGS:
        if not any(frag in p.upper() for p in excluded):
            say("REFUSED: the exclusion %r matched NO page in PAGE_MAP. Either the page is "
                "gone or the name is wrong; both need a person." % frag)
            return 2

    say("KEEP  %d" % len(keep))
    say("held  %d" % len(rejected))
    say("")
    for k in keep:
        say("  %-52s %-9s %s" % (k["page"][:52], k["stamp"][:9], ", ".join(k["outcomes"])[:40]))
    say("")
    for page, why in rejected:
        if why.startswith("EXCLUDED BY NAME"):
            say("  EXCLUDED  %-44s %s" % (page[:44], why[18:]))

    io.open(KEEP, "w", encoding="utf-8").write(
        "".join(k["page"] + chr(10) for k in keep))
    json.dump({"head": head, "keep": keep, "n_keep": len(keep),
               "excluded_by_name": {p: excluded_reason(p) for p in excluded},
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
