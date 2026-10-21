# Experiment Tree Schema

Defines `experiment-tree.json`, the single state file the orchestrator writes and every search-level skill reads.

```json
{
  "primary_metric_key": "string — from hypothesis.pre_registered_metrics.primary",
  "metric_direction": "maximize | minimize",
  "round": "integer — current round number",
  "nodes": {
    "<hash>": {
      "hash": "string — SHA-256(canonical spec JSON + parent hash)",
      "architecture_name": "string",
      "spec_class": "string — composition fingerprint",
      "parent_id": "string | null",
      "worktree_path": "string | null",
      "isolation_verdict": "COMPONENT_VALIDATED | FAIL | null",
      "evaluate_verdict": "ACCEPT | REJECT | INCONCLUSIVE | null",
      "review_verdict": "KEEP | DISCARD | KEEP_WITH_CONCERNS | null",
      "primary_metric": "float | null",
      "params": "integer | null",
      "round": "integer",
      "stop_reason": "budget_exhausted | patience_exceeded | chance_level_kill | wall_clock_limit | null",
      "structural_basis": "string — probe_N or proto_N id from the round's findings.json",
      "notes": "string"
    }
  },
  "pareto_front": [
    {
      "node_id": "string",
      "architecture_name": "string",
      "spec_class": "string",
      "primary_metric": "float",
      "params": "integer",
      "worktree_path": "string"
    }
  ],
  "pareto_history": [
    {
      "round": "integer",
      "front": ["<pareto_front entry>"]
    }
  ],
  "class_status": {
    "<spec_class>": "UNTRIED | EXPLORING | EXHAUSTED"
  },
  "search_status": "EXPLORING | CONVERGED | BLOCKED"
}
```

## Field Notes

| Field | Type | Writer | Computation rule |
|---|---|---|---|
| `primary_metric_key` | string | auto-discover | Copied verbatim from `hypothesis.pre_registered_metrics.primary` at initialization. Immutable. |
| `metric_direction` | enum | auto-discover | Copied from the hypothesis at initialization. Immutable. |
| `round` | integer | auto-discover | Starts at 0 at initialization. Incremented by 1 at the start of each loop iteration. |
| `nodes` | object | auto-discover | Keyed by `hash`. One entry per emitted genome spec. Entries are never deleted; DISCARDed nodes keep their entry. |
| `nodes.<hash>.hash` | string | auto-discover | `SHA-256(json.dumps(spec, sort_keys=True) + parent_hash)`. `parent_hash` is the empty string for root nodes. |
| `architecture_name` | string | research | Copied from the genome spec. |
| `spec_class` | string | auto-discover | Composition fingerprint computed after research emits the full spec: `(sorted novel_component.ops_used tuple, composition.strategy, composition.layer_arrangement)`. See `skills/research/references/genome-spec-schema.md` § Fingerprint Computation. The orchestrator computes the fingerprint from each emitted spec. |
| `parent_id` | string or null | auto-discover | `hash` of the node this spec refines. null for nodes that start a new direction. |
| `worktree_path` | string or null | build-variant | Absolute path of the isolated worktree. null until build-variant creates it. |
| `isolation_verdict` | enum or null | isolate-component | `COMPONENT_VALIDATED` when all three gates PASS; `FAIL` otherwise. null until isolation runs. |
| `evaluate_verdict` | enum or null | evaluate | Copied from `EVALUATION.json`. null until evaluate runs. |
| `review_verdict` | enum or null | review-strategy | Copied from `REVIEW.json`. null until review-strategy runs. Only ACCEPTed nodes receive a value. |
| `primary_metric` | float or null | evaluate | Value of `primary_metric_key` on the held-out evaluation set. null until evaluate runs. |
| `params` | integer or null | build-variant | Trainable parameter count of the built model. null until build-variant completes. |
| `nodes.<hash>.round` | integer | auto-discover | Value of top-level `round` when the node was created. |
| `stop_reason` | enum or null | build-variant | Reason training ended. Values defined in `skills/build-variant/references/early-stopping-rules.md`. null until training ends. |
| `structural_basis` | string | research | `probe_N` or `proto_N` id the spec traces to. Must exist in the round's `findings.json`. |
| `notes` | string | any | Free-text annotation. Empty string when absent. Never read by a gate. |
| `pareto_front` | array | review-strategy | Non-dominated ACCEPTed nodes after the current round. Dominance rules in `skills/review-strategy/references/pareto-computation.md`. |
| `pareto_front[].node_id` | string | review-strategy | `hash` of a node in `nodes`. |
| `class_status` | object | converge | One key per spec class seen or enumerated. Value is the class's current status. |
| `search_status` | enum | converge | See Convergence Fields. |

## Pareto History Format

Every `pareto_history` entry is an object `{round, front}`.

| Key | Type | Rule |
|---|---|---|
| `round` | integer | The round whose review-strategy pass produced this front. |
| `front` | array | Copy of `pareto_front` at the end of that round. Entries have the same shape as `pareto_front` entries. |

Rules:

- One entry is appended per round, including rounds where the front did not change.
- No entry is a bare array. No entry omits `round`.
- Entries are append-only. Existing entries are never rewritten.
- converge reads the last two entries to test front stability.

## Convergence Fields

| Field | Written by | Read by | Rule |
|---|---|---|---|
| `class_status` | converge | research, converge | Tier 1 result per spec class. |
| `search_status` | converge | auto-discover, Stop hook | `EXPLORING` while any Tier 1 or Tier 2 condition is open. `CONVERGED` when all Tier 2 conditions hold. `BLOCKED` when the tree is unassessable or every untried spec class is exhausted with zero ACCEPTed candidates. |

The Stop hook reads `search_status` to decide whether the session may end. No other skill writes `search_status`.
