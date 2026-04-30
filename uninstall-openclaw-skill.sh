#!/usr/bin/env bash
set -euo pipefail
WORKSPACE="${1:-/home/node/.openclaw/workspace}"
rm -rf "$WORKSPACE/skills/research-factory-orchestrator"
echo "Removed research-factory-orchestrator from $WORKSPACE/skills"
