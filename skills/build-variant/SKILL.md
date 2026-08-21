---
name: build-variant
description: "Trigger /build-variant when auto-discover dispatches a genome spec for building and training in an isolated worktree. Composes the architecture from the genome spec, composes the training loop matching the hypothesis budget, trains, writes metrics. All code composed at runtime in the user's repo language. Emits DONE, DONE_WITH_CONCERNS, or BLOCKED."
---

<!-- design-region-clean-of-hard-gates -->

# Build Variant

<HARD-GATE>
Do NOT build without a genome_spec.json and a pre-created worktree path from the dispatch prompt. STOP and report the missing input.
</HARD-GATE>

<HARD-GATE>
Do NOT proceed without matching the declared training budget. STOP and verify budget parity from the dispatch prompt.
</HARD-GATE>

<HARD-GATE>
Do NOT compose architecture code without deriving it from the genome spec. STOP and use only ops and composition fields.
</HARD-GATE>

<HARD-GATE>
Do NOT proceed outside the inline dispatch context. STOP and use only what the dispatch prompt provides.
</HARD-GATE>

<HARD-GATE>
Do NOT execute composed code without first writing it to `<worktree-path>/src/`. STOP and persist every composed file before running any of them.
</HARD-GATE>

## Anti-Pattern

**"I've seen architectures like this before, let me compose it the conventional way."** The genome spec is not a hint toward a known template — it is the complete and only blueprint. A composition that fills gaps from a remembered pattern is not building the spec, it is building something adjacent to it that happens to share a name.

## Core Principle

Build exactly what the genome spec describes at the pre-created worktree path, using only the dispatch context. The builder never sees other variants.

## Process Flow

```dot
digraph build_variant {
  rankdir=LR;
  node [shape=box];
  validate [label="Validate Dispatch"];
  read [label="Read Spec + Hypothesis"];
  data [label="Compose Data Generation"];
  arch [label="Compose Architecture"];
  loop [label="Compose Training Loop"];
  early_stop [label="Compose Early Stopping"];
  metrics [label="Compose Metric Extraction"];
  persist [label="Persist Composed Code\nto src/"];
  train [label="Train"];
  write_train [label="Write training_metrics.json"];
  write_final [label="Write final_metrics.json"];
  emit [label="Emit Verdict"];
  validate -> read -> data -> arch -> loop -> early_stop -> metrics -> persist -> train -> write_train -> write_final -> emit;
}
```

## Checklist

1. Validate the dispatch prompt carries genome_spec.json, the locked hypothesis, and a pre-created worktree path.
2. Read the genome spec and hypothesis in full.
3. Compose the data generation code for the hypothesis's problem instance.
4. Compose the architecture strictly from novel_component.ops_used and composition.strategy.
5. Compose the training loop matching training_budget exactly.
6. Compose an early stopping check into the training loop. Track the primary pre-registered metric on the held-out set at every checkpoint. Stop training when the metric has not improved for a patience window. The patience window is declared in hypothesis.yaml's search_config.early_stopping_patience — if not declared, derive from the declared compute budget (use a fraction of the total budget as patience, not a hardcoded number of epochs).
7. Compose metric extraction for every metric in pre_registered_metrics.
8. Write all composed files to `<worktree-path>/src/` — one file per unit (data generation, architecture, training loop with its early stopping check, metric extraction). These files are the audit trail and re-runnable record.
9. Train the candidate under the declared budget.
10. Write training_metrics.json (full per-checkpoint time series).
11. Write final_metrics.json (best-checkpoint snapshot of every pre-registered metric).
12. Emit DONE, DONE_WITH_CONCERNS, or BLOCKED.

## Step Details

### 1. Validate Dispatch

Confirm the dispatch prompt carries: the genome spec (inline JSON or a path to genome_spec.json), the locked hypothesis fields needed downstream (thesis, training_budget, pre_registered_metrics, seeds), and the pre-created worktree path. The worktree already exists — auto-discover created it before dispatching. If any of these three is absent, emit BLOCKED at once and name the missing piece.

### 2. Read Spec + Hypothesis

From the genome spec, read novel_component (type, class, ops_used), composition (strategy, hybrid_ratio, num_layers), and hyperparameters. From the hypothesis, read training_budget (max_epochs, max_wall_clock_minutes), pre_registered_metrics (primary, secondary), and the first entry of seeds — build-variant trains one seed; reproducibility-gate handles the rest, later, on the final candidate only.

### 3. Compose Data Generation

Compose the data-generation code for the problem instance the hypothesis describes. Use the exact same generation procedure establish-baseline used for the null hypothesis, so the candidate's metrics remain comparable to the baseline at the end of the search. Do not introduce a data variant of your own.

### 4. Compose Architecture

Derive the architecture entirely from novel_component.ops_used and composition.strategy. Every op in the spec must be present in the composed code; no op absent from the spec is permitted. If an op in ops_used is unfamiliar or ambiguous, compose it from its declared semantics in the hypothesis's genome_constraints — never substitute a known op that merely resembles it.

### 5. Compose Training Loop

Compose a training loop that runs for at most max_epochs and stops at max_wall_clock_minutes, whichever bound is hit first. Use the same optimizer, seed-handling, and checkpoint cadence conventions establish-baseline used, so the training procedure itself is not a confound when the candidate is compared to the baseline later.

### 6. Compose Early Stopping

Compose an early stopping check into the training loop. At every checkpoint, evaluate the primary pre-registered metric on the held-out set and compare it to the best value seen so far. Stop training when the metric has not improved for a full patience window. Read the patience window from hypothesis.yaml's search_config.early_stopping_patience. If the field is not declared, derive patience from the declared training_budget — a fraction of the total budget, never a hardcoded epoch count. Track the best checkpoint separately from the current checkpoint: training continues past the best point until the patience window elapses, so the two diverge by design. final_metrics.json records the best checkpoint's values, not the last checkpoint's. training_metrics.json records the full per-checkpoint series up to the stop point regardless of which checkpoint was best.

### 7. Compose Metric Extraction

For every metric named in pre_registered_metrics.primary and pre_registered_metrics.secondary, compose extraction code that computes it at each checkpoint and at the end of training. Extract nothing beyond the pre-registered set plus the raw diagnostics evaluate needs to do its forensics (loss, gradient norm per checkpoint) — a metric that doesn't trace to pre_registered_metrics has no reason to exist in this pipeline.

### 8. Persist Composed Code

Every composed script is written to disk before execution. Write each unit composed in Steps 3-5 and 7 — data generation, architecture, training loop (including its early stopping check), metric extraction — to its own file under `<worktree-path>/src/`. The worktree's `src/` directory is the reproducibility artifact. Anyone with the worktree can independently re-run the experiment by executing the files in `src/`.

### 9. Train

Run the composed training loop — the version already written to `<worktree-path>/src/` — inside the pre-created worktree. Let it run to completion, to a budget bound, or to its composed early stopping trigger — do not intervene with a subjective judgment on top of what the loop already checks; that judgment belongs to evaluate, not to the builder.

### 10. Write training_metrics.json

Write the full per-checkpoint time series to `<worktree-path>/training_metrics.json`: epoch (or step), every pre-registered metric's value at that checkpoint, loss, and gradient norm. This is the record evaluate's forensics layer reads — a sparse or averaged series cannot support forensic checks that need every checkpoint.

### 11. Write final_metrics.json

Write the best-checkpoint snapshot to `<worktree-path>/final_metrics.json`: the value of every pre-registered metric at the best checkpoint (not the last checkpoint when early stopping ran past it), plus trainable_params (the total parameter count of the composed architecture). review-strategy needs trainable_params to compute parameter efficiency against the baseline.

### 12. Emit Verdict

Emit one of:
- **DONE** — variant built and trained, training_metrics.json and final_metrics.json both written with every pre-registered metric present.
- **DONE_WITH_CONCERNS** — built and trained, but with flagged concerns (spec ambiguity resolved by inference, an op whose semantics required interpretation, a budget bound hit before the metric time series looked settled).
- **BLOCKED** — cannot build (dispatch context incomplete, spec references an op outside genome_constraints, worktree path absent).

## Gate Functions

- BEFORE composing anything: "Do I have the genome spec, the hypothesis fields, and the worktree path from the dispatch prompt — not inferred from elsewhere?"
- BEFORE composing the architecture: "Does every op in my composed code trace to novel_component.ops_used, with nothing added and nothing missing?"
- BEFORE composing the training loop: "Are max_epochs and max_wall_clock_minutes read from the dispatch prompt's training_budget, not assumed from convention?"
- BEFORE recording final metrics: "Are these from the best checkpoint (highest primary metric), not the last checkpoint?"
- BEFORE writing final_metrics.json: "Is every metric in pre_registered_metrics.primary and .secondary present with a numeric value?"
- BEFORE emitting DONE: "Do both metrics files exist at the worktree path with the full checkpoint series and the terminal snapshot?"

## Rationalization Table

| You think... | Reality |
|---|---|
| "This op is basically an attention mechanism, I'll compose it the usual way" | Derive the op from the spec's own declared semantics in genome_constraints. Never substitute a known op for the spec's definition. |
| "100 epochs is the standard budget for this kind of task" | Read max_epochs from the dispatch prompt's training_budget. The hypothesis declared the budget; convention does not override it. |
| "I can check the experiment tree to see what worked for other variants" | Use only the inline dispatch context. The builder never sees other variants — that is what keeps worktrees isolated. |
| "The loss is clearly not moving, I'll stop early and save time" | Run to the declared budget bound or the composed early stopping trigger — never a mid-run gut read. Whether the run was worth it is evaluate's judgment, not the builder's. |
| "I'll only log metrics at the end since that's all evaluate needs" | Write the full per-checkpoint series. evaluate's forensics layer needs every checkpoint, not just the terminal value. |
| "Training for the full budget is more thorough" | Track the primary metric and stop when improvement stalls. Continued training past peak degrades the result through overfit. |

## Red Flags

- "This looks like a transformer/CNN/[named architecture], let me build it that way"
- "The standard training budget for this task is..."
- "Let me check what the other variants did"
- "The run isn't going anywhere, I'll cut it short"
- "final_metrics.json is enough, no need for the full series"

## Key Principles

- The dispatch prompt is the single source of truth for what to build and how long to train it.
- Every op in the composed architecture traces to the genome spec; nothing is borrowed from a known pattern.
- The training procedure mirrors establish-baseline's conventions so later comparisons are not confounded by procedural drift.
- Worktree isolation means the builder produces its own record and never reads or writes another variant's state.
- Convergence and quality judgments belong to evaluate, not to build-variant.

## The Bottom Line

```bash
WORKTREE="$1"  # pass the worktree path as argument
STATUS=$(python3 -c "
import json, os, sys
worktree = sys.argv[1]
required = ['training_metrics.json', 'final_metrics.json']
missing = [f for f in required if not os.path.exists(os.path.join(worktree, f))]
if missing:
    print('FAIL: missing ' + ', '.join(missing)); sys.exit()
final = json.load(open(os.path.join(worktree, 'final_metrics.json')))
if 'trainable_params' not in final:
    print('FAIL: final_metrics.json missing trainable_params'); sys.exit()
print('PASS: both metrics files present')
" "$WORKTREE")
echo "VERDICT: $STATUS"
```

## Status Vocabulary

- **DONE** -- variant built and trained, training_metrics.json and final_metrics.json both written with every pre-registered metric present
- **DONE_WITH_CONCERNS** -- built and trained, but with flagged concerns
- **BLOCKED** -- cannot build (dispatch context incomplete, spec references a disallowed op, worktree path absent)
