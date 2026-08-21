#!/usr/bin/env bash
set -euo pipefail

TREE_FILE=".auto-discover/experiment-tree.json"

if [[ ! -f "$TREE_FILE" ]]; then
  echo '{"decision": "block", "reason": "experiment-tree.json not found"}'
  exit 1
fi

python3 -c "
import json, sys, os

with open('$TREE_FILE') as f:
    tree = json.load(f)

status = tree.get('search_status', '')
agents_pending = tree.get('agents_pending', 0)

if agents_pending > 0:
    sys.exit(0)

if status != 'CONVERGED':
    cs = tree.get('class_status', {})
    summary = ', '.join(f'{k}={v}' for k, v in cs.items()) if cs else 'no classes yet'
    print(json.dumps({'decision': 'block', 'reason': f'Search not converged: {summary}'}))
    sys.exit(1)

pf = tree.get('pareto_front', [])
if not pf:
    print(json.dumps({'decision': 'block', 'reason': 'CONVERGED but empty pareto_front'}))
    sys.exit(1)

leading = pf[0]
wt_path = tree['nodes'][leading].get('worktree_path', '')
evidence_path = os.path.join(wt_path, 'evidence.json') if wt_path else ''

if evidence_path and os.path.exists(evidence_path):
    sys.exit(0)
else:
    print(json.dumps({'decision': 'block', 'reason': 'CONVERGED but no evidence report yet'}))
    sys.exit(1)
"
