#!/usr/bin/env bash
set -euo pipefail
TARGET_ROOT="${1:-/home/node/.openclaw/workspace}"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
mkdir -p "$TARGET_ROOT/skills"
rm -rf "$TARGET_ROOT/skills/research-factory-orchestrator"
cp -a "$SCRIPT_DIR/skills/research-factory-orchestrator" "$TARGET_ROOT/skills/research-factory-orchestrator"
echo "installed research-factory-orchestrator to $TARGET_ROOT/skills/research-factory-orchestrator"
