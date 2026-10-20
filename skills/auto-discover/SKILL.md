---
name: auto-discover
description: "Orchestrator for evolutionary ML architectural discovery. Trigger /auto-discover whenever the user says \"experiment with this architecture\", \"test this thesis\", \"discover a new architecture\", or \"pre-register my hypothesis\". Manages the experiment tree and runs an evolutionary loop: analyze-problem (structural analysis) → explore (investigation agents) → propose-spec (per direction) → isolate-component → build-variant (parallel worktrees) → evaluate → review-strategy → converge. When converge returns CONVERGED, the best candidate goes through end gates: null-baseline-gate → reproducibility-gate → judge → evidence-report. Emits DISCOVERY_CONFIRMED, DISCOVERY_REFUTED, BLOCKED_DIVERGENCE, or BLOCKED_NEEDS_USER."
---

<!-- design-region-clean-of-hard-gates -->

# Auto Discover

## Contract

- **Reads**: `hypothesis.yaml` (user-provided), `.auto-discover/hypothesis.yaml`, `.auto-discover/hypothesis.sha256`, `.auto-discover/problem-analysis.json`, `.auto-discover/experiment-tree.json` (schema: `references/experiment-tree-schema.md`)
- **Writes**: `.auto-discover/experiment-tree.json`, `.auto-discover/worktrees/`, `.auto-discover/scripts/check_search_convergence.sh`
- **References**: `references/experiment-tree-schema.md`, `references/pipeline-overview.md`, `references/dispatch-contract.md`
- **Verdicts**: DISCOVERY_CONFIRMED, DISCOVERY_REFUTED, BLOCKED_DIVERGENCE, BLOCKED_NEEDS_USER

<HARD-GATE>
Do NOT begin without a hypothesis.yaml with all required fields. STOP and propagate whatever BLOCKED_NEEDS_USER pre-register emits.
</HARD-GATE>

<HARD-GATE>
Do NOT enter the evolutionary loop without a completed problem analysis. STOP and invoke analyze-problem first.
</HARD-GATE>

<HARD-GATE>
Do NOT proceed if the proposer, builder, or explorer is serving as judge. STOP and dispatch a separate agent.
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

Discovery is the output of a search that has covered its space, not the output of one favorable training run — and a search only covers its space quickly if branches advance independently. The problem analysis identifies what the task requires; explore turns those requirements into specs; the evolutionary loop tests them. converge, not a lockstep wave boundary, is the only checkpoint that requires the whole round to have settled.

## Process Flow

Read `references/pipeline-overview.md` for the full stage diagram, dispatch sequence, synchronization points, and loop exits.

## Checklist

1. Invoke pre-register
2. Invoke establish-baseline
3. Invoke analyze-problem
4. Initialize experiment tree (`.auto-discover/experiment-tree.json`)
4b. Compose `.auto-discover/scripts/check_search_convergence.sh` and register it as a command-type Stop hook
5. LOOP: Invoke explore
6. Invoke isolate-component per spec (parallel)
7. Invoke build-variant per survivor (parallel worktrees)
8. Invoke evaluate per completed variant
9. Invoke review-strategy per ACCEPTed variant
10. Invoke converge — EXPLORING → step 5; CONVERGED → continue
11. Invoke null-baseline-gate on best Pareto-front candidate
12. Invoke reproducibility-gate, then judge
13. Invoke evidence-report, emit terminal verdict

## Step Details

### 1. Pre-Register

Invoke the pre-register skill inline (Skill tool). Read `references/dispatch-contract.md` row: pre-register. It validates every required field, locks the hypothesis behind a SHA-256, and writes `.auto-discover/hypothesis.yaml` plus `.auto-discover/hypothesis.sha256`. On BLOCKED_NEEDS_USER, propagate immediately — do not proceed to any later step.

### 2. Establish Baseline

Dispatch via `Agent(isolation: "worktree", model: "sonnet")`. Read `references/dispatch-contract.md` row: establish-baseline. Pre-create `.auto-discover/baselines/`. Inline the hypothesis path and hypothesis.sha256 path. Tell the agent: "Read `skills/establish-baseline/SKILL.md` for your contract." The agent composes and trains the null hypothesis in its worktree. Verify `baseline_metrics.json` exists on return. On BLOCKED_NEEDS_USER, propagate immediately.

### 3. Analyze Problem

Dispatch via `Agent(isolation: "worktree", model: "opus")`. Read `references/dispatch-contract.md` row: analyze-problem. Inline the hypothesis path, hypothesis.sha256 path, and baseline_metrics.json path. Tell the agent: "Read `skills/analyze-problem/SKILL.md` for your contract." The agent composes and runs verification scripts on toy instances in its worktree, then writes `.auto-discover/problem-analysis.json`. On BLOCKED, propagate immediately.

This step runs once per experiment. The problem analysis produces the research directions the entire search consumes.

### 4. Initialize the Experiment Tree

Create `.auto-discover/worktrees/` and write `.auto-discover/experiment-tree.json`. Read `references/experiment-tree-schema.md` for the full schema. Initialize `primary_metric_key` and `metric_direction` from the hypothesis, `round` to 0, `nodes` as empty, `pareto_front` and `pareto_history` as empty arrays, `class_status` as empty.

### 4b. Register the Convergence Stop Hook

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

### 5. LOOP START — Explore

Dispatch via `Agent(isolation: "worktree", model: "opus")` — a single agent that handles all research directions for the round. Read `references/dispatch-contract.md` row: explore. Tell the agent: "Read `skills/explore/SKILL.md` for your contract." Inline the problem-analysis.json path, experiment-tree.json path, and round number. The agent needs cross-direction context (full analysis + full tree) to enforce divergence across the batch — per-direction agents cannot do this. Begin a new explore dispatch the instant converge returns EXPLORING. If explore returns BLOCKED, route to evidence-report.

Explore internally dispatches propose-spec for each surviving proposal. Verify genome_spec.json exists for each returned experiment hash.

### 6. Isolate Component Per Spec (Parallel Worktrees)

Dispatch via `Agent(isolation: "worktree", model: "sonnet")` per spec — all specs of the round in a single message (parallel dispatch). Read `references/dispatch-contract.md` row: isolate-component. Tell each agent: "Read `skills/isolate-component/SKILL.md` for your contract." Each agent runs the 3 isolation gates in its own worktree. If every spec in the round fails isolation, route to evidence-report with BLOCKED_NEEDS_USER.

### 7. Build Variant Per Survivor (Parallel Worktrees, Streamed)

Dispatch via `Agent(isolation: "worktree", model: "sonnet")` per spec. Read `references/dispatch-contract.md` row: build-variant. Pre-create `.auto-discover/worktrees/<hash>/`. Tell each agent: "Read `skills/build-variant/SKILL.md` for your contract." Inline: genome_spec path, training_budget, pre_registered_metrics, seeds[0], genome_constraints, worktree path. Dispatch each the instant its own isolation result arrives with COMPONENT_VALIDATED — do not batch-wait for siblings.

### 8. Evaluate Per Completed Variant (Streamed)

Dispatch via `Agent(isolation: "worktree", model: "sonnet")` per variant. Read `references/dispatch-contract.md` row: evaluate. Tell the agent: "Read `skills/evaluate/SKILL.md` for your contract." Dispatch the instant a variant's build-variant returns DONE or DONE_WITH_CONCERNS. Do not wait for sibling variants. The agent composes and runs forensic validation scripts in its worktree.

### 9. Review Strategy Per ACCEPTed Variant (Streamed)

Dispatch via `Agent(model: "sonnet")` per variant. Read `references/dispatch-contract.md` row: review-strategy. Dispatch the instant a variant's evaluate returns ACCEPT. Do not wait for siblings.

After every variant in the round has reached a terminal state, the orchestrator aggregates: add every node to experiment-tree.json, apply REVIEW.json's pareto block, append the resulting front to pareto_history. Aggregation runs in the orchestrator's context — it is the one place the orchestrator writes to the shared tree.

### 10. Converge — the Round Boundary

Invoke converge inline (Skill tool) — it reads the tree the orchestrator just aggregated and needs the orchestrator's context. Invoke only after every spec proposed this round has reached a terminal state and the tree has been aggregated. This is the one legitimate synchronization point.

- **EXPLORING** — return to Step 5.
- **CONVERGED** — continue to Step 11.
- **BLOCKED** — route to evidence-report.

### 11. Null-Baseline Gate on the Leading Candidate

Dispatch via `Agent(isolation: "worktree", model: "sonnet")`. Read `references/dispatch-contract.md` row: null-baseline-gate. Identify the Pareto front's leading candidate and inline that candidate's worktree path and baseline_metrics.json path. The agent trains shuffled-label and constant-predictor controls in its worktree. On NULL_BASELINE_FAILED, route to evidence-report.

### 12. Reproducibility Gate, Then Judge

Dispatch reproducibility-gate via `Agent(isolation: "worktree", model: "sonnet")`. Inline the worktree path, seeds, and variance_tolerance. The agent re-trains across the seed set. On REPRODUCIBILITY_FAILED, route to evidence-report. On REPRODUCIBILITY_PASSED, dispatch judge via `Agent(model: "opus")` — a separate agent that sees only the metrics manifest, hypothesis, and gate results. Never the agent that proposed, built, or reviewed.

### 13. Evidence Report and Terminal Verdict

Invoke evidence-report inline (Skill tool). Read `references/dispatch-contract.md` row: evidence-report. It writes evidence.json from the existing artifacts. Read the terminal verdict and emit it unchanged.

## Gate Functions

- BEFORE beginning: "Does a pre-registered hypothesis exist with a hash that round-trips?"
- BEFORE entering the loop: "Did analyze-problem complete and write problem-analysis.json with at least 3 research directions?"
- BEFORE holding any spec back at a stage: "Is this spec waiting for its own upstream result, or am I batching it behind round-mates?"
- BEFORE invoking converge: "Has every spec proposed this round reached a terminal state, and has the tree been aggregated?"
- BEFORE declaring CONVERGED: "Did converge itself return CONVERGED?"
- BEFORE dispatching an end gate: "Is this the single leading candidate from a CONVERGED front?"
- BEFORE dispatching judge: "Is this agent instance distinct from whichever proposed, built, or reviewed?"
- BEFORE emitting the terminal verdict: "Did evidence-report write it?"

## Rationalization Table

| You think... | Reality |
|---|---|
| "I'll wait for all N specs to clear isolation before building any" | Dispatch build-variant for each spec the moment its own isolation returns COMPONENT_VALIDATED. |
| "This candidate's metrics look great, let's call it CONVERGED" | Run converge and read its actual verdict. |
| "The proposer already sounds confident, skip isolate-component" | Run every spec through all three isolation gates. |
| "I already trained and reviewed this candidate, I can judge it" | Dispatch judge as a separate agent. |
| "Let's finish this wave before starting the following stage" | Dispatch each spec through stages independently the instant its own upstream result arrives. Only converge is a legitimate wave boundary. |
| "I can skip the problem analysis for a simple task" | Run analyze-problem on every task regardless. Simple tasks have the strongest structural constraints — skip the analysis and the search loses its grounding. |

## Red Flags

- "Let's finish this wave before starting the following stage"
- "This candidate looks converged, let's move on"
- "The thesis was strong, skip isolation"
- "I already know if this candidate works, I can judge it"
- "The problem analysis is obvious, skip it"

## Key Principles

- The problem analysis runs once and produces the signals the entire search consumes.
- Every genome spec traces to a research direction from the problem analysis.
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
analysis_file="${state_dir}/problem-analysis.json"
if [[ ! -f "$analysis_file" ]]; then
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
- **BLOCKED_NEEDS_USER** -- pre-registration, baseline, or problem analysis failed; explore found no viable proposals; all specs failed isolation
