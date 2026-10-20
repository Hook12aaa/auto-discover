# Null Comparisons

All three comparisons use only metrics from `pre_registered_metrics`. All three must PASS for NULL_BASELINE_PASSED. Each comparison runs as an executed script.

## Preconditions

| Check | Condition | On failure |
|---|---|---|
| Budget parity | Candidate and baseline `max_epochs` (or `max_steps`) match exactly in training_metrics.json | Stop. The comparison is invalid. |
| Metric scope | Every compared metric appears in `pre_registered_metrics` | Stop. Remove the metric. |

## Comparisons

| Comparison | Candidate metric | Control metric | PASS condition |
|---|---|---|---|
| Shuffled-label | Candidate primary metric on real labels | Same architecture, same data, labels randomly permuted, identical budget and hyperparameters | Candidate exceeds control by the margin declared in the hypothesis; when undeclared, by a statistically meaningful separation computed by the script |
| Constant-predictor | Candidate primary metric | Most-common-class predictor (classification) or training-set mean predictor (regression) | Candidate exceeds the constant predictor on the primary metric |
| Pre-registered baseline | Candidate final metrics | Immutable record from `.auto-discover/baselines/baseline_metrics.json` (null_hypothesis architecture) | Candidate outperforms baseline on the primary metric by at least the declared success threshold |

## Failure Modes Each Comparison Catches

| Comparison | Failure mode |
|---|---|
| Shuffled-label | Memorization, label leakage, evaluation-set contamination |
| Constant-predictor | No learning beyond class prior or mean |
| Pre-registered baseline | No improvement over the conventional approach |

## Result Fields (null_baseline_result.json)

| Field | Type |
|---|---|
| `status` | NULL_BASELINE_PASSED or NULL_BASELINE_FAILED |
| `shuffled_label_comparison` | `{passed, candidate_value, control_value}` |
| `constant_output_comparison` | `{passed, candidate_value, control_value}` |
| `baseline_comparison` | `{passed, candidate_value, baseline_value, threshold}` |
| `budget_parity_verified` | bool |
| `reason` | One line naming every failing comparison |

## Aggregation

| Comparisons passing | Status |
|---|---|
| 3 of 3 | NULL_BASELINE_PASSED |
| 0 to 2 of 3 | NULL_BASELINE_FAILED, naming each failing comparison |

Auxiliary measurements (training speed, parameter count) are recorded and never decide PASS or FAIL.
