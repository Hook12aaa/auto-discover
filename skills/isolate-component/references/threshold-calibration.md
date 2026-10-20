# Threshold Calibration

Defaults are identical across domains. The skill derives task-specific values at runtime when the hypothesis declares no override.

| Gate | Parameter | Mathematical | Graph | Sequence | Tabular | Sequence Labeling |
|---|---|---|---|---|---|---|
| Gradient flow | `max_norm` | 100 | 100 | 100 | 100 | 100 |
| Gradient flow | `mean_norm_limit` | `max_norm` / 10 | `max_norm` / 10 | `max_norm` / 10 | `max_norm` / 10 | `max_norm` / 10 |
| Output range | `bounds` | `hypothesis.search_config` or activation range | same | same | same | same |
| Toy convergence | `loss_ratio_threshold` | 0.1 | 0.1 | 0.1 | 0.1 | 0.1 |
| Toy convergence | `max_steps` | 100 | 100 | 100 | 100 | 100 |

## Override

`hypothesis.search_config` fields override these defaults:

| Default | Overriding field |
|---|---|
| `max_norm` | runtime default — derived by the skill |
| `bounds` | `isolation_output_range` |
| `loss_ratio_threshold` | `isolation_convergence_threshold` |
| `max_steps` | runtime default — derived by the skill |

| Rule | Detail |
|---|---|
| Declared value | Used in place of the table default. |
| Output range with no declared bounds | Bounds come from the component's final activation range. |
| Recording | Every gate JSON file records the threshold actually applied. |
