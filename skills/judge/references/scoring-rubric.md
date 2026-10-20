# Scoring Rubric

The judge scores from three inputs only: metrics manifest, locked hypothesis, gate results. The genome spec, training logs, and trainer narrative are out of scope. Thresholds are the values locked at pre-registration.

## Criteria

| Criterion | Weight | PASS condition |
|---|---|---|
| Success criteria met | Required | Primary metric (`metric_optimized` when upstream calibration produced one, else the raw value) meets the success threshold declared in the hypothesis. Every other declared success criterion is met. |
| Failure criteria avoided | Required | No failure criterion declared in the hypothesis is triggered by the metrics manifest. |
| Null baseline passed | Required | `null_baseline_result.json` status is NULL_BASELINE_PASSED. |
| Reproducibility passed | Required | `reproducibility_result.json` status is REPRODUCIBILITY_PASSED. |
| Isolation gates passed | Required | gradient_flow, output_range, and toy_convergence JSONs all show PASS. |
| Meaningful improvement | Required | Candidate exceeds the baseline on the primary metric by at least the declared success threshold. |

Every criterion carries weight Required. One failing criterion produces JUDGE_REFUTES. No criterion offsets another.

## Verdict

| Criteria passing | Verdict |
|---|---|
| All 6 | JUDGE_CONFIRMS |
| Any gate criterion (null baseline, reproducibility, isolation) failing | JUDGE_REFUTES, naming the failing gate. No re-scoring of the failed gate. |
| Gates pass, a metric criterion failing | JUDGE_REFUTES, naming the failing metric |

## Scope Limits

| Action | Allowed |
|---|---|
| Score metrics in `pre_registered_metrics` | Yes |
| Score a metric absent from `pre_registered_metrics` | No |
| Compute a new metric or alternate scoring function | No |
| Change a threshold | No |
| Treat a near-miss as a pass | No |
| Read genome_spec.json or architecture descriptions | No |
| Judge as the proposer, builder, evaluator, or reviewer of the candidate | No |

## judge_verdict.json Fields

| Field | Type | Rule |
|---|---|---|
| `status` | enum | JUDGE_CONFIRMS or JUDGE_REFUTES |
| `judge_agent_id` | string | Identifier distinct from the proposer and trainer |
| `prior_gates_passed` | bool | All gate criteria pass |
| `primary_metric` | object | name, value, threshold, meets_threshold |
| `secondary_metrics` | array | name, value, threshold (or null), meets_threshold (or null) |
| `reason` | string | One line naming the failing gate or metric, traceable to manifest numbers |
