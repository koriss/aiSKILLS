#!/usr/bin/env bash
set -euo pipefail

if ! command -v openclaw >/dev/null 2>&1; then
  echo "WARNING: openclaw CLI not found; run manual verification later."
  exit 0
fi

openclaw skills list || true
openclaw skills check || true

if openclaw skills list 2>/dev/null | grep -q "research_factory_orchestrator"; then
  echo "OK: research_factory_orchestrator appears in OpenClaw skills list"
else
  echo "WARNING: skill not visible in openclaw skills list. Check workspace path, /new session, gateway restart, and skills allowlist."
fi
