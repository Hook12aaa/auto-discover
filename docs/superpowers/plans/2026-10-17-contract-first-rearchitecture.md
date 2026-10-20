# Contract-First Rearchitecture Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Rewrite all 16 auto-discover skills as domain-agnostic contracts with colocated reference docs and formal JSON schemas.

**Architecture:** Each skill becomes a typed contract (reads → writes → verdict → references). Domain knowledge moves from skill prose into colocated `references/` decision tables and catalogs. Four formal schema docs govern inter-skill handoffs. New domains get reference doc sections, not skill rewrites.

**Tech Stack:** Pure Markdown. No code, no dependencies. Validation via skill-cheat stress-test lint.

**Spec:** `docs/superpowers/specs/2026-10-17-contract-first-rearchitecture-design.md`

## Global Constraints

- Plugin ships Markdown only — no Python engine, no bundled scripts
- Every SKILL.md must pass skill-cheat's voice-review lint (LINT-002, LINT-003, LINT-010, LINT-017, LINT-019, LINT-020)
- Skill contract template from the spec: Contract section, HARD-GATEs, Anti-Pattern, Core Principle, Checklist, Step Details, Gate Functions, Rationalization Table, Red Flags, Key Principles, The Bottom Line, Status Vocabulary
- HARD-GATE sentences open with imperative verb and carry a precondition keyword (without/if/until/outside/unless)
- Rationalization Table Reality cells open with an imperative verb from the lint allowlist (Run, Read, Write, Verify, Dispatch, Check, Name, Reject, Halt, Emit, Treat, Apply, Wait, Keep, Strip, Require, Accept, Push, Rerun, Commit, Rewrite)
- No hedge words in SKILL.md body (could, should, might, suggests, indicates, perhaps, possibly, arguably, likely, generally, typically, usually)
- Reference docs are decision tables and catalogs — never methodology prose
- Verdict vocabulary stays unchanged from current plugin
- The pipeline stages and their order stay unchanged

## Review Focus

1. **Domain detection false positive** — a hypothesis about graph-structured tabular data (e.g., molecular property prediction) could match both `graph` and `tabular` domain types. The domain-detection.md table must have tiebreaker rules, and analyze-problem must handle multi-domain hypotheses.
2. **Schema drift between reference doc and skill** — a skill references `structural_basis` but the schema calls it `source_property`. Every field name in a skill's Step Details must match the schema doc exactly.
3. **Reference doc too thin to be actionable** — a decision table with one row per domain gives Claude nothing to work with. Each domain section in analysis-catalog.md and component-vocabulary.md needs at least 4-5 concrete check/component rows grounded in the two existing experiments.
4. **Lint regression in near-contractual skills** — judge, null-baseline-gate, etc. currently pass lint. Extracting domain knowledge into references must not introduce hedge words or break HARD-GATE formatting.
5. **Circular reference between explore and propose-spec** — explore dispatches propose-spec and reads its output. The proposal-schema.md and genome-spec-schema.md must be consistent: every field explore produces must map to exactly one field propose-spec consumes.

---

### Task 1: Write the 4 Formal Schema Docs

These unblock every other task. Each schema doc defines the JSON format that skills validate against.

**Files:**
- Create: `skills/auto-discover/references/experiment-tree-schema.md`
- Create: `skills/analyze-problem/references/problem-analysis-schema.md`
- Create: `skills/propose-spec/references/genome-spec-schema.md`
- Create: `skills/explore/references/proposal-schema.md`

**Interfaces:**
- Consumes: Spec § Formal Schemas (the JSON blocks are already written there)
- Produces: 4 standalone schema docs that every downstream task references by path

- [ ] **Step 1: Create the 4 `references/` directories**

```bash
mkdir -p skills/auto-discover/references
mkdir -p skills/analyze-problem/references
mkdir -p skills/propose-spec/references
mkdir -p skills/explore/references
```

- [ ] **Step 2: Write `skills/auto-discover/references/experiment-tree-schema.md`**

Copy the experiment-tree schema from the spec's § Formal Schemas → 1. Add a header `# Experiment Tree Schema`, a one-line purpose statement, the JSON schema block, then a `## Field Notes` section with one row per field explaining computation rules (e.g., SHA computation: `SHA-256(json.dumps(spec, sort_keys=True) + parent_hash)`). Add `## Pareto History Format` section standardizing the format: every entry is `{round, front: [...]}` — no mixed object/array formats. Add `## Convergence Fields` section explaining that `search_status` is written by the converge skill and read by the Stop hook.

- [ ] **Step 3: Write `skills/analyze-problem/references/problem-analysis-schema.md`**

Copy from spec § Formal Schemas → 2. Header, purpose, JSON block. Add `## Domain Type Values` section listing each domain type with a one-sentence definition. Add `## Research Direction Priority Rules` section: high = addresses baseline failure gap, medium = follows from mathematical property without baseline signal, low = follows from theoretical constraints only.

- [ ] **Step 4: Write `skills/propose-spec/references/genome-spec-schema.md`**

Copy from spec § Formal Schemas → 3. Header, purpose, JSON block. Add `## Naming Convention` section: architecture_name derives from structural_basis + primary operation, never from a known architecture name. Add `## Fingerprint Computation` section: fingerprint = (sorted ops_used tuple, composition.strategy, layer arrangement).

- [ ] **Step 5: Write `skills/explore/references/proposal-schema.md`**

Copy from spec § Formal Schemas → 4. Header, purpose, JSON block. Add `## Field Mapping to Genome Spec` section: a table showing which proposal field maps to which genome-spec field (structural_basis → structural_basis, required_operations → novel_component.ops_used, composition_strategy → composition.strategy).

- [ ] **Step 6: Verify all 4 files exist and contain the JSON schema block**

```bash
for f in skills/auto-discover/references/experiment-tree-schema.md \
         skills/analyze-problem/references/problem-analysis-schema.md \
         skills/propose-spec/references/genome-spec-schema.md \
         skills/explore/references/proposal-schema.md; do
  test -f "$f" && grep -q '```json' "$f" && echo "OK: $f" || echo "MISSING: $f"
done
```

- [ ] **Step 7: Commit**

```bash
git add skills/*/references/*-schema.md
git commit -m "Add 4 formal inter-skill JSON schemas

Defines typed contracts for experiment-tree.json, problem-analysis.json,
genome_spec.json, and proposal format. Skills validate inputs against
these schemas and reject malformed data."
```

---

### Task 2: Write Reference Docs for analyze-problem and explore

The two skills that drive the search loop. Their reference docs carry the domain knowledge that makes the pipeline extensible.

**Files:**
- Create: `skills/analyze-problem/references/domain-detection.md`
- Create: `skills/analyze-problem/references/analysis-catalog.md`
- Create: `skills/explore/references/component-vocabulary.md`
- Create: `skills/explore/references/divergence-rules.md`

**Interfaces:**
- Consumes: Spec § Colocated Reference Docs (table structures defined there); experiment data from `experiments/01-modular-arithmetic/` and `experiments/02-graph-distinguishability/` for grounding the catalogs in real examples
- Produces: 4 reference docs that Task 5 (skill rewrites) will point at

- [ ] **Step 1: Write `skills/analyze-problem/references/domain-detection.md`**

Header `# Domain Detection`. Decision table with columns: Signal in hypothesis | Domain type | Tiebreaker. Populate from spec. Add a `## Multi-Domain Hypotheses` section: when signals match multiple domains, use the most specific (graph > tabular, mathematical > sequence). Add a `## Detection Method` section: scan the thesis, null_hypothesis, and success_criteria fields for domain keywords.

- [ ] **Step 2: Write `skills/analyze-problem/references/analysis-catalog.md`**

Header `# Analysis Catalog`. One section per domain type. Each section has a decision table with columns: Check | What to verify | How to verify | Output field (structural_properties entry).

For `§ Mathematical`, populate from the two existing experiments:

| Check | What to verify | How to verify | Output field |
|---|---|---|---|
| Group structure | Is the task a group operation? Associative? Commutative? Invertible? | Compose script testing properties on small instances | sp: algebraic, "group operation verified" |
| Representation theory | What are the irreducible representations? | Derive from the group classification | sp: algebraic, "N irreducible representations" |
| Symmetries | What transformations preserve the task? | Test on toy inputs | sp: geometric, "translation/permutation invariance" |
| Information bounds | Minimum faithful representation dimension | From representation theory or counting argument | sp: information_theoretic, "minimum dim = N" |
| Compositional structure | Does the task decompose as embed → operate → readout? | Analyze the mathematical formulation | sp: compositional, "functional decomposition" |
| Baseline failure mode | What structural gap does the baseline reveal? | Read baseline_metrics.json, compare to task requirements | baseline_failure_analysis fields |
| Theoretical constraints | Known expressiveness bounds or impossibility results | Mathematical argument | theoretical_constraints entries |

For `§ Graph`, populate from experiment 02:

| Check | What to verify | How to verify | Output field |
|---|---|---|---|
| Equivalence relation | What defines "same"? (isomorphism, WL-equivalence) | From the hypothesis | sp: algebraic, "equivalence = 1-WL" |
| Distinguishing invariants | What structural properties separate non-equivalent inputs? | Analyze the equivalence hierarchy | sp: algebraic, "invariants: degree, spectrum, subgraph counts" |
| Aggregation requirements | Does mean/max aggregation lose distinguishing information? | Test on known-separable pairs | sp: information_theoretic, "injective aggregation required" |
| Symmetry requirements | Permutation invariance of node ordering? | From task definition | sp: geometric, "permutation invariance" |
| Compositional structure | Local computation → global readout? | Analyze the task | sp: compositional, "neighborhood → global" |
| Baseline failure mode | Why does the conventional approach fail? | Read baseline metrics | baseline_failure_analysis fields |
| Expressiveness bounds | Known WL hierarchy bounds | Mathematical argument | theoretical_constraints entries |

Add stub sections for `§ Sequence`, `§ Tabular`, `§ Vision` with 3-4 placeholder checks each (marked as extensible).

- [ ] **Step 3: Write `skills/explore/references/component-vocabulary.md`**

Header `# Component Vocabulary`. One section per domain type. Each section has a table with columns: Operation type | What it does | When it applies | Limitations.

For `§ Mathematical`, populate from experiment 01 outcomes:

| Operation type | What it does | When it applies | Limitations |
|---|---|---|---|
| Frequency projection | Projects inputs onto a harmonic/Fourier basis | Group has known irreducible representations | Requires basis to be known or learnable |
| Pointwise combination | Element-wise operation in a transformed basis | Task operation is a convolution or group homomorphism | Only works if the right basis is found |
| Learned basis functions | Learns the representation basis from data | Optimal basis is unknown but structurally constrained | Optimization may get stuck |
| Inverse mapping | Recovers original domain from transformed representation | Architecture uses a frequency or spectral representation | Adds parameters |
| Amplitude weighting | Per-channel scaling in transformed domain | Some basis components are more informative than others | Minimal parameters |

For `§ Graph`, populate from experiment 02 outcomes:

| Operation type | What it does | When it applies | Limitations |
|---|---|---|---|
| Injective aggregation | Aggregates multiset without information loss (sum) | 1-WL expressiveness is required | High dimension needed for faithfulness |
| Partitioned embedding | Divides embedding dim into groups computing different statistics | Multiple structural statistics are informative | Partition boundaries are a design choice |
| Multi-statistic aggregation | Computes sum + max + std across partitioned dims | Single aggregation statistic loses information | More parameters per layer |
| Structural probe | High-dimensional embedding that preserves structural properties | Task requires distinguishing fine-grained structure | Large embedding dimension |
| Cross-partition mixing | Learned linear combination across partition groups | Independent statistics need to be combined | Adds a mixing layer |

Add stub sections for `§ Sequence`, `§ Tabular`, `§ Vision` with 3-4 placeholder operations each.

- [ ] **Step 4: Write `skills/explore/references/divergence-rules.md`**

Header `# Divergence Rules`. Three sections:

`## Fingerprint Computation`: fingerprint = (sorted_ops_tuple, composition_strategy, layer_arrangement). Define each component.

`## Collision Detection`: compare each proposal pair and each proposal against every prior spec in experiment-tree.json. Reject on exact fingerprint match. Shared ops alone are not a rejection — strategy or arrangement must also match.

`## Mandatory Divergence`: if UNTRIED classes exist (research directions in problem-analysis.json with no matching spec class in the tree), at least one research agent slot targets an UNTRIED class. Table:

| Tree state | Mandatory action |
|---|---|
| UNTRIED classes exist | At least one slot targets UNTRIED |
| All EXPLORING, none UNTRIED | Refine most promising + coverage slot for least-explored |
| All EXHAUSTED | Do not spawn agents, return to orchestrator |

- [ ] **Step 5: Verify all 4 files exist**

```bash
for f in skills/analyze-problem/references/domain-detection.md \
         skills/analyze-problem/references/analysis-catalog.md \
         skills/explore/references/component-vocabulary.md \
         skills/explore/references/divergence-rules.md; do
  test -f "$f" && echo "OK: $f" || echo "MISSING: $f"
done
```

- [ ] **Step 6: Commit**

```bash
git add skills/analyze-problem/references/ skills/explore/references/
git commit -m "Add reference docs for analyze-problem and explore

Domain detection table, per-domain analysis catalog, component vocabulary,
and divergence rules. Grounded in experiments 01 (modular arithmetic)
and 02 (graph distinguishability)."
```

---

### Task 3: Write Reference Docs for propose-spec, build-variant, evaluate, isolate-component

The four skills that execute on individual specs. Their references carry translation rules, training conventions, diagnostics, and gate definitions.

**Files:**
- Create: `skills/propose-spec/references/translation-rules.md`
- Create: `skills/build-variant/references/training-conventions.md`
- Create: `skills/build-variant/references/early-stopping-rules.md`
- Create: `skills/evaluate/references/training-diagnostics.md`
- Create: `skills/evaluate/references/metric-extraction.md`
- Create: `skills/isolate-component/references/isolation-gates.md`
- Create: `skills/isolate-component/references/threshold-calibration.md`

**Interfaces:**
- Consumes: Spec § Colocated Reference Docs; current skill prose (domain knowledge to extract)
- Produces: 7 reference docs that Task 6 (skill rewrites) will point at

- [ ] **Step 1: Write `skills/propose-spec/references/translation-rules.md`**

Header `# Translation Rules`. Decision table mapping proposal fields to genome-spec fields:

| Proposal field | Genome spec field | Rule |
|---|---|---|
| structural_basis | structural_basis | Copy verbatim |
| source_direction | structural_basis | Use rd_N id |
| required_operations | novel_component.ops_used | Map each abstract operation to an op name describing computation, not origin |
| composition_strategy | composition.strategy | Copy verbatim |
| expected_behavior | (not in spec) | Recorded in experiment tree node notes |
| falsification | (not in spec) | Recorded in experiment tree node notes |

Add `## Naming Conventions` section: architecture_name = structural_basis keyword + primary operation. Never use known architecture names (transformer, CNN, GNN, LSTM, attention, convolution, etc.).

Add `## Constraint Validation` section: every numeric value in hyperparameters checked against genome_constraints ranges. Out-of-range = BLOCKED, never silently clamped.

- [ ] **Step 2: Write `skills/build-variant/references/training-conventions.md`**

Header `# Training Conventions`. Per-domain defaults table:

| Convention | Default | Override source |
|---|---|---|
| Optimizer | Adam | hypothesis.search_config.optimizer |
| Seed handling | Use first seed from hypothesis.seeds | — |
| Checkpoint cadence | Every epoch | hypothesis.search_config.checkpoint_interval |
| Data generation | Same procedure as establish-baseline | — |
| Metric extraction | Every pre-registered metric at every checkpoint | — |
| Budget enforcement | max_epochs AND max_wall_clock_minutes, whichever first | hypothesis.training_budget |

Add `## Per-Domain Notes` with sections for mathematical, graph, sequence, tabular.

- [ ] **Step 3: Write `skills/build-variant/references/early-stopping-rules.md`**

Header `# Early Stopping Rules`. Decision table:

| Condition | Trigger | stop_reason value |
|---|---|---|
| Chance-level kill | Primary metric within 1% of chance at 10% budget | chance_level_kill |
| Patience exceeded | No improvement for patience window checkpoints | patience_exceeded |
| Budget exhausted | max_epochs or max_compute_flops reached | budget_exhausted |
| Wall clock limit | max_wall_clock_minutes reached | wall_clock_limit |

Add `## Chance Level Computation` section: 1/num_classes for classification, target variance for regression. Add `## Patience Window` section: from search_config.early_stopping_patience or derived from budget.

- [ ] **Step 4: Write `skills/evaluate/references/training-diagnostics.md`**

Header `# Training Diagnostics`. Check/condition/verdict table:

| Check | Condition | Verdict |
|---|---|---|
| NaN detection | Any metric value is NaN | REJECT |
| Gradient explosion | Gradient norm > 50 for 3 consecutive checkpoints | REJECT |
| Zero-variance output | Model predicts same value for all inputs | REJECT |
| Data leakage | Training metric suspiciously close to 1.0 on first checkpoint | flag for review |
| Metric completeness | All pre-registered metrics present in final_metrics.json | required for ACCEPT |

Add `## Trajectory Classification` section: record trajectory shape (monotonic_increase, spike_then_drop, plateau, oscillating) as a diagnostic field — never as the verdict.

- [ ] **Step 5: Write `skills/evaluate/references/metric-extraction.md`**

Header `# Metric Extraction`. Table:

| Metric type | Computation | Source |
|---|---|---|
| Primary metric | Value at best checkpoint | final_metrics.json |
| Secondary metrics | Values at best checkpoint | final_metrics.json |
| Gradient health | Mean gradient norm across checkpoints | training_metrics.json |
| Parameter count | Total trainable parameters | final_metrics.json.trainable_params |
| Compute used | FLOPs or samples processed | training_metrics.json |
| Stop reason | Why training ended | training_metrics.json.stop_reason |

- [ ] **Step 6: Write `skills/isolate-component/references/isolation-gates.md`**

Header `# Isolation Gates`. Three gate definitions:

| Gate | What it checks | PASS condition | FAIL condition |
|---|---|---|---|
| Gradient flow | Gradients propagate through the component | All gradient norms finite and > 0 | Any NaN, Inf, or zero gradient |
| Output range | Component output is bounded | All outputs within declared range | Any output outside range |
| Toy convergence | Component learns a trivial task | Loss decreases below threshold on toy data | Loss does not decrease after N steps |

- [ ] **Step 7: Write `skills/isolate-component/references/threshold-calibration.md`**

Header `# Threshold Calibration`. Per-domain defaults:

| Gate | Parameter | Mathematical | Graph | Sequence | Tabular |
|---|---|---|---|---|---|
| Gradient flow | max_norm | 100 | 100 | 100 | 100 |
| Output range | bounds | from hypothesis.search_config or activation range | same | same | same |
| Toy convergence | loss_ratio_threshold | 0.1 | 0.1 | 0.1 | 0.1 |
| Toy convergence | max_steps | 100 | 100 | 100 | 100 |

Add `## Override` section: hypothesis.search_config fields override these defaults.

- [ ] **Step 8: Create missing `references/` directories and verify all 7 files**

```bash
mkdir -p skills/build-variant/references skills/evaluate/references skills/isolate-component/references
for f in skills/propose-spec/references/translation-rules.md \
         skills/build-variant/references/training-conventions.md \
         skills/build-variant/references/early-stopping-rules.md \
         skills/evaluate/references/training-diagnostics.md \
         skills/evaluate/references/metric-extraction.md \
         skills/isolate-component/references/isolation-gates.md \
         skills/isolate-component/references/threshold-calibration.md; do
  test -f "$f" && echo "OK: $f" || echo "MISSING: $f"
done
```

- [ ] **Step 9: Commit**

```bash
git add skills/propose-spec/references/ skills/build-variant/references/ skills/evaluate/references/ skills/isolate-component/references/
git commit -m "Add reference docs for propose-spec, build-variant, evaluate, isolate-component

Translation rules, training conventions, early stopping decision table,
training diagnostics, metric extraction, isolation gate definitions,
and per-domain threshold calibration."
```

---

### Task 4: Write Reference Docs for Orchestrator and End-Gate Skills

The orchestrator (auto-discover), convergence, review, evidence, and the five near-contractual skills.

**Files:**
- Create: `skills/auto-discover/references/pipeline-overview.md`
- Create: `skills/auto-discover/references/dispatch-contract.md`
- Create: `skills/converge/references/convergence-conditions.md`
- Create: `skills/review-strategy/references/pareto-computation.md`
- Create: `skills/review-strategy/references/efficiency-thresholds.md`
- Create: `skills/evidence-report/references/evidence-schema.md`
- Create: `skills/evidence-report/references/verdict-rules.md`
- Create: `skills/judge/references/scoring-rubric.md`
- Create: `skills/null-baseline-gate/references/null-comparisons.md`
- Create: `skills/reproducibility-gate/references/variance-rules.md`
- Create: `skills/pre-register/references/validation-rules.md`
- Create: `skills/establish-baseline/references/baseline-conventions.md`

**Interfaces:**
- Consumes: Spec § Colocated Reference Docs; current skill prose for domain knowledge extraction
- Produces: 12 reference docs that Tasks 5-7 will point at

- [ ] **Step 1: Write `skills/auto-discover/references/pipeline-overview.md`**

Header `# Pipeline Overview`. Contains the dot digraph from the spec showing the full pipeline flow. Add a `## Stage Summary` table: Stage | Skill | Dispatched by | Verdicts (same pattern as auto_model_trainer's pipeline-overview.md).

- [ ] **Step 2: Write `skills/auto-discover/references/dispatch-contract.md`**

Header `# Dispatch Contract`. Copy the dispatch table from the spec:

| Stage | Pre-create | Inline to dispatch | Verify on return |
|---|---|---|---|
| analyze-problem | — | hypothesis path, baseline path | problem-analysis.json exists, status=DONE |
| explore | — | problem-analysis.json, experiment-tree.json | new pending nodes in tree |
| isolate-component | — | genome_spec.json path | gates/*.json exist |
| build-variant | worktree dir | genome_spec, hypothesis fields, worktree path | training_metrics.json, final_metrics.json |
| evaluate | — | worktree path, pre_registered_metrics | EVALUATION.json with verdict |
| review-strategy | — | evaluation_result, variant_params, baseline_params, pareto_front | REVIEW.json with verdict |
| null-baseline-gate | — | worktree path, baseline_metrics.json path | verdict |
| reproducibility-gate | — | worktree path, seeds, variance_tolerance | verdict |
| judge | — | metrics manifest, hypothesis path, gate results | verdict |
| evidence-report | — | worktree path (or partial tree state) | evidence.json with terminal_verdict |

- [ ] **Step 3: Write `skills/converge/references/convergence-conditions.md`**

Header `# Convergence Conditions`. Two tables:

**Tier 1 — Within-Class Exhaustion:**

| Condition | Fires when | Class status |
|---|---|---|
| Diminishing returns | Improvement < diminishing_returns_threshold over recent rounds AND depth >= min_exhaustion_depth | EXHAUSTED |
| Depth ceiling | depth >= min_exhaustion_depth with no untried variants at shallower depths | EXHAUSTED |
| Pareto domination | Another class strictly dominates on primary metric AND params, AND depth >= 1 | EXHAUSTED |

**Tier 2 — Cross-Class Coverage (all 3 required):**

| Condition | Passes when |
|---|---|
| Minimum class count | explored classes >= hypothesis minimum or derived default |
| All classes settled | no EXPLORING or UNTRIED classes remain |
| Pareto front stability | front identical for pareto_stability_window consecutive rounds |

Add `## Front Diversity Diagnostic` section: recorded but non-gating.

- [ ] **Step 4: Write `skills/review-strategy/references/pareto-computation.md`**

Header `# Pareto Computation`. Define: a node A dominates B if A is strictly better on primary_metric AND has fewer or equal params (or vice versa). Add `## Front Update` section: after evaluating a new node, recompute the front by testing every node against every other. Add `## History Tracking` section: append current front to pareto_history after each round, using format from experiment-tree-schema.md.

- [ ] **Step 5: Write `skills/review-strategy/references/efficiency-thresholds.md`**

Header `# Efficiency Thresholds`. Tables for parameter efficiency and stale pathway detection:

| Metric | Computation | Threshold source |
|---|---|---|
| Params per accuracy point | trainable_params / primary_metric | hypothesis.search_config or derived |
| Baseline efficiency ratio | variant efficiency / baseline efficiency | > 1.0 is more efficient |
| Stale pathway | sub-threshold improvement for N consecutive refinements | search_config.stale_pathway_count |

- [ ] **Step 6: Write `skills/evidence-report/references/evidence-schema.md`**

Header `# Evidence Schema`. The evidence.json format:

```json
{
  "hypothesis": "(copied verbatim from locked hypothesis)",
  "hypothesis_sha256": "string",
  "gate_results": {
    "null_baseline": { "verdict": "PASSED|FAILED", "details": {} },
    "reproducibility": { "verdict": "PASSED|FAILED", "details": {} },
    "judge": { "verdict": "CONFIRMS|REFUTES", "score": "float", "reasoning": "string" }
  },
  "comparison_table": { "<metric>": { "candidate": "float", "baseline": "float", "improvement": "string" } },
  "seed_variance_table": { "<seed>": { "<metric>": "float" } },
  "search_summary": { "rounds": "int", "classes_explored": "int", "variants_total": "int" },
  "leading_candidate": { "hash": "string", "architecture_name": "string", "total_parameters": "int" },
  "terminal_verdict": "DISCOVERY_CONFIRMED | DISCOVERY_REFUTED | BLOCKED_DIVERGENCE | BLOCKED_NEEDS_USER"
}
```

- [ ] **Step 7: Write `skills/evidence-report/references/verdict-rules.md`**

Header `# Verdict Rules`. Decision table:

| converge returned | null-baseline | reproducibility | judge | Terminal verdict |
|---|---|---|---|---|
| CONVERGED | PASSED | PASSED | CONFIRMS | DISCOVERY_CONFIRMED |
| CONVERGED | FAILED | — | — | DISCOVERY_REFUTED |
| CONVERGED | PASSED | FAILED | — | DISCOVERY_REFUTED |
| CONVERGED | PASSED | PASSED | REFUTES | DISCOVERY_REFUTED |
| BLOCKED | — | — | — | BLOCKED_DIVERGENCE |
| (pre-register/baseline/analyze BLOCKED) | — | — | — | BLOCKED_NEEDS_USER |
| (explore BLOCKED) | — | — | — | BLOCKED_NEEDS_USER |
| (all specs failed isolation) | — | — | — | BLOCKED_NEEDS_USER |

- [ ] **Step 8: Write the 5 near-contractual skill reference docs**

Write each as a single reference doc extracting domain knowledge from the current skill prose:

- `skills/judge/references/scoring-rubric.md`: scoring criteria table (success criteria met, failure criteria avoided, null baseline passed, reproducibility passed, meaningful improvement). Each row: criterion | weight | PASS condition.
- `skills/null-baseline-gate/references/null-comparisons.md`: three comparison definitions (shuffled-label, constant-predictor, baseline). Each row: comparison | candidate metric | control metric | PASS condition.
- `skills/reproducibility-gate/references/variance-rules.md`: seed variance computation (std across seeds per metric), tolerance check (variance < hypothesis.variance_tolerance), per-seed evaluate requirement.
- `skills/pre-register/references/validation-rules.md`: required fields list, phenomenon denylist, compute-normalized budget requirement, genome_constraints.max_parameters requirement.
- `skills/establish-baseline/references/baseline-conventions.md`: per-domain baseline defaults table: Domain | Baseline architecture | Training conventions | Derivation requirement.

- [ ] **Step 9: Create all directories and verify all 12 files**

```bash
mkdir -p skills/converge/references skills/review-strategy/references skills/evidence-report/references skills/judge/references skills/null-baseline-gate/references skills/reproducibility-gate/references skills/pre-register/references skills/establish-baseline/references
# verify all 12 files exist
```

- [ ] **Step 10: Commit**

```bash
git add skills/*/references/
git commit -m "Add reference docs for orchestrator, end-gates, and near-contractual skills

Pipeline overview, dispatch contract, convergence conditions, Pareto
computation, efficiency thresholds, evidence schema, verdict rules,
scoring rubric, null comparisons, variance rules, validation rules,
and baseline conventions."
```

---

### Task 5: Rewrite Core Loop Skills as Contracts (analyze-problem, explore, propose-spec)

The three skills that drive spec generation. Rewrite each to follow the skill contract template, pointing at reference docs instead of teaching methodology.

**Files:**
- Modify: `skills/analyze-problem/SKILL.md`
- Modify: `skills/explore/SKILL.md`
- Modify: `skills/propose-spec/SKILL.md`

**Interfaces:**
- Consumes: Reference docs from Tasks 1-2 (schemas, catalogs, vocabularies)
- Produces: 3 rewritten skills that define contracts, not methodology

- [ ] **Step 1: Rewrite `skills/analyze-problem/SKILL.md`**

Follow the skill contract template from the spec. Key changes:

**Contract section** (new, add after frontmatter):
```markdown
## Contract

- **Reads**: `.auto-discover/hypothesis.yaml`, `.auto-discover/baselines/baseline_metrics.json`
- **Writes**: `.auto-discover/problem-analysis.json` (schema: `references/problem-analysis-schema.md`)
- **References**: `references/domain-detection.md`, `references/analysis-catalog.md`, `references/problem-analysis-schema.md`
- **Verdicts**: ANALYSIS_COMPLETE, BLOCKED
```

**Step Details**: Replace all methodology prose ("Investigate the algebraic, geometric, or combinatorial structure...") with contract references: "Read `references/domain-detection.md`. Match hypothesis signals against the detection table. Record the domain_type. Read `references/analysis-catalog.md` § {domain_type}. Run each check in the domain's table. Produce one structural_properties entry per check matching `references/problem-analysis-schema.md`."

Strip all hedge words. Ensure all HARD-GATEs carry precondition keywords. Ensure all Rationalization Table Reality cells open with an allowlisted imperative verb.

- [ ] **Step 2: Rewrite `skills/explore/SKILL.md`**

**Contract section:**
```markdown
## Contract

- **Reads**: `.auto-discover/problem-analysis.json` (schema: `references/../analyze-problem/references/problem-analysis-schema.md`), `.auto-discover/experiment-tree.json` (schema: `references/../auto-discover/references/experiment-tree-schema.md`)
- **Writes**: Updated experiment-tree.json with pending nodes, dispatches propose-spec per proposal
- **References**: `references/proposal-schema.md`, `references/component-vocabulary.md`, `references/divergence-rules.md`
- **Verdicts**: EXPLORING, BLOCKED
```

**Step Details**: Replace "Each agent investigates its assigned direction by asking three questions..." with: "Read `references/component-vocabulary.md` § {domain_type}. For each selected research direction, produce a proposal matching `references/proposal-schema.md`. Map the direction's implication to operations from the vocabulary. Check divergence per `references/divergence-rules.md`."

- [ ] **Step 3: Rewrite `skills/propose-spec/SKILL.md`**

**Contract section:**
```markdown
## Contract

- **Reads**: Research proposal (schema: `references/../explore/references/proposal-schema.md`), `genome_constraints` from hypothesis
- **Writes**: `.auto-discover/experiments/<hash>/genome_spec.json` (schema: `references/genome-spec-schema.md`)
- **References**: `references/genome-spec-schema.md`, `references/translation-rules.md`
- **Verdicts**: SPEC_EMITTED, BLOCKED
```

**Step Details**: Replace translation prose with: "Read `references/translation-rules.md`. Map each proposal field to the corresponding genome-spec field per the mapping table. Validate against `references/genome-spec-schema.md`."

- [ ] **Step 4: Run lint on all 3 rewritten skills**

```bash
SKILL_CHEAT="/Users/hook/Documents/coding/python/Personal_AI  Projects/skill_cheat"
for skill in analyze-problem explore propose-spec; do
  echo "=== $skill ===" 
  bash "$SKILL_CHEAT/skills/skill-voice-review/scripts/lint.sh" "skills/$skill/SKILL.md" 2>&1 | python3 -c "import json,sys; d=json.load(sys.stdin); print(d.get('verdict','?'), len(d.get('findings',[])),'findings')"
done
```

Fix any findings. Re-run until all 3 return ACCEPT.

- [ ] **Step 5: Commit**

```bash
git add skills/analyze-problem/SKILL.md skills/explore/SKILL.md skills/propose-spec/SKILL.md
git commit -m "Rewrite analyze-problem, explore, propose-spec as contracts

Skills define typed inputs/outputs/verdicts and point at colocated
reference docs. Domain knowledge lives in catalogs and decision tables,
not in methodology prose."
```

---

### Task 6: Rewrite Execution Skills as Contracts (build-variant, evaluate, isolate-component, review-strategy)

**Files:**
- Modify: `skills/build-variant/SKILL.md`
- Modify: `skills/evaluate/SKILL.md`
- Modify: `skills/isolate-component/SKILL.md`
- Modify: `skills/review-strategy/SKILL.md`

**Interfaces:**
- Consumes: Reference docs from Tasks 1, 3 (schemas, conventions, diagnostics, gates)
- Produces: 4 rewritten skills

- [ ] **Step 1: Rewrite `skills/build-variant/SKILL.md`**

Add Contract section. Point Step Details at `references/training-conventions.md` and `references/early-stopping-rules.md`. Replace inline training convention prose with "Read `references/training-conventions.md` for per-domain defaults. Read `references/early-stopping-rules.md` for stopping conditions."

- [ ] **Step 2: Rewrite `skills/evaluate/SKILL.md`**

Add Contract section. Point at `references/training-diagnostics.md` and `references/metric-extraction.md`. Replace inline forensics prose with decision table references.

- [ ] **Step 3: Rewrite `skills/isolate-component/SKILL.md`**

Add Contract section. Point at `references/isolation-gates.md` and `references/threshold-calibration.md`. Replace inline gate definitions with "Read `references/isolation-gates.md` for gate definitions. Read `references/threshold-calibration.md` for per-domain thresholds."

- [ ] **Step 4: Rewrite `skills/review-strategy/SKILL.md`**

Add Contract section. Point at `references/pareto-computation.md` and `references/efficiency-thresholds.md`.

- [ ] **Step 5: Run lint on all 4 skills, fix findings**

- [ ] **Step 6: Commit**

```bash
git add skills/build-variant/SKILL.md skills/evaluate/SKILL.md skills/isolate-component/SKILL.md skills/review-strategy/SKILL.md
git commit -m "Rewrite build-variant, evaluate, isolate-component, review-strategy as contracts

Each skill points at colocated reference docs for domain knowledge.
Training conventions, diagnostics, gate definitions, and Pareto
computation rules live in decision tables."
```

---

### Task 7: Rewrite Orchestrator and End-Gate Skills as Contracts

**Files:**
- Modify: `skills/auto-discover/SKILL.md`
- Modify: `skills/converge/SKILL.md`
- Modify: `skills/evidence-report/SKILL.md`
- Modify: `skills/judge/SKILL.md`
- Modify: `skills/null-baseline-gate/SKILL.md`
- Modify: `skills/reproducibility-gate/SKILL.md`
- Modify: `skills/pre-register/SKILL.md`
- Modify: `skills/establish-baseline/SKILL.md`

**Interfaces:**
- Consumes: Reference docs from Tasks 1, 4
- Produces: 8 rewritten skills

- [ ] **Step 1: Rewrite `skills/auto-discover/SKILL.md`**

Add Contract section. Point at `references/experiment-tree-schema.md`, `references/pipeline-overview.md`, `references/dispatch-contract.md`. Replace inline dispatch instructions with "Read `references/dispatch-contract.md`. For each stage, pre-create per the Pre-create column, inline per the Inline column, verify per the Verify column."

- [ ] **Step 2: Rewrite `skills/converge/SKILL.md`**

Add Contract section. Point at `references/convergence-conditions.md`. Replace inline Tier 1/Tier 2 prose with table references.

- [ ] **Step 3: Rewrite `skills/evidence-report/SKILL.md`**

Add Contract section. Point at `references/evidence-schema.md` and `references/verdict-rules.md`.

- [ ] **Step 4: Rewrite `skills/judge/SKILL.md`**

Add Contract section. Point at `references/scoring-rubric.md`.

- [ ] **Step 5: Rewrite `skills/null-baseline-gate/SKILL.md`**

Add Contract section. Point at `references/null-comparisons.md`.

- [ ] **Step 6: Rewrite `skills/reproducibility-gate/SKILL.md`**

Add Contract section. Point at `references/variance-rules.md`.

- [ ] **Step 7: Rewrite `skills/pre-register/SKILL.md`**

Add Contract section. Point at `references/validation-rules.md`.

- [ ] **Step 8: Rewrite `skills/establish-baseline/SKILL.md`**

Add Contract section. Point at `references/baseline-conventions.md`.

- [ ] **Step 9: Run lint on all 8 skills, fix findings**

- [ ] **Step 10: Commit**

```bash
git add skills/auto-discover/SKILL.md skills/converge/SKILL.md skills/evidence-report/SKILL.md skills/judge/SKILL.md skills/null-baseline-gate/SKILL.md skills/reproducibility-gate/SKILL.md skills/pre-register/SKILL.md skills/establish-baseline/SKILL.md
git commit -m "Rewrite orchestrator and end-gate skills as contracts

All 8 skills point at colocated reference docs. Dispatch contract,
convergence conditions, evidence schema, verdict rules, scoring rubric,
null comparisons, variance rules, validation rules, and baseline
conventions live in decision tables."
```

---

### Task 8: Cleanup and Update Supporting Files

Delete the old project-level references, update CLAUDE.md, using-auto-discover, and marketplace.json.

**Files:**
- Delete: `references/structure-catalog.md`
- Delete: `references/representation-approaches.md`
- Delete: `references/` directory
- Modify: `CLAUDE.md`
- Modify: `skills/using-auto-discover/SKILL.md`
- Modify: `.claude-plugin/marketplace.json`

**Interfaces:**
- Consumes: All prior tasks completed
- Produces: Clean project with no stale references

- [ ] **Step 1: Delete project-level references directory**

Verify no skill still points at the old `references/` path:

```bash
grep -rn 'references/structure-catalog\|references/representation-approaches' skills/*/SKILL.md
```

If clean, delete:

```bash
rm -rf references/
```

- [ ] **Step 2: Update `CLAUDE.md`**

Update the Plugin Structure section to mention colocated references:
```markdown
- `skills/` -- SKILL.md files plus colocated `references/` directories with domain knowledge
```

Add a new section `## Adding a New Domain` listing the 6 reference doc sections to add (from the spec's Domain Registry section).

Remove any remaining references to Polya's method or allowed_ops.

- [ ] **Step 3: Update `skills/using-auto-discover/SKILL.md`**

Update the Core Principles to reflect contract-first approach. Update the skill inventory table descriptions to mention reference docs.

- [ ] **Step 4: Update `.claude-plugin/marketplace.json` description**

- [ ] **Step 5: Run full stress test**

```bash
SKILL_CHEAT="/Users/hook/Documents/coding/python/Personal_AI  Projects/skill_cheat"
TARGET="/Users/hook/Documents/coding/python/Personal_AI  Projects/auto_archicture_discovery"
bash "$SKILL_CHEAT/skills/skill-stress-test/scripts/layer-static.sh" --target "$TARGET" 2>&1 | python3 -c "
import json, sys
data = json.load(sys.stdin)
clean = sum(1 for s in data['per_skill'] if s['verdict'] == 'ACCEPT')
total = len(data['per_skill'])
print(f'{clean}/{total} skills ACCEPT')
for s in data['per_skill']:
    if s['verdict'] != 'ACCEPT':
        print(f'  {s[\"skill\"]}: {s[\"verdict\"]} ({len(s[\"findings\"])} findings)')
"
```

Fix any lint findings. Re-run until 15/16 ACCEPT (using-auto-discover is a bootstrap, LINT-010 expected).

- [ ] **Step 6: Commit**

```bash
git add -A
git commit -m "Complete contract-first rearchitecture

Deleted project-level references (now colocated). Updated CLAUDE.md with
domain extension instructions. All 15 pipeline skills pass lint as
contracts with colocated reference docs."
```
