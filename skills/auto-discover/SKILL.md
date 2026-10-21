---
name: auto-discover
description: "Orchestrator for evolutionary ML architectural discovery. Trigger /auto-discover whenever the user says \"experiment with this architecture\", \"test this thesis\", \"discover a new architecture\", or \"pre-register my hypothesis\". Manages the experiment tree and runs an evolutionary loop: research (probe, web search, prototype) → isolate-component → build-variant (parallel worktrees) → evaluate → review-strategy → converge. When converge returns CONVERGED, the best candidate goes through end gates: null-baseline-gate → reproducibility-gate → judge → evidence-report. Emits DISCOVERY_CONFIRMED, DISCOVERY_REFUTED, BLOCKED_DIVERGENCE, or BLOCKED_NEEDS_USER."
---

<!-- design-region-clean-of-hard-gates -->

# Auto Discover

## Contract

- **Reads**: `hypothesis.yaml` (user-provided), `.auto-discover/hypothesis.yaml`, `.auto-discover/hypothesis.sha256`, `.auto-discover/experiment-tree.json` (schema: `references/experiment-tree-schema.md`)
- **Writes**: `.auto-discover/experiment-tree.json`, `.auto-discover/worktrees/`, `.auto-discover/scripts/check_search_convergence.sh`
- **References**: `references/experiment-tree-schema.md`, `references/pipeline-overview.md`, `references/dispatch-contract.md`
- **Verdicts**: DISCOVERY_CONFIRMED, DISCOVERY_REFUTED, BLOCKED_DIVERGENCE, BLOCKED_NEEDS_USER

<HARD-GATE>
Do NOT begin without a hypothesis.yaml with all required fields. STOP and propagate whatever BLOCKED_NEEDS_USER pre-register emits.
</HARD-GATE>

<HARD-GATE>
Do NOT enter the evolutionary loop without a completed baseline. STOP and invoke establish-baseline first.
</HARD-GATE>

<HARD-GATE>
Do NOT proceed if the researcher or builder is serving as judge. STOP and dispatch a separate agent.
</HARD-GATE>

<HARD-GATE>
Do NOT run end gates until converge returns CONVERGED. STOP and gate only the single leading candidate.
</HARD-GATE>

<HARD-GATE>
Do NOT declare CONVERGED without the converge skill returning CONVERGED. STOP and invoke converge for the search-level convergence verdict.
</HARD-GATE>

<HARD-GATE>
Do NOT proceed if the Stop hook registered at initialization is missing or altered. STOP and re-register it.
</HARD-GATE>

## Anti-Pattern

**"Let me finish this round's isolation gates before I start building anything, and finish all the building before I evaluate anything."** Waiting for every sibling in a round to clear one stage before advancing any of them to the following stage is a generational barrier, not an evolutionary loop. The moment a spec's isolate-component result returns COMPONENT_VALIDATED, its worktree is ready for build-variant — it does not need its round-mates to catch up first.

## Core Principle

Discovery is the output of a search where the search space itself is discovered through probing and research, not prescribed through catalogs. A search only covers its space quickly if branches advance independently. converge, not a lockstep wave boundary, is the only checkpoint that requires the whole round to have settled.

## Process Flow

Read `references/pipeline-overview.md` for the full stage diagram, dispatch sequence, synchronization points, and loop exits.

## Checklist

1. Invoke pre-register
2. Invoke establish-baseline
3. Initialize experiment tree (`.auto-discover/experiment-tree.json`)
3b. Compose `.auto-discover/scripts/check_search_convergence.sh` and register it as a command-type Stop hook
4. LOOP: Dispatch research
5. Invoke isolate-component per spec from research (parallel)
6. Invoke build-variant per survivor (parallel worktrees)
7. Invoke evaluate per completed variant
8. Invoke review-strategy per ACCEPTed variant
9. Invoke converge — EXPLORING → step 4; CONVERGED → continue
10. Invoke null-baseline-gate on best Pareto-front candidate
11. Invoke reproducibility-gate, then judge
12. Invoke evidence-report, emit terminal verdict

## Step Details

### 1. Pre-Register

Invoke the pre-register skill inline (Skill tool). Read `references/dispatch-contract.md` row: pre-register. It validates every required field, locks the hypothesis behind a SHA-256, and writes `.auto-discover/hypothesis.yaml` plus `.auto-discover/hypothesis.sha256`. On BLOCKED_NEEDS_USER, propagate immediately — do not proceed to any later step.

### 2. Establish Baseline

Dispatch via `Agent(isolation: "worktree", model: "sonnet")`. Read `references/dispatch-contract.md` row: establish-baseline. Pre-create `.auto-discover/baselines/`. Inline the hypothesis path and hypothesis.sha256 path. Tell the agent: "Read `skills/establish-baseline/SKILL.md` for your contract." The agent composes and trains the null hypothesis in its worktree. Verify `baseline_metrics.json` exists on return. On BLOCKED_NEEDS_USER, propagate immediately.

### 3. Initialize the Experiment Tree

Create `.auto-discover/worktrees/` and write `.auto-discover/experiment-tree.json`. Read `references/experiment-tree-schema.md` for the full schema. Initialize `primary_metric_key` and `metric_direction` from the hypothesis, `round` to 0, `nodes` as empty, `pareto_front` and `pareto_history` as empty arrays, `class_status` as empty.

### 3b. Register the Convergence Stop Hook

Compose `.auto-discover/scripts/check_search_convergence.sh` — a shell script that reads `.auto-discover/experiment-tree.json` and blocks the stop if the search has not converged. Register it as a command-type Stop hook in the experiment repo's `.claude/settings.local.json` (create the file if absent; merge into it if present — never overwrite unrelated entries):

```json
{
  "hooks": {
    "Stop": [
      {
        "matcher": "",
        "hooks": [
          {
            "type": "command",
            "command": "bash \"${CLAUDE_PROJECT_DIR}/.auto-discover/scripts/check_search_convergence.sh\"",
            "timeout": 30000
          }
        ]
      }
    ]
  }
}
```

### 4. LOOP START — Research

Dispatch via `Agent(isolation: "worktree", model: "opus")`. Read `references/dispatch-contract.md` row: research. Tell the agent: "Read `skills/research/SKILL.md` for your contract." Inline the hypothesis path, baseline path, experiment-tree path, round number, and prior findings log path. The agent probes the problem, web-searches based on findings, builds prototypes, and writes genome specs to worktrees. Begin a new research dispatch the instant converge returns EXPLORING. If research returns BLOCKED, route to evidence-report. Verify genome_spec.json exists for each returned experiment hash.

### 5. Isolate Component Per Spec (Parallel Worktrees)

Dispatch via `Agent(isolation: "worktree", model: "sonnet")` per spec — all specs of the round in a single message (parallel dispatch). Read `references/dispatch-contract.md` row: isolate-component. Tell each agent: "Read `skills/isolate-component/SKILL.md` for your contract." Each agent runs the 3 isolation gates in its own worktree. If every spec in the round fails isolation, route to evidence-report with BLOCKED_NEEDS_USER.

### 6. Build Variant Per Survivor (Parallel Worktrees, Streamed)

Dispatch via `Agent(isolation: "worktree", model: "sonnet")` per spec. Read `references/dispatch-contract.md` row: build-variant. Pre-create `.auto-discover/worktrees/<hash>/`. Tell each agent: "Read `skills/build-variant/SKILL.md` for your contract." Inline: genome_spec path, training_budget, pre_registered_metrics, seeds[0], genome_constraints, worktree path. Dispatch each the instant its own isolation result arrives with COMPONENT_VALIDATED — do not batch-wait for siblings.

### 7. Evaluate Per Completed Variant (Streamed)

Dispatch via `Agent(isolation: "worktree", model: "sonnet")` per variant. Read `references/dispatch-contract.md` row: evaluate. Tell the agent: "Read `skills/evaluate/SKILL.md` for your contract." Dispatch the instant a variant's build-variant returns DONE or DONE_WITH_CONCERNS. Do not wait for sibling variants. The agent composes and runs forensic validation scripts in its worktree.

### 8. Review Strategy Per ACCEPTed Variant (Streamed)

Dispatch via `Agent(model: "sonnet")` per variant. Read `references/dispatch-contract.md` row: review-strategy. Dispatch the instant a variant's evaluate returns ACCEPT. Do not wait for siblings.

After every variant in the round has reached a terminal state, the orchestrator aggregates: add every node to experiment-tree.json, apply REVIEW.json's pareto block, append the resulting front to pareto_history. Aggregation runs in the orchestrator's context — it is the one place the orchestrator writes to the shared tree.

### 9. Converge — the Round Boundary

Invoke converge inline (Skill tool) — it reads the tree the orchestrator just aggregated and needs the orchestrator's context. Invoke only after every spec proposed this round has reached a terminal state and the tree has been aggregated. This is the one legitimate synchronization point.

- **EXPLORING** — return to Step 4.
- **CONVERGED** — continue to Step 10.
- **BLOCKED** — route to evidence-report.

### 10. Null-Baseline Gate on the Leading Candidate

Dispatch via `Agent(isolation: "worktree", model: "sonnet")`. Read `references/dispatch-contract.md` row: null-baseline-gate. Identify the Pareto front's leading candidate and inline that candidate's worktree path and baseline_metrics.json path. The agent trains shuffled-label and constant-predictor controls in its worktree. On NULL_BASELINE_FAILED, route to evidence-report.

### 11. Reproducibility Gate, Then Judge

Dispatch reproducibility-gate via `Agent(isolation: "worktree", model: "sonnet")`. Inline the worktree path, seeds, and variance_tolerance. The agent re-trains across the seed set. On REPRODUCIBILITY_FAILED, route to evidence-report. On REPRODUCIBILITY_PASSED, dispatch judge via `Agent(model: "opus")` — a separate agent that sees only the metrics manifest, hypothesis, and gate results. Never the agent that researched, built, or reviewed.

### 12. Evidence Report and Terminal Verdict

Invoke evidence-report inline (Skill tool). Read `references/dispatch-contract.md` row: evidence-report. It writes evidence.json from the existing artifacts. Read the terminal verdict and emit it unchanged.

## Gate Functions

- BEFORE beginning: "Does a pre-registered hypothesis exist with a hash that round-trips?"
- BEFORE entering the loop: "Did establish-baseline write baseline_metrics.json?"
- BEFORE holding any spec back at a stage: "Is this spec waiting for its own upstream result, or am I batching it behind round-mates?"
- BEFORE invoking converge: "Has every spec proposed this round reached a terminal state, and has the tree been aggregated?"
- BEFORE declaring CONVERGED: "Did converge itself return CONVERGED?"
- BEFORE dispatching an end gate: "Is this the single leading candidate from a CONVERGED front?"
- BEFORE dispatching judge: "Is this agent instance distinct from whichever researched, built, or reviewed?"
- BEFORE emitting the terminal verdict: "Did evidence-report write it?"

## Rationalization Table

| You think... | Reality |
|---|---|
| "I'll wait for all N specs to clear isolation before building any" | Dispatch build-variant for each spec the moment its own isolation returns COMPONENT_VALIDATED. |
| "This candidate's metrics look great, let's call it CONVERGED" | Run converge and read its actual verdict. |
| "The proposer already sounds confident, skip isolate-component" | Run every spec through all three isolation gates. |
| "I already trained and reviewed this candidate, I can judge it" | Dispatch judge as a separate agent. |
| "Let's finish this wave before starting the following stage" | Dispatch each spec through stages independently the instant its own upstream result arrives. Only converge is a legitimate wave boundary. |
| "The baseline is close enough, skip research probes" | Dispatch research every round. Probes ground each spec in a checked property of the problem. |

## Red Flags

- "Let's finish this wave before starting the following stage"
- "This candidate looks converged, let's move on"
- "The thesis was strong, skip isolation"
- "I already know if this candidate works, I can judge it"
- "The problem is obvious, skip the probes"

## Key Principles

- Research probes the problem each round and grounds every genome spec in probe findings.
- Every genome spec traces to a probe result or a cited source in the findings log.
- Each spec streams independently through stages; only converge requires the round to settle.
- CONVERGED is converge's verdict alone, never auto-discover's inference.
- End gates run exactly once, on exactly one candidate.
- The judge is always a separate agent from the proposer, builder, and reviewer.
- evidence-report writes the terminal verdict; auto-discover reads it.

## The Bottom Line

```bash
#!/usr/bin/env bash
set -euo pipefail
state_dir="${1:-.auto-discover}"
hash_file="${state_dir}/hypothesis.sha256"
if [[ ! -f "$hash_file" ]]; then
  echo "VERDICT: BLOCKED_NEEDS_USER"
  exit 1
fi
tree_file="${state_dir}/experiment-tree.json"
if [[ ! -f "$tree_file" ]]; then
  echo "VERDICT: BLOCKED_NEEDS_USER"
  exit 1
fi
latest_evidence=$(find "${state_dir}/worktrees" -name "evidence.json" -type f 2>/dev/null | sort | tail -1)
if [[ -z "$latest_evidence" ]]; then
  echo "VERDICT: BLOCKED_NEEDS_USER"
  exit 1
fi
verdict=$(python3 -c "import json,sys; d=json.load(open(sys.argv[1])); print(d.get('terminal_verdict','BLOCKED_NEEDS_USER'))" "$latest_evidence")
echo "VERDICT: ${verdict}"
```

## Status Vocabulary

- **DISCOVERY_CONFIRMED** -- converge returned CONVERGED and the leading candidate survived all end gates
- **DISCOVERY_REFUTED** -- converge returned CONVERGED but the leading candidate failed an end gate
- **BLOCKED_DIVERGENCE** -- converge cannot assess the tree, or full pass without a single ACCEPT
- **BLOCKED_NEEDS_USER** -- pre-registration or baseline failed; research found no viable proposals; all specs failed isolation
