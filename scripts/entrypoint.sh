#!/usr/bin/env bash
set -euo pipefail

mode="${1:-request}"

case "$mode" in
  request)
    exec /app/scripts/run_export.sh
    ;;
  bootstrap)
    exec /app/scripts/bootstrap_profile.sh
    ;;
  *)
    echo "Unknown mode: $mode" >&2
    echo "Valid modes: request, bootstrap" >&2
    exit 2
    ;;
esac
