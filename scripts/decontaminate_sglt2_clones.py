#!/usr/bin/env python
"""Decontaminate the 29 SGLT2-HF base-template clones (Task 2, in-place).

HONEST, NON-FABRICATING. Per app it:
  C) empties the false SGLT2 PUBLISHED_META_BENCHMARKS  -> {}  (consumer returns []
     = "no benchmark configured"; verified safe)
  A) retargets user-facing/SEO SGLT2-HF text to the app's OWN topic (parsed from
     <title>): meta+OG description, JSON-LD description/keywords/mentions, PICO
     population (trial-scoped truthful phrasing), H2 section header, subtitle,
     and the "hfref quadruple therapy" display slug (+ filename slug).
  B) retargets live CT.gov/PubMed/OpenAlex SEARCH queries off the SGLT2 drug terms
     to topic keywords (stops active wrong-topic ingestion).
  - mf-indication dropdown normalised to the topic.

It NEVER fabricates intervention/comparator/outcome drug names or benchmark numbers,
and LEAVES the deep engine residue (CV-relevance scoring regexes, HFrEF/HFpEF phenotype
subgroup options, outcome-taxonomy label maps, Arabic translation *values*) untouched —
that layer is a rebuild, documented in outputs/_sglt2_clone_rebuild_list.md.
realData (the correct trial evidence) is never touched.

Default = DRY RUN (writes nothing). Pass --apply to write. Idempotent.
"""
import io, re, sys, json, argparse
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
ROOT = Path(__file__).resolve().parent.parent
MAP = ROOT / "outputs" / "_sglt2_clone_rebuild_list.md"

STOP = {"the","in","for","of","and","or","vs","a","an","with","to","at","on",
        "older","adults","review","nma","protocol"}

def app_files():
    out = []
    for line in MAP.read_text(encoding="utf-8").splitlines():
        m = re.match(r"\|\s*([A-Z0-9_]+_REVIEW\.html)\s*\|", line)
        if m:
            out.append(m.group(1))
    return out

def parse_title(s):
    mt = re.search(r"<title>(.*?)</title>", s, re.S)
    t = re.sub(r"\s+", " ", mt.group(1)).strip() if mt else ""
    specialty, rest = "", t
    if "|" in t:
        left, rest = t.split("|", 1)
        specialty = re.sub(r"^RapidMeta\s*", "", left).strip()
    rest = rest.strip()
    topic = re.split(r"\s*(?:&mdash;|—|\bv0\.)", rest)[0]
    topic = re.sub(r"\bNMA\b.*$", "", topic).strip().rstrip("—-").strip()
    return specialty, topic

def topic_slug(topic):
    return re.sub(r"_+", "_", re.sub(r"[^a-z0-9]+", "_", topic.lower())).strip("_")

def query_terms(topic):
    words = [w for w in re.findall(r"[A-Za-z0-9-]+", topic) if w.lower() not in STOP and len(w) > 1]
    return words or [topic]

def balanced_empty(s, varname):
    """Replace `varname = {...}` (balanced braces, optional ws) with `varname={}`.
    Idempotent."""
    m = re.search(re.escape(varname) + r"\s*=\s*\{", s)
    if not m:
        return s, 0
    j = m.end() - 1               # index of the opening '{'
    # already empty?  (allow whitespace between the braces)
    if re.match(r"\{\s*\}", s[j:]):
        return s, 0
    decl_start = m.start()
    depth, k = 0, j
    while k < len(s):
        c = s[k]
        if c == "{": depth += 1
        elif c == "}":
            depth -= 1
            if depth == 0:
                break
        k += 1
    return s[:decl_start] + varname + "={}" + s[k+1:], 1

def build_repls(s, specialty, topic):
    """Return list of (old, new, label) literal replacements valid for THIS app."""
    slug = topic_slug(topic)
    desc = f"{topic}: living network meta-analysis of the included randomized trials."
    pop  = f"Participants of the included randomized trials for {topic}."
    qspace = " ".join(query_terms(topic))
    qplus  = "+".join(query_terms(topic))
    R = []

    # --- A: hfref-quadruple-therapy display slug (Tier-1). Global literal swaps. ---
    R.append(("hfref quadruple therapy", topic, "slug:display"))
    R.append(("hfref_quadruple_therapy", slug, "slug:filename"))
    R.append(("HFrEF Drug Comparison NMA", f"{topic} NMA", "h2:section-header"))

    # --- A: structured SEO/JSON-LD/PICO (anchored full-attribute strings) ---
    # meta + OG/twitter + jsonld description: the SGLT2 desc string (verbatim)
    SGLT2_DESC = ("Empagliflozin, Dapagliflozin, or Sacubitril/Valsartan; Adults with "
                  "chronic HFrEF (LVEF &lt;=40%, NYHA II-IV); CV death or HF hospitalization composite")
    SGLT2_DESC_LD = SGLT2_DESC  # same text inside JSON-LD
    R.append((f'content="{SGLT2_DESC}"', f'content="{desc}"', "meta:description"))
    R.append((f'"description":"{SGLT2_DESC_LD}"', f'"description":"{desc}"', "jsonld:description"))
    R.append(('"keywords":"meta-analysis, living review, RapidMeta, '
              'Empagliflozin, Dapagliflozin, or Sacubitril/Valsartan"',
              f'"keywords":"meta-analysis, living review, RapidMeta, {topic}"',
              "jsonld:keywords"))
    R.append(('"mentions":{"@type":"Drug","name":"Empagliflozin, Dapagliflozin, or Sacubitril/Valsartan"}',
              f'"mentions":{{"@type":"CreativeWork","name":"{topic}"}}',
              "jsonld:mentions"))
    R.append(('value="Adults with heart failure across EF spectrum"',
              f'value="{pop}"', "pico:population"))
    R.append(("SGLT2i in heart failure (+ SCORED T2D-CKD) · CV death or HHF "
              "· k=6 (star) + k=4 Stratum A sensitivity",
              f"{specialty} · living network meta-analysis of included randomized trials",
              "subtitle"))

    # --- B: live SEARCH queries off SGLT2 drug terms -> topic keywords ---
    R += [
        ("empagliflozin+OR+dapagliflozin+OR+sacubitril+AND+heart+failure+reduced", qplus, "q:ctgov-intr"),
        ("(dapagliflozin OR empagliflozin OR sotagliflozin) AND heart failure", qspace, "q:ctgov2"),
        ("dapagliflozin+OR+empagliflozin&query.cond=heart+failure", f"{qplus}&query.cond=", "q:ctgov-tier2"),
        ('(dapagliflozin OR empagliflozin OR "sglt2") AND "heart failure"', qspace, "q:ctgov-enc"),
        ("(dapagliflozin OR empagliflozin OR sglt2) AND heart failure", qspace, "q:ctgov-enc2"),
    ]

    # --- Tier-2 prose: drop the false SGLT2 (Vaduganathan) concordance citation ---
    R.append(("Concordance with published safety meta-analyses (Vaduganathan et al., "
              "Lancet 2022) should be verified for clinical interpretation.",
              "Concordance with published topic-specific meta-analyses should be "
              "verified for clinical interpretation.",
              "prose:vaduganathan-citation"))

    # --- mf-indication dropdown -> topic + Other (fixes the value/label bug) ---
    md = re.search(r'(<select id="mf-indication">.*?</select>)', s, re.S)
    if md:
        new_sel = (f'<select id="mf-indication"><option value="topic">{topic}</option>'
                   f'<option value="Other">Other</option></select>')
        if md.group(1) != new_sel:
            R.append((md.group(1), new_sel, "mf-indication"))

    return R

def process(fn, apply):
    p = ROOT / fn
    s0 = p.read_text(encoding="utf-8")
    specialty, topic = parse_title(s0)
    if not topic:
        return {"file": fn, "error": "no-topic"}
    s = s0
    changes = []
    # C: empty the false benchmark (balanced brace)
    s, n = balanced_empty(s, "PUBLISHED_META_BENCHMARKS")
    if n: changes.append(("PUBLISHED_META_BENCHMARKS->{}", 1))
    # A/B literal replacements
    for old, new, label in build_repls(s0, specialty, topic):
        c = s.count(old)
        if c:
            s = s.replace(old, new)
            changes.append((label, c))
    changed = (s != s0)
    if changed and apply:
        p.write_text(s, encoding="utf-8")
    return {"file": fn, "specialty": specialty, "topic": topic,
            "changed": changed, "changes": changes}

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    ap.add_argument("--only", nargs="*", help="limit to these filenames")
    args = ap.parse_args()
    files = app_files()
    if args.only:
        files = [f for f in files if f in args.only]
    mode = "APPLY" if args.apply else "DRY-RUN"
    print(f"=== decontaminate_sglt2_clones [{mode}] over {len(files)} apps ===\n")
    total = 0
    for fn in files:
        r = process(fn, args.apply)
        if r.get("error"):
            print(f"!! {fn}: {r['error']}"); continue
        tag = "CHANGED" if r["changed"] else "no-op"
        print(f"[{tag}] {fn}  topic={r['topic']!r}")
        for label, c in r["changes"]:
            print(f"        {label} x{c}")
        total += 1 if r["changed"] else 0
    print(f"\n{total}/{len(files)} apps {'would change' if not args.apply else 'changed'}")

if __name__ == "__main__":
    main()
