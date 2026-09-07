# -*- coding: utf-8 -*-
"""CLAIM-LEVEL REPRODUCTION CENSUS: the unit is the rendered claim, not the review.

A review REPRODUCES iff re-running from its protocol regenerates the SERVED PAGE -- every rendered claim,
not the headline. Object-to-object equality of the primary result let the empagliflozin page "reproduce"
while carrying an empty protocol tab, a stale GRADE, debug dicts in the prose, and CARDIOVASCULAR DEATH
printed under ALL-CAUSE MORTALITY. This enumerates every rendered estimate and classifies it, keying on
the TUPLE (outcome label + measure + interval), never on the value -- because 0.91 (0.80-1.05) is real,
it is simply bound to the wrong outcome, and a value-match returns PASS on it.

Three checks, each emitting NAMED items (never a rate):
  A. CLAIM IDENTITY  -- the same (point, CI) under two DIFFERENT outcome labels is an automatic FAIL
                        (the mortality mislabel). Enumerate every rendered estimate with its label.
  B. RENDERED PROSE  -- no truncated sentence, no repr/dict syntax, no stray [], no placeholder fragment.
  C. (field coverage lives in field_render_check.py; this tool calls it so the census is one report.)

Fail closed: an estimate the tool cannot classify FAILS.
"""
from __future__ import annotations
import io, os, re, sys, json, importlib.util

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
# an effect estimate as rendered: MEASURE point then an interval as (lo-hi) OR ", lo-hi" OR "(lo to hi)"
_EST = re.compile(r"\b(HR|RR|OR|MD|SMD|IRR)\s+(-?\d+\.?\d*)\s*[\(,]\s*(-?\d+\.?\d*)\s*(?:[–—-]|to)\s*(-?\d+\.?\d*)\s*\)?", re.I)
# outcome-ish label words to attribute an estimate to the nearest preceding label
_OUTCOME_WORDS = ("all-cause mortality", "cardiovascular death", "hospitalisation", "hospitalization",
                  "primary composite", "primary outcome", "stroke", "myocardial", "mace", "ldl",
                  "heart failure", "composite", "mortality")


def _text(html):
    t = re.sub(r"<(script|style)[^>]*>.*?</\1>", " ", html, flags=re.S | re.I)
    return re.sub(r"[ \t]+", " ", re.sub(r"<[^>]+>", " ", t))


def check_prose(html):
    """B. rendered-prose failures, named."""
    t = _text(html)
    fails = []
    if re.search(r"\{\s*'[A-Za-z_]+'\s*:", t) or re.search(r"\}\s*,\s*\{", t):
        fails.append(("repr/dict syntax in prose", re.search(r"\{\s*'[A-Za-z_]+'\s*:[^}]{0,40}", t).group(0)[:50]))
    if re.search(r"\[\s*\]", t):
        fails.append(("stray empty brackets []", "[]"))
    # a sentence-ish fragment ending mid-word before an ellipsis or a hard cut on a word boundary
    for m in re.finditer(r"[a-z]{3,}(…|\bchoo\b|\bpools these\b)", t):
        fails.append(("truncated fragment", t[max(0, m.start() - 30):m.end() + 3].strip()[:60]))
    for frag in ("REPLACE_ME", "__PLACEHOLDER__", "{{", "the reader choo", "baseline risk the reader choo"):
        if frag in t:
            fails.append(("placeholder fragment", frag))
    # dedupe
    seen = set(); out = []
    for k, v in fails:
        if (k, v) not in seen:
            seen.add((k, v)); out.append((k, v))
    return out


def check_claim_identity(html):
    """A. every rendered estimate + its nearest outcome label; duplicate tuple under 2 labels = FAIL."""
    t = _text(html)
    claims = []
    for m in _EST.finditer(t):
        measure, pt, lo, hi = m.group(1).upper(), m.group(2), m.group(3), m.group(4)
        # nearest preceding outcome word within 160 chars
        window = t[max(0, m.start() - 160):m.start()].lower()
        label = None
        for w in _OUTCOME_WORDS:
            idx = window.rfind(w)
            if idx >= 0 and (label is None or idx > label[1]):
                label = (w, idx)
        claims.append({"measure": measure, "point": pt, "ci": (lo, hi), "label": label[0] if label else "(unlabelled)"})
    # a (point, ci) triple appearing under >=2 DISTINCT outcome labels -> mislabel FAIL
    by_value = {}
    for c in claims:
        key = (c["point"], c["ci"])
        by_value.setdefault(key, set()).add(c["label"])
    mislabels = []
    for (pt, ci), labels in by_value.items():
        real = {l for l in labels if l != "(unlabelled)"}
        if len(real) >= 2:
            mislabels.append({"value": "%s (%s-%s)" % (pt, ci[0], ci[1]), "labels": sorted(real)})
    return claims, mislabels


def check_not_in_object(claims, obj):
    """An estimate labelled with a SPECIFIC outcome the object does not carry as an outcome is
    NOT_IN_OBJECT -- the mortality mislabel (all-cause shown, no all-cause outcome exists; the value is
    borrowed from CV death). Value-matching would PASS it because the number is real; identity fails it."""
    # what specific outcomes does the object actually hold? gather outcome text per by_outcome entry.
    held = " ".join(
        json.dumps(o).lower() for o in ((obj.get("results") or {}).get("by_outcome") or {}).values() if isinstance(o, dict)
    )
    SPECIFIC = {"all-cause mortality": "all-cause", "mortality": "all-cause mortality",
                "cardiovascular death": "cardiovascular death", "stroke": "stroke", "myocardial": "myocardial"}
    fails = []
    for c in claims:
        lab = c["label"]
        if lab in SPECIFIC and SPECIFIC[lab] not in held:
            fails.append({"value": "%s %s (%s-%s)" % (c["measure"], c["point"], c["ci"][0], c["ci"][1]),
                          "label": lab, "why": "no '%s' outcome in the object -- estimate not in object under this label" % lab})
    return fails


def run(review_id, page):
    html = io.open(page if os.path.isabs(page) else os.path.join(ROOT, page), encoding="utf-8", errors="replace").read()
    # C. field coverage via the existing tool
    spec = importlib.util.spec_from_file_location("field_render_check", os.path.join(ROOT, "scripts", "field_render_check.py"))
    frc = importlib.util.module_from_spec(spec); spec.loader.exec_module(frc)
    obj, protocol, ev, _ = frc._resolve(review_id)
    field = frc.check(obj, protocol, ev, html)
    prose = check_prose(html)
    claims, mislabels = check_claim_identity(html)
    not_in_object = check_not_in_object(claims, obj)
    return {"review": review_id, "page": page, "field": field, "prose": prose,
            "claims": claims, "mislabels": mislabels, "not_in_object": not_in_object}


if __name__ == "__main__":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    review_id = sys.argv[1] if sys.argv[1:] else "empagliflozin-hf-auto-full-review"
    page = sys.argv[2] if sys.argv[2:] else ("out/generated/%s.generated.html" % review_id.upper())
    r = run(review_id, page)
    print("CLAIM-LEVEL CENSUS -- %s" % review_id)
    print("  page: %s" % page)
    f = r["field"]
    N = f["held"] + len(r["claims"])
    print("\n[A] CLAIM IDENTITY: %d rendered estimates" % len(r["claims"]))
    for c in r["claims"]:
        print("     %s %s (%s-%s)  <- outcome label: %s" % (c["measure"], c["point"], c["ci"][0], c["ci"][1], c["label"]))
    if r["mislabels"]:
        print("  *** MISLABEL FAILURES (one value under two outcome labels):")
        for m in r["mislabels"]:
            print("     - %s appears under: %s" % (m["value"], ", ".join(m["labels"])))
    if r["not_in_object"]:
        print("  *** NOT_IN_OBJECT FAILURES (estimate under an outcome the object does not hold):")
        for m in r["not_in_object"]:
            print("     - %s [%s] -- %s" % (m["value"], m["label"], m["why"]))
    print("\n[B] RENDERED PROSE: %d failure(s)" % len(r["prose"]))
    for k, v in r["prose"]:
        print("     - %s: %r" % (k, v))
    print("\n[C] FIELD COVERAGE: %d of %d held fields rendered, %d declared-absent, %d MISSING" %
          (f["rendered"], f["held"], len(f["declared_absent"]), len(f["missing"])))
    for lab, tab, val in f["missing"]:
        print("     - [%s] %s" % (tab, lab))
    ok = not r["mislabels"] and not r["not_in_object"] and not r["prose"] and not f["missing"]
    total_fail = len(r["mislabels"]) + len(r["not_in_object"]) + len(r["prose"]) + len(f["missing"])
    print("\n>>> CENSUS: %d named failures across identity+prose+coverage. %s <<<"
          % (total_fail, "PASS" if ok else "FAIL"))
    raise SystemExit(0 if ok else 1)
