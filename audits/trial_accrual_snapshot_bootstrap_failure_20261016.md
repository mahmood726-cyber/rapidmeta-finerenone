# Trial accrual CI: ignored snapshot creates false-positive first-run change reports (16 October 2026)

Read-only audit; no clinical effect modification. Main pinned to 0434a90275ed08033911eb1f736344dae0e17af5.

## Reproduction
- Scheduled Actions run 38862388979 on 2026-10-16: CT.gov poll step SUCCESS and printed `Wrote report with 3530 change(s)`; subsequent Commit snapshot step FAILED at `git add .workflow-state/trial_status_snapshot.json`, with `The following paths are ignored ... .workflow-state` and exit 1.
- The root .gitignore intentionally ignores `.workflow-state/`. The workflow stages that exact path without any separate persistence. The file is not present in main's contents endpoint.
- `scripts/workflow/check_trial_status.py` initializes `prev = {}` when baseline is missing, and `diff_snapshots` counts every `old is None` entry as a change. Hence 3,530 first observations are **not evidence of 3,530 clinical trial status changes**.
- `fetch_status` represents transport failure as `{"error":"..."}`, which can enter snapshots or subsequent diffs as if an ordinary status; missing current NCTs are not tested. The workflow's issue step is conditioned on report existence, not persisted, verified change state.
- Workflow attempts unattended `git push origin main`; do not retain that behaviour in a correction.

## Proposed fail-closed remedy
1. Choose a documented, durable, access-controlled snapshot store that does not directly mutate main; preserve a pinned full expected NCT census and source timestamp. Verify previous snapshot and schema before reporting change.
2. Distinguish BOOTSTRAP (persist baseline, **zero clinical-change notifications**), INCOMPLETE_FETCH (retain previous, no notification), SCOPE_MISMATCH (manual review), and verified status/results transitions.
3. Deny notifications if fetch response contains an error/invalid date/missing expected NCT, and condition issue creation on a validated persisted changes manifest rather than mere report presence.
4. Add regression fixtures for bootstrap, partial/429 error, added/removed NCT, duplicate identities, transient failure and actual status/results updates.
5. Remove repeated direct main pushes and prove storage and permissions with real GitHub Actions integration tests.

Reference source blobs: workflow d366a2219bcb8dd26569fa552e9bc0029615a38b; status monitor 51d7fc743acce3aa18031c85f355476eee9fb74a.
Local prototype, 37 synthetic tests and manifest available separately (not GitHub CI). No independent clinical-status verification performed.