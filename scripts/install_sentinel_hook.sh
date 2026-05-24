#!/bin/sh
# Install the sentinel as a git pre-push hook.
# Usage: scripts/install_sentinel_hook.sh
set -e
REPO_ROOT="$(git -C "$(dirname "$0")/.." rev-parse --show-toplevel)"
HOOK="$REPO_ROOT/.git/hooks/pre-push"
cat > "$HOOK" <<'PRE'
#!/bin/sh
# Sentinel pre-push hook. See scripts/sentinel_check.py for what's enforced.
# Bypass once: SENTINEL_BYPASS=1 git push ...
REPO_ROOT="$(git rev-parse --show-toplevel)"
# Find HTML files that changed in the push range.
# stdin format from git: <local_ref> <local_sha> <remote_ref> <remote_sha>
files=""
while read local_ref local_sha remote_ref remote_sha; do
  if [ "$remote_sha" = "0000000000000000000000000000000000000000" ]; then
    range="$local_sha"
  else
    range="$remote_sha..$local_sha"
  fi
  more=$(git diff --name-only "$range" -- '*.html' 2>/dev/null || true)
  files="$files $more"
done
# Dedupe and filter to existing files.
files=$(echo "$files" | tr ' ' '\n' | sort -u | while read f; do [ -n "$f" ] && [ -f "$REPO_ROOT/$f" ] && echo "$f"; done)
if [ -z "$files" ]; then
  exit 0
fi
echo "Sentinel: scanning $(echo "$files" | wc -l) changed HTML file(s)..."
python "$REPO_ROOT/scripts/sentinel_check.py" $files
PRE
chmod +x "$HOOK"
echo "Installed sentinel pre-push hook -> $HOOK"
echo "To bypass once: SENTINEL_BYPASS=1 git push"
