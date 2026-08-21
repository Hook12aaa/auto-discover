#!/usr/bin/env bash
set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
skills_dir="${repo_root}/skills"

vocab=(
  # Search-level (converge)
  EXPLORING CONVERGED BLOCKED
  # Spec-class (within converge)
  UNTRIED EXHAUSTED
  # Experiment (evaluate)
  ACCEPT REJECT INCONCLUSIVE
  # Review (review-strategy)
  KEEP DISCARD KEEP_WITH_CONCERNS
  # Build (build-variant)
  DONE DONE_WITH_CONCERNS
  # Pipeline
  HYPOTHESIS_LOCKED BASELINE_LOCKED SPEC_EMITTED COMPONENT_VALIDATED
  NULL_BASELINE_PASSED NULL_BASELINE_FAILED
  REPRODUCIBILITY_PASSED REPRODUCIBILITY_FAILED JUDGE_CONFIRMS JUDGE_REFUTES
  DISCOVERY_CONFIRMED DISCOVERY_REFUTED BLOCKED_DIVERGENCE BLOCKED_NEEDS_USER
)

is_known() {
  local token="$1"
  for known in "${vocab[@]}"; do
    if [[ "${token}" == "${known}" ]]; then
      return 0
    fi
  done
  return 1
}

unknown_tokens=()

while IFS= read -r token; do
  [[ -z "${token}" ]] && continue
  if ! is_known "${token}"; then
    unknown_tokens+=("${token}")
  fi
done < <(grep -hoE '(emit(s)?|VERDICT:)[^A-Za-z_]*[A-Z_]{5,}' "${skills_dir}"/*/SKILL.md \
    | grep -v '\$[A-Z_]\{5,\}$' \
    | grep -oE '[A-Z_]{5,}$' \
    | sort -u)

if [[ "${#unknown_tokens[@]}" -eq 0 ]]; then
  echo "PASS"
  exit 0
else
  joined=$(IFS=", "; echo "${unknown_tokens[*]}")
  echo "FAIL ${joined}"
  exit 1
fi
