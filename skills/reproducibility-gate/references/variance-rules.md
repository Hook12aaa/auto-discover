# Variance Rules

## Seed Execution

| Rule | Value |
|---|---|
| Seed set | The full `seeds` list from the locked hypothesis (or `seed_count` with its deterministic derivation rule). No subset, no early stop. |
| Per-seed run | build-variant then evaluate, using the leading candidate's genome spec, composition, and budget |
| Storage | `.auto-discover/experiments/<hash>/seeds/<seed>/` holding training_metrics.json and final_metrics.json |

## Per-Seed Evaluate Requirement

| Seed evaluate verdict | Gate effect |
|---|---|
| ACCEPT | Seed counts toward variance computation |
| REJECT or INCONCLUSIVE | Gate fails immediately. No variance computation over a mix of ACCEPT and non-ACCEPT runs. |
| Seed missing | Gate fails. Every declared seed runs. |

A seed's `accuracy_trajectory` is recorded and never replaces its evaluate verdict.

## Variance Computation

| Quantity | Computation |
|---|---|
| values | `final_metrics.json` value of the metric for every seed |
| mean | arithmetic mean across seeds |
| std | standard deviation across seeds, per pre-registered metric |
| cv | std / mean, used when the hypothesis declares coefficient of variation as the variance measure |

Output per metric: `{"metric": name, "values": [...], "mean": float, "std": float, "cv": float}`. Every seed is included; no seed is excluded from the computation.

## Tolerance Check

| Rule | Value |
|---|---|
| Tolerance source | `variance_tolerance` in the locked hypothesis: a single value for all metrics, or per-metric values as declared |
| Per-metric PASS | variance measure <= declared tolerance |
| Metrics checked | Every metric in `pre_registered_metrics`, primary and secondary |
| Tolerance status | Hard threshold fixed at pre-registration |

## Verdict

| Condition | Status |
|---|---|
| Every declared seed run, every seed ACCEPT, every metric within tolerance | REPRODUCIBILITY_PASSED |
| Any seed not run, any seed not ACCEPT, or any metric outside tolerance | REPRODUCIBILITY_FAILED, naming the failing seed(s) or metric(s) |

## Result Fields (reproducibility_result.json)

| Field | Type |
|---|---|
| `status` | REPRODUCIBILITY_PASSED or REPRODUCIBILITY_FAILED |
| `seeds_declared` | int list |
| `seeds_run` | int list |
| `seeds_accepted` | int list |
| `variance_table` | per metric: `{metric, values, mean, std, tolerance, within_tolerance}` |
| `reason` | One line naming the failing seed or metric |
