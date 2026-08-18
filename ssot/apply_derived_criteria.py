"""Write derived criteria blocks. Additive, provenance-preserving, and it refuses more than it writes.

WHAT IT WRITES, per topic that supports a derivation:
  screening.eligibility               <- the derived prose statement
  screening.eligibility_as_extracted  <- THE ORIGINAL VALUE, preserved, never discarded
  screening.eligibility_provenance    <- the per-element block with source paths

WHY THE ORIGINAL IS PRESERVED. `screening.eligibility` currently reads "not recorded on the
page this object was built from". That is a TRUE STATEMENT about the source page and it stays
true after a derivation -- the derivation does not make the page have recorded criteria, it
makes the OBJECT state them. Overwriting the original would destroy the record that the source
page had none, which is exactly the fact `criteria_predefined` needs in order to keep failing.
So it moves to `eligibility_as_extracted` and nothing is lost.

THE GATE. verdict_is_publishable() must be True, and every topic must survive both derivation
guards. A topic whose objective never names its intervention, or whose fields declare their own
absence, gets NO block and keeps failing `criteria_stated`. That is a correct outcome.
"""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import derive_criteria as D
import preconditions as P
import topic_identity as T

ROOT = os.path.dirname(os.path.abspath(__file__))

# Topic -> its DECLARED synonym key in topic_identity. Only topics that currently FAIL
# criteria_stated are candidates; a topic that already states criteria is not touched.
CANDIDATES = {
    "ablation-af-review": "catheter ablation",
    "attr-cm-review": "tafamidis OR acoramidis",
    "bempedoic-acid-review": "bempedoic acid",
    "bococizumab-lipid-review": "bococizumab",
}


def all_keys(node, prefix="", out=None):
    out = set() if out is None else out
    if isinstance(node, dict):
        for k, v in node.items():
            out.add(f"{prefix}{k}")
            all_keys(v, f"{prefix}{k}.", out)
    elif isinstance(node, list):
        for i, v in enumerate(node):
            all_keys(v, f"{prefix}[{i}].", out)
    return out


if not P.verdict_is_publishable():
    raise SystemExit("REFUSING: verdict_is_publishable() is False.")

written, refused = [], []

for topic, syn_key in sorted(CANDIDATES.items()):
    path = os.path.join(ROOT, topic, f"{topic}.json")
    with open(path, "rb") as fh:
        original_bytes = fh.read()
    obj = json.loads(original_bytes.decode("utf-8"))

    block, unsupported = D.build_block(obj, topic, T.synonyms_for(syn_key))
    if block is None:
        refused.append((topic, unsupported))
        continue

    before_keys = all_keys(obj)
    screening = obj.setdefault("screening", {})
    existing = screening.get("eligibility")
    if existing is not None:
        screening["eligibility_as_extracted"] = existing
        screening["eligibility_as_extracted_means"] = (
            "The value `screening.eligibility` held BEFORE a criteria block was derived. It "
            "describes the SOURCE PAGE and remains true: the page recorded no criteria. It is "
            "preserved because `criteria_predefined` depends on it.")
    screening["eligibility"] = D.render_prose(block)
    screening["eligibility_provenance"] = block

    after_keys = all_keys(obj)
    lost = before_keys - after_keys
    if lost:
        with open(path, "wb") as fh:
            fh.write(original_bytes)
        raise SystemExit(f"ABORTED on {topic}: would remove {sorted(lost)[:6]}. Restored.")

    tmp = path + ".part"
    with open(tmp, "w", encoding="utf-8", newline="") as fh:
        json.dump(obj, fh, indent=1, ensure_ascii=True)
        fh.write("\n")
    os.replace(tmp, path)
    written.append(topic)

print(f"DERIVED AND WRITTEN ({len(written)})")
for t in written:
    print(f"  {t}")
print()
print(f"REFUSED -- no derivation possible ({len(refused)}), and each keeps failing criteria_stated")
for t, reasons in refused:
    print(f"  {t}")
    for r in reasons:
        print(f"     - {str(r)[:150]}")
