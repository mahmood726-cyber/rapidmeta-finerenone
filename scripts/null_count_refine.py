"""Re-classify null_count_audit's 'degenerate 2x2' flags by whether the trial is
still poolable. A count/ratio outcome with null events is NOT broken if it
carries a published effect + CI: it pools via generic inverse-variance on the
log-effect and its SE (derived from the CI). Only flag trials that have neither
a usable 2x2 NOR a published effect+CI (genuinely unpoolable), or zero-events in
both arms with no published effect (uninformative)."""
import re, glob, io, sys, json
from collections import Counter
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

NUM = lambda v: None if v is None or str(v).strip().lower() in ("null", "", "none") else v

# pull realData trial objects loosely: key:{...} with publishedHR/hrLCI/hrUCI/tE/cE/estimandType
trial_re = re.compile(
    r'(?:tE:(?P<tE>[^,}]*))?[^{}]*?tN:(?P<tN>[^,}]*)[^{}]*?cN:(?P<cN>[^,}]*)'
)

def field(blk, name):
    m = re.search(rf'{name}:([^,}}\]]*)', blk)
    return m.group(1).strip() if m else None

buckets = Counter()
unpoolable = []
for fn in glob.glob("*REVIEW*.html"):
    s = open(fn, encoding="utf-8", errors="replace").read()
    # each realData trial entry: NCTxxxx:{ ... publishedHR ... }
    for m in re.finditer(r'(NCT\d+|LEGACY[-\w]*)":?\{(.*?)allOutcomes', s):
        blk = m.group(2)
        if "publishedHR" not in blk:
            continue
        tE, cE = field(blk, "tE"), field(blk, "cE")
        hr = field(blk, "publishedHR")
        lci, uci = field(blk, "hrLCI"), field(blk, "hrUCI")
        est = field(blk, "estimandType")
        events_null = NUM(tE) is None or NUM(cE) is None
        events_zero = (str(tE).strip() == "0" and str(cE).strip() == "0")
        if not (events_null or events_zero):
            continue
        has_effect_ci = NUM(hr) is not None and NUM(lci) is not None and NUM(uci) is not None
        if has_effect_ci:
            buckets["valid_IV (effect+CI, events absent)"] += 1
        elif NUM(hr) is not None:
            buckets["effect_no_CI (SE not derivable)"] += 1
            unpoolable.append((fn, m.group(1), est, hr, lci, uci))
        else:
            buckets["no_effect_no_2x2 (unpoolable)"] += 1
            unpoolable.append((fn, m.group(1), est, hr, lci, uci))

print("Re-classification of null/zero-event trials with a published effect:")
for k, v in buckets.most_common():
    print(f"  {k:42} {v}")
print(f"\nGENUINELY problematic (no CI -> no SE, or no effect): {len(unpoolable)}")
for row in unpoolable[:25]:
    print("  ", row)
