# Genome Spec Schema

Defines `genome_spec.json`, the typed architecture description propose-spec emits and isolate-component and build-variant consume.

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
    "num_layers": "integer",
    "layer_arrangement": "string — ordered sequence of ops per layer and graph topology (skip connections, branch points, merge points)"
  },
  "hyperparameters": {
    "<key>": "number"
  }
}
```

## Naming Convention

| Rule | Detail |
|---|---|
| Derivation | `architecture_name` = structural_basis property + primary operation in `novel_component.ops_used`. |
| Prohibited | Any name of a published architecture or architecture family. |
| Format | lowercase words joined by underscores. |
| Example | A spec for `rd_2` (property: commutative pairwise structure) with primary op `symmetric_pair_aggregate` is named `commutative_symmetric_pair_aggregate`. |

## Fingerprint Computation

`spec_class` in the experiment tree is the fingerprint of the spec:

```
fingerprint = (sorted(novel_component.ops_used) as tuple,
               composition.strategy,
               composition.layer_arrangement)
```

| Element | Source | Rule |
|---|---|---|
| ops tuple | `novel_component.ops_used` | Sorted lexicographically, converted to a tuple. |
| strategy | `composition.strategy` | Copied verbatim. |
| layer arrangement | `composition.layer_arrangement` | Copied verbatim. Encodes the ops per layer and the graph topology. |

Two specs with equal fingerprints belong to the same spec class. Hyperparameter differences never change the fingerprint.

## Field Constraints

| Field | Constraint |
|---|---|
| `spec_version` | Schema version string. |
| `structural_basis` | Must equal a `research_directions[].id` in `problem-analysis.json`. |
| `novel_component.ops_used` | Non-empty. Names come from the proposal's `required_operations`. |
| `composition.layer_arrangement` | Non-empty. Lists ops for each of the `num_layers` layers and names every skip connection, branch point, and merge point. |
| `composition.num_layers` | Positive integer within `genome_constraints` in the hypothesis. |
| `hyperparameters` | Every value is a number. Every key is bounded by `genome_constraints`. |
