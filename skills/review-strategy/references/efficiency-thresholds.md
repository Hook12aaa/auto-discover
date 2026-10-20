# Efficiency Thresholds

## Parameter Efficiency

| Metric | Computation | Threshold source |
|---|---|---|
| Parameter ratio | variant_params / baseline_params | hypothesis.search_config or derived |
| Relative metric improvement | (variant_primary - baseline_primary) / baseline_primary | — |
| Efficiency | relative_metric_improvement / param_ratio | hypothesis.search_config or derived |
| Params per accuracy point | trainable_params / primary_metric | hypothesis.search_config or derived |
| Baseline efficiency ratio | variant efficiency / baseline efficiency | > 1.0 is more efficient |

When the hypothesis omits the thresholds, derive them from baseline variance and parameter scale, and record the derivation in REVIEW.json.

## Complexity Verdict

| Efficiency | param_ratio | Complexity verdict |
|---|---|---|
| Above the high efficiency threshold | any | Worth it |
| Between low and high efficiency thresholds | Below the param_ratio ceiling | Worth it |
| Between low and high efficiency thresholds | At or above the param_ratio ceiling | Diminishing returns |
| Below the low efficiency threshold | any | Not worth it |
| Variant params < baseline params AND primary metric degradation within the significance threshold | any | Worth it (simplification case, overrides computed efficiency) |

## Stale Pathway Detection

| Metric | Computation | Threshold source |
|---|---|---|
| Consecutive unimproved refinements | Walk experiment_history backward within the spec class, counting refinements whose relative primary-metric improvement over their own parent < diminishing_returns_threshold | search_config.diminishing_returns_threshold |
| Stale | consecutive unimproved refinements > stale_pathway_count | search_config.stale_pathway_count |

A "New class" variant has no prior refinement in its class and is never stale.

## Change Classification

| Change type | Condition against the immediate parent |
|---|---|
| New class | Fingerprint (sorted ops + composition strategy + layer_arrangement) matches no prior node. A layer_arrangement difference defines a new class. |
| Architecture refinement | Same fingerprint (including layer_arrangement); a structural field outside the fingerprint, such as num_layers, differs |
| Hyperparameter-only refinement | Same fingerprint, same ops, composition, and layer_arrangement; only hyperparameter values differ |

## Decision Matrix

| Complexity | Stale | Pareto | Verdict |
|---|---|---|---|
| Worth it | Not stale | Dominant or Neutral | KEEP |
| Worth it | Not stale | Dominated | KEEP_WITH_CONCERNS |
| Worth it | Stale | Dominant | KEEP_WITH_CONCERNS |
| Worth it | Stale | Neutral or Dominated | DISCARD |
| Diminishing returns | Not stale | Dominant | KEEP_WITH_CONCERNS |
| Diminishing returns | any | Neutral or Dominated | DISCARD |
| Not worth it | any | any | DISCARD |

## Untried-Class Floor

| spec_class_status before this variant | Change type | Verdict rule |
|---|---|---|
| UNTRIED | New class | Verdict floors at KEEP_WITH_CONCERNS. A matrix result of DISCARD becomes KEEP_WITH_CONCERNS. KEEP stays KEEP. |
| EXPLORING | any | Matrix verdict applies unchanged |
