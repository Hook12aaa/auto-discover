---
name: evidence-report
description: "Trigger /evidence-report when auto-discover needs to write the final structured evidence and emit a terminal verdict. Writes evidence.json to the candidate's worktree path containing: hypothesis (copied verbatim), gate results (pass/fail per gate), comparison table, seed variance table, judge verdict, accuracy trajectory, and terminal verdict. Emits DISCOVERY_CONFIRMED, DISCOVERY_REFUTED, BLOCKED_DIVERGENCE, or BLOCKED_NEEDS_USER."
---

<!-- design-region-clean-of-hard-gates -->

# Evidence Report

## Contract

- **Reads**: `.auto-discover/hypothesis.yaml`, `.auto-discover/hypothesis.sha256`, `.auto-discover/experiment-tree.json`, `<worktree-path>/EVALUATION.json`, `<worktree-path>/null_baseline_result.json`, `<worktree-path>/reproducibility_result.json`, `<worktree-path>/judge_verdict.json`, `.auto-discover/experiments/<hash>/gates/*.json`
- **Writes**: `<worktree-path>/evidence.json` (schema: `references/evidence-schema.md`)
- **References**: `references/evidence-schema.md`, `references/verdict-rules.md`
- **Verdicts**: DISCOVERY_CONFIRMED, DISCOVERY_REFUTED, BLOCKED_DIVERGENCE, BLOCKED_NEEDS_USER

<HARD-GATE>
Do NOT declare DISCOVERY_CONFIRMED without all conditions met. STOP and verify converge returned CONVERGED, both gates PASSED, and JUDGE_CONFIRMS.
</HARD-GATE>

<HARD-GATE>
Do NOT proceed without copying the hypothesis verbatim. STOP and embed it unchanged from the pre-registered file.
</HARD-GATE>

<HARD-GATE>
Do NOT emit evidence without structured JSON. STOP and write machine-readable fields, not prose.
</HARD-GATE>

<HARD-GATE>
Do NOT emit evidence without the accuracy_trajectory diagnostic. STOP and include it for the audit trail.
</HARD-GATE>

## Anti-Pattern

**"Everything passed and the story is clear, I'll write it up as a summary."** A prose summary can smooth over a borderline metric, omit a variance table entry, or paraphrase a gate result into something more favorable than it was. The evidence report is the permanent, auditable record — every field must be traceable to a specific file written by a specific gate, not to an agent's recollection of how the run felt.

## Core Principle

The evidence report is the structured record. Every field is computed, every gate result is pass/fail, every comparison is on pre-registered metrics. The terminal verdict follows mechanically from the evidence.

## Process Flow

```dot
digraph evidence_report {
  rankdir=TB;
  node [shape=box];

  copy_hyp [label="Copy hypothesis.yaml\nverbatim"];
  collect_gates [label="Collect gate results:\nisolation, null-baseline,\nreproducibility"];
  collect_convergence [label="Collect converge's CONVERGED status\n+ EVALUATION.json accuracy_trajectory\n(diagnostic)"];
  collect_judge [label="Collect judge_verdict.json"];
  build_tables [label="Build comparison table\nand seed variance table"];
  determine [label="Apply terminal\nverdict rules" shape=diamond];
  write [label="Write evidence.json"];

  confirmed [label="DISCOVERY_CONFIRMED", shape=ellipse];
  refuted [label="DISCOVERY_REFUTED", shape=ellipse];
  diverged [label="BLOCKED_DIVERGENCE", shape=ellipse];
  needs_user [label="BLOCKED_NEEDS_USER", shape=ellipse];

  copy_hyp -> collect_gates;
  collect_gates -> collect_convergence;
  collect_convergence -> collect_judge;
  collect_judge -> build_tables;
  build_tables -> determine;
  determine -> write;
  write -> confirmed [label="converge CONVERGED +\nall gates PASS +\nJUDGE_CONFIRMS"];
  write -> refuted [label="any gate FAIL\nor JUDGE_REFUTES"];
  write -> diverged [label="converge BLOCKED, or\nno ACCEPT anywhere\nafter all classes tried"];
  write -> needs_user [label="pre-register/baseline BLOCKED,\nexplore BLOCKED, or\nrepeated isolation failure"];
}
```

## Checklist

1. Copy hypothesis.yaml verbatim into the evidence record — no restatement, no paraphrase
2. Collect gate results: isolation gates, null-baseline gate, reproducibility gate — pass/fail each
3. Collect converge's search-level CONVERGED status, and the leading candidate's accuracy_trajectory diagnostic from EVALUATION.json
4. Collect the judge verdict from judge_verdict.json
5. Build the comparison table (candidate vs shuffled-label, constant-output, and pre-registered baseline)
6. Build the seed variance table from reproducibility_result.json
7. Apply the terminal verdict rules mechanically
8. Write evidence.json with every field populated from a source file
9. Emit exactly one terminal verdict

## Step Details

### 1. Copy the Hypothesis Verbatim

Read `.auto-discover/hypothesis.yaml` and embed its full contents into `evidence.json` under a `hypothesis` field, unchanged. Also embed `hypothesis.sha256` so the evidence record can be checked against the locked hash at any later time. Do not summarize or reword any field.

### 2. Collect Gate Results

Read `references/evidence-schema.md` § Field Sources. Populate each gate_results field from the source file named there. Isolation gates read from `.auto-discover/experiments/<hash>/gates/` (hash from the dispatch context, never from the worktree path). Null-baseline and reproducibility results read from the worktree path. Record each as a pass/fail entry with its own reason string — do not collapse them into a single boolean.

### 3. Collect Convergence Signals

Read `references/evidence-schema.md` § Field Sources for `search_convergence` and `accuracy_trajectory`. Copy converge's search-level CONVERGED status verbatim — do not re-derive it. Read `EVALUATION.json` from the leading candidate's worktree and record its `accuracy_trajectory` diagnostic. This diagnostic is never omitted, but it does not gate DISCOVERY_CONFIRMED; only converge's search-level status does.

### 4. Collect Judge Verdict

Read `references/evidence-schema.md` § Field Sources for `gate_results.judge`. Populate from `judge_verdict.json`, mapping JUDGE_CONFIRMS to CONFIRMS and JUDGE_REFUTES to REFUTES as the schema specifies.

### 5. Build Comparison Table

Read `references/evidence-schema.md` § Field Sources for `comparison_table`. Populate from `null_baseline_result.json` with one entry per pre-registered metric.

### 6. Build Seed Variance Table

Read `references/evidence-schema.md` § Field Sources for `seed_variance_table`. Populate from `reproducibility_result.json` with raw per-seed values for every pre-registered metric.

### 7. Apply Terminal Verdict Rules

Read `references/verdict-rules.md`. Apply the terminal verdict table and evaluation order mechanically. BLOCKED_DIVERGENCE is checked first (converge BLOCKED or full pass without any ACCEPT), then BLOCKED_NEEDS_USER (upstream pipeline failures), then DISCOVERY_CONFIRMED (all gates pass), then DISCOVERY_REFUTED (any end gate failed). Name the specific failing gate(s) in the evidence.

### 8. Write Evidence JSON

Read `references/evidence-schema.md` for the full schema and field sources. Write `evidence.json` to `<worktree-path>/evidence.json` — alongside training_metrics.json, final_metrics.json, and REVIEW.json, not under `.auto-discover/experiments/<hash>/`. Read `references/evidence-schema.md` § Population Rules for which fields are populated under each terminal verdict (BLOCKED verdicts carry null for fields with no upstream source file).

### 9. Emit Terminal Verdict

Return exactly one of the four terminal verdicts, matching `terminal_verdict` in the JSON just written. On `DISCOVERY_REFUTED` with inconclusive evidence (no single clean failing gate, e.g. a marginal miss on the success threshold), offer the user the option to mutate the genome spec and re-enter the pipeline through the `research` skill — do not decide this automatically.

## Gate Functions

- BEFORE writing the hypothesis field: "Is this copied verbatim, or have I reworded any part of it?"
- BEFORE declaring DISCOVERY_CONFIRMED: "Did converge itself return CONVERGED, do null-baseline-gate and reproducibility-gate both show PASS, AND is judge status exactly JUDGE_CONFIRMS?"
- BEFORE declaring BLOCKED_DIVERGENCE: "Did converge return BLOCKED because the tree was unassessable, or did the search exhaust every UNTRIED class without a single ACCEPT — or is this actually a CONVERGED search whose leading candidate merely failed an end gate, which is DISCOVERY_REFUTED, not BLOCKED_DIVERGENCE?"
- BEFORE writing any field: "Does this value trace back to a specific gate's JSON file, or am I inferring it?"
- BEFORE emitting the verdict: "Did I omit the accuracy_trajectory field anywhere in the record?"

## Rationalization Table

| You think... | Reality |
|---|---|
| "Everything looked good, I'll summarize it in prose" | Write structured JSON. Prose summaries are not machine-readable and invite paraphrase drift. |
| "The hypothesis is long, I'll condense the key points" | Read the hypothesis and write it verbatim into evidence.json. Condensing is where fields silently vanish. |
| "Judge confirmed and most gates passed, that's basically confirmed" | Verify ALL gates PASS, not most. One FAIL routes to DISCOVERY_REFUTED regardless of the judge's verdict. |
| "Convergence was fine, no need to record the exact type" | Keep the accuracy_trajectory diagnostic in the audit trail. DISCOVERY_CONFIRMED depends on converge's CONVERGED status, not on this diagnostic. |
| "This is clearly a discovery, I don't need to check every gate individually" | Apply the terminal verdict rules mechanically. Confidence is not a substitute for checking the gate list. |

## Red Flags

- "I'll write this up as a narrative instead of JSON"
- "The hypothesis is verbose, I'll paraphrase the key fields"
- "Most gates passed, that's close enough to CONFIRMED"
- "Convergence was fine, skip recording the exact type"
- "This is obviously a discovery, skip the mechanical check"

## Key Principles

- Every field in evidence.json traces to a specific upstream gate's output file.
- The hypothesis is embedded verbatim, never restated.
- The terminal verdict is derived mechanically from the four rules, never from impression.
- The candidate's accuracy_trajectory diagnostic is always recorded, but DISCOVERY_CONFIRMED depends on converge's search-level CONVERGED status, not on this diagnostic.
- On inconclusive DISCOVERY_REFUTED, offer genome mutation and re-entry — do not auto-decide.

## The Bottom Line

```bash
#!/usr/bin/env bash
set -euo pipefail
worktree_path="${1:?Usage: evidence-report <worktree_path>}"
evidence_file="${worktree_path}/evidence.json"
if [[ ! -f "$evidence_file" ]]; then
  echo "VERDICT: BLOCKED_NEEDS_USER"
  exit 1
fi
verdict=$(python3 -c "import json,sys; print(json.load(open(sys.argv[1]))['terminal_verdict'])" "$evidence_file")
echo "VERDICT: ${verdict}"
```

## Status Vocabulary

- **DISCOVERY_CONFIRMED** -- converge returned CONVERGED, all gates PASSED, and JUDGE_CONFIRMS
- **DISCOVERY_REFUTED** -- converge returned CONVERGED but an end gate FAILED or JUDGE_REFUTES
- **BLOCKED_DIVERGENCE** -- converge returned BLOCKED or no ACCEPT anywhere after all classes attempted
- **BLOCKED_NEEDS_USER** -- pre-register, baseline, explore, or repeated isolation failures blocked the pipeline
