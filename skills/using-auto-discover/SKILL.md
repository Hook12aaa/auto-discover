---
name: using-auto-discover
description: "Bootstrap context for the auto-discover plugin, auto-loaded at session start via SessionStart hook and never user-triggered. Stay in context whenever a user says \"experiment with this architecture\", \"test this thesis\", \"discover a new architecture\", \"run an architecture experiment\", or \"pre-register my hypothesis\", and route every such request through /auto-discover. Defers all gating to the pipeline skills which emit DISCOVERY_CONFIRMED, DISCOVERY_REFUTED, BLOCKED_DIVERGENCE, or BLOCKED_NEEDS_USER."
---

<!-- design-region-clean-of-hard-gates -->

# Using Auto Discover

This plugin orchestrates evolutionary ML architectural discovery. It analyzes the mathematical structure of the task to identify what any solution requires — symmetries, invariances, information bounds, baseline failure modes — and produces structured research directions. Explore's investigation agents then turn those structural signals into concrete genome specs, each traceable to a checked property of the problem. The search evolves a population through spec classes until a two-tier convergence check says the space is covered. Only then does one candidate, the Pareto front's leader, submit to the end gates.

## Skill Inventory

| Skill | Trigger | Purpose |
|---|---|---|
| `auto-discover` | `/auto-discover` | Orchestrator: evolutionary loop, tree management |
| `pre-register` | dispatched | Validates hypothesis, locks SHA-256 |
| `establish-baseline` | dispatched | Trains null hypothesis, stores immutable baseline |
| `analyze-problem` | dispatched | Structural analysis: symmetries, invariances, information requirements, baseline failure mode. Produces research directions |
| `explore` | dispatched | Reads problem analysis signals, spawns investigation agents per structural direction, enforces divergence |
| `propose-spec` | dispatched by explore | Translates research proposal into genome spec |
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

1. **Analyze, then assemble.** The problem analysis identifies what the task's mathematical structure requires of any solution. Explore reads those signals and assembles proposals. The creative work is grounded in checked structural properties, not in recalled knowledge of what architectures exist.

2. **Pre-registration is immutable.** Hypothesis, metrics, and thresholds are locked behind a SHA-256 before any experiment runs.

3. **Convergence is search-level, not training-run-level.** The two-tier converge skill measures whether the search space itself is covered: within-class exhaustion (Tier 1) and cross-class coverage (Tier 2). A single strong candidate satisfies none of these on its own.

4. **Discovery means surviving the gates, not that the model said it worked.** Every architecture submits to isolation gates, null-baseline comparisons, reproducibility checks, and an independently dispatched judge — only after convergence.

## Routing

Route all architecture experiment requests through `/auto-discover`. Do not attempt to run experiments, propose genome specs, evaluate architectures, or declare discoveries without invoking auto-discover.
