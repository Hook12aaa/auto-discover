# Early Stopping Rules

| Condition | Trigger | stop_reason value |
|---|---|---|
| Chance-level kill | Primary metric within 1% of chance at 10% budget | `chance_level_kill` |
| Patience exceeded | No improvement for the patience window, counted in checkpoints | `patience_exceeded` |
| Budget exhausted | `max_epochs` or `max_compute_flops` reached | `budget_exhausted` |
| Wall clock limit | `max_wall_clock_minutes` reached | `wall_clock_limit` |

`stop_reason` is written to both `training_metrics.json` and `final_metrics.json`.

## Chance Level Computation

| Task type | Chance level | Kill band |
|---|---|---|
| Binary classification | 0.5 | 0.5 ± 0.01 |
| Multiclass classification | 1/num_classes | 1/num_classes ± 0.01 |
| Regression | Variance of the target | Primary metric within 1% of the target variance |

| Item | Rule |
|---|---|
| Check point | Once, at 10% of `max_epochs` or 10% of `max_compute_flops`, whichever the hypothesis normalizes on. |
| Evaluation set | Held-out set. |
| Inside the band | Stop at once. Record `chance_level_kill`. |
| Outside the band | Training continues. The check never fires again. |

## Patience Window

| Source | Rule |
|---|---|
| `search_config.early_stopping_patience` | Use the declared value. |
| Not declared | Derive from `training_budget` as a fraction of total budget. No fixed epoch count. |

| Item | Rule |
|---|---|
| Comparison | Primary pre-registered metric on the held-out set against the best value so far, at every checkpoint. |
| Best checkpoint | Tracked apart from the current checkpoint. Training continues past the best checkpoint until the window elapses. |
| `final_metrics.json` | Values at the best checkpoint. |
| `training_metrics.json` | Full per-checkpoint series up to the stop point. |
