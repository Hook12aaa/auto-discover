#!/usr/bin/env bash

AUTO_DISCOVER_TRIGGER_KEYWORDS=(
  "experiment with this architecture"
  "test this thesis"
)

if [[ -f "${CLAUDE_PROJECT_DIR:-.}/.auto-discover.sh" ]]; then
  source "${CLAUDE_PROJECT_DIR:-.}/.auto-discover.sh"
fi
