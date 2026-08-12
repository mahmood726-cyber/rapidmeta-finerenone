#!/usr/bin/env bash
# Refuse destructive git on a dirty tree.
#
# WHY. On 2026-08-12 `git reset --hard HEAD~1`, run to undo a deliberately
# regressed test commit, reverted every tracked file and destroyed a day of
# uncommitted generator work -- the 8-tab shell, GRADE projection, ten SVG
# figures, the computed verdict, Paper Studio. It survived only as a .pyc that a
# probe had happened to import.
#
# The same command had already destroyed an uncommitted hook edit two hours
# earlier. The rule "never run destructive git on a tree with uncommitted work"
# was written after that first incident and then broken with the same command.
# That is the evidence that a note is not a control: a rule you have to remember
# at the moment of acting fails exactly when you are busy.
#
# This file was itself lost once, to a `git stash push -u` / `pop` cycle, because
# it was untracked. Commit it.
#
# Usage:  bash scripts/safe_git.sh reset --hard HEAD~1
#         SAFE_GIT_FORCE=1 bash scripts/safe_git.sh reset --hard HEAD~1
set -uo pipefail

DESTRUCTIVE=0
case "${1:-}" in
    reset)    for a in "$@"; do [ "$a" = "--hard" ] && DESTRUCTIVE=1; done ;;
    checkout) for a in "$@"; do [ "$a" = "--" ] && DESTRUCTIVE=1; done ;;
    clean)    for a in "$@"; do case "$a" in -*f*) DESTRUCTIVE=1 ;; esac; done ;;
    restore)  DESTRUCTIVE=1 ;;
    stash)    for a in "$@"; do [ "$a" = "drop" ] && DESTRUCTIVE=1; done ;;
esac

if [ "$DESTRUCTIVE" -eq 1 ]; then
    DIRTY="$(git status --porcelain | wc -l | tr -d ' ')"
    if [ "$DIRTY" -ne 0 ] && [ "${SAFE_GIT_FORCE:-0}" != "1" ]; then
        echo "safe_git: REFUSED -- '$*' is destructive and the tree has $DIRTY" >&2
        echo "safe_git: uncommitted change(s). They would be destroyed." >&2
        echo "" >&2
        git status --porcelain | head -20 >&2
        echo "" >&2
        echo "safe_git: stash first:  git stash push -u -m 'before $1'" >&2
        echo "safe_git: NOTE: stash -u then pop has itself lost untracked files" >&2
        echo "safe_git: here. Prefer committing to a scratch branch." >&2
        exit 1
    fi
    echo "safe_git: tree clean -- allowing '$*'" >&2
fi

git "$@"
