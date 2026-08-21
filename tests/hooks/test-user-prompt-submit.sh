#!/usr/bin/env bash
set -euo pipefail

CLAUDE_PLUGIN_ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
export CLAUDE_PLUGIN_ROOT

# Test: matching prompt triggers intent detection
output="$(echo '{"prompt":"I want to experiment with this architecture"}' | "$CLAUDE_PLUGIN_ROOT/hooks/user-prompt-submit" 2>&1)" || true

if [[ "$output" == *"auto-discover INTENT DETECTED"* ]]; then
  echo "PASS: matching prompt triggers auto-discover intent"
else
  echo "FAIL: matching prompt did not trigger intent"
  echo "Output: $output"
  exit 1
fi

# Test: non-matching prompt does not trigger
output2="$(echo '{"prompt":"just run the tests"}' | "$CLAUDE_PLUGIN_ROOT/hooks/user-prompt-submit" 2>&1)" || true

if [[ "$output2" == *"INTENT DETECTED"* ]]; then
  echo "FAIL: non-matching prompt triggered intent"
  exit 1
else
  echo "PASS: non-matching prompt correctly ignored"
fi
