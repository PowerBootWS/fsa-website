#!/bin/bash
# Purge the Cloudflare cache for fullsteamahead.ca
# Usage: ./scripts/purge_cloudflare.sh
# Reads CF_ZONE_ID and CF_API_TOKEN from .env or environment

set -e

# Load .env if present and vars not already set
ENV_FILE="$(dirname "$0")/../../.env"
if [ -f "$ENV_FILE" ] && [ -z "$CF_ZONE_ID" ]; then
  set -a
  source "$ENV_FILE"
  set +a
fi

# Also try ~/.env as fallback
if [ -z "$CF_ZONE_ID" ] && [ -f "$HOME/.env" ]; then
  set -a
  source "$HOME/.env"
  set +a
fi

if [ -z "$CF_ZONE_ID" ] || [ -z "$CF_API_TOKEN" ]; then
  echo "ERROR: CF_ZONE_ID and CF_API_TOKEN must be set in .env or environment"
  exit 1
fi

echo "Purging Cloudflare cache for zone $CF_ZONE_ID..."

RESPONSE=$(curl -s -X POST "https://api.cloudflare.com/client/v4/zones/${CF_ZONE_ID}/purge_cache" \
  -H "Authorization: Bearer ${CF_API_TOKEN}" \
  -H "Content-Type: application/json" \
  --data '{"purge_everything":true}')

SUCCESS=$(echo "$RESPONSE" | python3 -c "import sys,json; print(json.load(sys.stdin).get('success', False))")

if [ "$SUCCESS" = "True" ]; then
  echo "Cloudflare cache purged successfully."
else
  echo "Cloudflare purge may have failed. Response:"
  echo "$RESPONSE"
  exit 1
fi
