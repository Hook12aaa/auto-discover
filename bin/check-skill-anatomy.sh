#!/usr/bin/env bash
set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
skills_dir="${repo_root}/skills"

status=0

for skill_file in "${skills_dir}"/*/SKILL.md; do
  skill_name="$(basename "$(dirname "${skill_file}")")"
  reasons=()

  if ! grep -q '^name:' "${skill_file}"; then
    reasons+=("missing frontmatter name")
  fi
  if ! grep -q '^description:' "${skill_file}"; then
    reasons+=("missing frontmatter description")
  fi

  if [[ "${skill_name}" != "using-auto-discover" ]]; then
    if ! grep -q '<HARD-GATE>' "${skill_file}"; then
      reasons+=("missing <HARD-GATE>")
    fi
    if ! grep -q '^## Checklist' "${skill_file}"; then
      reasons+=("missing ## Checklist")
    fi
    if ! grep -q '^## Core Principle$' "${skill_file}"; then
      reasons+=("missing ## Core Principle")
    fi
  else
    if ! grep -qE '^## Core Principles?$' "${skill_file}"; then
      reasons+=("missing ## Core Principle(s)")
    fi
  fi

  if [[ "${#reasons[@]}" -eq 0 ]]; then
    echo "${skill_name}: PASS"
  else
    joined=$(IFS=", "; echo "${reasons[*]}")
    echo "${skill_name}: FAIL ${joined}"
    status=1
  fi
done

exit "${status}"
