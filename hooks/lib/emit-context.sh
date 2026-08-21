#!/usr/bin/env bash
set -euo pipefail

emit_context() {
  local content="$1"
  printf '{"hookSpecificOutput": "%s"}\n' "$(printf '%s' "$content" | sed 's/"/\\"/g' | tr '\n' ' ')"
}
