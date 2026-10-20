# Training Conventions

Conventions build-variant shares with establish-baseline, so the training procedure is never a confound between candidate and baseline.

| Convention | Default | Override source |
|---|---|---|
| Optimizer | Adam | runtime default — derived by the skill |
| Seed handling | Use the first seed in `hypothesis.seeds` | none |
| Checkpoint cadence | Every epoch | runtime default — derived by the skill |
| Data generation | Same procedure as establish-baseline | none |
| Metric extraction | Every pre-registered metric at every checkpoint | none |
| Budget enforcement | `max_epochs` AND `max_wall_clock_minutes`, whichever is reached first | `hypothesis.training_budget` |
| Per-checkpoint diagnostics | Loss and gradient norm recorded beside the pre-registered metrics | none |
| Best checkpoint | Highest primary metric observed, tracked apart from the current checkpoint | none |

## Per-Domain Notes

### Mathematical

| Item | Rule |
|---|---|
| Data | Regenerate the problem instance with the establish-baseline generator and the same seed. |
| Split | Same train/held-out split as establish-baseline. |
| Held-out metric | Evaluated on the held-out split at every checkpoint. |

### Graph

| Item | Rule |
|---|---|
| Data | Same graph generator, node count range, and edge construction as establish-baseline. |
| Batching | Same batching scheme as establish-baseline. |
| Held-out metric | Evaluated on graphs unseen in training. |

### Sequence

| Item | Rule |
|---|---|
| Data | Same sequence generator, length distribution, and vocabulary as establish-baseline. |
| Batching | Same padding and masking scheme as establish-baseline. |
| Held-out metric | Evaluated on sequences unseen in training. |

### Sequence Labeling

| Item | Rule |
|---|---|
| Data | Same tokenized, BIO-labeled corpus as establish-baseline. |
| Split | Same year-stratified train/val/test split as establish-baseline. |
| Representation | Fitted on training-set tokens only; val/test tokens may be OOV. |
| Label format | BIO sequences; labels list is parallel to tokens list. |
| Held-out metric | entity_f1 and venue_recall evaluated on the val split after training. |
| Layout features | Passed as per-token feature dicts when the genome spec enables them; ignored otherwise. |

### Tabular

| Item | Rule |
|---|---|
| Data | Same feature construction and preprocessing as establish-baseline. |
| Split | Same train/held-out split as establish-baseline. |
| Held-out metric | Evaluated on rows unseen in training. |
