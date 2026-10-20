# Evidence Schema

`evidence.json` is written to `<worktree-path>/evidence.json`, alongside training_metrics.json, final_metrics.json, and REVIEW.json.

```json
{
  "hypothesis": "(copied verbatim from locked hypothesis)",
  "hypothesis_sha256": "string",
  "search_convergence": "CONVERGED | BLOCKED",
  "gate_results": {
    "isolation": { "gradient_flow": "PASS|FAIL", "output_range": "PASS|FAIL", "toy_convergence": "PASS|FAIL" },
    "null_baseline": { "verdict": "PASSED|FAILED", "details": {} },
    "reproducibility": { "verdict": "PASSED|FAILED", "details": {} },
    "judge": { "verdict": "CONFIRMS|REFUTES", "score": "float", "reasoning": "string" }
  },
  "comparison_table": { "<metric>": { "candidate": "float", "baseline": "float", "improvement": "string" } },
  "seed_variance_table": { "<seed>": { "<metric>": "float" } },
  "search_summary": { "rounds": "int", "classes_explored": "int", "variants_total": "int" },
  "leading_candidate": { "hash": "string", "architecture_name": "string", "total_parameters": "int" },
  "accuracy_trajectory": "stable_high | stable_moderate | plateau_low_accuracy | spike_then_drop | budget_exhausted | diverged",
  "terminal_verdict": "DISCOVERY_CONFIRMED | DISCOVERY_REFUTED | BLOCKED_DIVERGENCE | BLOCKED_NEEDS_USER",
  "reason": "string — one line naming the deciding factor"
}
```

## Field Sources

| Field | Source file | Rule |
|---|---|---|
| `hypothesis` | `.auto-discover/hypothesis.yaml` | Embedded unchanged |
| `hypothesis_sha256` | `.auto-discover/hypothesis.sha256` | Copied |
| `search_convergence` | converge verdict | Copied verbatim, never re-derived |
| `gate_results.isolation` | `.auto-discover/experiments/<hash>/gates/{gradient_flow,output_range,toy_convergence}.json` | Hash from the dispatch context, never from the worktree path |
| `gate_results.null_baseline` | `<worktree>/null_baseline_result.json` | Verdict and per-comparison details |
| `gate_results.reproducibility` | `<worktree>/reproducibility_result.json` | Verdict and variance details |
| `gate_results.judge` | `<worktree>/judge_verdict.json` or experiment directory copy | Verdict mapped JUDGE_CONFIRMS to CONFIRMS, JUDGE_REFUTES to REFUTES |
| `comparison_table` | `null_baseline_result.json` | One entry per pre-registered metric: candidate value, baseline value, improvement |
| `seed_variance_table` | `reproducibility_result.json` | Raw per-seed value for every pre-registered metric |
| `search_summary` | `experiment-tree.json` | Rounds completed, classes with at least one node, total nodes |
| `leading_candidate` | `experiment-tree.json` pareto_front | The single candidate that entered the end gates |
| `accuracy_trajectory` | leading candidate's `EVALUATION.json` | Diagnostic. Always present. Never gates a verdict. |
| `terminal_verdict` | verdict-rules.md | Applied mechanically |

## Population Rules

| Terminal verdict | Fields populated |
|---|---|
| DISCOVERY_CONFIRMED, DISCOVERY_REFUTED | All fields |
| BLOCKED_DIVERGENCE, BLOCKED_NEEDS_USER | `hypothesis` (when pre-register completed), `hypothesis_sha256`, `search_convergence` (when converge ran), `search_summary`, `terminal_verdict`, `reason`. Fields with no upstream source file hold null. |
