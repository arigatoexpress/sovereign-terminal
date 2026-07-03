#!/bin/bash
# ai recipe: daily — knowledge vault daily pipeline
set -euo pipefail

echo "[ai::daily] Starting knowledge vault pipeline..."
cd "$HOME/Knowledge/7-Visual-Graphs"

# 1. Lint
echo "[ai::daily] Linting vault..."
./ai-knowledge lint || true

# 2. Pipeline (parse + embed + graph)
echo "[ai::daily] Running full pipeline..."
./ai-knowledge pipeline || true

# 3. Status
echo "[ai::daily] Vault status:"
./ai-knowledge status

# 4. Log to agent memory
echo "[ai::daily] Writing digest stub..."
mkdir -p "$HOME/Knowledge/6-Agent-Memory/daily-digests"
cat > "$HOME/Knowledge/6-Agent-Memory/daily-digests/$(date +%Y-%m-%d)-digest.md" <<EOF
---
title: "Daily Digest — $(date +%Y-%m-%d)"
type: daily-digest
created: $(date +%Y-%m-%d)
---

# Daily Digest — $(date +%Y-%m-%d)

- Pipeline run: $(date -u +%Y-%m-%dT%H:%M:%SZ)
- Agent: ai daily recipe
- Status: completed

## Notes

_Add insights here._
EOF

echo "[ai::daily] Done."
