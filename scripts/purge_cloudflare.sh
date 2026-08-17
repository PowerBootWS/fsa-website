#!/bin/bash
# Purge the Cloudflare cache for fullsteamahead.ca — last step of every deploy.
#
# Usage:
#   ./scripts/purge_cloudflare.sh                       # full-zone purge, core-page fallback
#   ./scripts/purge_cloudflare.sh /a.html /b.html ...    # fallback purges these instead
#   ./scripts/purge_cloudflare.sh https://fullsteamahead.ca/a.html
#
# Reads CF_ZONE_ID and CF_API_MGMT_TOKEN from .env or environment.
#
# WHY THE FALLBACK EXISTS (2026-08-17). A deploy purge failed with
# "Authentication error" on purge_everything while the SAME token verified as
# active, read the zone fine, and succeeded at single-file purge. Full-zone
# purge can be refused on its own — it is a distinct permission from the rest
# of the API — so a script with only one purge path turns a permissions
# problem into hours of stale pages. It now degrades to a file list instead of
# giving up, and it never exits 0 on a degraded purge.
#
# EXIT CODES — deliberately three, not two. This is the LAST step of a deploy,
# so a non-zero exit here does not abort anything half-done; it is the only way
# a degraded purge gets noticed at all.
#   0  full-zone purge succeeded — everything is cold
#   2  full-zone purge FAILED, file-list fallback succeeded — only the listed
#      URLs are cold, anything else may still be stale. Needs a human.
#   1  purge failed outright, or config is missing — nothing was purged

set -uo pipefail

# Overridable only so the fallback path can be exercised against a stub API —
# there is no second real Cloudflare endpoint. Leave unset in normal use.
API="${CF_API_BASE:-https://api.cloudflare.com/client/v4}"
SITE="https://fullsteamahead.ca"

# Core pages purged when no file list is passed. Not a full site map — the
# point is that the pages most likely to be looked at right after a deploy
# come back fresh even when full-zone purge is refused.
DEFAULT_PATHS=(
  "/"
  "/index.html"
  "/enroll.html"
  "/free-practice-exam.html"
  "/library.html"
  "/how-it-works.html"
  "/pricing.js"
  "/styles.css"
  "/sitemap.xml"
)

# ---------------------------------------------------------------- credentials
ENV_FILE="$(dirname "$0")/../../.env"
if [ -f "$ENV_FILE" ] && [ -z "${CF_ZONE_ID:-}" ]; then
  set -a; source "$ENV_FILE"; set +a
fi
if [ -z "${CF_ZONE_ID:-}" ] && [ -f "$HOME/.env" ]; then
  set -a; source "$HOME/.env"; set +a
fi

if [ -z "${CF_ZONE_ID:-}" ] || [ -z "${CF_API_MGMT_TOKEN:-}" ]; then
  echo "ERROR: CF_ZONE_ID and CF_API_MGMT_TOKEN must be set in .env or environment" >&2
  exit 1
fi

# ------------------------------------------------------------------- helpers
cf_purge() {  # $1 = JSON body -> prints raw response
  curl -s -X POST "${API}/zones/${CF_ZONE_ID}/purge_cache" \
    -H "Authorization: Bearer ${CF_API_MGMT_TOKEN}" \
    -H "Content-Type: application/json" \
    --data "$1"
}

# Parses success out of a Cloudflare response. Prints "true"/"false"; a
# response that is not JSON at all (edge HTML, 5xx) counts as false rather
# than crashing the script mid-deploy.
cf_ok() {
  printf '%s' "$1" | python3 -c "
import sys, json
try:
    print('true' if json.load(sys.stdin).get('success') else 'false')
except Exception:
    print('false')
"
}

cf_errors() {
  printf '%s' "$1" | python3 -c "
import sys, json
try:
    body = json.load(sys.stdin)
except Exception:
    print('non-JSON response from Cloudflare'); sys.exit()
errs = body.get('errors') or []
print('; '.join(f\"code {e.get('code')}: {e.get('message')}\" for e in errs) or 'no error detail returned')
"
}

# ------------------------------------------------------- 1. full-zone attempt
echo "Purging Cloudflare cache for zone ${CF_ZONE_ID}..."
RESPONSE=$(cf_purge '{"purge_everything":true}')

if [ "$(cf_ok "$RESPONSE")" = "true" ]; then
  echo "Cloudflare cache purged successfully (full zone)."
  exit 0
fi

FULL_ERR="$(cf_errors "$RESPONSE")"

echo "" >&2
echo "############################################################" >&2
echo "## FULL-ZONE CACHE PURGE FAILED" >&2
echo "##   ${FULL_ERR}" >&2
echo "## Falling back to a file-by-file purge." >&2
echo "############################################################" >&2
echo "" >&2

# ---------------------------------------------------- 2. file-list fallback
if [ "$#" -gt 0 ]; then
  TARGETS=("$@")
else
  TARGETS=("${DEFAULT_PATHS[@]}")
fi

# Accept bare paths or full URLs.
URLS=()
for t in "${TARGETS[@]}"; do
  case "$t" in
    http://*|https://*) URLS+=("$t") ;;
    /*)                 URLS+=("${SITE}${t}") ;;
    *)                  URLS+=("${SITE}/${t}") ;;
  esac
done

# Cloudflare caps a files[] purge at 30 URLs per request.
BATCH=30
FAILED=0
PURGED=0
i=0
while [ "$i" -lt "${#URLS[@]}" ]; do
  CHUNK=("${URLS[@]:i:BATCH}")
  BODY=$(printf '%s\n' "${CHUNK[@]}" | python3 -c "
import sys, json
print(json.dumps({'files': [l.strip() for l in sys.stdin if l.strip()]}))
")
  RESP=$(cf_purge "$BODY")
  if [ "$(cf_ok "$RESP")" = "true" ]; then
    PURGED=$((PURGED + ${#CHUNK[@]}))
    for u in "${CHUNK[@]}"; do echo "  purged  $u"; done
  else
    FAILED=1
    echo "  FAILED batch: $(cf_errors "$RESP")" >&2
    for u in "${CHUNK[@]}"; do echo "  stale?  $u" >&2; done
  fi
  i=$((i + BATCH))
done

if [ "$FAILED" -eq 1 ]; then
  echo "" >&2
  echo "CLOUDFLARE PURGE FAILED ENTIRELY — the site may serve stale content." >&2
  echo "Full-zone error was: ${FULL_ERR}" >&2
  exit 1
fi

echo "" >&2
echo "############################################################" >&2
echo "## PARTIAL PURGE ONLY — ${PURGED} URL(s) purged by file list." >&2
echo "## Full-zone purge is BROKEN: ${FULL_ERR}" >&2
echo "## Anything not in that list may still be served stale." >&2
echo "## Check the CF_API_MGMT_TOKEN zone permissions in Cloudflare." >&2
echo "############################################################" >&2
exit 2
