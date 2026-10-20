# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**auto-discover** is a Claude Code plugin for evolutionary ML architectural discovery. It ships as pure Markdown/YAML skills with no shipped code -- Claude Code composes and executes every verification script in-context, at runtime, in the language the experiment already uses.

Instead of training one genome spec through a linear pipeline, v2 evolves a population of candidates across an experiment tree. A problem analysis phase identifies what the task's mathematical structure requires — symmetries, invariances, information bounds, baseline failure modes — and produces structured research directions. Investigation agents then turn those structural signals into concrete genome specs, each traceable to a checked property of the problem. Convergence is judged at the level of the search space -- has this architecture family been exhausted, has that one been tried at all -- not at the level of a single training run's loss curve. Only the search's single leading candidate, chosen after convergence, submits to the null-baseline, reproducibility, and judge gates.

## Quick Start

```
/auto-discover hypothesis.yaml
```

Single entry point. Write a `hypothesis.yaml` declaring the thesis, null hypothesis, success/failure criteria, pre-registered metrics, seeds, training budget, and genome constraints. The orchestrator drives the evolutionary loop:

```
pre-register -> establish-baseline -> analyze-problem -> initialize experiment tree
-> LOOP {
    explore (investigation agents per structural direction) -> propose-spec (per proposal)
    -> isolate-component (per spec) -> build-variant (parallel worktrees)
    -> evaluate (per variant) -> review-strategy (Pareto front, efficiency)
    -> converge (two-tier search-level check)
    -> EXPLORING: loop again | CONVERGED: exit with the leading candidate
}
-> null-baseline-gate -> reproducibility-gate -> judge -> evidence-report
```

## Terminal Verdicts

- **DISCOVERY_CONFIRMED** -- `converge` returned CONVERGED and the leading candidate survived null-baseline-gate, reproducibility-gate, and judge.
- **DISCOVERY_REFUTED** -- `converge` returned CONVERGED but the leading candidate failed null-baseline-gate, reproducibility-gate, or judge.
- **BLOCKED_DIVERGENCE** -- `converge` itself returned BLOCKED because the experiment tree was unassessable, or the search exhausted every untried spec class without producing a single ACCEPTed candidate anywhere.
- **BLOCKED_NEEDS_USER** -- the pipeline stopped on a missing hypothesis field, `explore` found no viable research thesis, or a round's specs all failed component isolation three times.

## Key Constraint

The plugin ships Markdown only. There is no `scripts/` directory, no Python engine, no bundled library. Every numerical check -- spec-class exhaustion, Pareto dominance, null comparisons, seed variance, gate scoring -- is a script Claude composes and executes inside the user's experiment repo, in whatever language that repo already uses. The SKILL.md tells Claude what to check and what to print; Claude writes and runs the script.

## Plugin Structure

- `skills/` -- SKILL.md contract files plus colocated `references/` directories with domain knowledge (decision tables, catalogs, schemas)
- `commands/` -- `/auto-discover` slash command stub
- `hooks/` -- SessionStart bootstrap that injects `using-auto-discover`
- `bin/` -- shell checks that verify skill anatomy and verdict vocabulary
- `.claude-plugin/` -- plugin manifest

## Adding a New Domain

Adding a new problem domain (e.g., time-series, vision) requires reference doc sections, not skill rewrites:

1. Add a row to `skills/analyze-problem/references/domain-detection.md`
2. Add a section to `skills/analyze-problem/references/analysis-catalog.md`
3. Add a section to `skills/explore/references/component-vocabulary.md`
4. Add a section to `skills/build-variant/references/training-conventions.md`
5. Add a section to `skills/isolate-component/references/threshold-calibration.md`
6. Add a section to `skills/establish-baseline/references/baseline-conventions.md`

## Key Concepts

### Pre-registration is immutable

`pre-register` locks the hypothesis's thesis, null hypothesis, criteria, metrics, seeds, and budget behind a SHA-256 hash before any experiment runs. Nothing downstream can add a metric, loosen a threshold, or fill in a missing field after the fact.

### Analyze, then assemble

The `analyze-problem` skill runs 7 structural checks on the task — decomposition, algebraic structure, symmetries, information requirements, compositional structure, baseline failure analysis, and theoretical constraints — and produces structured research directions. Each direction connects a checked observation to an architectural implication. `explore` reads these directions and spawns investigation agents that turn structural signals into concrete proposals. Every genome spec traces to a specific research direction, which traces to a specific structural property that was verified. The search runs as a population across the experiment tree, not one linear attempt.

### Convergence is search-level, not training-run-level

The old single-run convergence check measured loss plateaus and accuracy spikes -- signals borrowed from the grokking literature, applied to one candidate. The two-tier `converge` skill instead measures whether the search space itself is covered: within-class exhaustion (diminishing returns, depth ceiling, or Pareto domination, per spec class) and cross-class coverage (minimum classes explored, every class settled, Pareto front stable for two iterations, front diverse across at least two classes). A single strong candidate satisfies none of these by itself. Training-run dynamics (grounded, collapsed, budget-exhausted) become a diagnostic field on `evaluate`'s output, not the convergence signal.

### Discovery means surviving the gates, not that the model said it worked

Every architecture, however novel its framing, submits to the same mechanical isolation gates, null-baseline comparisons, reproducibility checks, and an independently dispatched judge -- and only the search's single leading candidate does, exactly once, after `converge` returns CONVERGED. The proposer, the builder, and the judge are never the same agent; `judge` sees only the metrics manifest, the hypothesis file, and gate results, never the genome spec.

### Isolation before composition

`isolate-component` runs three gates on a novel component -- gradient flow, output range, toy convergence -- before it is ever composed into a full architecture. After three consecutive failures on the same component type, the pipeline stops and asks the user.

## Skills

| Skill | What it does |
|---|---|
| `using-auto-discover` | Bootstrap -- loaded at session start, establishes the skill inventory and core principles |
| `auto-discover` | Orchestrator -- manages the experiment tree, runs the evolutionary loop, dispatches the end gates |
| `pre-register` | Validates the hypothesis YAML, computes and locks its SHA-256 |
| `establish-baseline` | Trains the declared null hypothesis, stores an immutable baseline |
| `analyze-problem` | Structural analysis of the task — symmetries, invariances, information requirements, baseline failure mode. Produces research directions |
| `explore` | Reads problem analysis signals, spawns investigation agents per structural direction, enforces divergence |
| `propose-spec` | Translates one research proposal into a typed genome spec within declared constraints |
| `isolate-component` | Runs 3 isolation gates on a novel component before composition |
| `build-variant` | Builds and trains one genome spec in an isolated worktree |
| `evaluate` | Scores one trained candidate against pre-registered metrics; convergence type is a diagnostic, not the verdict |
| `review-strategy` | Scores a variant's contribution to the search: Pareto dominance, parameter efficiency, stale-pathway detection |
| `converge` | Two-tier search-level convergence: within-class exhaustion, cross-class coverage |
| `null-baseline-gate` | 3 null comparisons on pre-registered metrics only, run once on the leading candidate |
| `reproducibility-gate` | Multi-seed variance check against declared tolerance, run once on the leading candidate |
| `judge` | Independent scoring agent, sees only metrics manifest, hypothesis, and gate results |
| `evidence-report` | Writes structured evidence JSON and emits the terminal verdict |

## Key Principles

- **Execute, don't eyeball** -- every spec-class exhaustion check, null comparison, and variance calculation is a composed script, never a read-the-numbers judgment call
- **Structural distrust** -- no agent both produces and approves its own work
- **Pre-registration is immutable** -- the hypothesis, its metrics, and its thresholds are locked before any experiment runs
- **Analyze, then assemble** -- structural analysis identifies what the task requires; explore assembles from those signals, not from recalled patterns
- **Convergence is search-level, not training-run-level** -- a candidate's own training dynamics are a diagnostic, never the convergence signal
- **Composed, not shipped** -- the plugin ships Markdown only; every verification script is written and run in-context

## Status Vocabulary

- **Search-level** (`converge`): EXPLORING, CONVERGED, BLOCKED
- **Spec-class** (within `converge`): UNTRIED, EXHAUSTED
- **Experiment** (`evaluate`): ACCEPT, REJECT, INCONCLUSIVE
- **Review** (`review-strategy`): KEEP, DISCARD, KEEP_WITH_CONCERNS
- **Build** (`build-variant`): DONE, DONE_WITH_CONCERNS
- **Pipeline**: HYPOTHESIS_LOCKED, BASELINE_LOCKED, SPEC_EMITTED, COMPONENT_VALIDATED, NULL_BASELINE_PASSED, NULL_BASELINE_FAILED, REPRODUCIBILITY_PASSED, REPRODUCIBILITY_FAILED, JUDGE_CONFIRMS, JUDGE_REFUTES, DISCOVERY_CONFIRMED, DISCOVERY_REFUTED, BLOCKED_DIVERGENCE, BLOCKED_NEEDS_USER
