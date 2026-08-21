#!/usr/bin/env bash
set -euo pipefail

detect_skill_intent() {
  local prompt="$1"
  shift
  local keywords=("$@")
  local lower_prompt
  lower_prompt="$(printf '%s' "$prompt" | tr '[:upper:]' '[:lower:]')"

  for kw in "${keywords[@]}"; do
    local lower_kw
    lower_kw="$(printf '%s' "$kw" | tr '[:upper:]' '[:lower:]')"
    if [[ "$lower_prompt" == *"$lower_kw"* ]]; then
      return 0
    fi
  done
  return 1
}
