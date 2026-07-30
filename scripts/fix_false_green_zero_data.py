"""Kill the false green badge on the two cardio apps that ship ZERO trials.

EZETIMIBE_LIPID_AUTO_FULL_REVIEW.html and LISINOPRIL_HTN_AUTO_FULL_REVIEW.html
both render a green "INTERNAL CHECKS PASSED - Fabrication-risk 0.275 - Trials: 2"
badge, and both carry window.__verdict = {"verdict":"STABLE","n_trials_seen":2}.

Verified in a live browser render, not inferred from the file:
    realData                = {}          (0 trials)
    trials with status include = 0
    getAnalysisScopeDetails().analyzed = 0
    state.results           = null
    the displayed pooled estimate = "--"

So BOTH verdict surfaces are false, in the same direction, and they agree with
each other only because both are app-shell boilerplate inherited from a 2-trial
clone. Neither describes the page it sits on. A green pass over an empty ledger
is the most load-bearing false claim a page can make: it certifies nothing as
something.

Both surfaces are replaced together with the same truth - no data, therefore no
pass. The counts are not zeroed and left otherwise intact, because "0 findings"
on an empty ledger reads as a clean bill; the verdict says NO_DATA and every
gate is reported as NOT APPLICABLE rather than as a zero.
"""
import io
import json
import re
import sys

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

APPS = [
    {
        "file": "EZETIMIBE_LIPID_AUTO_FULL_REVIEW.html",
        "subject": "ezetimibe in hyperlipidaemia",
        "storage": "rapid_meta_ezetimibe_lipid_auto_v1_0",
    },
    {
        "file": "LISINOPRIL_HTN_AUTO_FULL_REVIEW.html",
        "subject": "lisinopril in hypertension",
        "storage": "rapid_meta_lisinopril_htn_auto_v1_0",
    },
]


def build_verdict(subject):
    return {
        "verdict": "NO_DATA",
        "counts": {
            "n_trials_in_ledger": 0,
            "n_trials_analysed": 0,
            "P0_internal": None,
            "P0_aact_nct_missing": None,
            "P0_grim": None,
            "P1_aact_concord": None,
            "P1_fi_critical": None,
            "P1_fi_warn": None,
            "P1_pi_gap": None,
            "P2_evidence_incomplete": None,
            "P2_aact_advisory": None,
            "n_trials_seen": 0,
        },
        "counts_note": (
            "Every gate count is null, not zero. There is no evidence in this app to "
            "test, so no gate ran. A zero here would read as a clean bill."
        ),
        "reasons": [
            "This app contains NO trial data. realData is empty, no trial is marked for "
            "inclusion, no analysis is produced, and the pooled estimate renders as '--'.",
            "The previous visible badge read 'INTERNAL CHECKS PASSED - Fabrication-risk "
            "score 0.275 - Trials: 2' in green, and this same window.__verdict object read "
            "'STABLE' with n_trials_seen 2. Both were app-shell boilerplate inherited from "
            "a 2-trial clone. Neither described this page. There were never 2 trials here.",
            "No integrity gate has run or could run: GRIM/GRIMMER, Benford, registry "
            "concordance, fragility index and arm-orientation checks all require per-arm "
            "data that does not exist in this file.",
            f"Nothing on this page may be cited as evidence about {subject}.",
            "AMSTAR-2 confidence: not assessable - there is no review to appraise.",
        ],
        "p0_total": None,
        "p0_total_note": (
            "null, not 0. No P0 check executed, because there is nothing to check."
        ),
        "pooled": None,
        "pooled_note": "No pooled estimate exists. The app displays '--'.",
    }


def build_badge(subject):
    return (
        '<div id="rapidmeta-integrity-badge" role="status" '
        'style="background:#7c2d12;color:#fff;padding:12px 20px;font-family:system-ui,sans-serif;'
        'font-size:13.5px;border-bottom:3px solid #431407;line-height:1.55;">'
        '<div style="display:flex;align-items:center;gap:12px;flex-wrap:wrap;">'
        '<strong style="font-size:14px;letter-spacing:0.04em;">NO DATA '
        '&mdash; THIS IS NOT AN INTEGRITY PASS</strong>'
        '<span style="font-size:11.5px;">Trials in ledger: <strong>0</strong> &middot; '
        'Trials analysed: <strong>0</strong> &middot; Pooled estimate: '
        '<strong>none</strong></span></div>'
        '<div style="margin-top:6px;font-size:12.5px;">'
        'This app contains <strong>no trial data</strong>. Its evidence ledger is empty, no '
        'trial is marked for inclusion, and the pooled estimate renders as &ldquo;--&rdquo;. '
        f'<strong>Nothing on this page may be cited as evidence about {subject}.</strong>'
        '</div>'
        '<div style="margin-top:6px;font-size:11.5px;">'
        '<strong>What this badge used to say, and why it was wrong.</strong> It read '
        '&ldquo;INTERNAL CHECKS PASSED &middot; Fabrication-risk score 0.275 &middot; '
        'Trials: 2&rdquo; on a green background, and the page&rsquo;s '
        '<code style="background:rgba(255,255,255,0.28);padding:1px 4px;border-radius:2px;">'
        'window.__verdict</code> agreed with it &mdash; &ldquo;STABLE&rdquo;, '
        '<em>n_trials_seen: 2</em>. Both were app-shell boilerplate inherited from a '
        'two-trial clone. <strong>There were never two trials in this app.</strong> The two '
        'surfaces agreed with each other and both were false; that is why agreement between '
        'them is checked against the ledger, not against each other.</div>'
        '<div style="margin-top:6px;font-size:10.5px;">'
        '<strong>No gate has run, and none could.</strong> GRIM/GRIMMER, Benford, '
        'ClinicalTrials.gov registry concordance, fragility index and arm-orientation checks '
        'all require per-arm counts that do not exist in this file. Every gate count in '
        '<code style="background:rgba(255,255,255,0.28);padding:1px 4px;border-radius:2px;">'
        'window.__verdict</code> is <strong>null, not zero</strong> &mdash; a zero would read '
        'as a clean bill, and absence of testing is not absence of defects. AMSTAR-2 '
        'confidence: <strong>not assessable</strong>; there is no review here to appraise.'
        '</div></div>'
    )


for app in APPS:
    path, subject = app["file"], app["subject"]
    s = open(path, encoding="utf-8").read()
    before = len(s)

    # Fail closed if the app is not actually empty.
    m = re.search(r"realData:\{\}", s)
    assert m, f"{path}: realData is NOT empty - refusing to write a NO_DATA badge"
    assert "AUTO_INCLUDE_TRIAL_IDS=new Set([])" in s, f"{path}: AUTO_INCLUDE is not empty"
    assert '"data/realData.json"' not in s, f"{path}: carries an embedded data blob"

    # ---- surface 1: window.__verdict ----
    old_v = re.search(r"<script>window\.__verdict = \{.*?\};</script>", s)
    assert old_v, f"{path}: no __verdict surface found"
    s = s.replace(
        old_v.group(0),
        "<script>window.__verdict = "
        + json.dumps(build_verdict(subject), ensure_ascii=False)
        + ";</script>",
        1,
    )

    # ---- surface 2: the visible badge ----
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
    old_badge = s[st:k]
    assert "INTERNAL CHECKS PASSED" in old_badge, f"{path}: badge is not the false-green one"
    s = s[:st] + build_badge(subject) + s[k:]

    open(path, "w", encoding="utf-8", newline="").write(s)
    print(f"{path}: {before} -> {len(s)} bytes")
    print("  - window.__verdict  STABLE / n_trials_seen 2  ->  NO_DATA / 0, gate counts null")
    print("  - visible badge     green INTERNAL CHECKS PASSED / Trials: 2  ->  NO DATA (not a pass)")


# ---------------------------------------------------------------------------
# Pre-existing base-engine contamination, identical in both apps.
# The contamination gate returns the SAME 4 HARD findings against the
# unmodified files at HEAD, so none of this was introduced by the badge fix.
# These apps hold no trials at all, so the honest alias table is the empty one.
# ---------------------------------------------------------------------------
OLD_ALIASES = (
    'const KNOWN_TRIAL_ALIASES={NCT01035255:["paradigm-hf","paradigm"],'
    'NCT01920711:["paragon-hf","paragon"],NCT02924727:["paradise-mi","paradise"],'
    'NCT03988634:["paraglide-hf","paraglide"]}'
)
OLD_NMA = (
    'trialData=["NCT01035255","NCT01920711","NCT02924727"]'
    ".filter(id=>!RapidMeta.state.excludedTrials?.[id])"
)
NEW_NMA = (
    "trialData=Object.keys(RapidMeta.realData??{})"
    ".filter(id=>!RapidMeta.state.excludedTrials?.[id])"
)

for app in APPS:
    path = app["file"]
    s = open(path, encoding="utf-8").read()
    before = len(s)
    notes = []
    if s.count(OLD_ALIASES) == 1:
        # Older lineage: table still holds the sacubitril/valsartan HF trials.
        s = s.replace(OLD_ALIASES, "const KNOWN_TRIAL_ALIASES={}", 1)
        notes.append("KNOWN_TRIAL_ALIASES: PARADIGM/PARAGON/PARADISE/PARAGLIDE -> {} (this app has no trials)")
    elif "const KNOWN_TRIAL_ALIASES={}" in s:
        # main already purged it (5e63960c9). Leave it empty - that purge IS the
        # anti-contamination fix, and an app holding zero trials has no aliases
        # of its own to resolve, so there is nothing that could need re-adding.
        notes.append("KNOWN_TRIAL_ALIASES: already EMPTY on main (5e63960c9) - left empty, main's fix preserved")
    else:
        raise AssertionError(f"{path}: KNOWN_TRIAL_ALIASES in an unrecognised state")

    if s.count(OLD_NMA) == 1:
        s = s.replace(OLD_NMA, NEW_NMA, 1)
        notes.append("NMAEngine.run: hardcoded HF trial list -> derived from this app's realData")
    elif NEW_NMA in s:
        notes.append("NMAEngine.run: already derived from realData - no change")
    else:
        raise AssertionError(f"{path}: NMAEngine trialData in an unrecognised state")

    open(path, "w", encoding="utf-8", newline="").write(s)
    print(f"{path}: {before} -> {len(s)} bytes")
    for n in notes:
        print("  - " + n)


# ---------------------------------------------------------------------------
# The LISINOPRIL redirect stub carries NEITHER verdict surface - the same defect
# as the APIXABAN stub. Same app, two files, one previously asserting PASSED and
# one asserting nothing. Give it both, agreeing with the full app.
# (EZETIMIBE_LIPID has no stub variant.)
# ---------------------------------------------------------------------------
STUB = "LISINOPRIL_HTN_AUTO_REVIEW.html"
s = open(STUB, encoding="utf-8").read()
if "__verdict" in s:
    print(f"{STUB}: already carries a verdict surface - skipped")
else:
    before = len(s)
    banner = (
        '<div id="rapidmeta-integrity-badge" role="status" '
        'style="background:#7c2d12;color:#fff;padding:12px 20px;font-family:system-ui,sans-serif;'
        'font-size:13.5px;border-bottom:3px solid #431407;line-height:1.55;">'
        '<strong style="font-size:14px;letter-spacing:0.04em;">NO DATA '
        '&mdash; THIS IS NOT AN INTEGRITY PASS</strong>'
        '<div style="margin-top:6px;font-size:12.5px;">This app contains '
        '<strong>no trial data</strong> &mdash; 0 trials in the ledger, 0 analysed, no '
        'pooled estimate. Nothing on it may be cited as evidence about lisinopril in '
        'hypertension. The full review previously showed a green &ldquo;INTERNAL CHECKS '
        'PASSED &middot; Trials: 2&rdquo; badge over an empty ledger; that claim has been '
        'removed.</div></div>\n'
    )
    verdict_js = (
        '<script>window.__verdict = {"verdict":"NO_DATA","counts":{"n_trials_in_ledger":0,'
        '"n_trials_analysed":0,"n_trials_seen":0},"reasons":["Redirect stub. Verdict mirrors '
        'LISINOPRIL_HTN_AUTO_FULL_REVIEW.html: this app holds no trial data, so no gate ran '
        'and no pooled estimate exists. The previous green pass badge was app-shell '
        'boilerplate from a 2-trial clone."],"p0_total":null,"p0_total_note":"null, not 0. '
        'Nothing was checked because there is nothing to check.","pooled":null};</script>\n'
    )
    m = re.search(r"<body[^>]*>", s)
    assert m, f"{STUB}: no <body> tag"
    s = s[:m.end()] + "\n" + banner + verdict_js + s[m.end():]
    open(STUB, "w", encoding="utf-8", newline="").write(s)
    print(f"{STUB}: {before} -> {len(s)} bytes  (badge + __verdict added; had neither)")
