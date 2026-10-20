# Problem Analysis Schema

Defines `problem-analysis.json`, the output of analyze-problem and the input to explore.

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

## Domain Type Values

| Value | Definition |
|---|---|
| `mathematical` | The task is defined by algebraic operations (group, ring, field, modular arithmetic) on discrete or numeric inputs. |
| `graph` | The input is a graph with node and edge features, and the output depends on connectivity, adjacency, or isomorphism class. |
| `sequence` | The input is an ordered or temporal series of fixed or variable length, and the output depends on order or time dependencies. |
| `tabular` | The input is a fixed set of columns of structured features, with classification or regression as the output. |
| `vision` | The input is an image or pixel grid, and the output depends on spatial structure. |

## Research Direction Priority Rules

| Priority | Condition |
|---|---|
| `high` | The direction addresses the gap named in `baseline_failure_analysis.structural_gap`. |
| `medium` | The direction follows from a verified structural property and has no baseline failure signal. |
| `low` | The direction follows from `theoretical_constraints` only, with no verified structural property and no baseline failure signal. |

## Field Constraints

| Field | Constraint |
|---|---|
| `structural_properties[].id` | Format `sp_N`, N unique and sequential from 1. |
| `research_directions[].id` | Format `rd_N`, N unique and sequential from 1. |
| `research_directions[].source_property` | Must equal an existing `structural_properties[].id`. |
| `structural_properties[].verification_method` | Non-null when `verified` is true. null when `verified` is false. |
| `status` | `BLOCKED` when no structural property reaches `verified: true`. `research_directions` is then empty. |
