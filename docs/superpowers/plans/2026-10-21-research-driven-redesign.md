# Research-Driven Redesign Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace catalog-driven analyze-problem + explore + propose-spec with a single research skill that probes, web-searches, prototypes, and produces genome specs directly.

**Architecture:** Delete 3 skills (11 files), create 1 skill (3 files), update 7 files. Everything from isolate-component onward stays unchanged. The research skill prescribes how to research (probe, search, prototype, learn), not what to find.

**Tech Stack:** Pure Markdown. Validation via skill-cheat stress-test lint.

**Spec:** `docs/superpowers/specs/2026-10-21-research-driven-redesign.md`

## Global Constraints

- Plugin ships Markdown only — no Python engine, no bundled scripts
- Every SKILL.md must pass skill-cheat voice-review lint
- HARD-GATE sentences open with imperative verb + precondition keyword (without/if/until/outside/unless)
- Rationalization Table Reality cells open with an allowlisted imperative verb (Run, Read, Write, Verify, Dispatch, Check, Name, Reject, Halt, Emit, Treat, Apply, Wait, Keep, Strip, Require, Accept, Push, Rerun, Commit, Rewrite)
- No hedge words in SKILL.md body (could, should, might, suggests, indicates, perhaps, possibly, arguably, likely, generally, typically, usually)
- Reference docs are decision tables and schemas — never methodology prose about what to find
- Verdict vocabulary unchanged; research emits EXPLORING or BLOCKED

## Review Focus

1. **Research skill teaches content despite the rule.** The spec says "prescribe how to research, not what to find." If the SKILL.md says "probe for group structure" or "search for Fourier properties," that's prescribing content. The skill names the phases (probe, search, prototype, learn, diverge) and their constraints (50-line probes, 100-line prototypes), never what structures to look for.
2. **Orphaned references to deleted skills.** Any file that mentions analyze-problem, explore, or propose-spec by name must be updated. Check CLAUDE.md, README.md, dispatch-contract.md, pipeline-overview.md, using-auto-discover, and the orchestrator SKILL.md.
3. **Dispatch contract row mismatch.** The orchestrator steps must reference the research row in dispatch-contract.md, not the deleted analyze-problem/explore/propose-spec rows.
4. **genome-spec-schema.md stays.** The research skill writes genome specs — it still needs the schema. Do not delete propose-spec/references/genome-spec-schema.md; move it to research/references/ or auto-discover/references/.
5. **Lint regression.** The research skill must pass all lint rules. The updated auto-discover and using-auto-discover must still pass.

---

### Task 1: Delete old skills and create research skill skeleton

Delete the 3 catalog-driven skills, relocate genome-spec-schema.md, and create the research skill with its reference docs.

**Files:**
- Delete: `skills/analyze-problem/SKILL.md`, `skills/analyze-problem/references/problem-analysis-schema.md`, `skills/analyze-problem/references/domain-detection.md`, `skills/analyze-problem/references/analysis-catalog.md`
- Delete: `skills/explore/SKILL.md`, `skills/explore/references/proposal-schema.md`, `skills/explore/references/component-vocabulary.md`, `skills/explore/references/divergence-rules.md`
- Delete: `skills/propose-spec/SKILL.md`, `skills/propose-spec/references/translation-rules.md`
- Move: `skills/propose-spec/references/genome-spec-schema.md` → `skills/research/references/genome-spec-schema.md`
- Create: `skills/research/SKILL.md`
- Create: `skills/research/references/research-protocol.md`
- Create: `skills/research/references/findings-log-schema.md`

**Interfaces:**
- Consumes: Spec § The Research Skill (contract, inner loop, reference docs)
- Produces: The research skill and its references; all downstream tasks reference these paths

- [ ] **Step 1: Delete the 3 old skill directories**

```bash
rm -rf skills/analyze-problem skills/explore skills/propose-spec
```

- [ ] **Step 2: Create the research skill directory structure**

```bash
mkdir -p skills/research/references
```

- [ ] **Step 3: Write `skills/research/references/genome-spec-schema.md`**

Copy the genome-spec-schema content from the spec (§ What Stays Unchanged says "genome-spec-schema.md — specs still need a typed format"). The file is the same content that was in `skills/propose-spec/references/genome-spec-schema.md` — it defines the typed JSON format for genome specs. Since propose-spec is deleted but the schema is still needed, it moves here.

The schema content: `spec_version`, `architecture_name`, `structural_basis`, `novel_component` (type, class, ops_used), `composition` (strategy, layer_arrangement, num_layers), `hyperparameters`. Include the Naming Convention, Fingerprint Computation, and Field Constraints sections from the original.

- [ ] **Step 4: Write `skills/research/references/research-protocol.md`**

Header `# Research Protocol`. One-line purpose: "Prescribes how to research, not what to find."

The protocol table from the spec:

```markdown
| Phase | Protocol | Constraint |
|---|---|---|
| Probe | Scripts must be self-contained, print structured JSON, and test one property each | Max 50 lines per probe |
| Search | Search terms derive from probe findings, not from prior knowledge | Record every search query and top-3 results in findings log |
| Prototype | Self-contained Python file, train on a data subset | Max 100 lines, max 500 epochs |
| Learn | Record failure mode + diagnosis in findings log | Every failed prototype gets a "why it failed" entry |
| Diverge | New probes target different structural properties than successful prototypes | At least 2 different mathematical bases per round |
```

Add a `## Round 2+ Protocol` section:

```markdown
| Input | What to read | What to target |
|---|---|---|
| Experiment tree | Prior specs, accuracies, spec classes | Gaps: unexplored structural bases |
| Findings log | Prior probes, searches, failures | Failures: what broke and why → new search queries |
| Review verdicts | Pareto-dominated, stale pathways | Stale: classes with diminishing returns |
```

Add a `## Anti-Content Rules` section:

```markdown
The research skill NEVER names specific structures to look for. These are violations:
- "Probe for group structure" — names the structure
- "Search for Fourier properties" — names the property
- "Check if the mapping is equivariant" — names the property

These are correct:
- "Probe the input/output relationship for symmetries" — names the phase, not the content
- "Search based on what the probes found" — derives from findings
- "Build a prototype that exploits the structural property the probes revealed" — references findings
```

- [ ] **Step 5: Write `skills/research/references/findings-log-schema.md`**

Header `# Findings Log Schema`. Copy the JSON schema from the spec verbatim (the `round`, `probes`, `searches`, `prototypes`, `genome_specs_produced` structure). Add a `## Field Notes` section explaining each field.

- [ ] **Step 6: Write `skills/research/SKILL.md`**

Follow the skill contract template. The full skill:

**Frontmatter:** name: research, description triggers on research dispatch from orchestrator, names EXPLORING and BLOCKED verdicts.

**Contract section:**
```markdown
## Contract

- **Reads**: `.auto-discover/hypothesis.yaml`, `.auto-discover/baselines/baseline_metrics.json`, `.auto-discover/experiment-tree.json` (schema: `../auto-discover/references/experiment-tree-schema.md`), `.auto-discover/research/` (prior round findings), web (via WebSearch/WebFetch)
- **Writes**: `.auto-discover/research/round_N/` (probe scripts, findings log), `.auto-discover/worktrees/<hash>/genome_spec.json` (schema: `references/genome-spec-schema.md`)
- **References**: `references/research-protocol.md`, `references/findings-log-schema.md`, `references/genome-spec-schema.md`
- **Verdicts**: EXPLORING, BLOCKED
```

**HARD-GATEs** (4):
1. Do NOT produce genome specs without running at least 3 probes first. STOP and probe the problem.
2. Do NOT run web searches without grounding them in probe findings. STOP and derive search terms from results.
3. Do NOT produce fewer than 2 genome specs from different structural bases unless no viable prototypes exist. STOP and diverge.
4. Do NOT name specific mathematical structures to look for outside of recording probe results. STOP and let the probes discover them.

**Anti-Pattern:** "I already know this is a group theory problem, let me search for group-theoretic architectures." — That is retrieval. Run the probes. Let them tell you what the structure is. Search based on what they find.

**Core Principle:** The search space emerges from the interaction between the problem and what the agent discovers through probing and research.

**Checklist** (7 steps):
1. Read hypothesis and baseline metrics
2. Read experiment tree and prior findings log (if round 2+)
3. Run probes per `references/research-protocol.md` § Probe
4. Run web searches per `references/research-protocol.md` § Search
5. Build prototypes per `references/research-protocol.md` § Prototype
6. Record findings per `references/findings-log-schema.md`
7. Write genome specs to worktrees per `references/genome-spec-schema.md`

**Step Details:** Each step says "Read `references/research-protocol.md` § {Phase}" and names the constraint (50-line probes, 100-line prototypes, etc.). Step 2 says "If round 2+, read `references/research-protocol.md` § Round 2+ Protocol." Step 7 says "Write genome specs matching `references/genome-spec-schema.md`."

CRITICAL: Step Details must NOT say "probe for symmetries" or "search for Fourier" — they say "probe the input/output relationship" and "search based on probe findings." Review Focus #1.

**Gate Functions, Rationalization Table, Red Flags, Key Principles, The Bottom Line, Status Vocabulary** — standard anatomy. Rationalization Table entries open with allowlisted verbs. No hedge words anywhere.

- [ ] **Step 7: Verify all files exist and grep for hedge words**

```bash
for f in skills/research/SKILL.md \
         skills/research/references/research-protocol.md \
         skills/research/references/findings-log-schema.md \
         skills/research/references/genome-spec-schema.md; do
  test -f "$f" && echo "OK: $f" || echo "MISSING: $f"
done
grep -rinE "could|should|might|suggests|indicates|perhaps|possibly|arguably|likely|generally|typically|usually" skills/research/
```

- [ ] **Step 8: Verify deleted skills are gone**

```bash
for d in skills/analyze-problem skills/explore skills/propose-spec; do
  test -d "$d" && echo "STILL EXISTS: $d" || echo "DELETED: $d"
done
```

- [ ] **Step 9: Commit**

```bash
git add -A
git commit -m "Replace analyze-problem + explore + propose-spec with research skill

Delete 3 catalog-driven skills (11 files). Create research skill that
probes, web-searches, prototypes, and produces genome specs directly.
Prescribes how to research, not what to find."
```

---

### Task 2: Update orchestrator and dispatch contract

Update auto-discover, dispatch-contract, and pipeline-overview to reference the research skill instead of the deleted 3-skill chain.

**Files:**
- Modify: `skills/auto-discover/SKILL.md`
- Modify: `skills/auto-discover/references/dispatch-contract.md`
- Modify: `skills/auto-discover/references/pipeline-overview.md`

**Interfaces:**
- Consumes: Task 1 (research skill exists at `skills/research/`)
- Produces: Updated orchestrator that dispatches research instead of analyze-problem + explore + propose-spec

- [ ] **Step 1: Update `skills/auto-discover/references/dispatch-contract.md`**

Remove the rows for analyze-problem, explore, and propose-spec from the Dispatch Method table, Dispatch Table, and Dispatch Timing. Add one research row:

Dispatch Method:
```markdown
| research | Dispatch | worktree | opus | Probes, web search, prototyping — needs worktree + full reasoning |
```

Dispatch Table:
```markdown
| research | — | hypothesis path, baseline path, experiment-tree path, round number, prior findings log path | genome_spec.json exists per returned hash in worktrees |
```

Dispatch Timing:
```markdown
| research | converge returned EXPLORING, or the first loop entry |
```

Remove analyze-problem and explore from the Failure Routing table. Add:
```markdown
| research BLOCKED | Invoke evidence-report with partial tree state. |
```

- [ ] **Step 2: Update `skills/auto-discover/references/pipeline-overview.md`**

Replace the pipeline diagram with the new flow from the spec:

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

Update the Stage Summary table: remove analyze-problem, explore, propose-spec rows. Add research row.

- [ ] **Step 3: Update `skills/auto-discover/SKILL.md`**

**Contract section:** Remove `.auto-discover/problem-analysis.json` from Reads.

**HARD-GATE #2:** Change from "Do NOT enter the evolutionary loop without a completed problem analysis" to "Do NOT enter the evolutionary loop without a completed baseline. STOP and invoke establish-baseline first." (The problem analysis phase no longer exists as a separate step.)

**Checklist:** Remove steps 3 (analyze-problem) and 5-6 (explore, isolate per spec from explore). Replace with:
```
3. Initialize experiment tree
3b. Register convergence Stop hook
4. LOOP: Dispatch research
5. Isolate-component per spec from research (parallel)
...
```

**Step Details:** Remove the analyze-problem step entirely. Replace the explore step with:

"Dispatch via `Agent(isolation: "worktree", model: "opus")`. Read `references/dispatch-contract.md` row: research. Tell the agent: 'Read `skills/research/SKILL.md` for your contract.' Inline the hypothesis path, baseline path, experiment-tree path, round number, and prior findings log path. The agent probes the problem, web-searches based on findings, builds prototypes, and writes genome specs to worktrees. If research returns BLOCKED, route to evidence-report."

Remove the propose-spec dispatch step (research produces specs directly).

**Core Principle:** Update to: "Discovery is the output of a search where the search space itself is discovered through probing and research, not prescribed through catalogs."

**Anti-Pattern:** Keep the existing one about generational barriers.

- [ ] **Step 4: Verify no references to deleted skills remain**

```bash
grep -rn "analyze-problem\|explore\|propose-spec" skills/auto-discover/SKILL.md skills/auto-discover/references/
```

Fix any remaining references.

- [ ] **Step 5: Grep for hedge words in modified files**

```bash
grep -rinE "could|should|might|suggests|indicates|perhaps|possibly|arguably|likely|generally|typically|usually" skills/auto-discover/SKILL.md skills/auto-discover/references/dispatch-contract.md skills/auto-discover/references/pipeline-overview.md
```

- [ ] **Step 6: Commit**

```bash
git add skills/auto-discover/
git commit -m "Update orchestrator to dispatch research instead of 3-skill chain

Dispatch contract, pipeline overview, and orchestrator steps all
reference the single research skill. No more analyze-problem,
explore, or propose-spec dispatch rows."
```

---

### Task 3: Update supporting files and run stress test

Update CLAUDE.md, README.md, using-auto-discover, marketplace.json. Run the full stress test.

**Files:**
- Modify: `skills/using-auto-discover/SKILL.md`
- Modify: `CLAUDE.md`
- Modify: `README.md`
- Modify: `.claude-plugin/marketplace.json`

**Interfaces:**
- Consumes: Tasks 1-2 (research skill exists, orchestrator updated)
- Produces: All docs consistent, stress test passes

- [ ] **Step 1: Update `skills/using-auto-discover/SKILL.md`**

Update the skill inventory table: remove analyze-problem, explore, propose-spec rows. Add research row:

```markdown
| `research` | dispatched | Probes the problem, web-searches based on findings, prototypes architectures, produces genome specs |
```

Update Core Principles: replace "Analyze, then assemble" with "Prescribe how to research, not what to find. The search space emerges from probing and web research, not from catalogs."

Update skill count in any place it says "16 skills" → "14 skills".

- [ ] **Step 2: Update `CLAUDE.md`**

Update the pipeline in Quick Start:
```
pre-register -> establish-baseline -> initialize experiment tree
-> LOOP {
    research (probe + web search + prototype) -> isolate-component (per spec)
    -> build-variant (parallel worktrees) -> evaluate (per variant)
    -> review-strategy (Pareto front, efficiency) -> converge (two-tier check)
    -> EXPLORING: loop again | CONVERGED: exit with leading candidate
}
-> null-baseline-gate -> reproducibility-gate -> judge -> evidence-report
```

Update the Key Concepts section: replace "Analyze, then assemble" with a new section "Research, don't prescribe" explaining the probe → search → prototype → learn loop.

Update the Skills table: remove analyze-problem, explore, propose-spec rows. Add research row.

Update the Key Principles list: replace "Analyze, then assemble" with "Research, don't prescribe — the search space emerges from probing and web research, not from catalogs or methodologies."

- [ ] **Step 3: Update `README.md`**

Update the pipeline mermaid diagram: remove the AP (analyze-problem) node. Replace EX (explore) + PS (propose-spec) with RS (research). Update the description paragraph below the diagram.

Update the skill table: remove analyze-problem, explore, propose-spec. Add research.

Update the "Architecture: contract-first, library-last" section: rename to "Architecture: research-driven, contract-gated" and update the description to explain the probe → search → prototype approach. Update the directory tree to show `skills/research/` instead of the 3 deleted skills.

Update "Adding a new domain" section: remove the 6 reference doc steps (catalogs are gone). Replace with: "The research skill discovers what the problem requires through probing and web search. No domain-specific reference docs are needed. The search space emerges from the problem."

- [ ] **Step 4: Update `.claude-plugin/marketplace.json`**

Update the plugin description to mention research-driven discovery instead of catalog-driven analysis.

- [ ] **Step 5: Verify no orphaned references to deleted skills**

```bash
grep -rn "analyze-problem\|propose-spec" skills/*/SKILL.md CLAUDE.md README.md .claude-plugin/marketplace.json | grep -v "superpowers\|experiments\|research.md\|docs/"
```

The word "explore" will appear in many valid contexts (the verb, not the skill). Check each hit manually — only references to the skill `skills/explore/` or the dispatch of `explore` need fixing.

- [ ] **Step 6: Run the full stress test**

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

Target: 13/14 ACCEPT (using-auto-discover is a bootstrap, LINT-010 expected). Fix any findings and re-run.

- [ ] **Step 7: Commit**

```bash
git add -A
git commit -m "Update docs and pass stress test for research-driven redesign

Updated CLAUDE.md, README.md, using-auto-discover, marketplace.json.
Removed all references to deleted skills. 13/14 lint ACCEPT."
```
