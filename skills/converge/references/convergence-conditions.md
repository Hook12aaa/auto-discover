# Convergence Conditions

converge reads `experiment-tree.json` and computes every condition below from it. Spec class = fingerprint of (sorted ops tuple, composition strategy, layer arrangement).

## Tier 1 — Within-Class Exhaustion

Any one firing settles the class. Every threshold comes from `search_config`, with the runtime-derived default recorded when the hypothesis omits the field.

| Condition | Fires when | Class status |
|---|---|---|
| Diminishing returns | Improvement < diminishing_returns_threshold over recent rounds AND depth >= min_exhaustion_depth | EXHAUSTED |
| Depth ceiling | depth >= min_exhaustion_depth with no untried variants at shallower depths | EXHAUSTED |
| Pareto domination | Another class strictly dominates on primary metric AND params, AND depth >= 1 | EXHAUSTED |

## Class Status Assignment

| Class state | Status |
|---|---|
| At least one Tier 1 condition fired | EXHAUSTED |
| Has nodes in the tree, no Tier 1 condition fired | EXPLORING |
| Implied by problem-analysis.json research directions, zero nodes in the tree | UNTRIED |

## Tier 2 — Cross-Class Coverage (all 3 required)

| Condition | Passes when |
|---|---|
| Minimum class count | explored classes (EXHAUSTED or EXPLORING) >= hypothesis minimum or derived default |
| All classes settled | no EXPLORING or UNTRIED classes remain |
| Pareto front stability | the last `pareto_stability_window` entries of pareto_history hold an identical front |

## Search Verdict

| Tree readable and complete | Tier 2 conditions passing | Verdict |
|---|---|---|
| No (missing file, malformed JSON, or missing nodes, pareto_front, pareto_history) | — | BLOCKED |
| Yes | 3 of 3 | CONVERGED |
| Yes | fewer than 3 | EXPLORING, naming each unmet condition and each EXPLORING or UNTRIED class |

## Front Diversity Diagnostic

Recorded in every verdict. Non-gating.

| Field | Value |
|---|---|
| `front_diversity` count | Distinct spec classes represented in the current pareto_front |
| Below min_front_diversity | Record the diagnostic |
| Count equals 1 | Record `front_diversity: "single_class_dominance"` |

When all three Tier 2 conditions hold, a single-class front means that class dominates every other reachable class. CONVERGED is emitted regardless of the diagnostic value.

## Signals Excluded From Convergence

| Signal | Owner |
|---|---|
| Loss plateau, accuracy spike, collapse, budget exhaustion of one run | evaluate (`accuracy_trajectory` diagnostic) |
| Quality of the best single candidate | evaluate and the end gates |
