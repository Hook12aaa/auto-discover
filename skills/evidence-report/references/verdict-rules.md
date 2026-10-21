# Verdict Rules

## Terminal Verdict Table

| converge returned | null-baseline | reproducibility | judge | Terminal verdict |
|---|---|---|---|---|
| CONVERGED | PASSED | PASSED | CONFIRMS | DISCOVERY_CONFIRMED |
| CONVERGED | FAILED | — | — | DISCOVERY_REFUTED |
| CONVERGED | PASSED | FAILED | — | DISCOVERY_REFUTED |
| CONVERGED | PASSED | PASSED | REFUTES | DISCOVERY_REFUTED |
| BLOCKED | — | — | — | BLOCKED_DIVERGENCE |
| (pre-register/baseline/analyze BLOCKED) | — | — | — | BLOCKED_NEEDS_USER |
| (explore BLOCKED) | — | — | — | BLOCKED_NEEDS_USER |
| (all specs failed isolation) | — | — | — | BLOCKED_NEEDS_USER |

"—" means the gate did not run. Gates after a failed gate do not run.

## Evaluation Order

| Priority | Check | Result |
|---|---|---|
| 1 | converge returned BLOCKED because the tree was unassessable, or the search made a full pass through every UNTRIED class without a single ACCEPT in the tree | BLOCKED_DIVERGENCE |
| 2 | pre-register or establish-baseline returned BLOCKED_NEEDS_USER; research BLOCKED with no viable thesis; every spec in a round failed isolate-component max_isolation_retries consecutive times | BLOCKED_NEEDS_USER |
| 3 | converge CONVERGED AND NULL_BASELINE_PASSED AND REPRODUCIBILITY_PASSED AND JUDGE_CONFIRMS | DISCOVERY_CONFIRMED |
| 4 | converge CONVERGED AND any of NULL_BASELINE_FAILED, REPRODUCIBILITY_FAILED, JUDGE_REFUTES | DISCOVERY_REFUTED, naming each failing gate |

## Disambiguation

| Situation | Verdict |
|---|---|
| converge CONVERGED, leading candidate failed an end gate | DISCOVERY_REFUTED, never BLOCKED_DIVERGENCE |
| accuracy_trajectory is diverged or plateau_low_accuracy, all conditions of row 3 hold | DISCOVERY_CONFIRMED. The diagnostic is recorded and gates nothing. |
| One end gate FAILED and JUDGE_CONFIRMS | DISCOVERY_REFUTED. Judge verdict does not offset a failed gate. |

## Inconclusive Refutation

| Condition | Action |
|---|---|
| DISCOVERY_REFUTED with no single clean failing gate (marginal miss on the success threshold) | Offer the user the option to mutate the genome spec and re-enter through the research skill. The user decides. |
