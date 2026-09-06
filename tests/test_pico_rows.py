#!/usr/bin/env python
"""The PROSPERO field-set table gains discrete Population / Intervention / Comparator rows,
sourced from the frozen v1.0 protocols by CONFIRMED exact stem. This locks the behaviour that
matters: real criteria where a protocol is mapped, a stated null+state where it is not, and the
adjudication decisions that keep a broader or wrong-indication protocol off a narrower review.

Run: python tests/test_pico_rows.py   (or via pytest)
"""
import io
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "ssot"))
import projectors2 as p2


def _checks():
    out, ok = [], True

    def check(name, cond):
        nonlocal ok
        ok &= bool(cond)
        out.append((name, "OK" if cond else "*** FAIL ***"))

    # --- confirmed mappings render REAL, testable criteria (numeric thresholds intact) ---
    iv = p2.load_protocol_pico("iv-iron-hf")
    check("iv-iron-hf maps and carries the ferritin threshold",
          iv and "ferritin <100" in iv["population"])
    fin = p2.load_protocol_pico("finerenone-cv")
    check("finerenone-cv maps to the T2D+CKD protocol (eGFR 25-75)",
          fin and "eGFR 25-75" in fin["population"])
    inc = p2.load_protocol_pico("incretin-hfpef-review")
    check("incretin-hfpef maps and carries LVEF >=45 / BMI >=30",
          inc and "LVEF >=45%" in inc["population"] and "BMI >=30" in inc["population"])
    for app in ("bempedoic-acid-review", "cangrelor-pci-review", "sglt2-hf"):
        pic = p2.load_protocol_pico(app)
        check("%s maps to a full P/I/C" % app,
              pic and set(pic) == {"population", "intervention", "comparator"})

    # exactly six confirmed mappings
    check("exactly 6 confirmed protocol mappings", len(p2._PICO_PROTOCOL) == 6)

    # --- adjudication exclusions, on the record ---
    check("arni-hfref is NOT mapped (program protocol broader than the HFrEF review)",
          "arni-hfref" not in p2._PICO_PROTOCOL)
    check("finerenone-review is NOT mapped (it is HEART FAILURE, not the CKD protocol)",
          "finerenone-review" not in p2._PICO_PROTOCOL)
    check("finerenone-cv IS the mapped finerenone page", "finerenone-cv" in p2._PICO_PROTOCOL)

    # --- pico_pairs: real where mapped, stated null+state where not ---
    pairs = p2.pico_pairs("iv-iron-hf")
    labels = [lab for lab, _ in pairs]
    check("pico_pairs emits Population/Intervention/Comparator in order",
          labels == ["Population", "Intervention", "Comparator"])
    check("a mapped value carries NO data-pico marker (it is a real value)",
          all("data-pico" not in v for _, v in pairs))

    none_pairs = p2.pico_pairs("some-unmapped-app")
    check("an unmapped review gets a machine-readable null+state, not a placeholder",
          all("data-pico='null'" in v and "NO_PROTOCOL_MAPPED" in v for _, v in none_pairs))
    check("the null+state is NOT the legacy 'not recorded on the page' placeholder",
          all("not recorded on the page" not in v for _, v in none_pairs))

    # --- load_protocol_pico is all-or-nothing (never a half-populated PICO) ---
    check("load_protocol_pico returns None for an unmapped app", p2.load_protocol_pico("nope") is None)

    return ok, out


if __name__ == "__main__":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    good, rows = _checks()
    print("test_pico_rows")
    for name, verdict in rows:
        print("  %-64s %s" % (name, verdict))
    print("\n%s" % ("ALL PASS" if good else "FAILURES ABOVE"))
    raise SystemExit(0 if good else 1)
