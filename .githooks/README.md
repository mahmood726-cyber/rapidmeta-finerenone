# Git hooks

Repository-level hooks for RapidMeta portfolio.

## pre-push -- regression check (P2-4)

Runs `scripts/regression_check.py` across all 53 `*_REVIEW.html` apps before
every push. The script loads each app in headless Chromium, clears
localStorage, reloads, and verifies 7 signals:

1. No `pageerror` events
2. `RapidMeta.state.trials.length >= 1`
3. At least one trial auto-included
4. Provisional RoB+GRADE banner present and correctly worded
5. Protocol link points to app-specific (not `arni_hf_protocol`)
6. `webr-validator.js` script tag present
7. Analysis-tab pool computes to a finite number (not `--`)

Runtime: ~60 s for the 53-app walk.

## Install (one-time per clone)

```bash
git config core.hooksPath .githooks
```

## Bypass

```bash
SKIP_REGRESSION=1 git push
```

Use sparingly (only when you know the regression is transient, e.g., CDN outage).
