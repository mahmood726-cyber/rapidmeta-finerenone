# Rollback anchor, recorded before any fast-forward of main

**`origin/main` at 2026-08-26T13:02:11Z is:**

    3c4217c4ae5f5abfd1fc949a11c72e35be0da61f

Recorded by the Paper Studio lane BEFORE proposing a fast-forward, so that undoing is one
command rather than an investigation. Verified by `git ls-remote origin main`, i.e. the
remote's answer, NOT a local ref -- a stale local `main` is what produced this lane's one
retracted finding today.

To undo a fast-forward:

    git push --force-with-lease=main:<the SHA above> origin <the SHA above>:main

`--force-with-lease` pinned to the recorded SHA refuses if anyone else moved main in the
meantime, which is the difference between an undo and a second incident.

The proposed new head is `4d6c18b35` (31 commits ahead, 0 behind, fast-forward).
