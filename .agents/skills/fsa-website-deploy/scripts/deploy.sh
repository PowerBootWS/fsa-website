#!/bin/bash
set -e

# FSA Website — Full Deploy Script
# Performs: git commit/push, Docker rebuild, Google sitemap submit, Cloudflare purge

ROOT="/home/debian/projects/fsa/fsa-website"
COMPOSE="$ROOT/docker-compose.yml"

cd "$ROOT"

echo "=== 1. Inspecting changes ==="
git status --short
CHANGED=$(git status --short)

if [ -z "$CHANGED" ]; then
  echo "No changes to deploy. Exiting."
  exit 0
fi

echo ""
echo "=== 2. Checking for new/deleted pages ==="
# Detect new root-level HTML pages
NEW_PAGES=$(git status --short | grep -E '^\?\? .*\.html$' | awk '{print $2}' || true)
DEL_PAGES=$(git status --short | grep -E '^ D .*\.html$' | awk '{print $2}' || true)

if [ -n "$NEW_PAGES" ] || [ -n "$DEL_PAGES" ]; then
  echo "New pages:"
  echo "$NEW_PAGES"
  echo "Deleted pages:"
  echo "$DEL_PAGES"
  echo "WARNING: sitemap.xml may need manual updating before commit."
  echo "Run the deploy skill's sitemap update step first if needed."
fi

echo ""
read -r -p "Continue with commit/push/deploy? [Y/n] " CONFIRM
if [[ "$CONFIRM" =~ ^[Nn]$ ]]; then
  echo "Cancelled."
  exit 0
fi

echo ""
echo "=== 3. Commit and push ==="
read -r -p "Commit message: " MSG
git add -A
git commit -m "$MSG"
git push origin master

echo ""
echo "=== 4. Rebuild Docker container ==="
docker compose -f "$COMPOSE" build --no-cache
docker rm -f fsa-website 2>/dev/null || true
docker compose -f "$COMPOSE" up -d

echo ""
echo "=== 5. Submit sitemap to Google ==="
python3 "$ROOT/scripts/submit_to_google.py" --sitemap-only

echo ""
echo "=== 6. Purge Cloudflare cache ==="
bash "$ROOT/scripts/purge_cloudflare.sh"

echo ""
echo "=== Deploy complete ==="
