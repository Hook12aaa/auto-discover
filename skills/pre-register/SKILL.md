---
name: pre-register
description: "Trigger /pre-register when auto-discover needs to validate and lock a hypothesis file. Parses the YAML, verifies all required fields, computes SHA-256, and emits HYPOTHESIS_LOCKED or BLOCKED_NEEDS_USER."
---

<!-- design-region-clean-of-hard-gates -->

# Pre-Register

## Contract

- **Reads**: `hypothesis.yaml` (user-provided)
- **Writes**: `.auto-discover/hypothesis.yaml`, `.auto-discover/hypothesis.sha256`
- **References**: `references/validation-rules.md`
- **Verdicts**: HYPOTHESIS_LOCKED, BLOCKED_NEEDS_USER

<HARD-GATE>
Do NOT proceed without all required fields: thesis, null_hypothesis, success_criteria, failure_criteria, pre_registered_metrics (primary, secondary, forbidden), seeds, training_budget, genome_constraints (with at least max_parameters). STOP and emit BLOCKED_NEEDS_USER with the missing fields list.
</HARD-GATE>

<HARD-GATE>
Do NOT proceed if the hypothesis was modified after locking. STOP and treat the SHA-256 as the immutability contract.
</HARD-GATE>

<HARD-GATE>
Do NOT lock a hypothesis if its success_criteria, failure_criteria, or metric names reference a named phenomenon (grokking, double descent, lottery ticket, neural scaling law, phase transition, memorization-then-generalization). STOP and require operationally-defined criteria that describe measurable outcomes without importing a training-dynamics story.
</HARD-GATE>

<HARD-GATE>
Do NOT lock a hypothesis without at least one compute-normalized budget field (max_compute_flops or max_samples_seen). STOP and require a compute-normalized bound alongside any epoch limit.
</HARD-GATE>

## Anti-Pattern

**"I'll fill in the missing fields myself so we can get started."** A hypothesis with fields inferred after the fact is not pre-registered — it is post-hoc rationalization wearing a pre-registration costume. Missing fields STOP the pipeline; they are never filled in on the hypothesis's behalf.

## Core Principle

Pre-registration is the firewall against post-hoc rationalization. Lock before you run.

## Process Flow

```dot
digraph pre_register {
    rankdir=TB;
    node [shape=box];
    parse [label="Parse hypothesis.yaml"];
    fields [label="Verify required\nfields present" shape=diamond];
    metrics [label="Verify pre_registered_metrics\nhas primary/secondary/forbidden" shape=diamond];
    seeds [label="Verify seeds\nlist >= declared\nmin_seeds" shape=diamond];
    budget [label="Verify training_budget has\nmax_epochs and max_wall_clock_minutes" shape=diamond];
    initdir [label="Create .auto-discover/"];
    hash [label="Compute SHA-256"];
    write [label="Write hypothesis.sha256"];
    copy [label="Copy hypothesis.yaml to\n.auto-discover/hypothesis.yaml"];
    locked [label="HYPOTHESIS_LOCKED", shape=ellipse];
    blocked [label="BLOCKED_NEEDS_USER", shape=ellipse];

    parse -> fields;
    fields -> metrics [label="yes"];
    fields -> blocked [label="no"];
    metrics -> seeds [label="yes"];
    metrics -> blocked [label="no"];
    seeds -> budget [label="yes"];
    seeds -> blocked [label="no"];
    budget -> initdir [label="yes"];
    budget -> blocked [label="no"];
    initdir -> hash;
    hash -> write;
    write -> copy;
    copy -> locked;
}
```

## Checklist

1. Parse YAML
2. Verify required fields
3. Verify pre_registered_metrics has primary/secondary/forbidden
4. Verify seeds list has at least the declared min_seeds entries
5. Verify training_budget has max_epochs and max_wall_clock_minutes
6. Scan success_criteria, failure_criteria, and all metric names for phenomenon terminology. Reject any criterion or metric that names a specific training dynamic rather than an operational measurement. `grokking_delay_ratio` fails — it names a phenomenon. `compute_to_threshold_ratio` passes — it names a measurement. Emit BLOCKED_NEEDS_USER listing the offending terms and suggesting operational alternatives.
7. Verify training_budget includes at least one compute-normalized field: max_compute_flops (total floating-point operations) or max_samples_seen (total training examples processed). Epoch counts alone import a frame assumption — different architectures consume different compute per epoch. An epoch-only budget anchors the experiment to a specific architecture's compute profile.
8. Validate search_config fields if present. For each declared field, verify its type and range. For undeclared fields, record that their defaults will be derived at runtime by the consuming skill.
9. Create .auto-discover/
10. Compute SHA-256
11. Write hypothesis.sha256
12. Copy hypothesis.yaml to `.auto-discover/hypothesis.yaml`. Downstream skills read the hypothesis from this canonical path.
13. Emit verdict

## Step Details

### 1. Parse YAML

Read the hypothesis file and parse it as YAML. If the file does not exist or fails to parse, emit BLOCKED_NEEDS_USER with the parse error and stop.

### 2. Verify Required Fields

Read `references/validation-rules.md` § Required Fields for the complete field list and requirements. Confirm every required field is present. Collect every missing field name before stopping — the user must see the complete list in one pass, not one field at a time across repeated runs.

### 3. Verify Pre-Registered Metrics

Confirm `pre_registered_metrics` has all three of `primary`, `secondary`, and `forbidden` keys. `forbidden` is allowed to be an empty list, but the key itself must be present — its role is to name metrics that must never be used to justify a discovery, and an absent key means that boundary was never considered.

### 4. Verify Seeds

Confirm `seeds` is a list with at least the declared min_seeds entries (read from search_config; defaults derive from the minimum required for reproducibility-gate). A single seed cannot support the reproducibility gate downstream, so pre-registration STOPs it here rather than letting it fail silently three pipeline stages later.

### 5. Verify Training Budget

Confirm `training_budget` contains both `max_epochs` and `max_wall_clock_minutes`. Both bounds are required because either one alone leaves an unbounded dimension for a runaway or an under-trained baseline.

### 6. Scan for Phenomenon Terminology

Read `references/validation-rules.md` § Phenomenon Denylist. Scan `success_criteria`, `failure_criteria`, and every metric name in `pre_registered_metrics` against the denied terms in the reference doc. For each rejected term, recommend the operational replacement listed in the reference doc. A criterion named after a phenomenon imports a training-dynamics story before any training has run.

### 7. Verify Compute-Normalized Budget

Read `references/validation-rules.md` § Compute-Normalized Budget. Confirm `training_budget` includes at least one compute-normalized field from the reference doc. Epoch counts alone anchor the experiment to one architecture's per-epoch compute.

### 8. Validate Search Config

Read `references/validation-rules.md` § search_config Fields for the recognized fields, their types, ranges, and default derivation sources. Validate each declared field against the reference doc. Undeclared fields are valid — the consuming skill derives the value at runtime. Reject any field whose type does not match or whose value is outside its valid range. Emit BLOCKED_NEEDS_USER naming every invalid field.

### 9. Create State Directory

Create `.auto-discover/` if it does not already exist. This is the root the rest of the pipeline writes beneath.

### 10. Compute SHA-256

Compute the SHA-256 hash of the canonical byte contents of the hypothesis file, exactly as parsed in Step 1.

### 11. Write Hash File

Write the hash to `.auto-discover/hypothesis.sha256`. If this file already exists, treat the hypothesis as already locked: re-verify the existing hash against the current file contents rather than overwriting, and emit BLOCKED_NEEDS_USER if they diverge — a diverging hash means the hypothesis was edited after locking.

### 12. Copy Hypothesis File

Copy hypothesis.yaml to `.auto-discover/hypothesis.yaml`. Downstream skills — explore, evidence-report, and every other skill that needs the locked hypothesis — read from this canonical path, never from the user-supplied file's original location. This copy happens after the hash is written, so a copy only ever exists for a hypothesis that has actually passed Step 12's lock check.

### 13. Emit Verdict

Emit HYPOTHESIS_LOCKED with the hash, or BLOCKED_NEEDS_USER with the complete list of missing or invalid fields.

## Gate Functions

- BEFORE parsing: "Does the hypothesis file exist at the expected path?"
- BEFORE hashing: "Are all required fields present, and do metrics/seeds/budget satisfy their sub-checks?"
- BEFORE writing hypothesis.sha256: "Does a lock file already exist, and if so does it match the current file?"
- BEFORE emitting HYPOTHESIS_LOCKED: "Was the hash written to disk, and was hypothesis.yaml copied to .auto-discover/hypothesis.yaml, not just computed/hashed?"
- BEFORE locking: "Do any metrics or criteria name a specific phenomenon rather than an operational measurement?"
- BEFORE locking: "Does training_budget include at least one compute-normalized field?"

## Rationalization Table

| You think... | Reality |
|---|---|
| "The missing field is implied by the thesis, I can infer it" | Halt and emit BLOCKED_NEEDS_USER. Inference is how post-hoc rationalization enters the pipeline. |
| "One seed is enough for a first pass" | Require seeds >= the declared min_seeds. A single seed cannot support the reproducibility gate. |
| "I'll re-hash after I tweak one field" | Treat the hypothesis as immutable once locked. A changed field means a new pre-registration. |
| "forbidden is empty, I can omit the key" | Keep the key even when the list is empty. Its presence records that the boundary was considered. |
| "grokking_delay_ratio describes what we're measuring" | Reject the name — it references a phenomenon, not a measurement. Read `references/validation-rules.md` § Phenomenon Denylist for the operational replacement. |
| "N epochs is a reasonable budget" | Require a compute-normalized bound (FLOPs or samples). Read `references/validation-rules.md` § Compute-Normalized Budget. |

## Red Flags

- "This field is basically implied"
- "I'll fill in the budget with a sensible default"
- "The hash doesn't need to match exactly"
- "One seed to start, more later"

## Key Principles

- Every required field is verified explicitly; none are inferred.
- The SHA-256 is computed only after every field check passes.
- A hash file that already exists is compared, never overwritten.
- BLOCKED_NEEDS_USER always carries the complete list of what is missing.

## The Bottom Line

```bash
STATUS=$(python3 -c "
import hashlib, os
hyp_path = 'hypothesis.yaml'
hash_path = '.auto-discover/hypothesis.sha256'
if not os.path.exists(hyp_path) or not os.path.exists(hash_path):
    print('FAIL'); exit()
with open(hyp_path, 'rb') as f:
    actual = hashlib.sha256(f.read()).hexdigest()
with open(hash_path) as f:
    stored = f.read().strip()
print('PASS' if actual == stored else 'FAIL')
")
echo "VERDICT: $STATUS"
```

## Status Vocabulary

- **HYPOTHESIS_LOCKED** -- all required fields present, hash computed and written
- **BLOCKED_NEEDS_USER** -- one or more required fields missing or invalid
