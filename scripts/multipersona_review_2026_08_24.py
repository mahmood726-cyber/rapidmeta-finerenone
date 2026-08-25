"""Multi-persona blind review of a delivered page, against a published comparator.

MAHMOOD, ON A LIVE PAGE: "this paper is now not that bad but needs mutlipersoan reviews to
be better." First positive verdict of the day, and a specific request. This builds it.

FIVE DISTINCT ROLES, NOT ONE QUESTION ASKED FIVE TIMES. A panel of five reviewers given the
same brief produces five correlated answers and reads like corroboration. These five want
different things and will disagree:

    student        can a medical student who does not know this field turn it into a good
                   paper WITHOUT BEING MISLED? This is the acceptance test Mahmood set, and
                   it has already found two defects no other framing surfaced.
    specialist     is anything WRONG, overstated, or misleading BY OMISSION for someone who
                   knows this literature?
    methodologist  are the pooling decisions, certainty ratings and uncertainty handled
                   properly?
    editor         send for review, or desk-reject, and why?
    sceptic        what would a hostile reviewer attack, and can it be defended FROM WHAT IS
                   ON THE PAGE?

A BLIND PUBLISHED COMPARATOR IN EVERY ROUND, AND IT IS NOT OPTIONAL. Each persona receives
TWO documents, labelled only A and B, and is told one may be published and one may not --
without being told which. One is our page; the other is Zelniker (Lancet 2019), a published
SGLT2 meta-analysis. The order alternates by persona index so a lazy reader who always
prefers A cannot produce a clean sweep.

This is what makes a bad verdict interpretable. Tonight, five separate confident findings
turned out to be about the PAYLOAD rather than the page -- a debug render mistaken for a
delivered manuscript, `render()` compared against built HTML, Git Bash paths tested on
Windows Python. If the panel savages our page and praises the comparator, that is a finding
about the page. If it savages both, the instrument is the suspect.

PERSONAS ROTATE ACROSS MODEL FAMILIES BETWEEN ROUNDS. Round 1 sends the student to Codex and
the specialist to Gemini; round 2 swaps them. A role that stays coupled to one model's
quirks produces that model's opinion dressed as a role.

PAYLOADS ARE VERIFIED BEFORE ANY VERDICT IS BELIEVED. `verify_payload` refuses text that is
truncated, carries markup, leaks an element id, or is implausibly short. A verdict about a
broken payload is worse than no verdict, because it is specific and confident.
"""
# collinearity-checked: this runs personas over one page rather than assigning raters across
# a corpus, so there is no rater-by-unit design to confound. The 'only' the linter matched is
# prose, not an assignment rule.

import io
import json
import os
import re
import shutil
import subprocess
import sys
import time

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SESSION = (r"F:\claude-temp\claude\F--rapidmeta-finerenone"
           r"\e2e2a1d5-c19e-44de-90ab-690dbc5235a1\scratchpad")
LEDGER = os.path.join(REPO, "outputs", "multipersona_rounds.jsonl")
CODEX = "/f/E156/outputs/codex_laptop.sh"

PERSONAS = {
    "student": """You are a MEDICAL STUDENT, bright but unfamiliar with this clinical field
and new to evidence synthesis. You have been asked to check one of these documents and
rewrite it into a publishable review.

Your question: COULD YOU IMPROVE IT WITHOUT BEING MISLED BY IT? Specifically -- what would
you believe that you should not? What could you check for yourself, and what would you have
to take on trust? Where would you make a mistake because the document let you?

A confident sentence over missing data is the worst thing you can find, because you would
not question it and it would survive your edit. Quote any you see.""",

    "specialist": """You are a SENIOR SPECIALIST in this clinical area. You know these trials,
their populations and their controversies.

Your question: IS ANYTHING WRONG? Say what is factually incorrect, overstated relative to the
evidence, or MISLEADING BY OMISSION -- something a reader would conclude only because a
relevant fact was left out. Name what is missing that changes the interpretation.""",

    "methodologist": """You are a METHODOLOGIST and statistician who reviews meta-analyses.

Your question: ARE THE METHODS SOUND AS REPORTED? Judge the pooling decisions -- should these
trials be combined at all, and does the document justify it? Judge the certainty ratings, the
handling of heterogeneity, and whether uncertainty is represented honestly or hidden. Say
where a number is presented with more confidence than its derivation supports.""",

    "editor": """You are the EDITOR of a clinical journal deciding what happens to a
submission today.

Your question: SEND FOR PEER REVIEW, or DESK-REJECT? Answer with one of those two, then the
reason. Be concrete about what would have to change to move a desk-reject to a review. Editors
reject for unclear question, unsound method, no advance, and unreadability -- say which
applies.""",

    "sceptic": """You are a SCEPTICAL PEER REVIEWER who expects to recommend rejection and
has to be argued out of it.

Your question: WHAT WOULD YOU ATTACK, and CAN IT BE DEFENDED FROM WHAT IS ON THE PAGE? For
each attack, say explicitly whether the document already answers it -- some of these
documents disclose their own limits, and an attack the text pre-empts is not a good attack.
Quote the defence where it exists, and say so where it does not.""",
}

COMMON = """
You are shown TWO documents, A and B. One may be a published paper and one may not; you are
not told which, and you should not assume either way. Judge BOTH on the same terms.

Answer for EACH document separately, in this order:

  {role_question}

Then, finally:

  WHICH IS BETTER, A or B, and by how much -- decisively better, slightly better, or no real
  difference? Say what separates them.

Quote verbatim from whichever document you are discussing. Be blunt and specific. Do not be
polite about it, and do not speculate about how either document was produced.
"""


def extract_paper(path):
    """The Paper tab of a built page, as plain text."""
    h = io.open(path, encoding="utf-8", errors="replace").read()
    m = re.search(r'id="pn-paper"(.*?)(?:id="pn-[a-z]|<!--\s*end-paper)', h, re.S)
    if not m:
        return None
    seg = re.sub(r"(?is)<(script|style)\b.*?</\1>", " ", m.group(1))

    # COLLAPSED CONTENT MUST REACH THE REVIEWER COLLAPSED, and getting this wrong produced a
    # false finding I nearly acted on.
    #
    # Round 1's editor desk-rejected the page over "completely unreadable strings such as
    # results.by_outcome.harmonised_cvdeath_or_hhf.POOL_FINDINGS_2026_08_21". That string is
    # inside a <details class='prov-block'> element -- collapsed, behind a one-line summary,
    # and a reader never meets it unless they choose to open it. The editor met it because
    # THIS EXTRACTOR FLATTENED THE DISCLOSURE and handed them a document no reader sees.
    #
    # The proposed fix would have been to strip the provenance apparatus -- the exact
    # feature the student, the sceptic and the methodologist each named as the reason they
    # trusted the page over a published Lancet paper. A payload defect would have deleted
    # the page's best property.
    #
    # So a disclosure is rendered AS a disclosure: the reviewer is told it exists and how
    # much is behind it, and does not have its contents poured into the reading flow.
    seg = re.sub(
        r"(?is)<details[^>]*>\s*<summary[^>]*>(.*?)</summary>(.*?)</details>",
        lambda md: "\n[%s -- collapsed on the page; %d entries behind a disclosure the "
                   "reader may open]\n"
                   % (" ".join(re.sub(r"<[^>]+>", " ", md.group(1)).split()),
                      len(re.findall(r"<li\b", md.group(2)))),
        seg)
    seg = re.sub(r"(?i)<h([1-6])[^>]*>", "\n\n## ", seg)
    seg = re.sub(r"(?i)</h[1-6]>", "\n", seg)
    seg = re.sub(r"(?i)<(p|tr|li|div)\b[^>]*>", "\n", seg)
    seg = re.sub(r"(?i)</td>\s*<td[^>]*>", "  |  ", seg)
    txt = re.sub(r"<[^>]+>", " ", seg)
    import html as _h
    txt = _h.unescape(txt)
    txt = re.sub(r"[ \t]+", " ", txt)
    return re.sub(r"\n\s*\n\s*\n+", "\n\n", txt).strip()


def verify_payload(name, txt):
    """(ok, reasons). REFUSES a payload before any verdict is drawn from it.

    Five confident findings tonight were about the payload and not the page. This is the
    cheapest possible defence and it should have existed from the first panel.
    """
    bad = []
    if not txt:
        return False, ["empty"]
    if len(txt.split()) < 120:
        bad.append("only %d words -- implausibly short for a manuscript" % len(txt.split()))
    if re.search(r"<[a-z/][^>]*>", txt):
        bad.append("markup survived extraction")
    # `id="` IN THE HTML ATTRIBUTE FORM, not the bare string `id=`.
    #
    # The first version refused SGLT2_HF on "an element id leaked into the text", and what
    # it had found was the page's OWN PROVENANCE LIST -- "outcomes[id=harmonised_cvdeath_
    # _or_hhf].name" -- which is deliberate, reader-facing, and the mechanism by which every
    # claim on the page is traceable. The verifier written to stop me believing verdicts
    # about broken payloads had refused a perfectly good one, on its first run, for content
    # that is a feature.
    #
    # Which is the night's rule arriving one more time: the check looked at something
    # ADJACENT to what it claimed to check. It cost one run rather than a false finding,
    # because it fails closed.
    if "pn-paper" in txt or 'id="' in txt:
        bad.append("an HTML element id leaked into the text")
    if "<!--" in txt or "-->" in txt:
        bad.append("an HTML comment leaked into the text")
    if txt.rstrip().endswith(("...", "…")) or re.search(r"\w-$", txt.rstrip()):
        bad.append("ends mid-word or with an ellipsis -- probably truncated")
    if "&#x27;" in txt or "&quot;" in txt or "&amp;" in txt:
        bad.append("HTML entities were not unescaped")
    return (not bad), bad


def ask(family, prompt, tag):
    """Send one prompt. VERIFY-AND-RETRY: the delegation bug is intermittent, and a job that
    silently received no prompt exits 0 with nothing, which looks exactly like success.

    THE TWO FAMILIES TAKE THE PROMPT DIFFERENTLY, and the difference is not cosmetic.
    Codex reads stdin, so a 40,000-character payload passes intact. `agy --print` takes the
    prompt as an ARGV ARGUMENT, and Windows caps a command line at 32,767 characters -- so
    the first run of this harness died with "The filename or extension is too long" on a
    41,594-character prompt.

    THE OBVIOUS FIX WAS TO SHORTEN THE PAYLOAD, AND IT WAS THE WRONG ONE. Truncating the
    manuscript to fit a CLI limit would have produced verdicts about a document no reader
    ever sees -- the exact failure this harness verifies payloads to prevent, reintroduced
    for the convenience of the transport. Measured first: the paper tab is 5,050 words and
    only 2% is provenance apparatus, so there was nothing to trim that a reader does not
    read.

    So the prompt is written to the session directory and Gemini is given the directory and
    told to read it. Complete payload, both families, no truncation.
    """
    out_path = os.path.join(SESSION, "mp_%s.txt" % tag)
    for attempt in (1, 2, 3):
        if family == "openai":
            # LOCAL `codex exec`, NOT THE LAPTOP WRAPPER, and the reason is a measured
            # ceiling rather than a preference. The wrapper ships the prompt to the laptop
            # over SSH, and at 41,594 characters that transport fails outright: exit 4,
            # "ssh transport failed (rc=255)". Earlier panels at ~17,000 characters went
            # through fine, so the ceiling sits between them.
            #
            # THE WRAPPER FAILED HONESTLY, which is why this is a routing problem and not a
            # data problem: it returned non-zero and empty rather than a truncated prompt's
            # answer, the harness retried three times, and then recorded the persona as
            # MISSING rather than inventing a verdict. Three layers each declined to guess.
            #
            # Local `codex exec` reads the prompt on STDIN with no argv limit and no SSH
            # hop. Confirmed GPT-5, so the family is unchanged and the rotation still means
            # what it says.
            # RESOLVED, NOT ASSUMED. `codex` runs fine from a shell and is invisible to
            # `CreateProcess`, which is what subprocess uses on Windows: bare "codex" raised
            # WinError 2, "the system cannot find the file specified". The shell finds it
            # through PATHEXT (codex.cmd); CreateProcess does not.
            exe = shutil.which("codex") or shutil.which("codex.cmd") or "codex"
            p = subprocess.run([exe, "exec", "-s", "read-only"],
                               input=prompt.encode("utf-8"),
                               capture_output=True, timeout=900)
        else:
            pf = os.path.join(SESSION, "mp_prompt_%s.txt" % tag)
            io.open(pf, "w", encoding="utf-8").write(prompt)
            p = subprocess.run(
                ["agy", "--add-dir", SESSION, "--print",
                 "Read the file %s in full. It contains your instructions and two "
                 "documents. Follow it exactly and reply with your answer only."
                 % os.path.basename(pf)],
                stdin=subprocess.DEVNULL, capture_output=True, timeout=900, shell=False)
        body = (p.stdout or b"").decode("utf-8", "replace").strip()
        if len(body) > 400:
            io.open(out_path, "w", encoding="utf-8").write(body)
            return body, attempt
        print("      %s attempt %d produced %d bytes -- retrying"
              % (tag, attempt, len(body)), flush=True)
        time.sleep(3)
    return None, 3


def run_round(page, round_no, anchor_text, only=None):
    """One round: five personas, families rotated by round, comparator blind in every one."""
    paper = extract_paper(os.path.join(REPO, page))
    ok, why = verify_payload(page, paper)
    print("PAYLOAD %s: %s  (%d words)" % (page, "OK" if ok else "REFUSED " + "; ".join(why),
                                          len((paper or "").split())))
    aok, awhy = verify_payload("anchor", anchor_text)
    print("PAYLOAD anchor: %s  (%d words)"
          % ("OK" if aok else "REFUSED " + "; ".join(awhy), len(anchor_text.split())))
    if not (ok and aok):
        print("REFUSED: a payload did not verify. No verdict is drawn from a broken payload.")
        return None
    print()

    # THE INDEX COMES FROM THE FULL PERSONA LIST, NOT THE FILTERED ONE.
    #
    # Re-running a subset with `only=` used to renumber the survivors from zero, so the
    # methodologist -- assigned openai in the full round -- came back google when re-run
    # alone. The rotation is the whole reason a role is not just one model's opinion, and a
    # rotation that silently changes when you re-run part of a round is not a rotation.
    all_names = sorted(PERSONAS)
    names = [n for n in all_names if (not only or n in only)]
    results = {}
    for role in names:
        i = all_names.index(role)
        # FAMILY ROTATES WITH THE ROUND, so a role is not permanently one model's opinion.
        family = ("openai", "google")[(i + round_no) % 2]
        # ORDER ALTERNATES, so "always prefers A" cannot produce a clean sweep.
        ours_is_a = (i % 2 == 0)
        doc_a, doc_b = (paper, anchor_text) if ours_is_a else (anchor_text, paper)
        prompt = (PERSONAS[role] + "\n" + COMMON.format(role_question="(the question above)")
                  + "\n\n=== DOCUMENT A ===\n" + doc_a
                  + "\n\n=== DOCUMENT B ===\n" + doc_b)
        tag = "%s_r%d_%s" % (page.replace(".html", ""), round_no, role)
        print("  %-14s family=%-7s ours=%s  chars=%d"
              % (role, family, "A" if ours_is_a else "B", len(prompt)), flush=True)
        body, attempts = ask(family, prompt, tag)
        if body is None:
            print("      NO OUTPUT after 3 attempts -- recorded as missing, not as a verdict")
            results[role] = {"family": family, "ours": "A" if ours_is_a else "B",
                             "verdict": None, "attempts": attempts}
            continue
        results[role] = {"family": family, "ours": "A" if ours_is_a else "B",
                         "verdict": body, "attempts": attempts, "bytes": len(body)}
        print("      %d bytes in %d attempt(s)" % (len(body), attempts))

    rec = {"page": page, "round": round_no,
           "personas": {k: {kk: vv for kk, vv in v.items() if kk != "verdict"}
                        for k, v in results.items()}}
    with io.open(LEDGER, "a", encoding="utf-8") as fh:
        fh.write(json.dumps(rec, ensure_ascii=False) + "\n")
    return results


def main():
    page = sys.argv[1] if len(sys.argv) > 1 else "SGLT2_HF_REVIEW.html"
    rnd = int(sys.argv[2]) if len(sys.argv) > 2 else 1
    anchor = io.open(os.path.join(SESSION, "anchor_zelniker.txt"),
                     encoding="utf-8").read().strip()
    res = run_round(page, rnd, anchor)
    if res is None:
        return 1
    print()
    for role in sorted(res):
        v = res[role]
        print("=" * 78)
        print("%s  [%s, ours=%s]" % (role.upper(), v["family"], v["ours"]))
        print(v["verdict"] or "(no output)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
