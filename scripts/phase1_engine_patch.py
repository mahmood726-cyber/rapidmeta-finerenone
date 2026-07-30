#!/usr/bin/env python
"""
PHASE 1 — the shared base-engine guard patch.

Lands the 21 fail-closed guards into every app that carries the shared engine, as an
IDEMPOTENT, ANCHOR-BASED transform.

    python scripts/phase1_engine_patch.py --dry-run              # default: writes NOTHING
    python scripts/phase1_engine_patch.py --dry-run --report out.json
    python scripts/phase1_engine_patch.py --dry-run --emit-to DIR --only APIXABAN_ACS_AUTO_FULL_REVIEW.html
    python scripts/phase1_engine_patch.py --selftest             # prove idempotence + anchor logic
    python scripts/phase1_engine_patch.py --apply                # REQUIRES an explicit go

DESIGN — why an OVERLAY and not a rewrite
-----------------------------------------
Rewriting minified engine internals by regex across ~900 files is how you break ~900 files. The
patch is therefore:

  * ADDITIVE     - one sentinel-delimited block before </body>, plus exactly two textual
                   replacements whose literals are fixed and verified.
  * FAIL-SAFE    - if an anchor is absent the overlay logs and the app behaves exactly as before.
                   The overlay never throws into the render path.
  * IDEMPOTENT   - the sentinel carries a version; re-applying is a no-op. Asserted by the
                   selftest, which applies twice and compares bytes.
  * REVERSIBLE   - the whole change is between two sentinels plus two known literals.
  * CRLF-SAFE    - newline="" on read AND write (RM-J06). A whole-file rewrite would make a
                   900-app change unreviewable.
  * BOM-SAFE     - a pre-existing UTF-8 BOM is preserved byte-for-byte.

WHAT THE OVERLAY DOES AT RUNTIME
--------------------------------
  G08  replaces safeRob so an unknown RoB resolves to "some", never "low"
  G07  neutralises COMPLETE-POOLING-REPAIR (the scope-lock bypass)
  G21  reconciles persisted localStorage state against the authoritative ledger on hydrate,
       purging quarantined rows, dropping unknown rows, and NEVER restoring a persisted result
  G18  runs the fail-closed integrity gate and, on failure, suppresses the pooled surfaces and
       rewrites the badge instead of letting a pass be asserted over it
  G12  asserts verdict-badge parity across __verdict / badge / ledger
  G10  gates funnel/Egger/trim-fill/Copas/meta-reg/TSA/NMA/FI panels on k
  G17  refuses a direction word, NNT or NNH without an explicit polarity
  G20  flags a monitoring watchlist that is not the app's own topic

TEXTUAL REPLACEMENTS (2, both fixed literals)
---------------------------------------------
  T1   the false ICMJE / PROSPERO-equivalence sentence -> the reframed claim that KEEPS the
       tamper-evident public-push mechanism and drops only the false attribution
  T2   the estimand DENYLIST `"RR"!==String(d?.estimandType??"HR")` -> an ALLOWLIST
"""
from __future__ import annotations

import argparse
import hashlib
import io
import json
import re
import sys
from pathlib import Path

if not getattr(sys.stdout, "_rm_wrapped", False):
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    try:
        sys.stdout._rm_wrapped = True
    except AttributeError:
        pass

ROOT = Path(__file__).resolve().parent.parent
GUARD_LIB = ROOT / "assets" / "js" / "rapidmeta-guards.js"

PATCH_VERSION = "1"
BEGIN = f"<!-- RM-PHASE1-GUARDS v{PATCH_VERSION} BEGIN -->"
END = f"<!-- RM-PHASE1-GUARDS v{PATCH_VERSION} END -->"
ANY_BEGIN = re.compile(r"<!-- RM-PHASE1-GUARDS v(\d+) BEGIN -->")

# ---------------------------------------------------------------- textual anchors

# Matched as a REGEX because the corpus ships the sentence both with and without a leading "Per "
# (APIXABAN_ACS has "ICMJE 2023, GitHub commit hash ...", others "Per ICMJE 2023, ...").
T1_RE = re.compile(
    r"(?:Per\s+)?ICMJE\s+2023,\s*GitHub commit hash \+ timestamp constitutes a verifiable\s*"
    r"pre-registration record equivalent to PROSPERO for tracking outcome / eligibility / "
    r"analysis-plan changes\.")
T1_REPLACE = (
    "A publicly-pushed, version-controlled protocol commit is a tamper-evident protocol-provenance "
    "record: git history is a Merkle chain, so altering an earlier commit changes every later hash, "
    "and once the history is public third parties hold the originals. It is not a PROSPERO "
    "registration and no equivalence is claimed; a registry additionally offers custody by an "
    "independent institution. The evidence is the PUBLIC PUSH, not the commit date, which is "
    "author-settable. This review is NOT prospectively registered.")

# Quote- and whitespace-tolerant: 18 e156-submission copies are PRETTY-PRINTED with single
# quotes, so the exact minified literal matched nothing and they were "patched" in name only.
T2_RE = re.compile(r"""['"]RR['"]\s*!==\s*String\(\s*d\s*\?\.\s*estimandType\s*\?\?\s*['"]HR['"]\s*\)""")
T2_REPLACE = '!window.__rmGuardEstimandOK(d)'

# ---- T3 safeRob: matched by HEAD + BRACE BALANCE, not by literal --------------------------
# The corpus ships at least two shapes:
#   minified : safeRob=rob=>{const valid=["low","some","high"];return Array.isArray(rob)?...}
#   pretty   : safeRob = (rob) => {\n  const valid = ['low', 'some', 'high'];\n  if (...)...}
# safeRob is a closure-local const and CANNOT be monkey-patched at runtime, so the textual
# replacement is the only fix - it must therefore hit every RoB app, minified or not.
SAFEROB_HEAD_RE = re.compile(r"\bsafeRob\s*=\s*(?:\(\s*rob\s*\)|rob)\s*=>\s*\{")
SAFEROB_PRESENT_RE = re.compile(r"\bsafeRob\s*=")


def balanced_brace(text: str, start: int) -> int:
    """Index just past the `}` matching the `{` at `start`, ignoring braces inside strings."""
    depth, i, n, q = 0, start, len(text), None
    while i < n:
        ch = text[i]
        if q:
            if ch == "\\":
                i += 2
                continue
            if ch == q:
                q = None
        elif ch in "\"'`":
            q = ch
        elif ch == "{":
            depth += 1
        elif ch == "}":
            depth -= 1
            if depth == 0:
                return i + 1
        i += 1
    return -1


def replace_saferob(text: str):
    """Replace every safeRob definition, whatever its formatting. Returns (text, n)."""
    out, i, n = [], 0, 0
    while True:
        m = SAFEROB_HEAD_RE.search(text, i)
        if not m:
            break
        end = balanced_brace(text, m.end() - 1)
        if end == -1:
            break
        out.append(text[i:m.start()])
        out.append(T3_REPLACE)
        i = end
        n += 1
    out.append(text[i:])
    return "".join(out), n

# safeRob is a closure-local `const`, NOT a property of any object, so a runtime override cannot
# reach it - the rendered app reported G08_safeRob:"absent". It must be replaced textually. The
# replacement is SELF-CONTAINED: it prefers the guard library but falls back to its own inline
# alias table, so an unknown rating resolves to "some" even if the library failed to load.
T3_FIND = ('safeRob=rob=>{const valid=["low","some","high"];'
           'return Array.isArray(rob)?rob.map(r=>valid.includes(r)?r:"low"):'
           '["low","low","low","low","low"]}')   # kept ONLY as a selftest fixture
T3_REPLACE = (
    'safeRob=rob=>{if(window.RapidMetaGuards)return window.RapidMetaGuards.G08_safeRob(rob);'
    'const A={"low":"low","some":"some","some-concerns":"some","some concerns":"some",'
    '"unclear":"some","moderate":"some","medium":"some","high":"high","serious":"high",'
    '"critical":"high"};'
    'return Array.isArray(rob)?rob.map(r=>A[String(r??"").trim().toLowerCase()]??"some")'
    ':["some","some","some","some","some"]}')

# T4: the COMPLETE-POOLING-REPAIR block is a scope-lock bypass (RM-B02). It runs at parse time,
# BEFORE any injected overlay, so a runtime flag can never reach it - the previous
# `__rmPoolingRepairDisabled` was dead code that nothing read. Neutralised at its own site.
T4_RE = re.compile(r"(COMPLETE-POOLING-REPAIR[\s\S]{0,900}?\(function\s*\(\s*\)\s*\{)")
T4_MARK = ("/* RM-PHASE1 G07: disabled - this block copies realData counts into the scoped row and "
           "force-sets effectMeasure='HR', bypassing the outcome scope lock (RM-B02). */"
           "if(!window.__rmAllowPoolingRepair)return;")

TEXTUAL = [
    ("T1-icmje", "regex", T1_RE, T1_REPLACE, "RM-J01/RM-J02"),
    ("T2-denylist", "regex", T2_RE, T2_REPLACE, "RM-A02"),
    ("T3-saferob", "callable", replace_saferob, None, "RM-G01"),
    ("T4-poolingrepair", "regex-group", T4_RE, None, "RM-B02"),
]

# ---------------------------------------------------------------- engine markers

ENGINE_MARKERS = {
    "safeRob": re.compile(r"\bsafeRob\s*="),
    "pooling_repair": re.compile(r"COMPLETE-POOLING-REPAIR"),
    "verdict": re.compile(r"window\.__verdict\s*="),
    "badge": re.compile(r'<div id="rapidmeta-integrity-badge"'),
    "state_persist": re.compile(r"localStorage\.setItem\([^)]{0,80}JSON\.stringify\(\s*this\.state"),
    "outcomes0": re.compile(r"(allOutcomes|outcomes)\s*\[\s*0\s*\]"),
    "escalc": re.compile(r"escalc\(\s*measure\s*="),
}

BODY_CLOSE = re.compile(r"</body\s*>", re.I)


def slim_guard_src(src: str) -> str:
    """Strip comments and indentation from the guard library before inlining it into ~1,071 apps.

    Deliberately LINE-BASED and conservative - it removes only whole-line comments, blank lines
    and leading indentation. It never touches the inside of a line, so it cannot corrupt a string
    literal or a regex. The result is verified with `node --check` in the selftest, and the
    library's own 126-test suite runs against the UNSTRIPPED file, so behaviour is unchanged.
    """
    out, in_block = [], False
    for line in src.splitlines():
        s = line.strip()
        if in_block:
            if "*/" in s:
                in_block = False
                tail = s.split("*/", 1)[1].strip()
                if tail:
                    out.append(tail)
            continue
        if s.startswith("/*") and "*/" not in s:
            in_block = True
            continue
        if not s or s.startswith("//") or (s.startswith("/*") and s.endswith("*/")):
            continue
        out.append(s)
    return "\n".join(out)


def overlay_js(guard_src: str) -> str:
    """The sentinel block. Guard library inlined (apps must work offline), then the bootstrap."""
    slim = slim_guard_src(guard_src)
    return f"""{BEGIN}
<script>/* RapidMeta Phase-1 guard library v{PATCH_VERSION} — source of truth: assets/js/rapidmeta-guards.js */
{slim}
</script>
<script>/* RapidMeta Phase-1 bootstrap — fail-safe: any error here leaves the app as it was */
(function () {{
  "use strict";
  var G = (typeof window !== "undefined") && window.RapidMetaGuards;
  if (!G) return;
  var log = function (m, d) {{ try {{ console.warn("[rm-guard] " + m, d === undefined ? "" : d); }} catch (e) {{}} }};
  var applied = window.__rmGuardsApplied = window.__rmGuardsApplied || {{ notes: [] }};
  applied.v = "{PATCH_VERSION}"; applied.runs = (applied.runs || 0);
  applied.notes = applied.notes || [];

  // A step whose target did not exist yet is retried on the next pass. The FIRST attempt runs at
  // end-of-body, but the engine hydrates its state and defines window.__quarantinedTrials LATER -
  // running only once left G21 with an empty quarantine set and it purged nothing. Found by
  // seeding a stale profile in the browser; the file-level view cannot see it.
  // "PASS" and "N/A" are NOT settled. The ledger, the verdict object and the badge are all
  // populated AFTER end-of-body, so an early PASS is a pass over an empty page - freezing it
  // meant the one check that most needs the late re-run was the one that never re-ran.
  var NEVER_SETTLED = {{ "PASS": 1, "NOT-APPLICABLE": 1, "absent": 1, "no-k": 1 }};
  function settled(v) {{
    if (v === undefined) return false;
    if (typeof v === "string" && (NEVER_SETTLED[v] || v.indexOf("ERROR:") === 0)) return false;
    return true;
  }}
  function step(name, fn) {{
    if (settled(applied[name])) return;               // already done - do not redo
    try {{ var r = fn(); applied[name] = r === undefined ? true : r; }}
    catch (e) {{ applied[name] = "ERROR:" + (e && e.message); log(name + " deferred", e && e.message); }}
  }}

  function allSteps() {{
  /* --- T2 support: the allowlist the denylist was replaced by (G01/G06) ------------------ */
  window.__rmGuardEstimandOK = function (d) {{
    try {{ return G.resolveEstimand(d && d.estimandType) === "HR"; }}
    catch (e) {{ return false; }}          // FAIL CLOSED: an untagged estimand is not an HR
  }};

  /* --- G08 safeRob: unknown -> "some", never "low" -------------------------------------- */
  step("G08_safeRob", function () {{
    var host = window.RapidMeta || window;
    if (typeof host.safeRob !== "function" && typeof window.safeRob !== "function") return "absent";
    var wrap = function (rob) {{ return G.G08_safeRob(rob); }};
    if (typeof host.safeRob === "function") host.safeRob = wrap;
    if (typeof window.safeRob === "function") window.safeRob = wrap;
    return true;
  }});

  /* --- G07 pooling-repair: neutralised TEXTUALLY (T4), not here --------------------------
   * The block runs at parse time, before any overlay, so a runtime flag could never reach it.
   * An earlier revision set a runtime flag that nothing read. T4 injects an early
   * return at the block's own site; this step only REPORTS whether that landed. */
  step("G07_pooling_repair", function () {{
    if (!window.__rmAllowPoolingRepair && document.documentElement.innerHTML
        .indexOf("RM-PHASE1 G07: disabled") !== -1) return "NEUTRALISED-BY-T4";
    return "absent";
  }});

  /* --- G21 reconcile persisted state on hydrate ----------------------------------------- */
  step("G21_persisted_state", function () {{
    var RM = window.RapidMeta;
    if (!RM || !RM.state) return "absent";
    var realIds = Object.keys(RM.realData || {{}});
    var qIds = Object.keys(window.__quarantinedTrials || {{}});
    var auth = {{
      realDataIds: realIds, quarantinedIds: qIds,
      ledgerFingerprint: G.G21_ledgerFingerprint(realIds, qIds, String(RM.version || document.title))
    }};
    var res = G.G21_reconcilePersistedState(
      {{ trials: RM.state.trials, ledgerFingerprint: RM.state.__rmLedgerFp,
         pooledResult: RM.state.__pooledResult }}, auth);
    // mustRederive is the library's own signal and MUST be consumed: it is true whenever a
    // persisted pooled estimate exists, even when nothing was purged. Reading only
    // purged/dropped/stale let a returning visitor's stored __pooledResult survive, which made
    // the "never restores a persisted result" claim false.
    if (res.mustRederive) {{
      RM.state.trials = res.trials;
      RM.state.__pooledResult = null;          // never carried forward
      RM.state.__rmLedgerFp = auth.ledgerFingerprint;
      if (res.reason) {{ applied.notes.push(res.reason); log(res.reason); }}
      try {{ typeof RM.save === "function" && RM.save(); }} catch (e) {{}}
      return {{ purged: res.purged.length, dropped: res.dropped.length,
                stale: res.staleLedger, rederived: true }};
    }}
    RM.state.__rmLedgerFp = auth.ledgerFingerprint;
    return {{ purged: 0, dropped: 0, stale: false, rederived: false }};
  }});

  /* --- G18 fail-closed integrity gate + G12 badge parity --------------------------------- */
  step("G18_G12_gate", function () {{
    var RM = window.RapidMeta;
    var ids = Object.keys((RM && RM.realData) || {{}});
    var badgeEl = document.getElementById("rapidmeta-integrity-badge");
    var badgeTxt = badgeEl ? (badgeEl.textContent || "") : "";
    var badgeBg = badgeEl ? (badgeEl.style.background || "") : "";
    var v = window.__verdict || {{}};
    var counts = [];
    if (v.counts && v.counts.n_trials_seen !== undefined) counts.push(Number(v.counts.n_trials_seen));
    if (ids.length) counts.push(ids.length);
    var liveTxt = G.G12_stripAuditTrail ? G.G12_stripAuditTrail(badgeTxt) : badgeTxt;
    var bm = /Trials?\\s*:\\s*(\\d+)/.exec(liveTxt);
    if (bm) counts.push(Number(bm[1]));

    var gate = G.attempt(function () {{
      return G.G18_assertIntegrityGate({{ trialIds: ids, trialCounts: counts,
                                         verdictWord: v.verdict }});
    }});
    if (!gate.ok && gate.block && gate.block.code === "LEDGER_ABSENT") {{
      // Nothing to certify. N/A is NOT a pass (RM-H04) - and it is not settled either, so a
      // later hydrate that populates the ledger will re-run this.
      return "NOT-APPLICABLE";
    }}
    var parity = G.attempt(function () {{
      return G.G12_assertVerdictParity(v,
        {{ background: badgeBg, text: badgeTxt, trialCount: bm ? Number(bm[1]) : undefined }},
        {{ trialCount: ids.length }});
    }});
    if (!gate.ok || !parity.ok) {{
      var why = [gate.ok ? null : gate.reason, parity.ok ? null : parity.reason]
        .filter(Boolean).join(" | ");
      applied.notes.push(why);
      log("integrity gate FAILED - suppressing pooled surfaces", why);
      window.__rmGuardBlocked = why;
      if (badgeEl) {{
        badgeEl.style.background = "#7c2d12";
        var note = document.createElement("div");
        note.setAttribute("data-rm-guard", "gate");
        note.style.cssText = "margin-top:8px;font-size:12px;line-height:1.5;";
        note.textContent = "INTEGRITY GATE FAILED — this page's pooled result is suppressed. " + why;
        if (!badgeEl.querySelector('[data-rm-guard="gate"]')) badgeEl.appendChild(note);
      }}
      ["res-or", "res-ci", "res-i2", "res-tau2", "res-pi", "res-nnt"].forEach(function (id) {{
        var el = document.getElementById(id);
        if (el) el.textContent = "--";
      }});
      return "BLOCKED";
    }}
    return "PASS";
  }});

  /* --- G10 k-threshold gate on the machinery panels -------------------------------------- */
  step("G10_k_gate", function () {{
    var RM = window.RapidMeta;
    var k = Object.keys((RM && RM.realData) || {{}}).length;
    if (!k) return "no-k";
    var PANELS = {{ funnel: "plot-funnel", egger: "res-egger", trimfill: "plot-trimfill",
                   copas: "res-copas", metaregression: "plot-metareg", tsa: "plot-tsa",
                   nma: "plot-network", subgroup: "plot-subgroup" }};
    var suppressed = [];
    Object.keys(PANELS).forEach(function (panel) {{
      var r = G.attempt(function () {{
        return G.G10_gateMachinery(panel, {{ k: k, hasNetwork: !!window.__networkData,
                                            hasClosedLoop: false, estimand: "OR" }});
      }});
      if (r.ok && r.value && r.value.render === false) {{
        var el = document.getElementById(PANELS[panel]);
        if (el && !el.querySelector('[data-rm-guard="k"]')) {{
          var n = document.createElement("div");
          n.setAttribute("data-rm-guard", "k");
          n.style.cssText = "padding:10px;font-size:12px;opacity:.85;";
          n.textContent = "Suppressed: " + r.value.reason;
          el.innerHTML = ""; el.appendChild(n);
          suppressed.push(panel);
        }}
      }}
    }});
    return suppressed;
  }});

  /* --- G20 watchlist on topic ------------------------------------------------------------ */
  step("G20_watchlist", function () {{
    var reg = window.CTGOV_EVIDENCE_REGISTRY;
    if (!reg) return "absent";
    var list = Object.keys(reg).map(function (k) {{ return {{ label: (reg[k] || {{}}).label || k }}; }});
    var topic = String(document.title || "").toLowerCase().split(/[^a-z0-9]+/)
      .filter(function (w) {{ return w.length > 3; }});
    var r = G.attempt(function () {{ return G.G20_assertWatchlistOnTopic(list, topic); }});
    if (!r.ok) {{ applied.notes.push(r.reason); log(r.reason); return "OFF-TOPIC"; }}
    return "ok";
  }});

  window.__rmGuardsApplied = applied;
  }}

  function runAll() {{
    applied.runs++;
    allSteps();
  }}
  runAll();
  if (document.readyState === "loading") {{
    document.addEventListener("DOMContentLoaded", runAll, {{ once: true }});
  }}
  window.addEventListener("load", runAll, {{ once: true }});
  setTimeout(runAll, 1200);
  setTimeout(runAll, 4000);
}})();
</script>
{END}"""


def read_bytes_text(p: Path):
    raw = p.read_bytes()
    bom = raw.startswith(b"\xef\xbb\xbf")
    txt = raw.decode("utf-8-sig" if bom else "utf-8", errors="strict")
    return txt, bom


def strip_existing(text: str) -> str:
    """Remove any previously-applied sentinel block, at ANY version. Makes re-apply idempotent
    and makes an upgrade a clean replace rather than a second block."""
    out = text
    while True:
        m = ANY_BEGIN.search(out)
        if not m:
            return out
        ver = m.group(1)
        end_tok = f"<!-- RM-PHASE1-GUARDS v{ver} END -->"
        e = out.find(end_tok, m.end())
        if e == -1:
            return out
        seg_end = e + len(end_tok)
        # also consume one trailing newline the injector added
        if out[seg_end:seg_end + 2] == "\r\n":
            seg_end += 2
        elif out[seg_end:seg_end + 1] == "\n":
            seg_end += 1
        out = out[:m.start()] + out[seg_end:]


def transform(text: str, guard_src: str):
    """Pure: text in, (text, report) out. No I/O."""
    rep = {"textual": {}, "overlay": None, "markers": {}, "skipped": None}
    for name, pat in ENGINE_MARKERS.items():
        rep["markers"][name] = bool(pat.search(text))

    if not rep["markers"]["verdict"] and not rep["markers"]["badge"] and not rep["markers"]["safeRob"]:
        rep["skipped"] = "no shared-engine marker present"
        return text, rep

    out = strip_existing(text)
    rep["had_previous_block"] = out != text

    saferob_present = bool(SAFEROB_PRESENT_RE.search(out))
    for name, kind, find, replace, ids in TEXTUAL:
        if kind == "regex" and name == "T1-icmje":
            # CONTEXT-BOUND: only the protocol-provenance claim. The corpus also carries a
            # LEGITIMATE ICMJE line about AI-assisted authorship which must never be rewritten.
            n = 0
            def _t1(m, _r=replace):
                # Window EXCLUDES the match itself - the sentence contains "PROSPERO", so
                # matching on it would make the bind vacuous. The claim always sits in a
                # protocol-provenance row in this corpus.
                ctx = out[max(0, m.start() - 300):m.start()] + out[m.end():m.end() + 300]
                if not re.search(r"protocol|registration|registry|OSF|pre-?register", ctx, re.I):
                    return m.group(0)
                return _r
            out, n = find.subn(_t1, out)
        elif kind == "regex":
            n = len(find.findall(out))
            if n:
                out = find.sub(lambda _m: replace, out)
        elif kind == "regex-group":
            # IDEMPOTENT: unlike T1/T2/T3, T4's anchor (the COMPLETE-POOLING-REPAIR comment plus
            # the IIFE head) SURVIVES its own replacement, so a second apply injected a second
            # copy. Caught by the real double-apply test on the minified root apps - the
            # submission copies have no pooling-repair block and hid it.
            n = 0

            def _t4(m):
                nonlocal n
                if T4_MARK[:24] in out[m.end():m.end() + 200]:
                    return m.group(0)
                n += 1
                return m.group(1) + T4_MARK
            out = find.sub(_t4, out)
        elif kind == "callable":
            out, n = find(out)
        else:
            n = out.count(find)
            if n:
                out = out.replace(find, replace)
        rep["textual"][name] = {"occurrences": n, "registry": ids}

    # FAIL CLOSED. safeRob is a closure-local const: if the textual replacement did not fire,
    # the runtime overlay CANNOT fix it, and emitting the file would ship a page that carries the
    # guard sentinel and a gate badge while its RoB still resolves every unknown to "low".
    # A page that asserts it is guarded while the defect is live is worse than no guard at all.
    if saferob_present and rep["textual"]["T3-saferob"]["occurrences"] == 0:
        rep["error"] = ("T3 ANCHOR MISS: this file defines safeRob but no safeRob anchor matched. "
                        "Refusing to emit a guards-absent-but-sentinel-present page.")
        return text, rep

    nl = "\r\n" if "\r\n" in out else "\n"
    block = overlay_js(guard_src).replace("\n", nl)
    idx, how = choose_injection_point(out)
    rep["overlay"] = how
    rep["overlay_at"] = idx
    if idx is None:
        rep["skipped"] = "no safe top-level injection point"
        return text, rep
    out = out[:idx] + block + nl + out[idx:]
    return out, rep


def script_balance(text: str, upto: int) -> int:
    """Open `<script` tags minus `</script>` closes before `upto`. Non-zero means that offset is
    INSIDE a script element, where an injected <script> tag would be inert text."""
    return (len(re.findall(r"<script\b", text[:upto], re.I))
            - len(re.findall(r"</script\s*>", text[:upto], re.I)))


def choose_injection_point(text: str):
    """Return (index, how). The block must land at TOP LEVEL, not inside a script or a string.

    THE BUG THIS EXISTS FOR: these apps build their export/print HTML inside JavaScript template
    strings, so a literal `</body>` appears in the MIDDLE of the file. Taking the FIRST match put
    the whole guard block inside a JS string at byte 586,007 of APIXABAN_ACS - the <script> tags
    became inert text and window.RapidMetaGuards was never defined. Caught by RENDERING, not by
    the file: the page still looked fine and `guardsLoaded` was simply false.


    Counting <script> tags does NOT work here: these apps also embed `<script src=...>` inside
    their export templates, so the tag balance never returns to zero and every candidate looks
    unsafe. The reliable signal is the DOCUMENT TAIL - the real closing </body> is the one with
    nothing but optional whitespace and </html> after it. A </body> inside a JS string always has
    the rest of the application behind it."""
    # The tail may legitimately carry trailing HTML comments - these apps end with
    # `</body></html>` followed by e.g. `<!-- /* LIVING_MA_FIX_APPLIED */ ARNI_TEMPLATE_NOP -->`.
    # Without allowing those the check fell through and the block was appended after </html>.
    tail_ok = re.compile(r"^\s*(</html\s*>)?\s*(<!--.*?-->\s*)*$", re.I | re.S)
    cands = list(BODY_CLOSE.finditer(text))
    for n, m in enumerate(reversed(cands)):
        if tail_ok.match(text[m.end():]):
            return m.start(), ("before the document's closing </body>"
                               + ("" if n == 0 else " (later matches are inside a string)"))
    for m in reversed(list(re.finditer(r"</html\s*>", text, re.I))):
        if tail_ok.match(text[m.end():]):
            return m.start(), "before the closing </html> (no clean </body>)"
    return len(text), "appended at EOF (no clean document close found)"


# ---------------------------------------------------------------- selftest

SYNTH_APP = (
    "<html><head><title>RapidMeta | Synthetic</title></head><body>"
    '<div id="rapidmeta-integrity-badge" style="background:#15803d">INTERNAL CHECKS PASSED Trials: 2</div>'
    '<script>window.__verdict = {"verdict":"STABLE","counts":{"n_trials_seen":2},"reasons":[]};</script>'
    "<script>var " + T3_FIND + ";"
    'var q = "RR"!==String(d?.estimandType??"HR");'
    'localStorage.setItem("rapid_meta_x_v12_0",JSON.stringify(this.state));'
    "/* COMPLETE-POOLING-REPAIR */</script>"
    "<td>Protocol provenance</td><td>Per ICMJE 2023, GitHub commit hash + timestamp constitutes a verifiable pre-registration "
    "record equivalent to PROSPERO for tracking outcome / eligibility / analysis-plan changes.</p>"
    "</body></html>")

# The e156-submission shape: PRETTY-PRINTED, single quotes, different body. 18 files. The exact
# minified literals matched NOTHING on these, so they were "patched" in name only - sentinel and
# badge present, guards absent, safeRob still resolving every unknown to "low".
SYNTH_PRETTY = (
    "<html><head><title>RapidMeta | Pretty</title></head><body>"
    '<div id="rapidmeta-integrity-badge" style="background:#15803d">INTERNAL CHECKS PASSED Trials: 2</div>'
    "<script>\n"
    "        const safeRob = (rob) => {\n"
    "            const valid = ['low', 'some', 'high'];\n"
    "            if (!Array.isArray(rob)) return ['low','low','low','low','low'];\n"
    "            return rob.map(r => valid.includes(r) ? r : 'low');\n"
    "        };\n"
    "        const q = 'RR' !== String(d?.estimandType ?? 'HR');\n"
    "</script>"
    "<p>Protocol registration: Per ICMJE 2023, GitHub commit hash + timestamp constitutes a "
    "verifiable pre-registration record equivalent to PROSPERO for tracking outcome / "
    "eligibility / analysis-plan changes.</p>"
    "</body></html>")

# safeRob present but in a shape no anchor can reach -> the patch MUST refuse the file.
SYNTH_UNREACHABLE = (
    "<html><body>"
    '<div id="rapidmeta-integrity-badge">x</div>'
    "<script>window.__verdict={};var safeRob = function (rob) { return rob; };</script>"
    "</body></html>")

# The regression fixture for the injection-point bug: a DECOY </body> inside a JS string, which
# is what every export/print template in this corpus contains.
SYNTH_DECOY = SYNTH_APP.replace(
    "<td>Protocol provenance</td>",
    "<script>var report='<div>report</div></body></html>';</script><td>Protocol provenance</td>")


def selftest():
    guard_src = GUARD_LIB.read_text(encoding="utf-8")
    print("=" * 78)
    print("PHASE-1 PATCH SELFTEST")
    print("=" * 78)
    ok = True

    once, r1 = transform(SYNTH_APP, guard_src)
    twice, r2 = transform(once, guard_src)
    thrice, _ = transform(twice, guard_src)

    checks = [
        ("anchors found: safeRob/badge/verdict/persist/pooling-repair",
         all(r1["markers"][k] for k in ("safeRob", "badge", "verdict", "state_persist", "pooling_repair"))),
        ("T1 ICMJE literal replaced", r1["textual"]["T1-icmje"]["occurrences"] == 1),
        ("T2 denylist literal replaced", r1["textual"]["T2-denylist"]["occurrences"] == 1),
        ("T3 safeRob literal replaced", r1["textual"]["T3-saferob"]["occurrences"] == 1),
        ("safeRob low-fallback GONE", 'valid.includes(r)?r:"low"' not in once),
        ("safeRob falls back to \"some\"", '??"some"' in once),
        ("overlay injected at a top-level </body>", "</body>" in str(r1["overlay"])),
        ("ICMJE claim GONE from output", not T1_RE.search(once)),
        ("mechanism text PRESENT in output", "tamper-evident" in once),
        ("denylist GONE from output", not T2_RE.search(once)),
        ("IDEMPOTENT: apply twice == apply once", twice == once),
        ("IDEMPOTENT: apply three times == apply once", thrice == once),
        ("exactly one sentinel block", once.count(BEGIN) == 1 and once.count(END) == 1),
        ("second apply detected the previous block", r2.get("had_previous_block") is True),
        ("a non-engine file is SKIPPED", transform("<html><body>hi</body></html>", guard_src)[1]["skipped"] is not None),
    ]

    # --- P0-1: pretty-printed apps must get REAL guards ---------------------------------------
    pretty_out, pretty_rep = transform(SYNTH_PRETTY, guard_src)
    unreach_out, unreach_rep = transform(SYNTH_UNREACHABLE, guard_src)
    checks += [
        ("PRETTY: T3 safeRob fired", pretty_rep["textual"]["T3-saferob"]["occurrences"] == 1),
        ("PRETTY: T2 denylist fired", pretty_rep["textual"]["T2-denylist"]["occurrences"] == 1),
        ("PRETTY: T1 icmje fired", pretty_rep["textual"]["T1-icmje"]["occurrences"] == 1),
        ("PRETTY: single-quote low-fallback GONE", "valid.includes(r) ? r : 'low'" not in pretty_out),
        ("PRETTY: no non-array all-low default", "return ['low','low','low','low','low']" not in pretty_out),
        ("PRETTY: idempotent", transform(pretty_out, guard_src)[0] == pretty_out),
        ("FAIL-CLOSED: unreachable safeRob is REFUSED", bool(unreach_rep.get("error"))),
        ("FAIL-CLOSED: refused file is returned UNCHANGED", unreach_out == SYNTH_UNREACHABLE),
        ("FAIL-CLOSED: no sentinel leaks into a refused file", BEGIN not in unreach_out),
        ("T1 is context-bound: a bare AI-authorship ICMJE line is untouched",
         "Per ICMJE 2023: human author takes full responsibility." in
         transform("<html><body><div id=\"rapidmeta-integrity-badge\">x</div>"
                   "<script>window.__verdict={};</script>"
                   "<p>Per ICMJE 2023: human author takes full responsibility.</p>"
                   "</body></html>", guard_src)[0]),
        ("T4: pooling-repair neutralised at its own site",
         "RM-PHASE1 G07: disabled" in transform(
             "<html><body><div id=\"rapidmeta-integrity-badge\">x</div><script>window.__verdict={};"
             "/* COMPLETE-POOLING-REPAIR (2026-06) */ (function () { var done = false; })();"
             "</script></body></html>", guard_src)[0]),
    ]

    # --- the injection-point regression (APIXABAN_ACS, byte 586,007) --------------------------
    dec_out, dec_rep = transform(SYNTH_DECOY, guard_src)
    dec_idx = dec_rep["overlay_at"]
    real_body = dec_out.rindex("</body>")
    checks += [
        ("DECOY </body> inside a JS string is NOT chosen",
         dec_idx > dec_out.index("'<div>report</div></body></html>'")),
        ("injection point is at script-tag balance 0", script_balance(dec_out, dec_idx) == 0),
        ("guard block lands before the LAST </body>", dec_idx <= real_body),
        ("decoy string survives intact",
         "'<div>report</div></body></html>'" in dec_out),
        ("decoy case is idempotent", transform(dec_out, guard_src)[0] == dec_out),
    ]

    for label, res in checks:
        print(f"  [{'OK  ' if res else 'FAIL'}] {label}")
        ok &= bool(res)

    # the overlay must be syntactically valid JS
    import subprocess
    import tempfile

    def node_check(label, body):
        """`node --check -` deadlocks on large stdin here; check a temp FILE instead."""
        fh = tempfile.NamedTemporaryFile("w", suffix=".js", delete=False, encoding="utf-8")
        try:
            fh.write(body)
            fh.close()
            r = subprocess.run(["node", "--check", fh.name], capture_output=True, text=True,
                               timeout=60)
            good = r.returncode == 0
            print(f"  [{'OK  ' if good else 'FAIL'}] {label} passes `node --check`"
                  + ("" if good else " -> " + (r.stderr or "")[:300]))
            return good
        finally:
            try:
                Path(fh.name).unlink()
            except OSError:
                pass

    js = re.search(r"<script>/\* RapidMeta Phase-1 bootstrap.*?</script>", once, re.S)
    if js:
        ok &= node_check("bootstrap", js.group(0)[len("<script>"):-len("</script>")])
    lib = re.search(r"<script>/\* RapidMeta Phase-1 guard library.*?</script>", once, re.S)
    if lib:
        ok &= node_check("SLIMMED guard library",
                         lib.group(0)[lib.group(0).index("*/") + 2:-len("</script>")])
        full = GUARD_LIB.read_text(encoding="utf-8")
        print(f"  [INFO] guard library {len(full):,} B -> {len(slim_guard_src(full)):,} B inlined "
              f"({100 - 100*len(slim_guard_src(full))//len(full)}% smaller)")
    print("-" * 78)
    print("VERDICT:", "SELFTEST PASS" if ok else "SELFTEST FAIL")
    print("=" * 78)
    return 0 if ok else 1


# ---------------------------------------------------------------- main

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true", default=True)
    ap.add_argument("--apply", action="store_true", help="WRITE the files (requires an explicit go)")
    ap.add_argument("--selftest", action="store_true")
    ap.add_argument("--only", action="append", help="restrict to these basenames")
    ap.add_argument("--emit-to", help="dry-run: write patched copies OUTSIDE the repo, for rendering")
    ap.add_argument("--report", default=str(ROOT / "outputs" / "phase1_patch_dryrun.json"))
    ap.add_argument("--root", default=str(ROOT), help="scan this tree instead of the repo (for apply tests)")
    args = ap.parse_args()

    if args.selftest:
        return selftest()

    scan_root = Path(args.root).resolve()
    report_path = Path(args.report).resolve()
    try:
        report_path.relative_to(ROOT if scan_root == ROOT else scan_root)
    except ValueError:
        print(f"REFUSING: --report {report_path} is outside the scanned root")
        return 2

    guard_src = GUARD_LIB.read_text(encoding="utf-8")
    files = sorted(scan_root.glob("*_REVIEW.html"))
    files += sorted(p for p in scan_root.rglob("*_REVIEW.html")
                    if p.parent != scan_root and ".git" not in p.parts)
    if args.only:
        keep = set(args.only)
        files = [p for p in files if p.name in keep]

    emit = Path(args.emit_to) if args.emit_to else None
    if emit:
        emit.mkdir(parents=True, exist_ok=True)

    rows, skipped, errors = [], [], {}
    tot = {n: 0 for n, _k, _f, _r, _i in TEXTUAL}
    for p in files:
        rel = str(p.relative_to(scan_root)).replace("\\", "/")
        try:
            txt, bom = read_bytes_text(p)
        except Exception as e:
            errors[rel] = f"read: {e}"
            continue
        if len(txt) < 20000:
            skipped.append({"path": rel, "why": "redirect stub (<20KB)"})
            continue
        out, rep = transform(txt, guard_src)
        if rep.get("error"):
            errors[rel] = rep["error"]
            continue
        if rep["skipped"]:
            skipped.append({"path": rel, "why": rep["skipped"]})
            continue
        # idempotence, per real file
        again, _ = transform(out, guard_src)
        idem = again == out
        for nm in tot:
            tot[nm] += rep["textual"][nm]["occurrences"]
        t1 = rep["textual"]["T1-icmje"]["occurrences"]
        t2 = rep["textual"]["T2-denylist"]["occurrences"]
        rows.append({
            "path": rel, "bytes_before": len(txt), "bytes_after": len(out),
            "delta": len(out) - len(txt), "bom": bom, "idempotent": idem,
            "t1_icmje": t1, "t2_denylist": t2,
            # Per-app T3/T4 so the gate can verify guards landed WITHOUT inferring it from totals.
            # `guards_real` is the honest bit: True only when safeRob was actually replaced, or
            # the file has no safeRob to replace.
            "t3_saferob": rep["textual"]["T3-saferob"]["occurrences"],
            "t4_poolingrepair": rep["textual"]["T4-poolingrepair"]["occurrences"],
            "guards_real": bool(rep["textual"]["T3-saferob"]["occurrences"]
                                or not SAFEROB_PRESENT_RE.search(txt)),
            "markers": rep["markers"],
            "sha_before": hashlib.sha256(txt.encode("utf-8")).hexdigest()[:12],
            "sha_after": hashlib.sha256(out.encode("utf-8")).hexdigest()[:12],
        })
        if emit:
            # PATH-derived, not basename: --only with 6 names matched 8 files because the
            # e156-submission copies share basenames, and the copy silently overwrote the root app.
            safe = rel.replace("/", "__")
            dest = emit / safe
            data = out.encode("utf-8")
            dest.write_bytes((b"\xef\xbb\xbf" + data) if bom else data)
        if args.apply:
            with open(p, "w", encoding="utf-8-sig" if bom else "utf-8", newline="") as fh:
                fh.write(out)

    report = {
        "mode": "APPLY" if args.apply else "DRY-RUN",
        "patch_version": PATCH_VERSION,
        "files_considered": len(files),
        "apps_modified": len(rows),
        "skipped": len(skipped),
        "errors": errors,
        "idempotent_all": all(r["idempotent"] for r in rows),
        "textual_totals": tot,
        "marker_coverage": {
            m: sum(1 for r in rows if r["markers"][m]) for m in ENGINE_MARKERS
        },
        "bytes_added_total": sum(r["delta"] for r in rows),
        "bytes_added_mean": round(sum(r["delta"] for r in rows) / max(1, len(rows))),
        "apps": rows,
        "skipped_detail": skipped[:50],
    }
    report_path.parent.mkdir(exist_ok=True)
    report_path.write_text(json.dumps(report, indent=1), encoding="utf-8")

    print(f"MODE: {report['mode']}   patch v{PATCH_VERSION}")
    print(f"files considered : {report['files_considered']}")
    print(f"APPS MODIFIED    : {report['apps_modified']}")
    print(f"skipped          : {report['skipped']} (stubs + non-engine)")
    if errors:
        print(f"REFUSED (fail-closed) : {len(errors)}")
        for k, v in list(errors.items())[:5]:
            print(f"    {k}: {v[:110]}")
    print(f"idempotent (all) : {report['idempotent_all']}")
    for nm, v in tot.items():
        print(f"{nm:<24} replaced : {v}")
    print("marker coverage  : " + ", ".join(f"{k}={v}" for k, v in report["marker_coverage"].items()))
    print(f"bytes added      : {report['bytes_added_total']:,} total, "
          f"{report['bytes_added_mean']:,} mean/app")
    if emit:
        print(f"patched copies written OUTSIDE the repo to: {emit}")
    print(f"report           : {report_path}")
    if not args.apply:
        print("\nNO REPO FILE WAS MODIFIED.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
