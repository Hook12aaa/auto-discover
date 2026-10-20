# Metric Extraction

| Metric type | Computation | Source |
|---|---|---|
| Primary metric | Value at best checkpoint | `final_metrics.json` |
| Secondary metrics | Values at best checkpoint | `final_metrics.json` |
| Gradient health | Mean gradient norm across checkpoints | `training_metrics.json` |
| Parameter count | Total trainable parameters | `final_metrics.json.trainable_params` |
| Compute used | FLOPs or samples processed | `training_metrics.json` |
| Stop reason | Why training ended | `training_metrics.json.stop_reason` |

| Rule | Detail |
|---|---|
| Metric set | Exactly `pre_registered_metrics.primary` and `.secondary` from the dispatch prompt. |
| Extraction | An executed script reads every value. No value is read by eye. |
| Presence | Every pre-registered metric is present and numeric, never NaN or Inf. |
| Best checkpoint | Highest primary metric observed, not the last checkpoint. |
| Stop reason agreement | `stop_reason` in `final_metrics.json` equals `stop_reason` in `training_metrics.json`. |
| Output | Raw values written to `EVALUATION.json` under `metrics`, with `trainable_params` and the diagnostic fields. |
