"""Wire the range control, the dark mode, and the raster handles into the build.

The range radios must be SIBLINGS of the range panels for a CSS-only switch to
reach them, so they are emitted as direct children of the card rather than tucked
inside a fieldset. That is a structural constraint of the sibling combinator, not
a style preference, and getting it wrong yields a control that renders and does
nothing.

Panels are hidden with height:0;overflow:hidden and NOT display:none. That was
established empirically on this project: display:none removes a node from
document.body.innerText, which would make every hidden variant invisible to the
reader-state-invariance detector -- the detector would then pass by seeing
nothing, which is the failure mode where a guard cannot fire.
"""
import io
import sys

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
n = 0


def patch(path, old, new, why):
    global n
    s = open(path, encoding="utf-8").read()
    if old not in s:
        raise SystemExit("ANCHOR MISSING (%s) in %s: %r" % (why, path, old[:70]))
    open(path, "w", encoding="utf-8").write(s.replace(old, new, 1))
    n += 1
    print("  patched: %s" % why)


PJ = "ssot/projectors.py"
BT = "ssot/build_tabbed.py"

# --------------------------------------------------- radios as siblings
patch(PJ,
      """    return ("<div class='card'>%s  <h3>Forest plot</h3>%s"
            "  <p><small>Drawn from the same stored estimates the table above "
            "lists. Box area is proportional to inverse-variance weight.</small>"
            "</p>%s  <fieldset class='fwset'>%s"
            "    <legend><small>x-axis range</small></legend>%s%s  </fieldset>%s"
            "%s  <p><small>Changing the range moves the axis window only. The "
            "guides stay labelled with the null and the extremes of the plotted "
            "intervals, so no plotted value and no printed number differs between "
            "these views &mdash; and that is checked at build time, not "
            "asserted.</small></p>%s</div>%s"
            % (NL, NL, NL, NL, NL, radios, NL, panels, NL, NL))""",
      """    return ("<div class='card fwcard'>%s  <h3>Forest plot</h3>%s"
            "  <p><small>Drawn from the same stored estimates the table above "
            "lists. Box area is proportional to inverse-variance weight.</small>"
            "</p>%s  <p><small>x-axis range</small></p>%s%s%s  <p><small>Changing "
            "the range moves the axis window only. The guides stay labelled with "
            "the null and the extremes of the plotted intervals, so no plotted "
            "value and no printed number differs between these views &mdash; and "
            "that is checked at build time, not asserted.</small></p>%s</div>%s"
            % (NL, NL, NL, NL, radios, panels, NL, NL))""",
      "forest card: radios as direct siblings of panels")

patch(PJ,
      """        radios += ('  <input type="radio" name="fw" id="fw-%s" class="fwr"%s>%s'
                   '  <label for="fw-%s" class="fwl">%s</label>%s'
                   % (key, " checked" if i == 0 else "", NL, key, e(label), NL))""",
      """        radios += ('  <input type="radio" name="fw" id="fw-%s" class="fwr"%s>%s'
                   % (key, " checked" if i == 0 else "", NL))
    for key, label, _svg in variants:
        radios += ('  <label for="fw-%s" class="fwl">%s</label>%s'
                   % (key, e(label), NL))""",
      "forest radios emitted before labels")

# --------------------------------------------------- CSS
patch(BT,
      " body{font-family:system-ui,-apple-system,sans-serif;max-width:64rem;"
      "margin:0 auto;padding:1.5rem;line-height:1.6;color:#111}",
      """ :root{--bg:#fff;--fg:#111;--line:#d4d4d8;--muted:#3f3f46;
       --warnb:#b45309;--warnbg:#fffbeb;--accent:#1d4ed8}
 @media (prefers-color-scheme:dark){:root{--bg:#0f1115;--fg:#e8e8ec;
       --line:#33363d;--muted:#a8adb8;--warnb:#d99b3c;--warnbg:#241d10;
       --accent:#7aa2ff}}
 /* Manual override, checkbox + CSS only. :has() keeps the control at the top of
    the document without wrapping the whole body in an extra element. */
 body:has(#dm:checked){--bg:#0f1115;--fg:#e8e8ec;--line:#33363d;--muted:#a8adb8;
       --warnb:#d99b3c;--warnbg:#241d10;--accent:#7aa2ff}
 @media (prefers-color-scheme:dark){body:has(#dm:checked){--bg:#fff;--fg:#111;
       --line:#d4d4d8;--muted:#3f3f46;--warnb:#b45309;--warnbg:#fffbeb;
       --accent:#1d4ed8}}
 body{font-family:system-ui,-apple-system,sans-serif;max-width:64rem;
       margin:0 auto;padding:1.5rem;line-height:1.6;
       color:var(--fg);background:var(--bg)}
 #dm{position:absolute;width:1px;height:1px;opacity:0}
 .dml{position:fixed;top:.5rem;right:.5rem;z-index:9;border:1px solid var(--line);
       border-radius:1rem;padding:.15rem .6rem;font-size:.8rem;cursor:pointer;
       background:var(--bg);color:var(--muted)}
 svg{color:var(--fg)}
 .fwr{position:absolute;width:1px;height:1px;opacity:0}
 .fwl{display:inline-block;border:1px solid var(--line);border-radius:.35rem;
       padding:.1rem .55rem;margin:0 .3rem .4rem 0;font-size:.85rem;
       cursor:pointer;color:var(--muted)}
 /* height:0 rather than display:none -- display:none drops the node from
    document.body.innerText and the invariance detector would see nothing. */
 .fwp{height:0;overflow:hidden}
 #fw-fit:checked~#fwp-fit,#fw-w1:checked~#fwp-w1,
 #fw-w2:checked~#fwp-w2,#fw-w3:checked~#fwp-w3{height:auto;overflow:visible}
 #fw-fit:checked~.fwl[for=fw-fit],#fw-w1:checked~.fwl[for=fw-w1],
 #fw-w2:checked~.fwl[for=fw-w2],#fw-w3:checked~.fwl[for=fw-w3]{
       border-color:var(--accent);color:var(--fg);font-weight:600}""",
      "theme variables, dark mode, range-control CSS")

patch(BT,
      " .card{border:1px solid #d4d4d8;border-radius:.5rem;padding:1rem;margin:1rem 0}\n"
      " .card.warn{border-color:#b45309;background:#fffbeb}",
      " .card{border:1px solid var(--line);border-radius:.5rem;padding:1rem;"
      "margin:1rem 0}\n"
      " .card.warn{border-color:var(--warnb);background:var(--warnbg)}")

patch(BT,
      " table{border-collapse:collapse;width:100%%} th,td{border:1px solid #d4d4d8;"
      "padding:.5rem;text-align:left;vertical-align:top}\n"
      " small{color:#3f3f46}",
      " table{border-collapse:collapse;width:100%%} th,td{border:1px solid "
      "var(--line);padding:.5rem;text-align:left;vertical-align:top}\n"
      " small{color:var(--muted)}\n"
      " a{color:var(--accent)}")

print("\n%d edits applied" % n)
