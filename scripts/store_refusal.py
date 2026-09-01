"""THE ONE READER OF THE STORE'S WITHHOLDING FACTS.

Two questions are asked of ONE object, and both were previously answered in
different places -- gate_unpoolable_override.py read the refusal inline, and the
pools table carried hand-written withholding that no generator knew about. A
second reader is how two surfaces begin disagreeing about one artefact, which is
the defect this repository spends most of its gates on.

    store-refusal      the store recorded that it will not pool this, and why.
                       `by_outcome.primary.poolable is False`, or
                       `by_outcome.primary.pooled.withdrawn` set.
    polarity-unknown   the store records no `favours`, so a value above 1 cannot
                       be read as benefit or as harm. The trials have endpoints;
                       we did not record which direction is good. That is OUR
                       recording gap, not a property of the evidence, and the
                       reason text says so.

A page may carry both, one, or neither. Callers render; they do not re-decide.
"""
import io
import json
import os

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def _primary(store):
    return ((store.get("results") or {}).get("by_outcome") or {}).get("primary") or {}


def withholdings(store, store_path=""):
    """[{kind, reason, source}] for one store object. Empty means nothing withheld."""
    out = []
    bo = _primary(store)
    if not bo:
        return out
    pooled = bo.get("pooled") or {}
    if pooled.get("withdrawn") or bo.get("poolable") is False:
        reason = (bo.get("poolable_reason") or pooled.get("withdrawn_reason")
                  or pooled.get("withdrawn_because") or "")
        out.append({
            "kind": "store-refusal",
            "reason": ("The store refused to pool this and recorded why: %s" % reason.strip()
                       if reason.strip() else
                       "The store recorded a refusal to pool this and gave no reason text. "
                       "An unexplained refusal is still a refusal."),
            "source": store_path})
    favours = bo.get("favours", pooled.get("favours"))
    if favours in (None, "", "unknown"):
        out.append({
            "kind": "polarity-unknown",
            "reason": ("The direction this number points is not recorded anywhere we hold, "
                       "so a value above 1 cannot be read as benefit or as harm. The trials "
                       "have endpoints; we did not record which way is good. This is our "
                       "recording gap, not a property of the evidence."),
            "source": store_path})
    return out


def load(path):
    try:
        with io.open(os.path.join(REPO, path), encoding="utf-8") as fh:
            return json.load(fh)
    except Exception:
        return None


def for_page(page, page_map):
    """[{kind, reason, source}] for one served page, via PAGE_MAP."""
    path = (page_map.get("pages") or page_map).get(page)
    if not path:
        return []
    store = load(path)
    if store is None:
        return []
    return withholdings(store, path)


# --- CONTROLS. Synthetic objects, so they cannot retire when a real page is fixed.
CONTROLS = [
    ({"results": {"by_outcome": {"primary": {"poolable": False,
                                             "poolable_reason": "only one trial",
                                             "favours": "treatment"}}}},
     ["store-refusal"], "a recorded refusal is recognised, and a recorded favours is not withheld"),
    ({"results": {"by_outcome": {"primary": {"poolable": True, "favours": "treatment"}}}},
     [], "a poolable outcome with a recorded direction withholds NOTHING"),
    ({"results": {"by_outcome": {"primary": {"poolable": True}}}},
     ["polarity-unknown"], "no favours recorded -- direction is not readable"),
    ({"results": {"by_outcome": {"primary": {"pooled": {"withdrawn": True,
                                                        "withdrawn_reason": "estimand drift"}}}}},
     ["store-refusal", "polarity-unknown"], "withdrawn AND no favours -- both, not one"),
    ({"results": {"by_outcome": {}}}, [], "no primary outcome -- nothing to say either way"),
]


def run_controls(say=print):
    bad = 0
    for store, want, why in CONTROLS:
        got = [w["kind"] for w in withholdings(store, "<control>")]
        ok = got == want
        bad += (not ok)
        say("   %-5s got %-34s expected %-34s %s"
            % ("PASS" if ok else "FAIL", ",".join(got) or "(none)",
               ",".join(want) or "(none)", why))
    return bad == 0


if __name__ == "__main__":
    import sys
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    print("scripts/store_refusal.py -- CONTROLS")
    ok = run_controls()
    print("\n   %s" % ("all controls held" if ok else "A CONTROL FAILED -- do not use"))
    sys.exit(0 if ok else 1)
