# Validation Rules

Every failing check is collected before stopping. BLOCKED_NEEDS_USER carries the complete list of missing or invalid fields.

## Required Fields

| Field | Requirement |
|---|---|
| `thesis` | Present |
| `null_hypothesis` | Present |
| `success_criteria` | Present |
| `failure_criteria` | Present |
| `pre_registered_metrics` | Present with keys `primary`, `secondary`, `forbidden`. `forbidden` may be an empty list; the key must exist. |
| `seeds` | List with at least `min_seeds` entries (search_config value, or derived from the reproducibility-gate requirement) |
| `training_budget` | Contains `max_epochs` and `max_wall_clock_minutes` |
| `genome_constraints` | Contains `max_parameters` |

## Compute-Normalized Budget

| Field in `training_budget` | Meaning |
|---|---|
| `max_compute_flops` | Total floating-point operations |
| `max_samples_seen` | Total training examples processed |

At least one is required alongside any epoch limit. Epoch counts alone anchor the experiment to one architecture's per-epoch compute.

## Phenomenon Denylist

Scanned in `success_criteria`, `failure_criteria`, and every metric name in `pre_registered_metrics`.

| Denied term |
|---|
| grokking |
| double descent |
| lottery ticket |
| neural scaling law |
| phase transition |
| memorization-then-generalization |
| sudden generalization |
| delayed emergence |

| Rejected name | Operational replacement |
|---|---|
| `grokking_delay_ratio` | `compute_to_threshold_ratio` |
| `convergence_speed_epochs_to_99pct` | `samples_to_threshold_accuracy` |

## search_config Fields

Undeclared fields are valid; the consuming skill derives the value at runtime. A declared field must match its type and range.

| Field | Type and range | Derived from |
|---|---|---|
| `isolation_convergence_threshold` | float in (0, 1) | the task's noise floor |
| `max_isolation_retries` | int >= 1 | the search space breadth |
| `diminishing_returns_threshold` | float in (0, 1) | baseline variance |
| `min_exhaustion_depth` | int >= 1 | the search space breadth |
| `pareto_stability_window` | int >= 1 | the population size per round |
| `min_front_diversity` | int >= 1 | the reachable class space |
| `min_seeds` | int >= 2 | the reproducibility-gate statistical requirement |
| `stale_pathway_count` | int >= 1 | min_exhaustion_depth |
| `isolation_output_range` | [float, float] | the activation function range |
| `early_stopping_patience` | int >= 1 | a fraction of the declared training_budget |

`divergence_threshold` is removed. Divergence is a binary fingerprint match.

## Lock Procedure

| Step | Rule |
|---|---|
| Hash | SHA-256 of the hypothesis file's bytes as parsed |
| State directory | Create `.auto-discover/` if absent |
| Hash file | Write `.auto-discover/hypothesis.sha256`. An existing hash file is compared, never overwritten. A mismatch emits BLOCKED_NEEDS_USER. |
| Canonical copy | Copy hypothesis.yaml to `.auto-discover/hypothesis.yaml` after the hash is written |

## Verdict

| Condition | Status |
|---|---|
| Every check passes, hash and copy written | HYPOTHESIS_LOCKED |
| Any check fails, file unparseable, or hash mismatch | BLOCKED_NEEDS_USER with the full list |
