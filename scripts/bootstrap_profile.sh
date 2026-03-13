#!/usr/bin/env bash
set -euo pipefail

mkdir -p "${PROFILE_PATH:-/app/profile}" "${LOG_DIR:-/app/logs}" "${SCREENSHOT_DIR:-/app/screenshots}"

export HEADLESS=false
python /app/scripts/bootstrap_profile.py
