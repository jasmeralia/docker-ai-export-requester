#!/usr/bin/env bash
set -euo pipefail

mkdir -p "${PROFILE_PATH:-/app/profile}" "${LOG_DIR:-/app/logs}" "${SCREENSHOT_DIR:-/app/screenshots}"

python /app/scripts/request_export.py
