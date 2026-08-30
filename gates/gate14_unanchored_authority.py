"""An external authority making a claim with nothing in the block to follow or date.

AN UNSOURCED CLAIM DOES NOT MERELY LACK SUPPORT -- IT DRIFTS TO ITS STRONGEST FORM,
because nothing holds it to the weaker one. "WHO has recommended the ring" lost the
conditionality, the certainty grade, the population and the combination framing: every
qualifier a clinician needs in order to act on it. The sentence gets shorter and more
confident as it drifts, which is why nobody notices.

WHAT THE CORPUS ACTUALLY CARRIES, measured across 932,327 rendered blocks on 1,464
delivered pages: 26 unanchored authority claims on 11 pages. The dominant one is
"Regulator: FDA approved label", eleven times across three heart-failure reviews, with no
date and no label version. A label is not a fixed object -- indications get added,
warnings get boxed, approvals get withdrawn -- so an undated "approved label" cannot be
checked by a reader and cannot be wrong in any way they could detect. SOTAGLIFLOZIN
carries "Regulator: EMA, authorisation for a different indication, withdrawn" with no date
attached to the withdrawal.

THIS IS THE DISPLAYED-BYTES LEG AND IT IS THE COMPLEMENT OF ANOTHER LANE'S DETECTOR, not
a duplicate of it. Where the two disagree that is a finding to report, not to reconcile
quietly. What this leg uniquely sees is what a reader receives: a sibling check elsewhere
passed a page that RENDERED sentence[:300] while the check read the whole stored sentence,
so the anchor existed in the data and was cut off before the reader ever saw it.

RATCHETED AT 26, and the note says what that means. Rewriting the prose on 11 pages is
editorial work with a ruling attached; stopping the 27th is the property that was missing.
"""
from __future__ import annotations

import io
import json
import os
import subprocess
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _harness as H                                                        # noqa: E402

DETECTOR = os.path.join("scripts", "sweep_unanchored_authority_2026_08_30.py")
RESULT = os.path.join("outputs", "unanchored_authority_2026_08_30.json")
BACKLOG = "UNANCHORED_AUTHORITY_BACKLOG.json"


def main(argv):
    gate = H.Gate("14 UNANCHORED AUTHORITY",
                  "an authority named as the source of a claim, with nothing in the block "
                  "a reader could follow or date")
    # THE NAMED CASE IS THE DISCRIMINATION, NOT A PAGE. Naming a defective page would make
    # this gate vacuous the moment that page is edited -- and these pages are meant to be
    # edited. What must keep working is the ability to tell a claim from a method
    # statement and an organisation from a pronoun in emphatic capitals; each of those
    # cost a measured false positive to learn.
    gate.expect_case("discriminates",
                     "a tool label, a pronoun in capitals and an anchored citation are all "
                     "left alone, while an undated authority claim is caught")
    gate.requires_control()

    repo = H.repo_root()
    path = os.path.join(repo, DETECTOR)
    if not os.path.exists(path):
        gate.broken("%s is absent; this gate RUNS the detector rather than reimplementing "
                    "it." % DETECTOR)
        gate.kinds({"detector present": 0, "detector absent": 1})
        return gate.report(denominator="0 pages -- the detector could not run")

    plant = subprocess.run([sys.executable, path, "--plant"], cwd=repo, capture_output=True)
    pout = plant.stdout.decode("utf-8", "replace")
    held = plant.returncode == 0 and pout.count("[PASS]") == 13
    if held:
        gate.control(13, 0, [], accuses=True)
        gate.saw("discriminates")
    else:
        gate.control(13, 13, ["the detector's own plant did not hold"], accuses=True)
        gate.broken("the detector's plant did not pass 13/13, so its counts are not "
                    "usable. stdout: %s" % pout[-300:].replace(chr(10), " "))

    proc = subprocess.run([sys.executable, path], cwd=repo, capture_output=True)
    if proc.returncode == 2:
        gate.broken("the detector REFUSED its own controls: %s"
                    % proc.stdout.decode("utf-8", "replace")[-300:].replace(chr(10), " "))
        gate.kinds({"pages reached": 0})
        return gate.report(denominator="the detector refused rather than reporting a pass")

    try:
        doc = json.load(io.open(os.path.join(repo, RESULT), encoding="utf-8"))
    except Exception as e:
        gate.broken("the detector ran but its result could not be read: %s" % e)
        gate.kinds({"result file readable": 0})
        return gate.report(denominator="no result to ratchet")

    hits = doc.get("findings") or []
    claims = doc.get("n_claims", 0)

    found = ["%s|%s" % (h["page"], h["block"][:70]) for h in hits]
    if "--plant" in argv:
        found.append("__control_planted_page.html|WHO has recommended the ring.")
        gate.note("PLANTED: a new page asserting an authority with nothing to follow")

    new = H.ratchet(gate, BACKLOG, found,
                    "blocks naming an external authority as the source of a claim with no "
                    "year, identifier, document version or link in the same block.")

    gate.kinds({
        "delivered pages read": doc.get("n_pages_read", 0),
        "rendered blocks examined": doc.get("n_blocks", 0),
        "blocks naming an external authority": doc.get("n_blocks_with_authority", 0),
        "  the authority is the SUBJECT OF A CLAIM": claims,
        "  it NAMES A TOOL used -- a method statement": doc.get("n_tool_mentions", 0),
        "  every uppercase WHO is a relative PRONOUN": doc.get("n_pronoun_blocks", 0),
        "  a bare mention with no assertion attached": doc.get("n_bare_mentions", 0),
        "UNANCHORED, of which NEW since the freeze": len(new),
    })
    gate.coverage(claims, max(doc.get("n_blocks_with_authority", 0), claims),
                  "blocks that name an authority without asserting anything through it -- "
                  "tool labels, bare mentions and pronouns. They carry no claim to anchor, "
                  "so this gate makes no statement about them either way")
    gate.note("the discriminations cost three measured false positives on live data: a "
              "tool label is not a claimant (1,115 raw hits collapsed to 74), the pronoun "
              "in emphatic capitals is not the organisation (1 of 27), and suppressing on "
              "ANY pronoun killed a real claim, so the test is per-occurrence.")
    gate.note("ratcheted, not blocked. Rewriting the prose on 11 pages is editorial work "
              "with a ruling attached; stopping the 27th instance is the property that was "
              "missing.")

    for f in new:
        page, _, block = f.partition("|")
        gate.finding("AUTHORITY-CLAIM-WITH-NO-ANCHOR",
                     "%s asserts something through an external authority with nothing in "
                     "the same block to follow or date: %r. An unsourced claim drifts to "
                     "its strongest form." % (page, block[:90]),
                     numerator=len(new), denominator=claims)

    return gate.report(denominator="%d authority claims in rendered blocks; %d unanchored, "
                                   "%d frozen"
                       % (claims, len(hits), len(found) - len(new)))


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
