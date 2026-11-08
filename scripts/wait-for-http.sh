#!/usr/bin/env bash
# Usage: wait-for-http.sh URL [TIMEOUT_SECONDS]
# Polls URL until it returns HTTP 2xx, or fails after the timeout.
set -euo pipefail
url="$1"; timeout="${2:-120}"; waited=0
until curl -fsS -o /dev/null "$url"; do
  (( waited >= timeout )) && { echo "timed out after ${timeout}s waiting for $url" >&2; exit 1; }
  sleep 3; waited=$((waited + 3))
done
echo "$url is up (${waited}s)"
