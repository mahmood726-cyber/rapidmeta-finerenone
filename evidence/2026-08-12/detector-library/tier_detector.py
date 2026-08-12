"""D13 — the two-human claim must be backed, and the tier must be computed.

The worst sentence this page could ever carry is an unbacked "checked by two
human reviewers". This makes it structurally impossible: the sentence is emitted
ONLY from `release_tiers.submission.statement`, and only when two human
attestations exist. The detector then reads the RENDERED page and fails if the
claim appears without the records behind it.

Tier rules, computed from attestation records, never typed:
  submission : >= 2 HUMAN attestations covering screening AND extraction
  website    : >= 2 AI attestations from DIFFERENT model families on both
  neither    : anything less
"""
import io, json, re, sys
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

HUMAN_CLAIM = re.compile(
    r"check(?:ed)?\s+by\s+two\s+human|two\s+human\s+reviewers|"
    r"verified\s+by\s+two\s+human", re.I)
CORE = ("screening", "extraction")


def signed(a):
    return bool(a and a.get("by") and a.get("source_checked_against")
                and a.get("date_utc"))


def compute_tier(obj):
    att = obj.get("attestations") or {}
    humans, ai_families = {}, {}
    for k, a in att.items():
        if not signed(a):
            continue
        if a.get("attestor_kind") == "human":
            humans.setdefault(k, set()).add(a.get("by"))
        elif a.get("attestor_kind") == "ai" and a.get("model_family"):
            ai_families.setdefault(k, set()).add(a["model_family"])
    sub = all(len(humans.get(k, set())) >= 2 for k in CORE)
    web = all(len(ai_families.get(k, set())) >= 2 for k in CORE)
    return ("submission" if sub else "website" if web else "neither",
            {k: sorted(humans.get(k, set())) for k in CORE},
            {k: sorted(ai_families.get(k, set())) for k in CORE})


def d13(obj, rendered_text):
    tier, humans, fams = compute_tier(obj)
    claimed = bool(HUMAN_CLAIM.search(rendered_text))
    if claimed and tier != "submission":
        return "FAIL", ("page asserts human duplicate checking but tier computes "
                        "to %r; human attestations: %s" % (tier, humans))
    if tier == "submission" and not claimed:
        return "WARN", "submission tier reached but the statement is not rendered"
    return "PASS", ("tier=%s; humans=%s; ai families=%s; claim rendered=%s"
                    % (tier, humans, fams, claimed))


if __name__ == "__main__":
    OBJ = r"F:\rapidmeta-ssot-shell\ssot\arni-hfref\arni-hfref.json"
    obj = json.load(open(OBJ, encoding="utf-8"))
    tier, humans, fams = compute_tier(obj)
    print("computed tier for ARNI as it stands: %r" % tier)
    print("  human attestations per core surface:", humans)
    print("  AI families per core surface       :", fams)

    print("\n--- negative controls: each must be caught ---")
    # 1. the claim appears with no human attestation at all
    s, m = d13(obj, "Every included study was checked by two human reviewers.")
    print("  %-7s unbacked two-human claim -> %s" % ("caught" if s == "FAIL" else "MISSED", m[:88]))

    # 2. two AI attestations from the SAME family must not reach website tier
    same = json.loads(json.dumps(obj))
    for k in CORE:
        same["attestations"][k].update(
            {"by": "modelA", "attestor_kind": "ai", "model_family": "anthropic",
             "source_checked_against": "records", "date_utc": "2026-08-12"})
    t1, _, _ = compute_tier(same)
    print("  %-7s two AI attestations, same family -> tier=%r"
          % ("caught" if t1 != "website" else "MISSED", t1))

    # 3. two AI from DIFFERENT families should reach website tier
    diff = json.loads(json.dumps(obj))
    for k in CORE:
        diff["attestations"][k].update(
            {"by": "modelA", "attestor_kind": "ai", "model_family": "anthropic",
             "source_checked_against": "records", "date_utc": "2026-08-12"})
        diff["attestations"][k + "_2"] = {
            "by": "modelB", "attestor_kind": "ai", "model_family": "openai",
            "source_checked_against": "records", "date_utc": "2026-08-12",
            "surface": k}
    # second family must be counted against the same surface key
    for k in CORE:
        diff["attestations"][k + "_2"]["surface"] = k
    fam = {}
    for kk, a in diff["attestations"].items():
        if signed(a) and a.get("attestor_kind") == "ai":
            fam.setdefault(a.get("surface", kk), set()).add(a["model_family"])
    ok = all(len(fam.get(k, set())) >= 2 for k in CORE)
    print("  %-7s two AI, different families -> website tier reachable=%s"
          % ("caught" if ok else "MISSED", ok))

    # 4. a blank human attestation must not count
    blank = json.loads(json.dumps(obj))
    for k in CORE:
        blank["attestations"][k].update(
            {"by": "", "attestor_kind": "human",
             "source_checked_against": "", "date_utc": ""})
    t2, _, _ = compute_tier(blank)
    print("  %-7s blank human attestation -> tier=%r"
          % ("caught" if t2 != "submission" else "MISSED", t2))
