#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
failed=0

for test_file in "$SCRIPT_DIR"/hooks/test-*.sh; do
  echo "--- Running: $(basename "$test_file") ---"
  if bash "$test_file"; then
    echo ""
  else
    failed=1
    echo ""
  fi
done

if (( failed )); then
  echo "SOME TESTS FAILED"
  exit 1
else
  echo "ALL TESTS PASSED"
fi
