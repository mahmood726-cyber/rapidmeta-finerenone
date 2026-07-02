"""Additively surface the 6 corrected values on the DEFAULT (tab-protocol)
landing view of GLP1_CVOT_REVIEW.html. Reads RapidMeta.realData at runtime
(single source of truth). CRLF-preserving, ASCII-only."""
import sys
p = r"C:\Users\mahmo\rmf-live-fix\GLP1_CVOT_REVIEW.html"
s = open(p, "r", encoding="utf-8", newline="").read()
orig = s
apply = "--apply" in sys.argv

# --- 1) add verified P value to REWIND nonfatal stroke outcome (single source) ---
rewind_old = 'Nonfatal Stroke",tE:135,cE:175,type:"SECONDARY",matchScore:78,effect:.76,lci:.61,uci:.95,estimandType:"HR"'
rewind_new = rewind_old + ',p:"0.017"'
assert s.count(rewind_old) == 1, "REWIND stroke anchor not unique"
s = s.replace(rewind_old, rewind_new, 1)

# --- 2) insert the two landing cards at the top of tab-protocol ---
sec = '<section id="tab-protocol"'
si = s.index(sec)
divanchor = '<div class="max-w-5xl mx-auto space-y-8">'
di = s.index(divanchor, si) + len(divanchor)
cards = (
    '\r\n\r\n'
    '                <div class="glass rounded-[2rem] border border-slate-800 overflow-hidden shadow-2xl" id="landing-key-outcomes-card">\r\n'
    '                    <div class="bg-slate-900/80 p-4 border-b border-slate-800">\r\n'
    '                        <h3 class="text-lg font-bold text-white">Key Secondary CV Outcomes (per study)</h3>\r\n'
    '                        <p class="text-xs text-slate-500">Shown on load from the trial dataset; open the Analysis tab and pick an outcome for the full pooled forest.</p>\r\n'
    '                    </div>\r\n'
    '                    <div id="landing-secondary-outcomes" class="p-4 text-slate-300 text-sm overflow-x-auto">Loading...</div>\r\n'
    '                </div>\r\n\r\n'
    '                <div class="glass rounded-[2rem] border border-slate-800 overflow-hidden shadow-2xl" id="landing-soul-card">\r\n'
    '                    <div class="bg-slate-900/80 p-4 border-b border-slate-800">\r\n'
    '                        <h3 class="text-lg font-bold text-white">SOUL Baseline: Ethnicity &amp; Race (NIH/OMB)</h3>\r\n'
    '                    </div>\r\n'
    '                    <div id="landing-soul-baseline" class="p-4 text-slate-300 text-sm">Loading...</div>\r\n'
    '                </div>\r\n'
)
s = s[:di] + cards + s[di:]

# --- 3) insert the populate script before the LAST </body> ---
script = (
    '<script>\r\n'
    '(function(){\r\n'
    '  function findStudy(name){var rd=(window.RapidMeta&&RapidMeta.realData)||{};for(var k in rd){if(rd[k]&&rd[k].name===name)return rd[k];}return null;}\r\n'
    '  function outc(e,code){if(!e)return null;var a=e.allOutcomes||[];for(var i=0;i<a.length;i++){if((a[i].shortLabel||"")===code)return a[i];}return null;}\r\n'
    '  function fmt(o){if(!o)return "n/a";var s=o.tE+"/"+o.cE+" HR "+o.effect+" ("+o.lci+"-"+o.uci+")";if(o.p)s+=" P="+o.p;return s;}\r\n'
    '  function render(){\r\n'
    '    var rd=(window.RapidMeta&&RapidMeta.realData);if(!rd)return false;\r\n'
    '    var rewind=findStudy("REWIND"),sel=findStudy("SELECT"),soul=findStudy("SOUL");\r\n'
    '    var rows=[["REWIND","Nonfatal stroke",outc(rewind,"Stroke")],'
    '["SELECT","All-cause mortality",outc(sel,"ACM")],'
    '["SELECT","Nonfatal MI",outc(sel,"MI")],'
    '["SELECT","Nonfatal stroke",outc(sel,"Stroke")]];\r\n'
    '    var h=\'<table class="w-full text-left text-sm"><thead><tr class="text-slate-400 text-xs uppercase"><th class="p-2">Trial</th><th class="p-2">Outcome</th><th class="p-2">Drug events vs Placebo events</th></tr></thead><tbody>\';\r\n'
    '    for(var i=0;i<rows.length;i++){h+=\'<tr class="border-t border-slate-800"><td class="p-2 font-bold text-white">\'+rows[i][0]+\'</td><td class="p-2">\'+rows[i][1]+\'</td><td class="p-2 text-slate-200">\'+fmt(rows[i][2])+\'</td></tr>\';}\r\n'
    '    h+="</tbody></table>";\r\n'
    '    var el=document.getElementById("landing-secondary-outcomes");if(el)el.innerHTML=h;\r\n'
    '    var card=null;if(soul&&soul.evidence){for(var j=0;j<soul.evidence.length;j++){var lb=soul.evidence[j].label||"";if(/ethnicit|race/i.test(lb)){card=soul.evidence[j];break;}}}\r\n'
    '    var sc=document.getElementById("landing-soul-baseline");if(sc)sc.textContent=card?(card.label+" -- "+card.text):"SOUL baseline ethnicity/race not available.";\r\n'
    '    return true;\r\n'
    '  }\r\n'
    '  function tryRender(n){if(render())return;if(n>0)setTimeout(function(){tryRender(n-1);},300);}\r\n'
    '  if(document.readyState!=="loading")tryRender(25);else document.addEventListener("DOMContentLoaded",function(){tryRender(25);});\r\n'
    '})();\r\n'
    '</script>\r\n'
)
bi = s.rindex("</body>")
s = s[:bi] + script + s[bi:]

# non-ASCII / curly guard on the inserted content only
inserted = cards + script + ',p:"0.017"'
bad = [c for c in inserted if ord(c) > 127]
assert not bad, "non-ASCII in inserted content: %r" % bad[:5]
assert not any(c in inserted for c in "‘’“”"), "curly quote in inserted content"

print("delta chars:", len(s) - len(orig))
if apply:
    open(p, "w", encoding="utf-8", newline="").write(s)
    print("APPLIED")
else:
    print("DRY-RUN (no write)")
