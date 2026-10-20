# Proposal Schema

Defines the proposal object each investigation agent returns to explore and explore dispatches to propose-spec.

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

## Field Mapping to Genome Spec

| Proposal field | Genome spec field | Rule |
|---|---|---|
| `structural_basis` | `structural_basis` | Copied verbatim. |
| `source_direction` | — | Recorded in the experiment tree node `notes`. Not a spec field. |
| `required_operations` | `novel_component.ops_used` | Copied as a list of abstract operation names. |
| `composition_strategy` | `composition.strategy` | Copied verbatim. |
| `expected_behavior` | — | Carried to evaluate as the prediction under test. Not a spec field. |
| `falsification` | — | Carried to evaluate as the refutation criterion. Not a spec field. |

## Field Constraints

| Field | Constraint |
|---|---|
| `structural_basis` | Must equal a `research_directions[].id` in `problem-analysis.json`. |
| `source_direction` | Must equal a `research_directions[].id` in `problem-analysis.json`. |
| `required_operations` | Non-empty. Names are abstract operations, never named architectures. |
| `expected_behavior` | Names a pre-registered metric and a direction of effect. |
| `falsification` | States an observable outcome on a pre-registered metric that refutes the proposal. |
