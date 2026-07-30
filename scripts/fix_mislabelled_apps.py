"""Fix the two mis-labelled cardio apps. Rebuilt on current origin/main.

Filenames and URLs are DELIBERATELY NOT CHANGED - renaming would break every
existing link. The displayed identity is corrected instead, and the URL/content
mismatch is stated on the page so a reader arriving from a stale link is not
misled.

TIRZEPATIDE_ARDS_AUTO_FULL_REVIEW.html  -> a review of ANDEXANET ALFA
ICAGEN_AUTO_FULL_REVIEW.html            -> a review of EDOXABAN

Both shipped a green "INTERNAL CHECKS PASSED" badge with window.__verdict
"STABLE" / n_trials_seen 2 over 3-row ledgers, and both displayed a pooled
estimate. Verified live in a browser before this fix:
    TIRZEPATIDE_ARDS  displayed RR 0.06 (0.01-0.21)
    ICAGEN            displayed RR 0.52 (0.33-0.84)

=== THE IMPOSSIBLE HAZARD RATIO (TIRZEPATIDE_ARDS / andexanet) ===

All three rows stored a PERCENT CHANGE in the hazard-ratio fields
(publishedHR / hrLCI / hrUCI / pubHR / pubHR_LCI / pubHR_UCI):

    NCT02220725  73.83  (65.1542 - 82.5058)
    NCT02207725  73.15  (67.5193 - 78.7807)
    NCT02329327   0.80  (-0.5509 - 2.1509)   <-- NEGATIVE lower bound

A hazard ratio is a ratio of positive rates and cannot be <= 0, so the third row
is not merely implausible, it is impossible; any log transform yields NaN.

Arithmetic origin, verified against ClinicalTrials.gov API v2 this session. The
posted primary for both ANNEXA-A and ANNEXA-R is "Percent change in anti-fXa
activity" (paramType MEAN), and every posted value is NEGATIVE - these are
reductions:
    NCT02220725 Part I: placebo -18.39 (n=14), andexanet -92.22 (n=27)
                        -92.22 - (-18.39) = -73.83  -> the ledger's  73.83
    NCT02207725 Part I: placebo -20.71 (n=9),  andexanet -93.86 (n=24)
                        -93.86 - (-20.71) = -73.15  -> the ledger's  73.15
Both reproduce EXACTLY. The stored figure is an absolute mean difference in
percent-change units, with its sign stripped, written into a hazard-ratio field.

NCT02329327 (ANNEXA-4) posts its percent change as a MEDIAN with a 95% CI, by
FXa inhibitor: apixaban -93.3 (-94.2 to -92.5), rivaroxaban -94.1 (-95.1 to
-93.0), edoxaban -71.3 (-82.3 to -65.2), enoxaparin -75.41 (-79.17 to -66.67).
The ledger's 0.80 (-0.5509 to 2.1509) matches NONE of them. It is therefore
marked UNVERIFIED rather than reconstructed - no value is invented for it.

DISPOSITION. There is no hazard ratio for any of these rows, so all six HR
fields are set to null on all three. The outcome is a continuous
pharmacodynamic surrogate, so there is also no valid binary 2x2: the stored
per-arm "counts" (1/14, 0/9, 2/477 vs 26/27, 24/24, 0/2) are arm sizes and
indices, not event counts, and the RR 0.06 the page displayed was computed from
them. The three rows are QUARANTINED - retained in window.__quarantinedTrials
with their verified posted values, never deleted - and the app therefore shows
no pooled estimate rather than a meaningless one.

A GENUINE estimand does exist and is recorded, though NOT pooled here: ANNEXA-I
(NCT03661528), the randomised phase 4 trial, posts effective haemostasis as
andexanet 150/224 vs usual care 121/228 -> OR 1.7925 (1.2246-2.6238), p=0.0027
(Mantel-Haenszel, verified in R 4.6.0 / metafor rma.mh). Adding it to the pool
would create a new headline claim and is a separate, gated decision.

=== ICAGEN / edoxaban ===

Scope here is identity + badge honesty, as instructed - NO number is changed.
Two findings are recorded on the badge rather than silently corrected, because a
data correction needs its own cross-family gate:
  - the declared subject is "Edoxaban TIMI 48 cancer-VTE", but none of the three
    pooled trials is a cancer-VTE trial or ENGAGE AF-TIMI 48. NCT02798471 is the
    Hokusai study in PAEDIATRIC VTE; NCT01181102 and NCT01181141 are edoxaban VTE
    prophylaxis after orthopaedic surgery.
  - a registry spot-check of NCT02798471 disagrees with the ledger: the posted
    primary is edoxaban 5/145 vs standard of care 2/141; the ledger carries
    0/147 vs 1/143.
"""
import io
import json
import re
import sys

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

RETRIEVED = "2026-07-30"


def read(path):
    raw = open(path, "rb").read()
    return raw.decode("utf-8-sig" if raw.startswith(b"\xef\xbb\xbf") else "utf-8"), raw.startswith(b"\xef\xbb\xbf")


def write(path, s, bom):
    data = s.encode("utf-8")
    if bom and not data.startswith(b"\xef\xbb\xbf"):
        data = b"\xef\xbb\xbf" + data          # preserve the pre-existing BOM exactly
    open(path, "wb").write(data)


def replace_badge(s, new_badge):
    i = s.index('id="rapidmeta-integrity-badge"')
    st = s.rfind("<div", 0, i)
    depth, k = 0, st
    while k < len(s):
        if s.startswith("<div", k):
            depth += 1
        elif s.startswith("</div>", k):
            depth -= 1
            if depth == 0:
                k += 6
                break
        k += 1
    assert "INTERNAL CHECKS PASSED" in s[st:k], "badge is not the false-green one"
    return s[:st] + new_badge + s[k:]


def replace_verdict(s, obj, extra=""):
    m = re.search(r"<script>window\.__verdict = \{.*?\};</script>", s, re.S)
    assert m, "no __verdict surface"
    return (s[:m.start()] + "<script>window.__verdict = "
            + json.dumps(obj, ensure_ascii=False) + ";" + extra + "</script>" + s[m.end():])


BADGE_CSS = ('style="background:#7c2d12;color:#fff;padding:12px 20px;font-family:system-ui,sans-serif;'
             'font-size:13.5px;border-bottom:3px solid #431407;line-height:1.55;"')
NOTE_CSS = ('style="margin-top:6px;font-size:12px;background:rgba(255,255,255,0.16);padding:8px 11px;'
            'border-left:4px solid #fed7aa;border-radius:3px;"')

# ==========================================================================
# APP 1 - TIRZEPATIDE_ARDS_AUTO_FULL_REVIEW.html  =  ANDEXANET ALFA
# ==========================================================================
F1, S1 = "TIRZEPATIDE_ARDS_AUTO_FULL_REVIEW.html", "TIRZEPATIDE_ARDS_AUTO_REVIEW.html"
s, bom = read(F1)
before = len(s)

QUAR1 = {
    "NCT02220725": {
        "trial": "ANNEXA-A", "pmid": "26559317", "phase": "III", "randomised": True,
        "identity_source": "ClinicalTrials.gov NCT02220725, read " + RETRIEVED,
        "posted_primary": "Efficacy: Percent Change From Baseline in Anti-fXa Activity at the "
                          "Nadir (Parts I and II)",
        "unit": "Percent change in anti-fXa activity (paramType MEAN, dispersion SD)",
        "posted_values": {"Part I placebo": "-18.39 (n=14)", "Part I andexanet": "-92.22 (n=27)",
                          "Part II placebo": "-44.75 (n=13)", "Part II andexanet": "-96.72 (n=26)"},
        "previous_ledger_HR": "73.83 (65.1542-82.5058)",
        "previous_ledger_defect": (
            "A PERCENT CHANGE stored in a hazard-ratio field. -92.22 - (-18.39) = -73.83, "
            "reproducing the stored 73.83 EXACTLY with its sign stripped. It is an absolute "
            "mean difference in percent-change units, not a hazard ratio."),
        "previous_ledger_counts": "tE 1 / tN 14 vs cE 26 / cN 27 - not event counts; arm sizes "
                                  "and indices for a CONTINUOUS outcome.",
        "disposition": "HR fields nulled; row quarantined from the binary pool.",
    },
    "NCT02207725": {
        "trial": "ANNEXA-R", "pmid": "26559317", "phase": "III", "randomised": True,
        "identity_source": "ClinicalTrials.gov NCT02207725, read " + RETRIEVED,
        "posted_primary": "Efficacy: Percent Change From Baseline in Anti-fXa Activity at the "
                          "Nadir (Parts I and II)",
        "unit": "Percent change in anti-fXa activity (paramType MEAN, dispersion SD)",
        "posted_values": {"Part I placebo": "-20.71 (n=9)", "Part I andexanet": "-93.86 (n=24)",
                          "Part II placebo": "-32.70 (n=8)", "Part II andexanet": "-92.34 (n=23)"},
        "previous_ledger_HR": "73.15 (67.5193-78.7807)",
        "previous_ledger_defect": (
            "Same defect. -93.86 - (-20.71) = -73.15, reproducing the stored 73.15 exactly."),
        "previous_ledger_counts": "tE 0 / tN 9 vs cE 24 / cN 24 - not event counts.",
        "disposition": "HR fields nulled; row quarantined from the binary pool.",
    },
    "NCT02329327": {
        "trial": "ANNEXA-4", "pmid": "27573206", "phase": "III", "randomised": False,
        "design_note": "SINGLE-ARM (ClinicalTrials.gov allocation: NA). There is no comparator, "
                       "so no between-group effect is defined for it at all.",
        "identity_source": "ClinicalTrials.gov NCT02329327, read " + RETRIEVED,
        "posted_primary": "Percent Change From Baseline In Anti-fXa Activity By FXa Inhibitor",
        "unit": "Percent Change (paramType MEDIAN, dispersion 95% CI)",
        "posted_values": {"apixaban": "-93.3 (-94.2 to -92.5), n=169",
                          "rivaroxaban": "-94.1 (-95.1 to -93.0), n=130",
                          "edoxaban": "-71.3 (-82.3 to -65.2), n=28",
                          "enoxaparin": "-75.41 (-79.17 to -66.67), n=17"},
        "second_primary": "Participants Achieving Hemostatic Efficacy - overall 272/340",
        "previous_ledger_HR": "0.80 (-0.5509 to 2.1509)",
        "previous_ledger_defect": (
            "IMPOSSIBLE AS STATED: the lower confidence bound is NEGATIVE. A hazard ratio is a "
            "ratio of positive rates and cannot be <= 0; any log transform yields NaN. The value "
            "also matches NO posted result for this trial - every posted percent change is "
            "between -71.3 and -94.1. Marked UNVERIFIED; deliberately NOT reconstructed."),
        "previous_ledger_counts": "tE 2 / tN 477 vs cE 0 / cN 2 - not event counts.",
        "disposition": "HR fields nulled and marked UNVERIFIED; row quarantined.",
    },
}

GENUINE = {
    "trial": "ANNEXA-I (NCT03661528)", "phase": "IV", "randomised": True,
    "why_it_matters": "The one randomised trial of andexanet alfa with a genuine COMPARATIVE "
                      "binary primary outcome, and therefore the only row here from which a real "
                      "effect estimate can be derived.",
    "posted_primary": "Number of Participants Who Achieved Effective Hemostasis",
    "posted": "andexanet alfa 150/224 vs usual care 121/228",
    "derived": "OR 1.7925 (95% CI 1.2246-2.6238), p=0.0027 - Mantel-Haenszel with "
               "Robins-Breslow-Greenland SE, computed in R 4.6.0 / metafor rma.mh",
    "source": "ClinicalTrials.gov NCT03661528 posted results, read " + RETRIEVED,
    "status": "NOT POOLED IN THIS APP. Adding it would create a new headline claim and is a "
              "separate decision requiring its own cross-family gate.",
}

V1 = {
    "verdict": "UNCERTAIN",
    "preliminary": True,
    "identity_correction": {
        "file_and_url_say": "TIRZEPATIDE_ARDS",
        "actual_subject": "andexanet alfa for factor-Xa-inhibitor reversal",
        "filename_retained": True,
        "why": "The .html filename and its published URL are deliberately unchanged - renaming "
               "would break every existing link to this page. The displayed identity is the "
               "correct one and the mismatch is stated on the page.",
        "note": "This app contains no tirzepatide trial and no ARDS trial, and never did.",
    },
    "counts": {"n_trials_in_ledger": 0, "n_trials_analysed": 0, "n_trials_quarantined": 3,
               "n_trials_seen": 0, "P0_internal": None, "P0_grim": None, "P1_aact_concord": None,
               "P2_evidence_incomplete": 3},
    "counts_note": "Gate counts are null, not zero: with every row quarantined there is nothing "
                   "left to test, and a zero would read as a clean bill.",
    "reasons": [
        "IDENTITY CORRECTED. This page is a review of ANDEXANET ALFA for factor-Xa-inhibitor "
        "reversal. Its filename and URL say TIRZEPATIDE_ARDS; they are retained unchanged so "
        "existing links keep working. There is no tirzepatide trial and no ARDS trial in it.",
        "IMPOSSIBLE HAZARD RATIO REMOVED. All three rows stored a PERCENT CHANGE in the "
        "hazard-ratio fields, and NCT02329327's lower confidence bound was NEGATIVE (-0.5509). "
        "A hazard ratio cannot be <= 0. All six HR fields are now null on all three rows.",
        "Arithmetic origin verified against ClinicalTrials.gov: -92.22 - (-18.39) = -73.83 and "
        "-93.86 - (-20.71) = -73.15, reproducing the stored 73.83 and 73.15 exactly, with the "
        "sign stripped. They are absolute mean differences in percent-change units.",
        "NCT02329327's 0.80 (-0.5509 to 2.1509) matches NO posted value for that trial - every "
        "posted percent change lies between -71.3 and -94.1. Marked UNVERIFIED and deliberately "
        "NOT reconstructed.",
        "THE PREVIOUSLY DISPLAYED POOLED ESTIMATE, RR 0.06 (0.01-0.21), IS WITHDRAWN. It was "
        "computed from per-arm 'counts' that are not event counts - they are arm sizes and "
        "indices for a CONTINUOUS pharmacodynamic outcome (percent change in anti-fXa activity). "
        "No valid binary 2x2 exists for any row, so no pooled binary estimate is shown.",
        "All three rows are QUARANTINED, not deleted - retained in window.__quarantinedTrials "
        "with their verified posted values.",
        "The endpoint is a pharmacodynamic SURROGATE (anti-fXa activity), not a clinical outcome. "
        "NCT02329327 (ANNEXA-4) is additionally SINGLE-ARM, so no between-group effect is defined "
        "for it at all.",
        "A genuine comparative estimand exists and is recorded but NOT pooled here: ANNEXA-I "
        "(NCT03661528), effective haemostasis 150/224 vs 121/228, OR 1.7925 (1.2246-2.6238), "
        "p=0.0027. Adding it is a separate, gated decision.",
        "Verification is registry-level (ClinicalTrials.gov API v2, " + RETRIEVED + "). "
        "AMSTAR-2 confidence: CRITICALLY LOW.",
    ],
    "p0_total": None,
    "p0_total_note": "null, not 0 - no gate ran, because every row is quarantined.",
    "pooled": None,
    "pooled_note": "No pooled estimate. The previous RR 0.06 (0.01-0.21) was withdrawn as "
                   "meaningless, not merely uncertain.",
    "genuine_estimand_available_not_pooled": GENUINE,
}

BADGE1 = (
    f'<div id="rapidmeta-integrity-badge" role="status" {BADGE_CSS}>'
    '<div style="display:flex;align-items:center;gap:12px;flex-wrap:wrap;">'
    '<strong style="font-size:14px;letter-spacing:0.04em;">IDENTITY CORRECTED &mdash; '
    'THIS IS A REVIEW OF ANDEXANET ALFA</strong>'
    '<span style="font-size:11.5px;">Pooled: <strong>0</strong> trials &middot; Quarantined: '
    '<strong>3</strong> &middot; Pooled estimate: <strong>withdrawn</strong></span></div>'

    f'<div {NOTE_CSS}>'
    '<strong>Correction &mdash; this page&rsquo;s address does not match its contents.</strong> '
    'The file is named <code style="background:rgba(255,255,255,0.28);padding:1px 4px;'
    'border-radius:2px;">TIRZEPATIDE_ARDS_AUTO_FULL_REVIEW.html</code> and its published URL says '
    'the same. <strong>It is a review of andexanet alfa for factor-Xa-inhibitor reversal.</strong> '
    'It contains no tirzepatide trial and no ARDS trial, and never did. '
    '<em>The filename and URL are deliberately left unchanged so that existing links keep '
    'working; only the displayed identity is corrected.</em></div>'

    '<div style="margin-top:6px;font-size:12.5px;">'
    '<strong>An impossible hazard ratio has been removed.</strong> All three rows stored a '
    '<em>percent change</em> in the hazard-ratio fields, and NCT02329327 carried '
    '<strong>0.80 with a lower confidence bound of &minus;0.5509</strong>. A hazard ratio is a '
    'ratio of positive rates and <strong>cannot be &le; 0</strong>; any log transform of it '
    'yields NaN. All six HR fields are now <strong>null</strong> on all three rows.</div>'

    '<div style="margin-top:6px;font-size:11.5px;">'
    '<strong>Where the numbers came from</strong> (ClinicalTrials.gov API v2, retrieved '
    f'{RETRIEVED}). The posted primary for ANNEXA-A and ANNEXA-R is &ldquo;Percent change in '
    'anti-fXa activity&rdquo;, and every posted value is <em>negative</em> &mdash; these are '
    'reductions. &minus;92.22 &minus; (&minus;18.39) = <strong>&minus;73.83</strong> and '
    '&minus;93.86 &minus; (&minus;20.71) = <strong>&minus;73.15</strong>, reproducing the stored '
    '73.83 and 73.15 <em>exactly</em>, with the sign stripped. They are absolute mean differences '
    'in percent-change units, not hazard ratios. ANNEXA-4&rsquo;s stored 0.80 '
    '(&minus;0.5509 to 2.1509) matches <strong>no</strong> posted value for that trial &mdash; '
    'every posted percent change lies between &minus;71.3 and &minus;94.1 &mdash; so it is marked '
    '<strong>UNVERIFIED and deliberately not reconstructed</strong>.</div>'

    '<div style="margin-top:6px;font-size:11.5px;">'
    '<strong>The pooled estimate is withdrawn, not merely caveated.</strong> This page previously '
    'displayed <strong>RR 0.06 (0.01&ndash;0.21)</strong>. That figure was computed from per-arm '
    '&ldquo;counts&rdquo; which are not event counts at all &mdash; they are arm sizes and indices '
    'for a <em>continuous</em> outcome. No valid 2&times;2 table exists for any row, so no pooled '
    'binary estimate is shown. All three rows are <strong>quarantined, not deleted</strong> (see '
    '<code style="background:rgba(255,255,255,0.28);padding:1px 4px;border-radius:2px;">'
    'window.__quarantinedTrials</code>), with their verified posted values.</div>'

    '<div style="margin-top:6px;font-size:11.5px;">'
    '<strong>A genuine result does exist &mdash; and it is not pooled here.</strong> '
    '<strong>ANNEXA-I</strong> (NCT03661528), the randomised phase 4 trial, posts effective '
    'haemostasis as <strong>andexanet alfa 150/224 vs usual care 121/228</strong> &rarr; '
    '<strong>OR 1.79 (1.22&ndash;2.62), p=0.003</strong> (Mantel-Haenszel, Robins-Breslow-Greenland '
    'SE, computed in R 4.6.0 / metafor). It is recorded rather than pooled: adding it would create '
    'a new headline claim and is a separate decision requiring its own cross-family gate.</div>'

    '<div style="margin-top:6px;font-size:10.5px;">'
    '<strong>Limits, stated.</strong> The endpoint in every quarantined row is a '
    '<strong>pharmacodynamic surrogate</strong> (anti-fXa activity), not a clinical outcome. '
    'ANNEXA-4 is additionally <strong>single-arm</strong> (ClinicalTrials.gov allocation: NA), so '
    'no between-group effect is defined for it at all. Two rows share one publication '
    '(PMID 26559317) because ANNEXA-A and ANNEXA-R are two distinct trials reported together '
    '&mdash; that duplication is correct and is not an error. Verification here is '
    '<strong>registry-level</strong>; no full text or regulatory document was consulted. Gate '
    'counts in <code style="background:rgba(255,255,255,0.28);padding:1px 4px;border-radius:2px;">'
    'window.__verdict</code> are <strong>null, not zero</strong> &mdash; with every row '
    'quarantined there is nothing left to test. AMSTAR-2 confidence: '
    '<strong>CRITICALLY LOW</strong>.</div></div>'
)

# empty the analysis pool - the quarantined rows keep their record elsewhere
i = s.index("realData:{")
j = i + len("realData:")
depth = 0
for k in range(j, len(s)):
    if s[k] == "{":
        depth += 1
    elif s[k] == "}":
        depth -= 1
        if depth == 0:
            break
assert "NCT02220725" in s[j:k + 1], "unexpected ledger content"
s = s[:j] + "{}" + s[k + 1:]

s = replace_verdict(s, V1, "\nwindow.__quarantinedTrials = "
                    + json.dumps(QUAR1, ensure_ascii=False) + ";")
s = replace_badge(s, BADGE1)
write(F1, s, bom)
print(f"{F1}: {before} -> {len(s)} chars (BOM preserved: {bom})")
print("  - identity corrected to andexanet alfa; filename/URL unchanged")
print("  - impossible HR removed: all 6 HR fields null on all 3 rows")
print("  - pooled RR 0.06 (0.01-0.21) withdrawn; 3 rows quarantined")
print("  - ANNEXA-I genuine estimand recorded (OR 1.7925, 1.2246-2.6238) - not pooled")

# ---- stub ----
t, tbom = read(S1)
tb = len(t)
assert "__verdict" not in t, "stub already carries a verdict"
stub_badge = (
    f'<div id="rapidmeta-integrity-badge" role="status" {BADGE_CSS}>'
    '<strong style="font-size:14px;letter-spacing:0.04em;">IDENTITY CORRECTED &mdash; '
    'THIS IS A REVIEW OF ANDEXANET ALFA</strong>'
    '<div style="margin-top:6px;font-size:12.5px;">This page&rsquo;s filename and URL say '
    '<em>TIRZEPATIDE_ARDS</em>; it is a review of <strong>andexanet alfa</strong> for '
    'factor-Xa-inhibitor reversal, and contains no tirzepatide or ARDS trial. The filename is '
    'kept so existing links keep working. Its previously displayed pooled estimate '
    '(RR 0.06) has been <strong>withdrawn</strong> and an impossible hazard ratio (lower CI '
    '&minus;0.5509) removed. See the full review. AMSTAR-2 confidence: '
    '<strong>CRITICALLY LOW</strong>.</div></div>\n'
)
stub_v = {"verdict": "UNCERTAIN", "preliminary": True,
          "identity_correction": V1["identity_correction"],
          "counts": {"n_trials_in_ledger": 0, "n_trials_quarantined": 3, "n_trials_seen": 0},
          "reasons": ["Redirect stub. Mirrors TIRZEPATIDE_ARDS_AUTO_FULL_REVIEW.html: a review of "
                      "andexanet alfa; pooled estimate withdrawn; impossible hazard ratio removed; "
                      "3 rows quarantined."],
          "p0_total": None, "pooled": None}
m = re.search(r"<body[^>]*>", t)
assert m, "stub has no <body>"
t = (t[:m.end()] + "\n" + stub_badge
     + "<script>window.__verdict = " + json.dumps(stub_v, ensure_ascii=False) + ";</script>\n"
     + t[m.end():])
write(S1, t, tbom)
print(f"{S1}: {tb} -> {len(t)} chars (badge + __verdict added; had neither)")

# ==========================================================================
# APP 2 - ICAGEN_AUTO_FULL_REVIEW.html  =  EDOXABAN
# Identity + badge honesty ONLY. No number is changed.
# ==========================================================================
print()
F2, S2 = "ICAGEN_AUTO_FULL_REVIEW.html", "ICAGEN_AUTO_REVIEW.html"
s, bom = read(F2)
before = len(s)

V2 = {
    "verdict": "UNCERTAIN",
    "preliminary": True,
    "identity_correction": {
        "file_and_url_say": "ICAGEN",
        "actual_subject": "edoxaban",
        "filename_retained": True,
        "why": "The .html filename and its published URL are deliberately unchanged - renaming "
               "would break every existing link. The displayed identity is corrected instead.",
        "note": "'Icagen' is a company name, not a drug and not an indication. This app contains "
                "no icagen trial.",
    },
    "counts": {"n_trials_in_ledger": 3, "n_trials_analysed": 3, "n_trials_seen": 3,
               "P0_internal": None, "P0_grim": None, "P1_aact_concord": None,
               "P2_evidence_incomplete": 3},
    "counts_note": "Gate counts are null, not zero. No per-trial data-integrity gate has been run "
                   "against this app; a zero would read as a clean bill.",
    "reasons": [
        "IDENTITY CORRECTED. This page is a review of EDOXABAN. Its filename and URL say ICAGEN - "
        "a company name, not a drug or an indication - and are retained unchanged so existing "
        "links keep working.",
        "THE DISPLAYED POOLED ESTIMATE IS UNVERIFIED. The page shows RR 0.52 (0.33-0.84). No "
        "per-trial source verification has been run against this app, and the figure should not "
        "be cited.",
        "DECLARED SUBJECT DOES NOT MATCH THE EVIDENCE. The page calls itself 'Edoxaban TIMI 48 "
        "cancer-VTE'. Not one of its three trials is a cancer-VTE trial or ENGAGE AF-TIMI 48: "
        "NCT02798471 is the Hokusai study in PAEDIATRIC VTE patients; NCT01181102 and NCT01181141 "
        "are edoxaban VTE prophylaxis after orthopaedic surgery. Verified against "
        "ClinicalTrials.gov API v2, " + RETRIEVED + ".",
        "REGISTRY DISCREPANCY FOUND IN A SPOT-CHECK, recorded not corrected: for NCT02798471 the "
        "posted primary is edoxaban 5/145 vs standard of care 2/141, while this ledger carries "
        "0/147 vs 1/143. Neither the counts nor the denominators agree. This row alone therefore "
        "cannot be relied on, and the pooled figure rests partly on it.",
        "NO NUMBER HAS BEEN CHANGED IN THIS PASS. A data correction requires its own source "
        "verification and cross-family gate; this commit corrects the identity and replaces a "
        "false 'INTERNAL CHECKS PASSED' badge, nothing more.",
        "AMSTAR-2 confidence: CRITICALLY LOW.",
    ],
    "p0_total": None,
    "p0_total_note": "null, not 0 - no gate has been run against this app.",
    "pooled": {"displayed": "RR 0.52 (0.33-0.84)",
               "status": "UNVERIFIED - do not cite. At least one contributing row disagrees with "
                         "its own registry source."},
}

BADGE2 = (
    f'<div id="rapidmeta-integrity-badge" role="status" {BADGE_CSS}>'
    '<div style="display:flex;align-items:center;gap:12px;flex-wrap:wrap;">'
    '<strong style="font-size:14px;letter-spacing:0.04em;">IDENTITY CORRECTED &mdash; '
    'THIS IS A REVIEW OF EDOXABAN</strong>'
    '<span style="font-size:11.5px;">Trials: <strong>3</strong> &middot; Pooled estimate: '
    '<strong>UNVERIFIED</strong> &middot; Integrity gates: <strong>not run</strong></span></div>'

    f'<div {NOTE_CSS}>'
    '<strong>Correction &mdash; this page&rsquo;s address does not match its contents.</strong> '
    'The file is named <code style="background:rgba(255,255,255,0.28);padding:1px 4px;'
    'border-radius:2px;">ICAGEN_AUTO_FULL_REVIEW.html</code> and its published URL says the same. '
    '&ldquo;Icagen&rdquo; is a <em>company name</em>, not a drug and not an indication. '
    '<strong>This is a review of edoxaban.</strong> '
    '<em>The filename and URL are deliberately left unchanged so that existing links keep '
    'working; only the displayed identity is corrected.</em></div>'

    '<div style="margin-top:6px;font-size:12.5px;">'
    '<strong>The pooled estimate on this page is UNVERIFIED &mdash; do not cite it.</strong> The '
    'page displays <strong>RR 0.52 (0.33&ndash;0.84)</strong>. No per-trial source verification '
    'and no data-integrity gate has been run against this app. The previous badge claimed '
    '&ldquo;INTERNAL CHECKS PASSED&rdquo;; that claim was false and has been removed.</div>'

    '<div style="margin-top:6px;font-size:11.5px;">'
    '<strong>The declared subject does not match the evidence.</strong> This page calls itself '
    '&ldquo;Edoxaban TIMI 48 cancer-VTE&rdquo;. <strong>Not one</strong> of its three trials is a '
    'cancer-VTE trial or ENGAGE AF-TIMI 48. Verified against ClinicalTrials.gov API v2 on '
    f'{RETRIEVED}: <strong>NCT02798471</strong> is the Hokusai study in <em>paediatric</em> VTE '
    'patients; <strong>NCT01181102</strong> and <strong>NCT01181141</strong> are edoxaban VTE '
    'prophylaxis after <em>orthopaedic surgery</em>.</div>'

    '<div style="margin-top:6px;font-size:11.5px;">'
    '<strong>A registry spot-check already disagrees with this ledger.</strong> For '
    'NCT02798471 the posted primary outcome is <strong>edoxaban 5/145 vs standard of care '
    '2/141</strong>; this page&rsquo;s ledger carries <strong>0/147 vs 1/143</strong>. Neither the '
    'counts nor the denominators agree. That row cannot be relied on, and the pooled figure above '
    'rests partly on it.</div>'

    '<div style="margin-top:6px;font-size:10.5px;">'
    '<strong>What this commit did and did not do.</strong> It corrected the displayed identity and '
    'replaced a false green &ldquo;INTERNAL CHECKS PASSED&rdquo; badge. <strong>No number was '
    'changed.</strong> Correcting the data requires full per-trial source verification and a '
    'cross-family gate, as was done for the apixaban-in-ACS review; that work is not in this '
    'commit and the figures above remain unverified until it is. Gate counts in '
    '<code style="background:rgba(255,255,255,0.28);padding:1px 4px;border-radius:2px;">'
    'window.__verdict</code> are <strong>null, not zero</strong> &mdash; nothing was tested. '
    'AMSTAR-2 confidence: <strong>CRITICALLY LOW</strong>.</div></div>'
)

s = replace_verdict(s, V2)
s = replace_badge(s, BADGE2)
write(F2, s, bom)
print(f"{F2}: {before} -> {len(s)} chars (BOM preserved: {bom})")
print("  - identity corrected to edoxaban; filename/URL unchanged")
print("  - false-green badge replaced; pooled RR 0.52 marked UNVERIFIED")
print("  - PICO mismatch + NCT02798471 registry discrepancy recorded; NO number changed")

t, tbom = read(S2)
tb = len(t)
assert "__verdict" not in t, "stub already carries a verdict"
stub_badge2 = (
    f'<div id="rapidmeta-integrity-badge" role="status" {BADGE_CSS}>'
    '<strong style="font-size:14px;letter-spacing:0.04em;">IDENTITY CORRECTED &mdash; '
    'THIS IS A REVIEW OF EDOXABAN</strong>'
    '<div style="margin-top:6px;font-size:12.5px;">This page&rsquo;s filename and URL say '
    '<em>ICAGEN</em> &mdash; a company name, not a drug. It is a review of '
    '<strong>edoxaban</strong>. The filename is kept so existing links keep working. Its pooled '
    'estimate is <strong>UNVERIFIED</strong> and its declared subject '
    '(&ldquo;TIMI 48 cancer-VTE&rdquo;) matches none of its trials. See the full review. '
    'AMSTAR-2 confidence: <strong>CRITICALLY LOW</strong>.</div></div>\n'
)
stub_v2 = {"verdict": "UNCERTAIN", "preliminary": True,
           "identity_correction": V2["identity_correction"],
           "counts": {"n_trials_seen": 3},
           "reasons": ["Redirect stub. Mirrors ICAGEN_AUTO_FULL_REVIEW.html: a review of edoxaban; "
                       "pooled estimate UNVERIFIED; declared subject matches none of its trials."],
           "p0_total": None,
           "pooled": {"displayed": "RR 0.52 (0.33-0.84)", "status": "UNVERIFIED - do not cite"}}
m = re.search(r"<body[^>]*>", t)
assert m, "stub has no <body>"
t = (t[:m.end()] + "\n" + stub_badge2
     + "<script>window.__verdict = " + json.dumps(stub_v2, ensure_ascii=False) + ";</script>\n"
     + t[m.end():])
write(S2, t, tbom)
print(f"{S2}: {tb} -> {len(t)} chars (badge + __verdict added; had neither)")


# ==========================================================================
# Returning-visitor safety: purge quarantined rows from PERSISTED state.
#
# Emptying realData stops a FRESH visitor pooling the withdrawn rows, but the
# app persists state.trials to localStorage. A reader who opened this page
# before the fix keeps the old auto-seeded rows and would still be shown a
# pooled estimate computed from them - verified in the browser: a stale profile
# still rendered RR 0.03 (0.00-0.52) after realData was emptied.
#
# Added as a normal guarded migration, matching the app's existing chain. The
# row's data is MOVED to _quarantinedData, not destroyed - quarantine, never
# delete - and the row is excluded with a stated reason.
# ==========================================================================
MIG_ANCHOR = ('if(this.state.trials?.length&&!this.state._migrated_v120_phase2_exclusion){')
MIGRATION = (
    'if(this.state.trials?.length&&!this.state._migrated_v123_quarantine_purge){'
    'let mutated=!1;'
    'const QIDS=new Set(Object.keys(window.__quarantinedTrials||{}));'
    'this.state.trials.forEach(t=>{'
    'if(!QIDS.has(String(t?.id??"").toUpperCase()))return;'
    'if(t.data){t._quarantinedData=t.data;t.data=null;mutated=!0}'
    'if("exclude"!==String(t?.status??"").toLowerCase()){t.status="exclude";mutated=!0}'
    't.verified=!1;t.screenReview=null;'
    't.reason="Quarantined 2026-07-30: registry verification could not support this row. '
    'Its stored values are retained in _quarantinedData and described in '
    'window.__quarantinedTrials.";'
    '}),this.state._migrated_v123_quarantine_purge=!0,mutated&&this.save()}'
)

s, bom = read(F1)
before = len(s)
assert s.count(MIG_ANCHOR) == 1, f"migration anchor count = {s.count(MIG_ANCHOR)}"
s = s.replace(MIG_ANCHOR, MIGRATION + MIG_ANCHOR, 1)
write(F1, s, bom)
print()
print(f"{F1}: {before} -> {len(s)} chars")
print("  - migration _migrated_v123_quarantine_purge added: returning visitors with stale")
print("    localStorage also stop pooling the quarantined rows (data retained, not destroyed)")
