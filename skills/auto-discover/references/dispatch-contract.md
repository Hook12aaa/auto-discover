# Dispatch Contract

The orchestrator uses two verbs: **Invoke** (Skill tool, runs inline in the orchestrator's context) and **Dispatch** (Agent tool, runs in a fresh subagent). The orchestrator pre-creates what the dispatched agent needs, inlines the listed values into the dispatch prompt, and verifies the listed artifacts on return.

## Vocabulary

- **Invoke** = `Skill()`. Runs in the orchestrator's own context. Use only for fast stages that need the orchestrator's state.
- **Dispatch** = `Agent()` or `Agent(isolation: "worktree")`. Runs in a fresh subagent. Use for any stage that composes code, runs scripts, or performs long-running compute.
- **The orchestrator never runs Bash for code composition or training.** All code composition and execution happens in dispatched agents. Only JSON summaries return to the orchestrator.

## Dispatch Method

| Stage | Verb | Isolation | Model | Reason |
|---|---|---|---|---|
| pre-register | Invoke | — | — | Reads and validates YAML, no compute |
| establish-baseline | Dispatch | worktree | sonnet | Composes and trains the baseline — long-running compute |
| research | Dispatch | worktree | opus | Probes, web search, prototyping — needs worktree + full reasoning |
| isolate-component | Dispatch (per spec) | worktree | sonnet | Each spec's isolation gates run independently |
| build-variant | Dispatch (per spec) | worktree | sonnet | Each variant trains in its own worktree — the core parallelism |
| evaluate | Dispatch (per variant) | worktree | sonnet | Composes and runs forensic validation scripts |
| review-strategy | Dispatch (per variant) | none | sonnet | Reads evaluation JSON and computes Pareto — no code composition |
| converge | Invoke | — | — | Reads the tree the orchestrator just aggregated — needs orchestrator context |
| null-baseline-gate | Dispatch | worktree | sonnet | Trains shuffled-label and constant-predictor controls |
| reproducibility-gate | Dispatch | worktree | sonnet | Re-trains across seed set |
| judge | Dispatch | none | opus | Reads metrics only — must be a separate agent from proposer/builder |
| evidence-report | Invoke | — | — | Writes final JSON from existing artifacts |

## Dispatch Prompt Structure

Every dispatch prompt includes:

1. **Skill path:** "Read `skills/<name>/SKILL.md` for your contract and `skills/<name>/references/` for domain knowledge."
2. **Inline context:** The values from the Dispatch Table's Inline column.
3. **Return contract:** "Write your results to `<path>`. Return: verdict, artifact paths, concerns if any."

Subagents do not inherit the orchestrator's skills. The skill path in the dispatch prompt is how the agent learns its contract.

## Dispatch Table

| Stage | Pre-create | Inline to dispatch | Verify on return |
|---|---|---|---|
| establish-baseline | `.auto-discover/baselines/` | hypothesis path, hypothesis.sha256 path | baseline_metrics.json exists |
| research | — | hypothesis path, baseline path, experiment-tree path, round number, prior findings log path | genome_spec.json exists per returned hash in worktrees |
| isolate-component | — | genome_spec.json path | gates/*.json exist, all PASS |
| build-variant | `.auto-discover/worktrees/<hash>/` | genome_spec path, training_budget, pre_registered_metrics, seeds[0], genome_constraints, worktree path | training_metrics.json, final_metrics.json at worktree path |
| evaluate | — | worktree path, pre_registered_metrics | EVALUATION.json with verdict |
| review-strategy | — | evaluation_result, variant_params, baseline_params, baseline_primary, metric_direction, pareto_front | REVIEW.json with verdict |
| null-baseline-gate | — | worktree path, baseline_metrics.json path | null_baseline_result.json with verdict |
| reproducibility-gate | — | worktree path, seeds, variance_tolerance | reproducibility_result.json with verdict |
| judge | — | metrics manifest, hypothesis path, gate results | judge_verdict.json with verdict |
| evidence-report | — | worktree path (or partial tree state) | evidence.json with terminal_verdict |

## Worktree Persistence

Agents dispatched with `isolation: "worktree"` get an auto-cleaned worktree — it is deleted if the agent makes no changes. For stages that must persist files (build-variant writes training_metrics.json and final_metrics.json to the pre-created worktree path), the agent writes to `.auto-discover/worktrees/<hash>/` which is in the main repo, not the worktree's isolated copy. The orchestrator verifies the files exist at the main repo path after the agent returns.

## Dispatch Timing

| Stage | Dispatch trigger |
|---|---|
| research | converge returned EXPLORING, or the first loop entry |
| isolate-component | genome_spec.json exists for specs in the round — dispatch all specs together in one Agent batch |
| build-variant | That spec's own isolate-component returned COMPONENT_VALIDATED — dispatch immediately, do not wait for siblings |
| evaluate | That variant's build-variant returned DONE or DONE_WITH_CONCERNS — dispatch immediately |
| review-strategy | That variant's evaluate returned ACCEPT — dispatch immediately |
| converge | Every spec of the round is terminal and the tree is aggregated |
| null-baseline-gate | converge returned CONVERGED |
| reproducibility-gate | null-baseline-gate returned NULL_BASELINE_PASSED |
| judge | reproducibility-gate returned REPRODUCIBILITY_PASSED |
| evidence-report | Any loop exit or end-gate failure |

## Parallel Dispatch Pattern

The evolutionary loop dispatches multiple agents in a single message for independent work:

```
# Isolation: dispatch all specs of a round together
Agent(name: "isolate-spec-a1b2", isolation: "worktree", model: "sonnet",
  prompt: "Read skills/isolate-component/SKILL.md. Run isolation gates on <path>...")
Agent(name: "isolate-spec-c3d4", isolation: "worktree", model: "sonnet",
  prompt: "Read skills/isolate-component/SKILL.md. Run isolation gates on <path>...")

# Build: dispatch each as its own isolation clears
Agent(name: "build-a1b2", isolation: "worktree", model: "sonnet",
  prompt: "Read skills/build-variant/SKILL.md. Build and train <spec> at <worktree>...")

# Evaluate: dispatch each as its own build completes
Agent(name: "eval-a1b2", isolation: "worktree", model: "sonnet",
  prompt: "Read skills/evaluate/SKILL.md. Score the variant at <worktree>...")
```

## Failure Routing

| Returned verdict | Orchestrator action |
|---|---|
| pre-register BLOCKED_NEEDS_USER | Stop. Invoke evidence-report with partial tree state. |
| establish-baseline BLOCKED_NEEDS_USER | Stop. Invoke evidence-report with partial tree state. |
| research BLOCKED | Invoke evidence-report with partial tree state. |
| isolate-component BLOCKED_NEEDS_USER for every spec of a round | Invoke evidence-report with partial tree state. |
| build-variant BLOCKED | Mark the node terminal in the tree. Do not dispatch evaluate. |
| evaluate REJECT or INCONCLUSIVE | Mark the node terminal. Do not dispatch review-strategy. |
| converge BLOCKED | Invoke evidence-report with partial tree state. |
| null-baseline-gate NULL_BASELINE_FAILED | Invoke evidence-report. Skip reproducibility-gate and judge. |
| reproducibility-gate REPRODUCIBILITY_FAILED | Invoke evidence-report. Skip judge. |

## Separation Rules

| Role | Must differ from |
|---|---|
| judge | the agents that proposed, built, evaluated, or reviewed the leading candidate |
