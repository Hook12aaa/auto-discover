---
name: build-variant
description: "Trigger /build-variant when auto-discover dispatches a genome spec for building and training in an isolated worktree. Composes the architecture from the genome spec, composes the training loop matching the hypothesis budget, trains, writes metrics. All code composed at runtime in the user's repo language. Emits DONE, DONE_WITH_CONCERNS, or BLOCKED."
---

<!-- design-region-clean-of-hard-gates -->

# Build Variant

## Contract

- **Reads**: `genome_spec.json` (inline or path from dispatch prompt; schema: `propose-spec/references/genome-spec-schema.md`), locked hypothesis fields from dispatch prompt (`thesis`, `training_budget`, `pre_registered_metrics`, `seeds`)
- **Writes**: `<worktree-path>/src/*` (composed code), `<worktree-path>/training_metrics.json`, `<worktree-path>/final_metrics.json`
- **References**: `references/training-conventions.md`, `references/early-stopping-rules.md`
- **Verdicts**: DONE, DONE_WITH_CONCERNS, BLOCKED

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
6. Compose early stopping conditions per `references/early-stopping-rules.md`.
7. Compose metric extraction for every metric in pre_registered_metrics.
8. Write all composed files to `<worktree-path>/src/` — one file per unit (data generation, architecture, training loop with its early stopping check, metric extraction).
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

Read `references/training-conventions.md` for per-domain data generation conventions. Compose the data-generation code for the problem instance the hypothesis describes, using the same generation procedure establish-baseline used. Do not introduce a data variant.

### 4. Compose Architecture

Derive the architecture entirely from novel_component.ops_used and composition.strategy. Every op in the spec is present in the composed code; no op absent from the spec is permitted. If an op in ops_used is unfamiliar or ambiguous, compose it from its declared semantics in the hypothesis's genome_constraints — never substitute a known op that resembles it.

### 5. Compose Training Loop

Read `references/training-conventions.md` for optimizer, seed-handling, and checkpoint cadence conventions. Compose a training loop that runs for at most max_epochs and stops at max_wall_clock_minutes, whichever bound is hit first.

### 6. Compose Early Stopping

Read `references/early-stopping-rules.md` for stopping conditions, chance-level computation, patience window rules, and stop_reason values. Compose the stopping conditions into the training loop. Track the best checkpoint apart from the current checkpoint — final_metrics.json records the best checkpoint's values, training_metrics.json records the full per-checkpoint series up to the stop point.

### 7. Compose Metric Extraction

Read `references/training-conventions.md` for per-checkpoint diagnostic requirements. For every metric named in pre_registered_metrics.primary and pre_registered_metrics.secondary, compose extraction code that computes it at each checkpoint and at the end of training. Extract the pre-registered set plus the raw diagnostics evaluate needs (loss, gradient norm per checkpoint).

### 8. Persist Composed Code

Every composed script is written to disk before execution. Write each unit composed in Steps 3-7 — data generation, architecture, training loop (including its early stopping check), metric extraction — to its own file under `<worktree-path>/src/`. The worktree's `src/` directory is the reproducibility artifact.

### 9. Train

Run the composed training loop — the version already written to `<worktree-path>/src/` — inside the pre-created worktree. Run to completion, to a budget bound, or to a composed early stopping trigger — do not intervene with a subjective judgment on top of what the loop already checks.

### 10. Write training_metrics.json

Write the full per-checkpoint time series to `<worktree-path>/training_metrics.json`: epoch (or step), every pre-registered metric's value at that checkpoint, loss, and gradient norm. Include a top-level `stop_reason` field per `references/early-stopping-rules.md`. This is the record evaluate's forensics layer reads — a sparse or averaged series cannot support forensic checks that need every checkpoint.

### 11. Write final_metrics.json

Write the best-checkpoint snapshot to `<worktree-path>/final_metrics.json`: the value of every pre-registered metric at the best checkpoint (not the last checkpoint when early stopping ran past it), plus trainable_params (the total parameter count of the composed architecture), plus `stop_reason` (matching training_metrics.json). For chance-level kills, the "best checkpoint" is the highest primary metric observed, even if it is near chance — this value enters the experiment tree and Pareto comparison like any other. review-strategy needs trainable_params to compute parameter efficiency against the baseline.

### 12. Emit Verdict

Emit one of:
- **DONE** — variant built and trained, training_metrics.json and final_metrics.json both written with every pre-registered metric present.
- **DONE_WITH_CONCERNS** — built and trained, but with flagged concerns (spec ambiguity resolved by inference, an op whose semantics required interpretation, a budget bound hit before the metric time series looked settled).
- **BLOCKED** — cannot build (dispatch context incomplete, worktree path absent, or an op's semantics are unresolvable from the genome spec and genome_constraints).

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
| "This op is basically an attention mechanism, I'll compose it the usual way" | Read the spec's declared semantics in genome_constraints. Reject any substitution of a known op for the spec's definition. |
| "100 epochs is the standard budget for this kind of task" | Read max_epochs from the dispatch prompt's training_budget. The hypothesis declared the budget; convention does not override it. |
| "I can check the experiment tree to see what worked for other variants" | Read only the inline dispatch context. The builder never sees other variants — that is what keeps worktrees isolated. |
| "The loss is clearly not moving, I'll stop early and save time" | Run to the declared budget bound or the composed early stopping trigger — never a mid-run gut read. Whether the run was worth it is evaluate's judgment, not the builder's. |
| "I'll only log metrics at the end since that's all evaluate needs" | Write the full per-checkpoint series. evaluate's forensics layer needs every checkpoint, not just the terminal value. |
| "Training for the full budget is more thorough" | Run the early stopping check at every checkpoint per `references/early-stopping-rules.md`. |
| "The model will improve after 10% budget" | Halt at the 10% checkpoint if accuracy is within the chance-level kill band per `references/early-stopping-rules.md`. |

## Red Flags

- "This looks like a transformer/CNN/[named architecture], let me build it that way"
- "The standard training budget for this task is..."
- "Let me check what the other variants did"
- "The run isn't going anywhere, I'll cut it short"
- "final_metrics.json is enough, no need for the full series"

## Key Principles

- The dispatch prompt is the single source of truth for what to build and how long to train it.
- Every op in the composed architecture traces to the genome spec; nothing is borrowed from a known pattern.
- The training procedure follows `references/training-conventions.md` so later comparisons are not confounded by procedural drift.
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
- **BLOCKED** -- cannot build (dispatch context incomplete, spec references an op outside genome_constraints, worktree path absent)
