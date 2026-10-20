# Baseline Conventions

The baseline is the declared `null_hypothesis` trained on the same data, splits, preprocessing, and budget the candidate uses. It is trained, never estimated, and written once.

## Per-Domain Baseline Defaults

| Domain | Baseline architecture | Training conventions | Derivation requirement |
|---|---|---|---|
| Whatever `null_hypothesis` declares | The architecture named in `null_hypothesis` | Repo's data pipeline, splits, and preprocessing; budget read from `training_budget` | Every hyperparameter derived and recorded in derivation.json |
| Mathematical / algorithmic tasks | Conventional model class named in `null_hypothesis` (for example StandardTransformer) | Same data pipeline as the candidate; train within max_epochs, max_wall_clock_minutes, and the compute-normalized bound | Learning rate from micro-batch gradient scale; regularization from parameter-to-example ratio |
| Graph tasks | Conventional graph model named in `null_hypothesis` | Same graph splits and feature construction as the candidate | Same derivation set |
| Sequence tasks | Conventional sequence model named in `null_hypothesis` | Same tokenization and context length as the candidate | Same derivation set |
| Tabular tasks | Conventional tabular model named in `null_hypothesis` | Same feature encoding and splits as the candidate | Same derivation set |
| Vision tasks | Conventional vision model named in `null_hypothesis` | Same augmentation and splits as the candidate | Same derivation set |
| Sequence labeling tasks | Conventional labeler or rule-based system named in `null_hypothesis` (e.g., spaCy `en_core_web_sm` + rule-based matchers) | Same tokenized corpus, BIO labels, and train/val/test split as the candidate | Learning rate and regularization from parameter-to-example ratio; N/A for rule-based baselines with no trainable parameters |

The architecture comes from `null_hypothesis` in every domain. No domain substitutes its own choice.

## Hyperparameter Derivation

| Hyperparameter | Derivation | input_measurement |
|---|---|---|
| Learning rate | Probe gradient scale on one micro-batch of the real training data; set the rate so one update moves each parameter by 1% of its current magnitude | probed gradient scale |
| Regularization strength | Ratio of trainable parameters to training examples; higher ratio demands stronger regularization, lower ratio tolerates weaker or none | parameter-to-example ratio |
| Optimizer | Adam, unless gradient variance across several micro-batches selects a different optimizer | gradient variance across micro-batches |
| Compute budget | Hypothesis-declared compute bound converted to steps at this architecture's measured per-step cost | measured per-step cost |

A value traced to a paper, benchmark, or known recipe is retrieval and is rejected, whether or not the number matches a derived one.

## Preconditions

| Check | Condition | On failure |
|---|---|---|
| Hypothesis lock | `hypothesis.yaml` re-hashes to `.auto-discover/hypothesis.sha256` | BLOCKED_NEEDS_USER |
| Existing baseline | `.auto-discover/baselines/baseline_metrics.json` absent | BLOCKED_NEEDS_USER. Changing a baseline requires re-registration. |
| Budget parity | Training bounds equal the hypothesis `training_budget` exactly | Stop. No extension past the declared budget. |

## Outputs

| File | Contents |
|---|---|
| `.auto-discover/baselines/baseline_metrics.json` | `metrics` (all of `pre_registered_metrics.primary` and `.secondary`, measured from the trained baseline), training budget used, null_hypothesis description |
| `.auto-discover/baselines/derivation.json` | One entry per hyperparameter: `hyperparameter`, `value`, `derivation_method`, `input_measurement` |

Forbidden metrics are not recorded.

## Verdict

| Condition | Status |
|---|---|
| Both files written, primary and secondary metrics present | BASELINE_LOCKED |
| Hash mismatch, existing baseline, or training failure | BLOCKED_NEEDS_USER |
