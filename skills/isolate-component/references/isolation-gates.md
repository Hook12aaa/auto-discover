# Isolation Gates

Each gate runs on the novel component alone, with no other part of the architecture present. Each gate writes its own JSON file to `.auto-discover/experiments/<hash>/gates/` recording the verdict, the measured values, and the thresholds compared against.

| Gate | What it checks | PASS condition | FAIL condition | Output file |
|---|---|---|---|---|
| Gradient flow | Gradients propagate through the component | Every parameter-tensor gradient norm is finite and > 0, max norm < `max_norm`, mean norm < `max_norm` / 10 | Any NaN, Inf, or zero gradient norm, or max norm >= `max_norm`, or mean norm >= `max_norm` / 10 | `gradient_flow.json` |
| Output range | Component output is bounded | Every output value inside the declared range, with no NaN and no Inf | Any output outside the range, or any NaN or Inf | `output_range.json` |
| Toy convergence | Component learns a trivial task | `final_loss / initial_loss` < `loss_ratio_threshold` within `max_steps` | Ratio >= `loss_ratio_threshold` after `max_steps` | `toy_convergence.json` |

## Gate Procedures

| Gate | Input | Measurement |
|---|---|---|
| Gradient flow | Random input matching the declared input shape | Forward pass, backpropagate a scalar loss, gradient norm at every parameter tensor |
| Output range | Random input matching the declared input shape | Full output tensor, never a sample |
| Toy convergence | Minimal structured synthetic task | Loss at step 0 and at the final step |

## Failure Handling

| Condition | Action |
|---|---|
| Any gate FAIL | Increment the consecutive-failure counter for `novel_component.type`. Re-invoke propose-spec with the failed gate's mode as a constraint mutation. |
| Gradient explosion | Narrow the relevant hyperparameter range. |
| Output range failure | Propose a different normalization operation. |
| Toy convergence failure | Mutate the component's operations or composition. |
| Counter reaches `max_isolation_retries` | Emit BLOCKED_NEEDS_USER. |
| Counter reset | Only when all three gates PASS together. |
| All three gates PASS | Emit COMPONENT_VALIDATED. |
