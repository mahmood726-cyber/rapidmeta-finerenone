"""Project the authored manuscript into a full paper.

The previous Paper Studio emitted a definition list of field labels -- Question,
Search, Result, Robustness -- which reads as a form someone has filled in, not as
a paper. Mahmood called it barebones three times, and he was right each time: a
heading over a projected value is a scaffold no matter how many headings it has.

What this projects instead is continuous prose with the numbers inside the
sentences, assembled from `canon["manuscript"]`, whose text is authored and
stored in the object and whose every quantity is a [[token]] filled here from the
results block. That split is the whole design: interpretation is reviewable
because it sits in one place, and numerals cannot drift because prose never
carries them literally.

An unfilled token is treated as a BUILD FAILURE. A manuscript that renders
"pooled hazard ratio of [[pooled]]" to a reader is worse than one that fails to
build, and the placeholder-leak family has reached readers on this corpus before
-- 1110 dashboards -- so it is raised, not warned about.
"""
import re

# THE ONE PLACE CERTAINTY IS RESOLVED. A tolerant import because this module is loaded
# both from inside ssot/ (bare name) and as a package member.
try:
    import grade_authority as _ga
except ImportError:  # pragma: no cover -- package import path
    from . import grade_authority as _ga


NL = "\n"


class UnfilledToken(Exception):
    """A {token} in the manuscript had no value. Never render this to a reader."""


def _fmt(v, nd=4):
    """Display formatting. Estimates go to 3 significant figures.

    The manuscript reported HR 0.8392 (0.7429 to 0.948) -- four figures, then
    four, then three, on one line. Consistent numeric formatting is one of the
    things a journal editor actually reads for, and inconsistent formatting is
    read as machine output. The object keeps full precision; this is the report.
    """
    if v is None:
        return None
    if isinstance(v, float):
        import projectors as _pj
        return _pj.sig(v, 3)
    return str(v)


def build_tokens(canon, res, oid):
    """Every substitutable quantity, resolved from the object only."""
    pooled = res.get("pooled") or {}
    het = res.get("heterogeneity") or {}
    g = res.get("grade") or {}
    sens = res.get("sensitivity") or {}
    reg = canon.get("registration") or {}
    od = reg.get("ordering") or {}
    rb = canon.get("rob2") or {}
    ag = rb.get("agreement") or {}
    per = [r for r in (res.get("per_trial") or []) if r.get("point")]
    corpus = (canon.get("screening") or {}).get("corpus") or []

    n_total = 0
    for t in canon["inputs"]["trials"]:
        for a in (t.get("arms") or []):
            if a.get("participants"):
                n_total += a["participants"]

    # leave-one-out: the omission of the heaviest trial, whatever it is called.
    loo = None
    heaviest = None
    if per:
        heaviest = min(per, key=lambda r: r.get("log_se") or 9e9).get("trial_id")
    for a in (sens.get("analyses") or []):
        if not isinstance(a, dict):
            continue
        omitted = a.get("omitted") or a.get("trial_omitted") or a.get("trial")
        if omitted and heaviest and str(omitted).lower() == str(heaviest).lower():
            p_, l_, h_ = a.get("point"), a.get("ci_low"), a.get("ci_high")
            if p_ is not None and l_ is not None:
                loo = "%s (%s to %s)" % (_fmt(p_), _fmt(l_), _fmt(h_))
    if loo is None:
        f = sens.get("leave_one_out_finding") or ""
        m = re.search(r"(\d+\.\d+)\s*\(\s*(\d+\.\d+)\s*(?:to|-|&ndash;)\s*(\d+\.\d+)",
                      f)
        if m:
            loo = "%s (%s to %s)" % m.groups()

    proto = None
    for a in ((canon.get("protocol") or {}).get("amendment_history") or []):
        if not a.get("post_dates_first_query"):
            proto = a
            break

    pts = [r["point"] for r in per]
    tok = {
        "k": _fmt(res.get("k")),
        "pooled": _fmt(pooled.get("point")),
        "ci_low": _fmt(pooled.get("ci_low")),
        "ci_high": _fmt(pooled.get("ci_high")),
        "ci_level": _fmt(pooled.get("ci_level", 95)),
        "measure": pooled.get("measure"),
        "i2": _fmt(het.get("i2"), 1),
        "tau2": _fmt(het.get("tau2")),
        "q": _fmt(het.get("q"), 2),
        "df": _fmt(het.get("df")),
        "n_total": "{:,}".format(n_total) if n_total else None,
        "n_records": _fmt(len(corpus)) if corpus else None,
        # THE SAME RESOLVER THE PAGE USES. This token read `results.*.grade` only, so a
        # manuscript could say "not rated" about an outcome the structured record rated,
        # on the one surface a reader is most likely to quote.
        "certainty": _ga.resolve(canon, oid)["cell"],
        "certainty_state": _ga.resolve(canon, oid)["state"],
        "certainty_comment": _ga.resolve(canon, oid)["comment"],
        "estimator": res.get("estimator_used") or res.get("estimator"),
        "min_point": _fmt(min(pts)) if pts else None,
        "max_point": _fmt(max(pts)) if pts else None,
        "loo_paradigm": loo,
        "search_date": (canon.get("search") or {}).get("capture_date"),
        "protocol_permalink": (proto or {}).get("permalink"),
        "protocol_utc": (proto or {}).get("committed_utc"),
        "ordering_margin": od.get("margin_vs_registration"),
        "rob2_agree": _fmt(ag.get("per_domain_agreed")),
        "rob2_total": _fmt(ag.get("per_domain_total")),
        "rob2_rate": _fmt(ag.get("per_domain_rate_pct"), 1),
        "rob2_overall_agree": _fmt(ag.get("overall_agreed")),
        "rob2_overall_total": _fmt(ag.get("overall_total")),
    }
    # Quantities the expanded Results section reports. Added as TOKENS rather
    # than typed into the prose: a number written into manuscript text is a copy
    # that drifts the moment the pool changes, which is the defect that put a
    # k=3 leave-one-out under a k=4 headline and a three-trial title on a
    # four-trial paper.
    pan = res.get("panels") or {}
    pred, eg = pan.get("prediction") or {}, pan.get("egger") or {}
    sp = res.get("post_hoc_aetiology_split") or {}
    strata = sp.get("strata") or []
    it = sp.get("interaction_test") or {}
    pc = (canon.get("published_comparison") or {}).get("denominator") or {}
    loo_rows = [a for a in (sens.get("analyses") or []) if isinstance(a, dict)]
    kept = [a for a in loo_rows if a.get("still_excludes_null")]
    extra = {
        "pi_low": _fmt(pred.get("pi_low")), "pi_high": _fmt(pred.get("pi_high")),
        "egger_p": _fmt(eg.get("p"), 3),
        "egger_intercept": _fmt(eg.get("intercept")),
        "loo_n_excluding_null": _fmt(len(kept)) if loo_rows else None,
        "loo_n_total": _fmt(len(loo_rows)) if loo_rows else None,
        "cmp_checked": _fmt(pc.get("rows_checked")),
        "cmp_confirmed": _fmt(pc.get("confirmed")),
        "cmp_errors": _fmt(pc.get("errors")),
        "cmp_absent": _fmt(pc.get("absent")),
    }
    for i, st in enumerate(strata[:2]):
        extra["strat%d_name" % (i + 1)] = st.get("stratum") or st.get("name")
        extra["strat%d_k" % (i + 1)] = _fmt(st.get("k"))
        extra["strat%d_point" % (i + 1)] = _fmt(st.get("point"))
        extra["strat%d_low" % (i + 1)] = _fmt(st.get("ci_low"))
        extra["strat%d_high" % (i + 1)] = _fmt(st.get("ci_high"))
    extra["interaction_p"] = _fmt(it.get("p"), 3)
    extra["rhr"] = _fmt(it.get("ratio_of_hazard_ratios_chagas_vs_unrestricted"))
    extra["rhr_low"] = _fmt(it.get("rhr_ci_low"))
    extra["rhr_high"] = _fmt(it.get("rhr_ci_high"))
    tok.update(extra)
    return {k: v for k, v in tok.items() if v is not None}


# [[name]] and NOT {name}: build_app_v2.resolve() treats {alias.path} as an
# object reference anywhere in a string, so {pooled} was being resolved by the
# generator before this projector ever saw it. Two templating systems sharing
# one delimiter is a collision, not a style choice.
_TOK = re.compile(r"\[\[([a-z0-9_]+)\]\]")


def fill(text, tok, where, num_span=True):
    """Substitute {tokens}. Raise on any that cannot be filled.

    num_span wraps each substituted quantity so a reader can see which parts of a
    sentence are projected and which are authored, and so the numeral detectors
    have a stable hook.
    """
    missing = []

    def sub(m):
        k = m.group(1)
        if k not in tok:
            missing.append(k)
            return m.group(0)
        v = str(tok[k])
        return ("<span class='num'>%s</span>" % v) if num_span else v

    out = _TOK.sub(sub, text)
    if missing:
        raise UnfilledToken("%s: %s" % (where, ", ".join(sorted(set(missing)))))
    return out


def manuscript_section(canon, res, oid, p, tables_html=""):
    """The full paper: abstract, IMRaD prose, tables inline, declared gaps."""
    m = canon.get("manuscript")
    if not m:
        return ""
    tok = build_tokens(canon, res, oid)

    def f(t, where):
        return fill(t, tok, where)

    ab = m["abstract"]
    ab_rows = "".join(
        "    <tr><th>%s</th><td>%s</td></tr>%s"
        % (k.replace("_", " ").capitalize(), f(v, "abstract." + k), NL)
        for k, v in ab.items() if not k.startswith("_"))

    intro = "".join("  <p>%s</p>%s" % (f(x["text"], "introduction"), NL)
                    for x in m.get("introduction", []))
    intro_basis = "".join(
        "    <li><small>%s &mdash; %s</small></li>%s"
        % (x["text"][:60].rsplit(" ", 1)[0] + "&hellip;", p(x.get("basis", "")), NL)
        for x in m.get("introduction", []))

    def prose_block(items, key):
        return "".join(
            "  <h4>%s</h4>%s  <p>%s</p>%s"
            % (p(x["heading"]), NL, f(x["text"], key + "." + x["heading"]), NL)
            for x in items)

    meth = prose_block(m.get("methods_prose", []), "methods")
    resu = prose_block(m.get("results_prose", []), "results")
    disc = prose_block(m.get("discussion", []), "discussion")
    lims = "".join("    <li>%s</li>%s" % (f(x, "limitations"), NL)
                   for x in m.get("limitations", []))
    concl = f(m.get("conclusions", ""), "conclusions")
    title = f(m.get("title", ""), "title")

    gaps = "".join(
        "    <li><strong>%s.</strong> %s</li>%s"
        % (p(x["section"]), p(x["why"]), NL) for x in m.get("not_written", []))

    wc = len(re.sub(r"<[^>]+>", " ", intro + meth + resu + disc + concl).split())

    def card(inner, cls=""):
        return "<div class='card%s'>%s%s</div>%s" % (cls, NL, inner, NL)

    # Built by concatenation, not by one wide %-format. The previous form took
    # thirty-odd positional arguments and a single insertion silently shifted
    # every one after it, which is how a word count ended up in a string slot.
    parts = [
        card("  <h2>Manuscript</h2>%s  <p><strong>%s</strong></p>%s"
             "  <p><small>%s</small></p>%s"
             % (NL, title, NL, p(m.get("_provenance", "")), NL)),
        card("  <h3>Abstract</h3>%s  <table>%s%s  </table>%s"
             % (NL, NL, ab_rows, NL)),
        card("  <h3>Introduction</h3>%s%s"
             "  <details><summary><small>What each paragraph rests on</small>"
             "</summary>%s  <ul>%s%s  </ul></details>%s"
             % (NL, intro, NL, NL, intro_basis, NL)),
        card("  <h3>Methods</h3>%s%s" % (NL, meth)),
        card("  <h3>Results</h3>%s%s%s" % (NL, resu, tables_html)),
        card("  <h3>Discussion</h3>%s%s" % (NL, disc)),
        card("  <h3>Limitations</h3>%s  <ul>%s%s  </ul>%s" % (NL, NL, lims, NL)),
        card("  <h3>Conclusions</h3>%s  <p>%s</p>%s" % (NL, concl, NL)),
    ]
    if gaps:
        parts.append(card("  <h3>Sections not written, and why</h3>%s  <ul>%s%s"
                          "  </ul>%s" % (NL, NL, gaps, NL), " warn"))
    parts.append(card(
        "  <h4>How to read this manuscript</h4>%s  <p>%s</p>%s"
        "  <p><small>Approximately %s words of prose. Quantities shown in "
        "<span class='num'>this style</span> are projected from the analysis at "
        "build time and appear nowhere in the stored text, so the prose cannot "
        "disagree with the numbers. An unfilled placeholder fails the build "
        "rather than reaching a reader.</small></p>%s"
        % (NL, p(m.get("_token_contract", "")), NL, "{:,}".format(wc), NL)))
    return "".join(parts)
