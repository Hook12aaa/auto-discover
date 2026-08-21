#!/usr/bin/env bash
set -euo pipefail

CLAUDE_PLUGIN_ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
export CLAUDE_PLUGIN_ROOT

output="$("$CLAUDE_PLUGIN_ROOT/hooks/session-start" 2>&1)" || true

if [[ "$output" == *"hookSpecificOutput"* ]]; then
  echo "PASS: session-start emits hookSpecificOutput"
else
  echo "FAIL: session-start did not emit hookSpecificOutput"
  echo "Output: $output"
  exit 1
fi
