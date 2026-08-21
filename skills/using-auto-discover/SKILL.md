---
name: using-auto-discover
description: "Bootstrap context for the auto-discover plugin, auto-loaded at session start via SessionStart hook and never user-triggered. Stay in context whenever a user says \"experiment with this architecture\", \"test this thesis\", \"discover a new architecture\", \"run an architecture experiment\", or \"pre-register my hypothesis\", and route every such request through /auto-discover. Defers all gating to the pipeline skills which emit DISCOVERY_CONFIRMED, DISCOVERY_REFUTED, BLOCKED_DIVERGENCE, or BLOCKED_NEEDS_USER."
---

<!-- design-region-clean-of-hard-gates -->

# Using Auto Discover

This plugin orchestrates evolutionary ML architectural discovery. It confines the AI to proposing typed genome specs derived from Polya-method research theses — never free-form architecture code, never a pattern retrieved from training data — pre-registers every metric before any run, validates novel components in isolation before composition, and evolves a population of candidates through spec classes until a two-tier, search-level convergence check says the space is covered. Only then does one candidate, the Pareto front's leader, submit to the end gates.

## Skill Inventory

| Skill | Trigger | Purpose |
|---|---|---|
| `auto-discover` | `/auto-discover` | Orchestrator: evolutionary loop, tree management |
| `pre-register` | dispatched | Validates hypothesis, locks SHA-256 |
| `establish-baseline` | dispatched | Trains null hypothesis, stores immutable baseline |
| `explore` | dispatched | Spawns Polya-method research subagents, proposes batch |
| `propose-spec` | dispatched by explore | Translates research thesis into genome spec |
| `isolate-component` | dispatched | 3 component isolation gates |
| `build-variant` | dispatched | Builds + trains one spec in isolated worktree |
| `evaluate` | dispatched | Scores trained candidate, dynamics as diagnostics |
| `review-strategy` | dispatched | Pareto front, efficiency, stale pathway detection |
| `converge` | dispatched | Two-tier search-level convergence |
| `null-baseline-gate` | dispatched (end) | 3 null comparisons on final candidate |
| `reproducibility-gate` | dispatched (end) | Multi-seed validation on final candidate |
| `judge` | dispatched (end) | Independent scoring, structural distrust |
| `evidence-report` | dispatched (end) | Structured evidence JSON + terminal verdict |

## Core Principles

1. **Pre-registration is immutable.** Hypothesis, metrics, and thresholds are locked behind a SHA-256 before any experiment runs. Post-hoc adjustment turns negative results into false positives.

2. **A system that retrieves its answer cannot discover it.** Every genome spec traces through explore's Polya-method research subagents — understand, plan, carry out, look back — each on a distinct analogy domain, under HARD-GATEs that forbid proposing a known architecture pattern. The search runs as a population across the tree, not one linear attempt: branches evolve concurrently, and a spec class only counts as settled once it has actually been tried.

3. **Convergence is search-level, not training-run-level.** The old single-run convergence check measured loss plateaus and accuracy spikes — signals borrowed from the grokking literature. The two-tier converge skill measures whether the search space itself is covered: within-class exhaustion (Tier 1) and cross-class coverage — minimum classes explored, all settled, Pareto front stable, front diverse (Tier 2). A single strong candidate satisfies none of these on its own.

4. **Discovery means surviving the gates, not that the model said it worked.** Every architecture, however novel its framing, submits to the same mechanical isolation gates, null-baseline comparisons, reproducibility checks, and an independently dispatched judge — and only the search's single leading candidate does, exactly once, after convergence.

## Routing

Route all architecture experiment requests through `/auto-discover`. Do not attempt to run experiments, propose genome specs, evaluate architectures, or declare discoveries without invoking auto-discover.
