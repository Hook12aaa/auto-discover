# Contract-First Rearchitecture Design

**Date:** 2026-10-17
**Scope:** Rewrite all 16 auto-discover skills as domain-agnostic contracts with colocated reference docs and formal inter-skill JSON schemas.

## Problem

auto-discover's skills teach methodology instead of defining contracts. Each skill describes *how to think about* the problem in prose, baking domain knowledge (mathematical structure analysis, group theory, symmetry detection) into the skill logic. This creates three failures:

1. **Skills can't build independently.** Domain knowledge lives in skill prose, not in reference docs the skill consults. Changing the domain means rewriting the skill.
2. **The pipeline is hardcoded to one domain.** analyze-problem talks about algebraic properties and group structure. explore prescribes structural investigation. These are mathematical-discovery-specific.
3. **Inter-skill contracts are implicit.** The format of experiment-tree.json, genome_spec.json, and problem-analysis.json exists only as prose examples embedded in skill text.

## Design Principle

**Contract-first, library-last.** Every skill defines typed inputs, typed outputs, verdicts, and which reference docs to consult. Domain knowledge lives in colocated reference docs as decision tables and catalogs. A new domain gets reference docs, not skill rewrites.

This follows the NAS three-axis decomposition:
- **Search space** (what can be built) → reference docs (component vocabularies, analysis catalogs)
- **Search strategy** (how to explore) → skill contracts (inputs → outputs → verdict)
- **Performance estimation** (how to evaluate) → evaluate + review-strategy contracts with diagnostic references

## Architecture

### Formal Schemas

Four schema reference docs govern every inter-skill handoff. Each defines field name, type, purpose, and computation method. Skills validate inputs against the schema and reject malformed data.

#### 1. experiment-tree-schema.md (auto-discover/references/)

```json
{
  "primary_metric_key": "string — from hypothesis.pre_registered_metrics.primary",
  "metric_direction": "maximize | minimize",
  "round": "integer — current round number",
  "nodes": {
    "<hash>": {
      "hash": "string — SHA-256(canonical spec JSON + parent hash)",
      "architecture_name": "string",
      "spec_class": "string — composition fingerprint",
      "parent_id": "string | null",
      "worktree_path": "string | null",
      "isolation_verdict": "COMPONENT_VALIDATED | FAIL | null",
      "evaluate_verdict": "ACCEPT | REJECT | INCONCLUSIVE | null",
      "review_verdict": "KEEP | DISCARD | KEEP_WITH_CONCERNS | null",
      "primary_metric": "float | null",
      "params": "integer | null",
      "round": "integer",
      "stop_reason": "budget_exhausted | patience_exceeded | chance_level_kill | wall_clock_limit | null",
      "structural_basis": "string — research direction id from problem-analysis.json",
      "notes": "string"
    }
  },
  "pareto_front": [
    {
      "node_id": "string",
      "architecture_name": "string",
      "spec_class": "string",
      "primary_metric": "float",
      "params": "integer",
      "worktree_path": "string"
    }
  ],
  "pareto_history": [
    {
      "round": "integer",
      "front": ["<pareto_front entry>"]
    }
  ],
  "class_status": {
    "<spec_class>": "UNTRIED | EXPLORING | EXHAUSTED"
  },
  "search_status": "EXPLORING | CONVERGED | BLOCKED"
}
```

#### 2. problem-analysis-schema.md (analyze-problem/references/)

```json
{
  "status": "DONE | BLOCKED",
  "domain_type": "mathematical | graph | sequence | tabular | vision",
  "task": {
    "input_type": "string",
    "output_type": "string",
    "mapping": "string",
    "instance_structure": "string | null"
  },
  "structural_properties": [
    {
      "id": "string — sp_N",
      "category": "algebraic | geometric | topological | information_theoretic | compositional",
      "property": "string — what was found",
      "verified": "boolean — was it tested on toy instances",
      "verification_method": "string | null"
    }
  ],
  "baseline_failure_analysis": {
    "accuracy": "float",
    "failure_mode": "string",
    "structural_gap": "string"
  },
  "theoretical_constraints": [
    {
      "constraint": "string",
      "source": "string — mathematical argument",
      "implication": "string"
    }
  ],
  "research_directions": [
    {
      "id": "string — rd_N",
      "source_property": "string — sp_N reference",
      "observation": "string",
      "implication": "string",
      "priority": "high | medium | low"
    }
  ]
}
```

#### 3. genome-spec-schema.md (propose-spec/references/)

```json
{
  "spec_version": "string",
  "architecture_name": "string — derived from structural basis, never a known pattern name",
  "structural_basis": "string — rd_N reference from problem-analysis.json",
  "novel_component": {
    "type": "string",
    "class": "string",
    "ops_used": ["string — abstract operation names"]
  },
  "composition": {
    "strategy": "string — sequential | parallel | branching | residual | ...",
    "num_layers": "integer"
  },
  "hyperparameters": {
    "<key>": "number"
  }
}
```

#### 4. proposal-schema.md (explore/references/)

```json
{
  "structural_basis": "string — rd_N reference from problem-analysis.json",
  "source_direction": "string — rd_N",
  "required_operations": ["string — abstract operation names"],
  "composition_strategy": "string",
  "expected_behavior": "string — metric prediction from structural analysis",
  "falsification": "string — how to know this proposal is wrong"
}
```

### Colocated Reference Docs

Every skill gets a `references/` directory with the domain knowledge it needs. Reference docs are decision tables, catalogs, and schemas — never methodology prose.

#### analyze-problem/references/

| Doc | Purpose |
|---|---|
| `problem-analysis-schema.md` | Output schema (formal) |
| `domain-detection.md` | Decision table: hypothesis signals → domain type |
| `analysis-catalog.md` | Per-domain structural checks as decision tables (§ Mathematical, § Graph, § Sequence, § Tabular) |

**domain-detection.md** structure:

| Signal in hypothesis | Domain type |
|---|---|
| Group/ring/field operations, modular arithmetic, algebraic structure keywords | mathematical |
| Graph inputs, node/edge features, adjacency, isomorphism | graph |
| Sequential/temporal inputs, time dependencies, variable-length | sequence |
| Tabular features, fixed columns, classification/regression on structured data | tabular |
| Image/pixel inputs, spatial structure | vision |

**analysis-catalog.md** structure (per domain section):

| Check | What to verify | How to verify | Output field |
|---|---|---|---|
| (per-domain rows) | (concrete check) | (script or reasoning) | (which structural_properties entry) |

#### explore/references/

| Doc | Purpose |
|---|---|
| `proposal-schema.md` | Output schema (formal) |
| `component-vocabulary.md` | Per-domain component catalogs: operation types, composition patterns, when-to-use criteria |
| `divergence-rules.md` | Fingerprint computation, collision detection, mandatory divergence rules |

**component-vocabulary.md** structure (per domain section):

| Operation type | What it does | When it applies | Limitations |
|---|---|---|---|
| (per-domain rows) | (computation description) | (structural signal that implies it) | (known failure modes) |

#### propose-spec/references/

| Doc | Purpose |
|---|---|
| `genome-spec-schema.md` | Output schema (formal) |
| `translation-rules.md` | Decision table: proposal field → spec field mapping, naming conventions |

#### auto-discover/references/

| Doc | Purpose |
|---|---|
| `experiment-tree-schema.md` | Tree schema (formal) |
| `pipeline-overview.md` | Stage diagram and dispatch sequence |
| `dispatch-contract.md` | Per-stage inline dispatch rules: what to pre-create, what to inline, what to verify on return |

**dispatch-contract.md** structure:

| Stage | Pre-create | Inline to dispatch | Verify on return |
|---|---|---|---|
| isolate-component | — | genome_spec.json path | gates/*.json exist, all PASS |
| build-variant | worktree dir | genome_spec, hypothesis fields, worktree path | training_metrics.json, final_metrics.json |
| evaluate | — | worktree path, pre_registered_metrics | EVALUATION.json with verdict |
| review-strategy | — | evaluation_result, variant_params, baseline_params, pareto_front | REVIEW.json with verdict |

#### build-variant/references/

| Doc | Purpose |
|---|---|
| `training-conventions.md` | Per-domain training defaults (optimizer, checkpoint cadence, seed handling) |
| `early-stopping-rules.md` | Decision table: stopping conditions, thresholds, stop_reason values |

#### evaluate/references/

| Doc | Purpose |
|---|---|
| `training-diagnostics.md` | Check/condition/verdict table for forensic layer |
| `metric-extraction.md` | Per-metric computation rules |

#### isolate-component/references/

| Doc | Purpose |
|---|---|
| `isolation-gates.md` | Gate definitions: gradient flow, output range, toy convergence |
| `threshold-calibration.md` | Per-domain default thresholds for each gate |

#### review-strategy/references/

| Doc | Purpose |
|---|---|
| `pareto-computation.md` | Dominance rules, front update logic |
| `efficiency-thresholds.md` | Parameter efficiency computation, stale pathway detection rules |

#### converge/references/

| Doc | Purpose |
|---|---|
| `convergence-conditions.md` | Tier 1 and Tier 2 conditions as decision tables with thresholds |

#### evidence-report/references/

| Doc | Purpose |
|---|---|
| `evidence-schema.md` | evidence.json output format |
| `verdict-rules.md` | Terminal verdict decision table: gate results → verdict |

#### Remaining skills (judge, null-baseline-gate, reproducibility-gate, pre-register, establish-baseline)

These are already near-contractual. Each gets 1 reference doc extracting any embedded domain knowledge:

| Skill | Reference doc |
|---|---|
| `judge` | `scoring-rubric.md` — scoring criteria as decision table |
| `null-baseline-gate` | `null-comparisons.md` — three comparison definitions |
| `reproducibility-gate` | `variance-rules.md` — seed variance computation and tolerance rules |
| `pre-register` | `validation-rules.md` — field validation rules, phenomenon denylist, budget requirements |
| `establish-baseline` | `baseline-conventions.md` — per-domain baseline defaults |

### Skill Contract Template

Every rewritten SKILL.md follows this structure:

```markdown
---
name: <skill-name>
description: "<trigger, inputs, outputs, verdicts>"
---

## Contract

- **Reads**: <list of JSON files/fields with schema references>
- **Writes**: <list of JSON files with schema references>
- **References**: <list of references/ docs to consult>
- **Verdicts**: <ALL-CAPS verdict tokens>

<HARD-GATE>
(precondition checks on inputs — schema validation, required files)
</HARD-GATE>

## Anti-Pattern
(what NOT to do — one paragraph)

## Core Principle
(one sentence)

## Checklist
(numbered steps: what to produce, not how to think)

## Step Details
(per step: "Read references/X.md. Produce Y matching Z schema.")

## Gate Functions
(per gate: input/output verification questions)

## Rationalization Table
(imperative-led Reality cells)

## Red Flags
## Key Principles
## The Bottom Line
## Status Vocabulary
```

The key difference from current skills: Step Details say **"Read references/X.md for the Y catalog. Produce Z matching schema W."** — never **"Here's how to analyze the mathematical structure of the problem."**

### Domain Registry

The extensibility mechanism. Adding a new domain requires:

1. Add a row to `analyze-problem/references/domain-detection.md`
2. Add a section to `analyze-problem/references/analysis-catalog.md`
3. Add a section to `explore/references/component-vocabulary.md`
4. Add a section to `build-variant/references/training-conventions.md`
5. Add a section to `isolate-component/references/threshold-calibration.md`
6. Add a section to `establish-baseline/references/baseline-conventions.md`

No skill rewrites. The skills read the catalogs; the catalogs carry the domain knowledge.

### Migration from Current State

| Current | Target |
|---|---|
| 2 project-level reference docs | ~28 colocated reference docs across 16 skills |
| 0 formal schemas | 4 formal schema docs |
| Skills teach methodology in prose | Skills define contracts pointing at references |
| Domain knowledge in SKILL.md body | Domain knowledge in references/ decision tables |
| Implicit JSON formats in prose examples | Formal schemas with field types and computation rules |
| project-level `references/` directory | Deleted — all content moves to skill-level `references/` |

### What Stays the Same

- The pipeline stages and their order
- The verdict vocabulary
- The evolutionary loop structure
- The Stop hook enforcement
- Pre-registration immutability
- Structural distrust (separate proposer/builder/judge)
- The experiment tree as the audit trail

## Implementation Order

1. Write the 4 formal schema docs (these unblock everything else)
2. Write colocated reference docs for the 6 core loop skills (analyze-problem, explore, propose-spec, build-variant, evaluate, isolate-component)
3. Rewrite the 6 core loop skills as contracts
4. Write colocated reference docs for the orchestrator and end-gate skills
5. Rewrite the orchestrator and end-gate skills as contracts
6. Write reference docs for the remaining near-contractual skills
7. Update the remaining skills
8. Delete project-level `references/` directory
9. Update CLAUDE.md, using-auto-discover, marketplace.json
10. Run stress test to verify lint compliance
