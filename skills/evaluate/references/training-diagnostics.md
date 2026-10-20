# Training Diagnostics

| Check | Condition | Verdict |
|---|---|---|
| NaN detection | Any metric value in any checkpoint is NaN | REJECT |
| Inf detection | Any metric value in any checkpoint is Inf | REJECT |
| Gradient explosion | Gradient norm > 50 for 3 consecutive checkpoints | REJECT |
| Zero-variance output | Model predicts the same value for all inputs | REJECT |
| Incomplete run | Series ends before a declared budget bound or a recorded `stop_reason` | REJECT |
| Data leakage | Training metric within 1% of 1.0 at the first checkpoint | flag for review, recorded in diagnostics |
| Metric completeness | All pre-registered metrics present and numeric in `final_metrics.json`, plus `trainable_params` | required for ACCEPT |
| Unstabilized budget-limited run | Both layers pass and `accuracy_trajectory` is `budget_exhausted` | INCONCLUSIVE |

Every check reads the full `training_metrics.json` series, never the final checkpoint alone. A failing check reports the check name and the checkpoint.

## Trajectory Classification

Trajectory shape is a diagnostic field. It never decides the verdict.

| Field | Values |
|---|---|
| `accuracy_trajectory_shape` | `monotonic_increase`, `spike_then_drop`, `plateau`, `oscillating` |
| `accuracy_trajectory` | `stable_high`, `stable_moderate`, `plateau_low_accuracy`, `spike_then_drop`, `budget_exhausted`, `diverged` |
| `train_test_gap_trajectory` | `converging`, `diverging`, `stable`, `oscillating` |
| `compute_to_threshold` | FLOPs or samples to reach each pre-registered threshold; `"unreached"` when never crossed |
| `peak_accuracy`, `peak_epoch` | Maximum primary metric and the epoch it occurred |
| `collapse_detected` | true when the primary metric peaked and then fell back |

| Rule | Detail |
|---|---|
| Vocabulary | Shapes only. Phenomenon names (grokking and similar) are never recorded. |
| `compute_to_threshold` | `"unreached"` is a first-class value, not an error and not null. |
| Baseline comparison | Never performed here. null-baseline-gate owns it. |
