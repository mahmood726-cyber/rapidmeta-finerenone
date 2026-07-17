"""Self-contained tests for the card<->object consistency guard.

Run:  python scripts/test_card_object_consistency.py     (standalone)
  or: pytest scripts/test_card_object_consistency.py
"""
import os, tempfile, importlib.util

HERE = os.path.dirname(os.path.abspath(__file__))
spec = importlib.util.spec_from_file_location(
    "cocc", os.path.join(HERE, "check_card_object_consistency.py"))
cocc = importlib.util.module_from_spec(spec)
spec.loader.exec_module(cocc)

# minimal app shell: one trial, one card, one allOutcomes array
def app(card_text, obj):
    return (
        '<html><script>const trials=[{name:"T",allOutcomes:[' + obj + '],'
        'cards:[{label:"Secondary CV Outcomes",text:"' + card_text + '"}]}];</script></html>'
    )

CLEAN = app("Cardiovascular death: 102 (2.2%) vs 130 (2.8%) (HR 0.93; 0.73-1.19).",
            '{shortLabel:"CVD",title:"Cardiovascular Death",tE:102,cE:130,effect:.93,lci:.73,uci:1.19,estimandType:"HR"}')
COUNT_BAD = app("Cardiovascular death: 105 (2.2%) vs 130 (2.8%) (HR 0.93; 0.73-1.19).",
                '{shortLabel:"CVD",title:"Cardiovascular Death",tE:135,cE:130,effect:.93,lci:.73,uci:1.19,estimandType:"HR"}')
OMIT_BAD = app("Cardiovascular death was not reported as a standalone endpoint in this trial.",
               '{shortLabel:"CVD",title:"Cardiovascular Death",tE:102,cE:130,effect:.93,lci:.73,uci:1.19,estimandType:"HR"}')
# null-count object + "not reported" prose is CONSISTENT (must stay green)
OMIT_OK = app("Cardiovascular death was not reported as a standalone endpoint in this trial.",
              '{shortLabel:"CVD",title:"Cardiovascular Death",tE:null,cE:null,effect:.93,lci:.73,uci:1.19,estimandType:"HR"}')

def _scan(text):
    with tempfile.TemporaryDirectory() as d:
        p = os.path.join(d, "X_REVIEW.html")
        open(p, "w", encoding="utf-8").write(text)
        return cocc.scan_file(p)

def test_clean_passes():
    assert _scan(CLEAN) == []

def test_count_mismatch_flagged():
    f = _scan(COUNT_BAD)
    assert any(x["class"] == "COUNT_MISMATCH" for x in f), f

def test_omission_flagged():
    f = _scan(OMIT_BAD)
    assert any(x["class"] == "OMISSION" for x in f), f

def test_null_count_omission_is_consistent():
    assert _scan(OMIT_OK) == []

if __name__ == "__main__":
    for name, fn in list(globals().items()):
        if name.startswith("test_") and callable(fn):
            fn(); print("PASS", name)
    print("all tests passed")
