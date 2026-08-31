# -*- coding: utf-8 -*-
"""Cards that CALL THE DERIVERS at build time, so they fire on any topic.

THE DIFFERENCE FROM `projectors_reader_layers.py`. That module renders blocks a
per-topic apply script had already written into the store; if the script was
never run for a topic, the card is empty. These cards call
`topic_judgements.derive`, `absolute_effect.derive`, `recompute_envelope.derive`
and `count_bases.derive` DIRECTLY, so a topic gets them without anyone having
written anything for it. Adding a topic adds no code and no apply script.

Every card returns "" when its deriver declines with nothing to say, and no
card may break a build: a deriver that raises is caught and rendered as an
error row, because a projector that can take the page down is worse than one
that reports a gap.
"""
import html


def _e(x):
    return html.escape("—" if x is None else str(x))


def _card(title, inner, cls="card"):
    return "<div class='%s'>\n  <h2>%s</h2>\n%s</div>\n" % (cls, _e(title), inner)


def _para(s):
    return "  <p>%s</p>\n" % _e(s)


def _small(s):
    return "  <p><small>%s</small></p>\n" % _e(s)


def _h3(s):
    return "  <h3>%s</h3>\n" % _e(s)


def _warn(s):
    return "  <div class='absent-state'>%s</div>\n" % _e(s)


def _dv(mod, canon, oid):
    try:
        return mod.derive(canon, oid)
    except Exception as exc:              # a projector must never kill a build
        return {"state": "ERROR",
                "reason": "%s: %s" % (type(exc).__name__, exc)}


def _outcomes(canon):
    res = canon.get("results")
    bo = (res.get("by_outcome") if isinstance(res, dict) else None) or {}
    if not isinstance(bo, dict):
        return []
    return [(oid, r) for oid, r in bo.items()
            if isinstance(r, dict) and r.get("pooled")]


# --------------------------------------------------- judgement register -----
def generated_judgements_card(canon, p=None):
    try:
        import topic_judgements as TJ
    except Exception:
        return ""
    outs = _outcomes(canon)
    if not outs:
        return ""
    inner = ""
    for oid, _ in outs:
        reg = _dv(TJ, canon, oid)
        if not reg or reg.get("state") == "ERROR" or not reg.get("entries"):
            continue
        c = reg.get("count") or {}
        rows = ""
        for e in reg["entries"]:
            cls = {"DECLARED": "ok", "UNDECLARED": "warn"}.get(e["state"], "")
            rows += ("    <tr class='%s'><td><code>%s</code></td>"
                     "<td><strong>%s</strong></td><td>%s</td>"
                     "<td><small>%s</small></td><td><small>%s</small></td>"
                     "<td><small>%s</small></td></tr>\n"
                     % (cls, _e(e["slot"]), _e(e["state"]), _e(e["decided"]),
                        _e(e["decided_by"]), _e(e["alternative"]),
                        _e(e["if_alternative"])))
        inner += (_h3("Outcome %s — %s declared, %s undeclared"
                      % (oid, c.get("declared"), c.get("undeclared")))
                  + "  <table>\n    <tr><th>Judgement</th><th>State</th>"
                    "<th>Decided</th><th>Decided by</th><th>Alternative</th>"
                    "<th>If the alternative had been taken</th></tr>\n"
                  + rows + "  </table>\n")
        if reg.get("⭐_the_scaling_claim"):
            inner += _para(reg["⭐_the_scaling_claim"])
        if reg.get("what_this_does_NOT_do"):
            inner += _small(reg["what_this_does_NOT_do"])
    if not inner:
        return ""
    head = (_para("Judgements a harness cannot derive, per outcome, with the "
                  "alternative and its consequence. DERIVED AT BUILD TIME by "
                  "ssot/topic_judgements.py — this table is not written for "
                  "this topic and the same code produces it for every topic.")
            + _warn("⛔ No entry is resolved by inferring from the included "
                    "trials. Deriving a review's question from the populations "
                    "that were enrolled returns DIRECT by construction. Where "
                    "the store does not declare a judgement this table says "
                    "UNDECLARED and stops."))
    return _card("Judgement register — what a harness cannot derive",
                 head + inner)


# ------------------------------------------------------ absolute effect -----
def absolute_effect_card(canon, p=None):
    try:
        import absolute_effect as AE
    except Exception:
        return ""
    inner = ""
    for oid, _ in _outcomes(canon):
        r = _dv(AE, canon, oid)
        if r.get("state") == "EMITTED":
            rows = ""
            for row in r["rows"]:
                b = row.get("baseline_per_1000")
                pv = row.get("events_prevented_per_1000")
                ci = row.get("prevented_ci") or ["", ""]
                nnt = row.get("number_needed_to_treat")
                nci = row.get("nnt_ci") or [None, None]
                rows += ("    <tr><td>%s</td><td>%s</td><td>%s (%s to %s)</td>"
                         "<td>%s</td></tr>\n"
                         % (b, row.get("with_the_intervention"), pv,
                            ci[0], ci[1],
                            ("%s (%s to %s)" % (nnt, nci[0], nci[1]))
                            if nnt else "—"))
            lic = r.get("indirectness_argument_that_licenses_this") or {}
            inner += (_h3("Outcome %s — %s %s"
                          % (oid, r["measure"], r["pooled"]["point"]))
                      + _para(r["_why_a_grid_and_not_one_assumed_risk"])
                      + "  <table>\n    <tr><th>Baseline per 1000</th>"
                        "<th>With the intervention</th>"
                        "<th>Events prevented (95% CI)</th><th>NNT</th></tr>\n"
                      + rows + "  </table>\n"
                      + _small(r["measure_caveat"])
                      + _small("Licensed by %s: %s"
                               % (lic.get("kind"), lic.get("reason"))))
        elif r.get("state") == "DECLINED":
            inner += _warn("Outcome %s — NOT EMITTED. %s"
                           % (oid, r.get("reason")))
    if not inner:
        return ""
    return _card("Absolute effect at a baseline risk the reader chooses",
                 _para("Derived by ssot/absolute_effect.py for any topic with "
                       "a pooled ratio measure AND a declared indirectness "
                       "argument. Where either is missing it DECLINES with a "
                       "reason rather than emitting a table the review has not "
                       "licensed — a ratio becomes an absolute effect only "
                       "against a baseline risk, and a baseline risk belongs "
                       "to a population.") + inner)


# --------------------------------------------------- recompute envelope -----
def recompute_envelope_card(canon, p=None):
    try:
        import recompute_envelope as RE
    except Exception:
        return ""
    inner = ""
    for oid, _ in _outcomes(canon):
        r = _dv(RE, canon, oid)
        if r.get("state") == "EMITTED":
            rec = r["recomputed"]
            fe, dl = rec["fixed_effect"], rec["dersimonian_laird"]
            inner += (_h3("Outcome %s" % oid)
                      + "  <table>\n    <tr><th>Source</th><th>Point</th>"
                        "<th>95% CI</th></tr>\n"
                      + ("    <tr><td>stored on this page</td>"
                         "<td><strong>%s</strong></td><td>—</td></tr>\n"
                         % _e(r["stored_point"]))
                      + ("    <tr><td>fixed effect, recomputed from the rows"
                         "</td><td>%s</td><td>%s to %s</td></tr>\n"
                         % (fe["point"], fe["ci_low"], fe["ci_high"]))
                      + ("    <tr><td>DerSimonian-Laird, recomputed</td>"
                         "<td>%s</td><td>%s to %s</td></tr>\n"
                         % (dl["point"], dl["ci_low"], dl["ci_high"]))
                      + "  </table>\n"
                      + _para(r["verdict"])
                      + _small("Scale used: %s. Declared estimator: %s."
                               % (r.get("scale_used"),
                                  r.get("declared_estimator")))
                      + _warn(r["⚠️_what_agreement_does_NOT_prove"])
                      + _small(r["_why_DL_and_not_REML"]))
        elif r.get("state") == "DECLINED":
            inner += _warn("Outcome %s — not rechecked. %s"
                           % (oid, r.get("reason")))
    if not inner:
        return ""
    return _card("Recompute envelope — the headline against the rows shown",
                 _para("Derived by ssot/recompute_envelope.py. The pooled "
                       "number is recomputed from the per-trial rows this same "
                       "page shows, so the arithmetic between the extraction "
                       "table and the headline is checkable with no tool the "
                       "reader does not already have.") + inner)


# ---------------------------------------------------------- count bases -----
def count_bases_card(canon, p=None):
    try:
        import count_bases as CB
    except Exception:
        return ""
    inner = ""
    for oid, _ in _outcomes(canon):
        r = _dv(CB, canon, oid)
        if r.get("state") != "EMITTED":
            continue
        rows = ""
        for name, pool in (r.get("pooled_by_basis") or {}).items():
            hl = (" <strong>(headline)</strong>"
                  if name == r.get("headline_basis") else "")
            det = (r.get("detail_by_basis") or {}).get(name) or {}
            rows += ("    <tr><td><code>%s</code>%s<br><small>%s</small></td>"
                     "<td>%s</td><td><strong>%s</strong> (%s to %s)</td></tr>\n"
                     % (_e(name), hl, _e(det.get("source")),
                        _e(det.get("scale")), pool["point"],
                        pool["ci_low"], pool["ci_high"]))
        inner += (_h3("Outcome %s" % oid)
                  + "  <table>\n    <tr><th>Basis</th><th>Scale</th>"
                    "<th>Pooled</th></tr>\n" + rows + "  </table>\n"
                  + _para(r.get("⭐_what_this_shows"))
                  + _small(r.get("what_was_compared", "")))
        dis = r.get("trials_whose_COUNTS_DIFFER_between_bases") or []
        if dis:
            drows = ""
            for d in dis:
                vals = [v for k, v in d.items()
                        if k not in ("trial", "compared")]
                drows += ("    <tr class='warn'><td><code>%s</code></td>%s</tr>\n"
                          % (_e(d.get("trial")),
                             "".join("<td>%s</td>" % _e(v) for v in vals)))
            inner += ("  <table>\n    <tr><th>Trial</th><th>Basis A</th>"
                      "<th>Basis B</th></tr>\n" + drows + "  </table>\n")
        inner += _small(r.get("and_the_estimand_moves_with_it", ""))
        if not r.get("headline_basis"):
            inner += _warn(r.get("⛔_headline_not_named", ""))
    if not inner:
        return ""
    return _card("Two count bases — both pooled, and the headline named",
                 _para("Derived by ssot/count_bases.py. Any topic declaring "
                       "two or more count bases renders BOTH pools side by "
                       "side and names which is the review's answer. A page "
                       "carrying two estimates for one result and naming "
                       "neither is a worse defect than either being wrong.")
                 + inner)
