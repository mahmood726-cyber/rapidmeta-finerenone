"""TIER-2 PLANT for unit 12 -- an estimate outside its own confidence interval.

Leg 2 of the four. The plant goes into a real delivered page, the gate is watched to FAIL on
it, and the page is restored with its sha256 and byte count asserted.
"""
A = "append"

PLANTS = [
    dict(id="D01", cls="X2 estimate outside its own confidence interval", layer="served",
         path="MALARIA_ACT_REVIEW.html", mode=A,
         replace='<p>The pooled effect was RR 1.20 (95% CI 0.60 to 1.10).</p>',
         what="a point estimate printed above the interval printed with it"),
    dict(id="D02", cls="X2 estimate outside its own confidence interval", layer="served",
         path="SGLT2_CKD_REVIEW.html", mode=A,
         replace='<p>Secondary outcome: OR 0.30 (95% CI 0.55 to 0.90).</p>',
         what="a point estimate printed below the interval printed with it"),
]
