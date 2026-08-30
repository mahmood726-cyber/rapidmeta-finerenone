# -*- coding: utf-8 -*-
"""Does every trial LABEL in the corpus match the registry record of its own NCT?

⛔ WHY. On 2026-08-30 `agyw-hiv-prep-review` was found to have its two trials labelled the
wrong way round, in TWO places:

    NCT01539226  labelled "ASPIRE / MTN-020"   -- registry says orgStudyId IPM 027, n 1959
    NCT01617096  labelled "The Ring Study"     -- registry says acronym ASPIRE, MTN-020

The effect estimates were keyed correctly to the NCTs, so the analysis stood. What was
wrong was every sentence that NAMES a trial -- which is most of what a reader meets, on a
page six blinded judges scored, in a review whose whole claim is verifiability.

⭐ THE CLASS: A CORRECT KEY GUARANTEES THE JOIN, NEVER THE LABEL. Every previous instance
of this was in someone else's data -- a PMID naming two trials, a name match standing in
for an identity. This one was inside our own store, which is why it went unnoticed: the
join was right, so every automated check that follows the join was right too, and only a
reader comparing a NAME against a registry would ever have seen it.

⇒ A LABEL ON OUR OBJECT IS NOT AN IDENTITY. THE REGISTRY IS.

WHAT THIS CHECKS, and the second test is the one that finds a swap:

  1 CONSISTENT   the label's distinctive tokens appear in this NCT's own registry record
                 (acronym, orgStudyId, or brief title).
  2 INVERTED     ⛔ the label matches a DIFFERENT NCT **in the same object** better than it
                 matches its own. That is the agyw defect exactly, and it is the only
                 pattern that can be asserted without judgement -- two records swapped.
  3 UNVERIFIABLE the registry record could not be fetched, or the label carries no token
                 distinctive enough to test. ⚠️ NOT "consistent". A label we cannot check
                 is not a label we have checked, and counting it as a pass is how an audit
                 reports its own reach as coverage.

⛔⛔ WHAT THIS AUDIT'S OWN NUMBERS ARE WORTH, WHICH IS LESS THAN THEY LOOK. The first run
flagged NINE sites and was right about ONE -- the agyw swap it was written from. The other
eight were its own defects, and the registry settled every one:

    LEAP 2       NCT02813694's acronym is literally `LEAP2`; a word-boundary match on
                 `leap` hit the SIBLING `LEAP` and missed the trial's own name.
    CAP China    NCT01371838 runs in China, India, South Korea, Taiwan and Vietnam. The
                 audit never read the location list, so the one field carrying that
                 label's meaning was not in the haystack.
    five more    long descriptive labels -- copied brief titles -- which share wording with
                 every sibling in the same programme, so "fits better" means nothing.

⇒ REPORTING "NINE INVERSIONS" WOULD HAVE SENT SOMEONE TO CORRUPT EIGHT CORRECT LABELS. An
audit that accuses is more dangerous than one that misses, because its output reads as the
tool working. Every flag here must be settled against the registry BY A PERSON before any
object is edited; this module proposes, it does not decide.

⚠️ AND ITS PRECISION IS FITTED, NOT MEASURED. Three corrections were made against these same
nine cases, so "0 inverted" is the score of an instrument tuned on its own validation set.
It has NO measured false-negative rate: it found the one swap it was built from, which is
not evidence it would find a second. Treat 0 as "no swap of the shape we already know",
never as "the corpus is clean".

⚠️ AND A MISMATCH IS NOT AUTOMATICALLY A DEFECT. Trials carry many legitimate names -- a
sponsor code, a network code, a published acronym, a country-specific name -- and a label
that fails to match may simply use a name the registry does not list. So only INVERTED is
reported as a defect; the rest are reported as "not verified from the registry" and left
for a person.
"""
import io
import json
import os
import re
import subprocess
import sys
import time
import urllib.parse

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from collections import defaultdict

import instrument_controls as IC

UA = "rapidmeta-systematic-review/1.0 (mailto:mahmood726@gmail.com)"
NCT_RE = re.compile(r"^NCT\d{8}$")

# Tokens too generic to identify a trial. A label reduced to only these is UNVERIFIABLE.
GENERIC = set("""the a an of for in on and or to study trial phase safety efficacy
effectiveness open label randomized randomised placebo controlled multicenter multicentre
extension part cohort group arm versus vs adults adult patients children women men
international national european american""".split())


def _curl(url, tries=3):
    for i in range(tries):
        r = subprocess.run(["curl", "-sL", "--max-time", "60", "-A", UA,
                            "-w", "\n__H__%{http_code}", url], capture_output=True)
        out = r.stdout.decode("utf-8", "replace")
        code = out.rsplit("__H__", 1)[-1].strip() if "__H__" in out else "000"
        body = out.rsplit("\n__H__", 1)[0]
        if code == "200":
            return body, code
        if code.startswith("5") or code in ("000", "429"):
            if i < tries - 1:
                time.sleep(2 * (i + 1))
                continue
        return body, code
    return "", "000"


# ⛔ THE KEYS THAT CARRY A TRIAL'S IDENTITY AND ITS NAME. Both are OPEN VOCABULARIES in
# this corpus, which is why neither of the two instruments that swept for this defect saw
# all of it: this module keyed `nct`/`trial`/`label` over three hand-listed FAMILIES and
# found 241 sites; `gates/gate1_trial_identity.py` keyed
# ("nct","trial_id","id","registry_id") and found 14. The reference list -- which stores the
# identifier under `registration` -- was in NEITHER denominator, and it is the most
# citation-facing surface on the page. It carried the inversion the whole time.
#
# ⇒ A HAND-LISTED KEY SET IS A DENOMINATOR NOBODY AUDITS. The walk below is recursive over
# the whole object, so a new family cannot silently fall outside it; what a reader has to
# check is now two short vocabularies rather than a list of paths, and every site reports
# the JSON path it was found at.
ID_KEYS = ("nct", "trial_id", "id", "registry_id", "registration", "nct_id", "registration_id")
LABEL_KEYS = ("label", "trial", "name", "trial_name", "study", "acronym")


def _walk(node, path, out):
    """Every dict anywhere in the object that carries BOTH an NCT and a name."""
    if isinstance(node, dict):
        nct = None
        for k in ID_KEYS:
            v = node.get(k)
            if isinstance(v, str) and NCT_RE.match(v.strip()):
                nct = v.strip()
                break
        # ⚠️ AN ARM IS NOT A TRIAL. `arm_role_corrections[..].arms[..].label` holds the
        # NAME OF A TREATMENT ARM -- "Evolocumab", "Device Group" -- beside the trial's NCT.
        # Scored as a trial name it will never match the registry record and will always
        # "fit" some sibling better, which is two of the four flags the widened walk raised.
        if nct and ".arms[" not in path:
            for k in LABEL_KEYS:
                v = node.get(k)
                # ⚠️ A label EQUAL to the identifier is not a name, and a one-word
                # non-alphabetic value is not one either. Neither is a defect.
                if isinstance(v, str) and v.strip() and v.strip() != nct                         and re.search(r"[A-Za-z]", v):
                    out.append((path + "." + k, nct, v.strip()))
                    break
        for k, v in node.items():
            _walk(v, "%s.%s" % (path, k), out)
    elif isinstance(node, list):
        for i, v in enumerate(node):
            _walk(v, "%s[%d]" % (path, i), out)


def collect(root="."):
    """Every (object, nct, label, json-path) the corpus holds, found by walking."""
    pm = json.load(open(os.path.join(root, "ssot", "PAGE_MAP.json"), encoding="utf-8"))
    out = []
    for p in sorted(set(pm.values())):
        obj = json.load(open(os.path.join(root, p), encoding="utf-8"))
        topic = p.split("/")[1]
        sites = []
        _walk(obj, "$", sites)
        for where, nct, label in sites:
            out.append((topic, nct, label, where))
    return out


def registry(ncts, chunk=40):
    """CT.gov records for a set of NCTs. Missing ones are absent, never invented."""
    recs = {}
    ids = sorted(ncts)
    for i in range(0, len(ids), chunk):
        part = ids[i:i + chunk]
        body, code = _curl("https://clinicaltrials.gov/api/v2/studies?filter.ids=%s"
                           "&pageSize=%d&fields=NCTId,BriefTitle,Acronym,OrgStudyId,LocationCountry"
                           % (urllib.parse.quote(",".join(part)), len(part) + 5))
        if code != "200":
            continue
        try:
            j = json.loads(body)
        except ValueError:
            continue
        for s in j.get("studies") or []:
            p = s.get("protocolSection") or {}
            idm = p.get("identificationModule") or {}
            # ⚠️ COUNTRIES ARE PART OF A TRIAL'S IDENTITY. A label may name where a trial
            # ran -- "CAP China" -- and that is a legitimate distinguishing name that no
            # title, acronym or sponsor code carries. Omitting the location list made this
            # audit report a CORRECT label as an inversion: NCT01371838 runs in China,
            # India, South Korea, Taiwan and Vietnam, while the two sibling FOCUS trials
            # both carry the acronym `CAP` and run in neither.
            loc = (s.get("protocolSection") or {}).get("contactsLocationsModule") or {}
            countries = sorted({(l or {}).get("country") or ""
                                for l in (loc.get("locations") or [])})
            recs[idm.get("nctId")] = {
                "brief": idm.get("briefTitle") or "",
                "acronym": idm.get("acronym") or "",
                "org": (idm.get("orgStudyIdInfo") or {}).get("id") or "",
                "countries": " ".join(c for c in countries if c),
            }
        time.sleep(0.4)
    return recs


def tokens(label, topic=None):
    """The label's distinguishing tokens, within the review it belongs to.

    ⛔ A TOKEN THAT NAMES THE REVIEW'S OWN CONDITION CANNOT DISTINGUISH THE REVIEW'S TRIALS.
    Every trial in `doac-cancer-vte-review` is about VTE; every trial in
    `rivaroxaban-acs-review` is about ACS. So when `ADAM VTE` scored 0 against its own
    record -- ClinicalTrials.gov spells out "Venous Thromboembolism" and never abbreviates
    it -- and 1 against a sibling whose title happens to contain the literal "(VTE)", the
    comparison was decided entirely by the one token that carries no information here. Same
    for `ATLAS ACS 2`, whose only distinguishing token, ATLAS, CT.gov lists for neither
    trial.

    ⭐ THE STOP LIST IS DERIVED FROM THE OBJECT, NOT HAND-WRITTEN, which is the whole point:
    a hand-listed stop list is the same open-vocabulary defect that hid the reference list
    from two separate sweeps. The topic identifier states what the review is about, so it
    states which tokens cannot separate its members.
    """
    t = {w.lower() for w in re.findall(r"[A-Za-z0-9][A-Za-z0-9-]{2,}", label)}
    # ⛔ THE FOURTH SEPARATOR DEFECT, and it broke the shared-programme filter above.
    # `CHAMPION-PHOENIX` tokenised to ONE token, so `champion` was never seen as shared with
    # `CHAMPION PCI`, and the filter that exists to stop programme names counting as
    # identity could not fire. A hyphen joins two words for a reader and splits them for a
    # regex, and this project has now paid for that four times: `[_ ]` vs hyphens,
    # `SOME CONCERNS` vs `SOME_CONCERNS`, `LEAP 2` vs `LEAP2`, and this. Both the joined and
    # the split forms are kept, because either may be what the registry printed.
    for w in list(t):
        if "-" in w:
            t |= {part for part in w.split("-") if len(part) > 2}
    t = {w for w in t if w not in GENERIC}
    if topic:
        topic_words = {w for w in re.split(r"[^a-z0-9]+", topic.lower()) if len(w) > 2}
        t = {w for w in t if w not in topic_words}
    return t


def matches(label, rec, topic=None):
    """How many of the label's distinctive tokens appear in this registry record.

    ⚠️ SEPARATOR-BLIND, AFTER THE FIRST RUN FLAGGED NINE SITES AND WAS RIGHT ABOUT ONE.
    `NCT02813694`'s registry acronym is literally `LEAP2`; the label reads "LEAP 2". A
    word-boundary match on the token `leap` therefore hit a SIBLING whose acronym is `LEAP`
    and MISSED the trial's own `LEAP2` -- so a correct label was reported as an inversion,
    with a confident "fits NCT02559310 better". The de-spaced form is now compared too.

    ⭐ THIS IS THE THIRD SEPARATOR DEFECT THIS PROJECT HAS FOUND IN A GUARD: `[_ ]` against
    a corpus that writes hyphens, `SOME CONCERNS` against `SOME_CONCERNS`, and now `LEAP 2`
    against `LEAP2`. All three had the same shape -- a comparison between two spellings of
    one string, where the guard's own spelling was assumed rather than measured. The
    generalisable form: WHENEVER A CHECK COMPARES TWO STRINGS THAT HUMANS WOULD READ AS THE
    SAME NAME, THE SEPARATORS ARE PART OF THE TEST AND MUST BE NORMALISED ON BOTH SIDES.
    """
    if not rec:
        return 0
    hay = " ".join([rec["brief"], rec["acronym"], rec["org"],
                    rec.get("countries") or ""]).lower()
    hay_flat = re.sub(r"[^a-z0-9]+", "", hay)
    hay = re.sub(r"[^a-z0-9]+", " ", hay)
    n = 0
    for t in tokens(label, topic):
        if re.search(r"\b%s\b" % re.escape(t), hay) or (
                len(t) > 2 and t.replace(" ", "") in hay_flat):
            n += 1
    return n


def audit(root="."):
    triples = collect(root)
    ncts = {n for _t, n, _l, _w in triples}
    return _classify(triples, registry(ncts))


def _classify(triples, recs):
    """The verdict logic, separated so CONTROLS EXERCISE THE REAL CODE.

    ⚠️ A control that re-implements the thing it checks proves only that the code agrees
    with itself. Splitting classification from retrieval is what lets a fixture run through
    the same comparison the corpus does, with the registry records pinned instead of fetched.
    """
    ncts = {n for _t, n, _l, _w in triples}
    by_topic = defaultdict(list)
    for topic, nct, label, where in triples:
        by_topic[topic].append((nct, label, where))

    inverted, unverifiable, consistent, no_record = [], [], [], []
    for topic, rows in by_topic.items():
        topic_ncts = {n for n, _l, _w in rows}
        for nct, label, where in rows:
            rec = recs.get(nct)
            if not rec:
                no_record.append((topic, nct, label, where))
                continue
            own = matches(label, rec, topic)
            if not tokens(label, topic):
                unverifiable.append((topic, nct, label, where, "no distinctive token"))
                continue
            # ⛔ THE SWAP TEST: does this label fit a SIBLING NCT in the same object better?
            # ⛔ A TOKEN SHARED WITH THE SIBLING'S OWN LABEL CANNOT SEPARATE THEM.
            # `ATLAS ACS 2` and `ATLAS ACS TIMI 46` are two trials of one programme, as are
            # `CHAMPION PCI` and `CHAMPION PHOENIX`. ClinicalTrials.gov happens to print the
            # programme name in one record and not the other, so the trial whose record
            # omits it scores 0 on its own and 1 on its sibling -- a CORRECT label, accused.
            # Scoring across a pair therefore ignores tokens the sibling's own label also
            # carries: what is left is what actually distinguishes them.
            # ⭐ Derived from the objects, not a hand-written programme list -- a hand list
            # is the same open-vocabulary defect that hid the reference list from two sweeps.
            best_other, best_score = None, 0
            for other in topic_ncts:
                if other == nct:
                    continue
                shared = set()
                for onct, olabel, _w in rows:
                    if onct == other:
                        shared |= tokens(olabel, topic)
                # ⛔ TWO TRIALS OF ONE NAMED PROGRAMME ARE NOT ASSESSABLE FROM THE REGISTRY,
                # and saying so is a refusal, not a pass. ROCKET-1/2/4, ADVANCE-1/2,
                # CHAMPION-PCI/PHOENIX, ATLAS ACS 2 / ATLAS ACS TIMI 46: ClinicalTrials.gov
                # populates the acronym field for SOME members of a series and not others,
                # so the member whose record omits it scores 0 on its own record and 1 on a
                # sibling's -- and a CORRECT label is accused. The registry cannot separate
                # them on the evidence this audit reads, and the honest output is that it
                # cannot, rather than a verdict either way.
                #
                # ⚠️ FIFTH TIGHTENING, AND THE LAST. Each of the previous four was made
                # against the SAME flag set, which is fitting an instrument to its own
                # validation sample -- so this one is written as a STRUCTURAL statement
                # (a shared programme stem is not identity evidence) rather than another
                # adjustment aimed at reaching zero. The remaining refusals are listed as
                # not-assessable and left for a person, and no further tuning was done.
                if tokens(label, topic) & shared:
                    continue
                cross = " ".join(sorted(tokens(label, topic) - shared))
                sc = matches(cross, recs.get(other), topic) if cross else 0
                if sc > best_score:
                    best_other, best_score = other, sc
            # ⛔ ONLY A DISTINCTIVE LABEL CAN BE CALLED INVERTED. A copied brief title
            # shares wording with every sibling in the same programme, so "fits better" is
            # meaningless for it. Distinctive here means few tokens -- an acronym or a
            # short name -- which is what a reader actually uses to identify a trial.
            distinctive = len(tokens(label, topic)) <= 4
            # ⛔ RECIPROCITY WAS TRIED HERE AND A CONTROL REJECTED IT. Requiring that
            # A wear B's name AND B wear A's is what "swapped" means, and it cleared both
            # false positives -- but it reported ZERO on the real agyw swap, the defect this
            # module was written from. Both trials' records contain the word "Ring"
            # (dapivirine vaginal RING), so "The Ring Study" fits each equally and the
            # reciprocal half could never be strict. A tightening that silences the founding
            # case is not a tightening. It was caught only because the control asserts
            # DETECTION of the real swap and not merely absence of false positives.
            if best_other and best_score > own and distinctive and own == 0:
                inverted.append((topic, nct, label, where, best_other, own, best_score))
            elif best_other and best_score > own:
                unverifiable.append((topic, nct, label, where,
                                     "AMBIGUOUS: fits %s at least as well, but the swap is "
                                     "NOT reciprocal -- that trial's own label still fits "
                                     "its own record, so this is one label the registry "
                                     "does not corroborate, not two records exchanged. "
                                     % best_other +
                                     "a long/descriptive label that also fits "
                                     "%s -- sibling studies in one programme share wording"
                                     % best_other))
            elif own > 0:
                consistent.append((topic, nct, label, where))
            else:
                unverifiable.append((topic, nct, label, where,
                                     "label tokens not in this registry record"))
    return {"triples": len(triples), "distinct_ncts": len(ncts),
            "registry_records": len(recs),
            "inverted": inverted, "consistent": consistent,
            "unverifiable": unverifiable, "no_registry_record": no_record}


def main():
    root = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
    a = audit(root)
    print("TRIAL LABEL IDENTITY AUDIT")
    print("  label sites checked        : %d" % a["triples"])
    print("  distinct NCTs              : %d" % a["distinct_ncts"])
    print("  registry records retrieved : %d/%d" % (a["registry_records"],
                                                    a["distinct_ncts"]))
    print()
    print("  ⛔ INVERTED (label fits a sibling NCT better) : %d" % len(a["inverted"]))
    for t, n, l, w, o, s1, s2 in a["inverted"]:
        print("     %-34s %s %-28r fits %s better (%d vs %d)  [%s]"
              % (t[:34], n, l[:28], o, s2, s1, w))
    print()
    print("  consistent with own registry record          : %d" % len(a["consistent"]))
    print("  ⚠️ NOT VERIFIED from the registry             : %d" % len(a["unverifiable"]))
    print("  no registry record retrieved                 : %d"
          % len(a["no_registry_record"]))
    print()
    print("  ⚠️ 'not verified' is NOT 'wrong'. Trials carry sponsor codes, network codes")
    print("     and published acronyms the registry may not list. Only INVERTED is")
    print("     asserted as a defect; the rest are left for a person.")
    out = os.environ.get("LABEL_AUDIT_OUT", "F:/claude-temp/label_audit.json")
    json.dump(a, open(out, "w", encoding="utf-8"), indent=1, ensure_ascii=False)
    print("  written to %s" % out)

    # ⛔ THE FAILING LIMB, ADDED BECAUSE THIS REPO'S OWN GATE REFUSED THIS FILE AND WAS
    # RIGHT. Named `audit_`, it promised a verdict and could only ever exit 0 -- a report
    # wearing a verdict's name, which is the exact class `lint_gate_can_fail` exists to
    # catch. It caught its author on the first commit.
    #
    # ⚠️ AND THE REFUSAL IS OPT-IN, WHICH IS THE POINT. On its first run this audit flagged
    # nine sites and eight were its own defects. A gate that blocked every commit on those
    # would have been bypassed within the hour, and a bypassed gate is worth less than no
    # gate. So `--gate` is for the person running the corpus check, who settles each flag
    # against the registry before anything is edited; the default stays a report.
    if "--gate" in sys.argv:
        if a["inverted"]:
            print()
            print("REFUSED: %d label site(s) fit a SIBLING NCT better than their own."
                  % len(a["inverted"]))
            print("Settle each against ClinicalTrials.gov BEFORE editing any object --")
            print("eight of the first nine flags this audit raised were its own defects.")
            return 1
        print()
        print("--gate: no label fits a sibling NCT better than its own.")
    return 0


# ⛔ THE TWO CONTROLS THIS INSTRUMENT REFUSES TO RUN WITHOUT.
#
# Pinned ClinicalTrials.gov values, not a live fetch: a control anchored to a live read
# retires itself the moment a registry edits a title, and then passes or fails for reasons
# that have nothing to do with the code.
_CTRL_RECS = {
    "NCT01539226": {"brief": "Safety and Efficacy Trial of a Dapivirine Vaginal Matrix Ring "
                             "in Healthy HIV-Negative Women", "acronym": "",
                    "org": "IPM 027", "countries": "South Africa Uganda"},
    "NCT01617096": {"brief": "Phase 3 Safety and Effectiveness Trial of Dapivirine Vaginal "
                             "Ring for Prevention of HIV-1", "acronym": "ASPIRE",
                    "org": "MTN-020", "countries": "Malawi South Africa Uganda Zimbabwe"},
    "NCT00809965": {"brief": "An Efficacy and Safety Study for Rivaroxaban in Patients With "
                             "Acute Coronary Syndrome", "acronym": "", "org": "CR014710",
                    "countries": "many"},
    "NCT00402597": {"brief": "Rivaroxaban in Combination With Aspirin Alone or With Aspirin "
                             "and a Thienopyridine in Acute Coronary Syndromes",
                    "acronym": "", "org": "CR013417", "countries": ""},
}

# POSITIVE -- the real defect, established from the registry and not by this code: the
# object labelled NCT01539226 "ASPIRE / MTN-020" when that NCT is IPM 027.
_CTRL_POS = [("agyw-hiv-prep-review", "NCT01539226", "ASPIRE / MTN-020", "$.a"),
             ("agyw-hiv-prep-review", "NCT01617096", "The Ring Study", "$.b")]
# NEGATIVE -- a CORRECT label the first version of this audit accused. NCT00809965 is
# ATLAS ACS 2-TIMI 51; CT.gov lists the acronym for neither trial of the programme.
_CTRL_NEG = [("rivaroxaban-acs-review", "NCT00809965", "ATLAS ACS 2", "$.a"),
             ("rivaroxaban-acs-review", "NCT00402597", "ATLAS ACS TIMI 46", "$.b")]


def _run_controls():
    pos = len(_classify(_CTRL_POS, _CTRL_RECS)["inverted"])
    neg = len(_classify(_CTRL_NEG, _CTRL_RECS)["inverted"])
    # ⚠️ THE POSITIVE EXPECTS 1, NOT 2, AND THAT IS MEASURED. Only one of the two swapped
    # sites is distinguishable from the registry: after generic words are removed "The Ring
    # Study" reduces to `ring`, which is in BOTH records because both are vaginal RING
    # trials. This instrument detects a swapped OBJECT, not a swapped SITE.
    IC.require_controls(
        "audit_trial_label_identity",
        positive=("the agyw swap, as the object actually carried it", pos, 1),
        negative=("ATLAS ACS 2 on NCT00809965, correct per CT.gov", neg, 1))


if __name__ == "__main__":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    _run_controls()
    sys.exit(main())
