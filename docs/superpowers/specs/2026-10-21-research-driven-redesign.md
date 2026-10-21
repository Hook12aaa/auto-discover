# Research-Driven Redesign

**Date:** 2026-10-21
**Scope:** Replace the catalog-driven analysis phase (analyze-problem + explore + propose-spec) with a single research skill that probes, web-searches, prototypes, and produces genome specs directly. Keep all formal gates from isolation through judge.

## Problem

The contract-first rearchitecture (v2) moved domain knowledge from skill prose into reference doc catalogs. The proof run showed this was a ceiling: the catalog-driven pipeline found a 17,311-param architecture, while a research-driven session (no catalogs, just probes and web search) found a 124-param architecture on the same problem. The catalogs prescribe what to look for instead of letting the agent discover it.

## Evidence

Three approaches tested on modular addition (mod p for primes 5-31):

| Approach | Winner params | Accuracy | Method |
|---|---|---|---|
| Polya v1 | 160 | 100% | Prescribed 4-step methodology |
| Contract-first v2 | 17,311 | 100% | Catalog-driven analysis + component vocabulary |
| Research-driven v3 | 124 | 100% | Probes + web search + prototyping |

The v3 session probed the addition table structure, discovered it was circulant, web-searched for Fourier properties of cyclic groups, built a minimal complex-multiply architecture, and tested 3 competing approaches — all without a catalog or prescribed methodology.

## Design Principle

**Prescribe how to research, not what to find.** The research skill defines the process (probe, search, prototype, learn from failure) but never the content (what structures to look for, what components exist). The search space emerges from the interaction between the problem and what the agent discovers.

## New Pipeline

```
pre-register → establish-baseline → init tree + stop hook
→ RESEARCH LOOP {
    research (probe + web search + prototype)
    → produces genome specs in worktrees
    → isolate-component (per spec, parallel)
    → build-variant (per survivor, parallel worktrees, streamed)
    → evaluate (per completed variant, streamed)
    → review-strategy (per ACCEPTed variant, streamed)
    → converge (round boundary)
    → EXPLORING: loop | CONVERGED: exit
}
→ null-baseline-gate → reproducibility-gate → judge → evidence-report
```

## The Research Skill

### Contract

- **Reads**: `.auto-discover/hypothesis.yaml`, `.auto-discover/baselines/baseline_metrics.json`, `.auto-discover/experiment-tree.json`, web (via WebSearch/WebFetch)
- **Writes**: `.auto-discover/research/` (probe scripts, findings log), genome specs in `.auto-discover/worktrees/<hash>/genome_spec.json`
- **References**: `references/research-protocol.md`, `references/findings-log-schema.md`
- **Verdicts**: EXPLORING (specs produced), BLOCKED (no viable directions found)

### The Inner Loop

The research skill runs an inner loop within each round:

**1. Probe** — Compose and run small Python scripts that test properties of the input/output relationship. Not from a catalog. The first probe on a fresh problem tests the most basic structural properties: symmetry, dimensionality, whether the mapping is injective, what the output distribution looks like. Each probe is a self-contained script that prints structured results.

**2. Search** — Web-search based on what the probes reveal. The search terms come from findings, not from a prescribed list. Probe finds circulant structure → search "circulant matrix properties neural network." Probe finds permutation invariance → search "permutation invariant architectures expressiveness bounds." The search is targeted by evidence, not by a catalog.

**3. Prototype** — Build a small (<100 line) test architecture based on the intersection of probes and search results. Train for a few hundred epochs on a subset of the data. The prototype tests whether the structural insight translates to a working architecture.

**4. Learn** — If the prototype shows signal (accuracy above chance after 10% of the mini-budget), record the approach and prepare a genome spec. If it fails, record WHY in the findings log. The failure diagnosis becomes the next search query or probe target.

**5. Diverge** — After the first successful prototype, probe for alternative structural properties. The goal is at least 3 genome specs from different structural insights per round. Divergence is measured by different mathematical bases (Fourier vs group-theoretic vs algebraic), not by different hyperparameters.

### Round 2+ Behavior

On subsequent rounds, the research skill reads:
- The experiment tree (what specs exist, their accuracies, their spec classes)
- The findings log from prior rounds (what probes found, what searches returned, what failed and why)
- The review-strategy verdicts (what's Pareto-dominated, what's stale)

It targets gaps: if all round 1 specs exploited Fourier structure, round 2 probes for non-Fourier approaches. If a spec class hit a param floor, round 2 searches for theoretical lower bounds.

### What the Research Skill Does NOT Do

- Read a catalog of structures to check for
- Read a vocabulary of components to assemble
- Follow a prescribed analysis methodology
- Produce an intermediate format for another skill to translate
- Limit its search to predefined operation types

### Reference Docs

**`references/research-protocol.md`** — Prescribes how to research, not what to find:

| Phase | Protocol | Constraint |
|---|---|---|
| Probe | Scripts must be self-contained, print structured JSON, and test one property each | Max 50 lines per probe |
| Search | Search terms derive from probe findings, not from prior knowledge | Record every search query and top-3 results in findings log |
| Prototype | Self-contained Python file, train on a data subset | Max 100 lines, max 500 epochs |
| Learn | Record failure mode + diagnosis in findings log | Every failed prototype gets a "why it failed" entry |
| Diverge | New probes target different structural properties than successful prototypes | At least 2 different mathematical bases per round |

**`references/findings-log-schema.md`** — Schema for the structured research log:

```json
{
  "round": "integer",
  "probes": [
    {
      "id": "string — probe_N",
      "question": "string — what property this tests",
      "script_path": "string",
      "result": "string — structured finding",
      "implication": "string — what this means for architecture design"
    }
  ],
  "searches": [
    {
      "query": "string — the search terms used",
      "source": "string — probe_N that motivated this search",
      "top_results": ["string — title + key finding"],
      "implication": "string — what this means for architecture design"
    }
  ],
  "prototypes": [
    {
      "id": "string — proto_N",
      "based_on": "string — which probes + searches motivated it",
      "script_path": "string",
      "accuracy": "float",
      "params": "integer",
      "succeeded": "boolean",
      "failure_diagnosis": "string | null — why it failed, if it did"
    }
  ],
  "genome_specs_produced": ["string — hash of each spec written to worktree"]
}
```

## Dispatch Model

| Stage | Verb | Isolation | Model | Reason |
|---|---|---|---|---|
| pre-register | Invoke | — | — | Fast YAML validation |
| establish-baseline | Dispatch | worktree | sonnet | Long-running training |
| **research** | **Dispatch** | **worktree** | **opus** | **Probes, web search, prototyping — needs worktree + full reasoning** |
| isolate-component | Dispatch (per spec) | worktree | sonnet | Parallel isolation gates |
| build-variant | Dispatch (per spec) | worktree | sonnet | Parallel training |
| evaluate | Dispatch (per variant) | worktree | sonnet | Forensic scripts |
| review-strategy | Dispatch (per variant) | none | sonnet | Reads JSON, computes Pareto |
| converge | Invoke | — | — | Reads tree, needs orchestrator context |
| null-baseline-gate | Dispatch | worktree | sonnet | Trains controls |
| reproducibility-gate | Dispatch | worktree | sonnet | Multi-seed training |
| judge | Dispatch | none | opus | Independent scoring |
| evidence-report | Invoke | — | — | Writes final JSON |

## What Gets Deleted

| Path | Reason |
|---|---|
| `skills/analyze-problem/SKILL.md` | Replaced by research |
| `skills/analyze-problem/references/*` (3 files) | Catalogs replaced by probes |
| `skills/explore/SKILL.md` | Replaced by research |
| `skills/explore/references/*` (3 files) | Component vocabulary replaced by web search |
| `skills/propose-spec/SKILL.md` | Research produces specs directly |
| `skills/propose-spec/references/*` (2 files) | Translation rules unnecessary |

## What Gets Created

| Path | Purpose |
|---|---|
| `skills/research/SKILL.md` | The research skill contract |
| `skills/research/references/research-protocol.md` | How to probe, search, prototype, learn |
| `skills/research/references/findings-log-schema.md` | Findings log format |

## What Gets Updated

| Path | Change |
|---|---|
| `skills/auto-discover/SKILL.md` | Replace 3-step chain with research dispatch |
| `skills/auto-discover/references/dispatch-contract.md` | Replace 3 rows with 1 research row |
| `skills/auto-discover/references/pipeline-overview.md` | New pipeline diagram |
| `skills/using-auto-discover/SKILL.md` | Updated skill inventory (16 → 14 skills) |
| `CLAUDE.md` | Updated pipeline, principles, skill table |
| `README.md` | Updated architecture section |
| `.claude-plugin/marketplace.json` | Updated description |

## What Stays Unchanged

- pre-register, establish-baseline
- isolate-component, build-variant, evaluate, review-strategy, converge
- null-baseline-gate, reproducibility-gate, judge, evidence-report
- experiment-tree-schema.md, genome-spec-schema.md (specs still need a typed format)
- The dispatch pattern (orchestrator dispatches agents, stays lean)
- The Stop hook enforcement
- All formal gates and structural distrust rules
