"""BANNER ANCHOR -- where a top-of-page notice can safely go, per page GENERATION.

WHY THIS EXISTS
    A banner patcher assumed every page opens with
    `<body class="h-screen flex flex-col overflow-hidden">`. MAVACAMTEN_OHCM did not
    match and the patch declined rather than guessing, which was right -- but leaving
    it skipped would have treated a CLASS as a special case.

    Measured across the 54 cardiology pages:
        24  <body class="h-screen flex flex-col overflow-hidden">   the app generation
        28  NO <body> TAG AT ALL                                    the v1 projector
         2  <body>                                                  bare

    THE 28 ARE NOT MALFORMED. The v1 projector emits
    `<!doctype html><html lang="en"><meta ...><title>...</title><style>...</style>`
    and then content directly. An implied body is valid HTML5, and ARNI -- the
    flagship, live at 6.17 MB -- is one of them. So "no body tag" is a GENERATION,
    not a defect, and more than half the corpus is in it.

WHAT IT RETURNS
    (anchor_bytes, kind) for a page, or (None, reason) when no safe anchor exists.
    The v1 anchor is the single `</style>`, which that generation has exactly once
    and which is immediately followed by the theme toggle -- so inserting after it
    puts the notice in the reader's first screen, as on the app pages.

WHAT THIS DOES NOT ESTABLISH -- written in advance
    - NOT that inserting at the anchor is visually correct. It is structurally safe;
      whether it LOOKS right on a given generation is not checked here.
    - NOT that a page with no anchor is broken. It means this helper cannot place a
      notice on it, and the caller must decline rather than guess.
"""
from __future__ import annotations
import io
import re
import sys

if __name__ == "__main__":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

APP = b'<body class="h-screen flex flex-col overflow-hidden">'
BARE = b"<body>"
V1 = b"</style>"


def anchor_for(raw: bytes):
    """(anchor, kind) -- the bytes to insert AFTER, and which generation it is."""
    if raw.count(APP) == 1:
        return APP, "app"
    if raw.count(BARE) == 1 and raw.count(APP) == 0:
        return BARE, "bare-body"
    if raw.count(b"<body") == 0 and raw.count(V1) == 1:
        return V1, "v1-projector (implied body)"
    if raw.count(b"<body") == 0:
        return None, ("no body tag and %d </style> -- the v1 anchor needs exactly one"
                      % raw.count(V1))
    return None, "body tag present but not in a recognised form"


def selftest() -> int:
    ok = True
    cases = [
        ("app generation", b"<html>" + APP + b"<div>x</div>", "app"),
        ("v1 projector, implied body", b"<html><style>a{}</style>\n<input>", "v1-projector (implied body)"),
        ("bare body", b"<html><body><p>x", "bare-body"),
        ("v1 with TWO style blocks has no safe anchor",
         b"<html><style>a{}</style><style>b{}</style>", None),
    ]
    for label, raw, want in cases:
        a, kind = anchor_for(raw)
        got = kind if a else None
        good = got == want
        ok &= good
        print("  %-52s -> %-30s %s" % (label[:52], str(got)[:30],
                                       "correct" if good else "WRONG"))
    print()
    print("WHAT A FAILURE WOULD LOOK LIKE: the two-style case returning an anchor. That")
    print("would insert a banner between two stylesheets on a page whose structure this")
    print("helper does not actually understand.")
    print("-> SELFTEST PASS" if ok else "-> SELFTEST FAILED")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(selftest())
