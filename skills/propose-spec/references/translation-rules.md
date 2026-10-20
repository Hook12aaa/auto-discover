# Translation Rules

Maps each proposal field (see `skills/explore/references/proposal-schema.md`) to a genome spec field (see `genome-spec-schema.md`).

| Proposal field | Genome spec field | Rule |
|---|---|---|
| `structural_basis` | `structural_basis` | Copy verbatim. |
| `source_direction` | (not in spec) | Record in the experiment tree node `notes`. |
| `required_operations` | `novel_component.ops_used` | Map each abstract operation to an op name describing the computation, not its origin. One proposal operation yields one op name. Add none, omit none. |
| `composition_strategy` | `composition.strategy` | Copy verbatim. |
| `composition_strategy` + `required_operations` | `composition.layer_arrangement` | Order the translated ops per layer as the strategy dictates. Name every skip connection, branch point, and merge point. |
| `expected_behavior` | (not in spec) | Carry to evaluate as the prediction under test. |
| `falsification` | (not in spec) | Carry to evaluate as the refutation criterion. |

## Op Naming

| Proposal operation | Spec op name | Pattern |
|---|---|---|
| frequency projection | `frequency_project` | verb_noun describing the computation |
| pointwise combination | `pointwise_combine` | verb_noun describing the computation |

An op name that cites a paper, a model family, or a product is rejected.

## Naming Conventions

| Element | Rule |
|---|---|
| `architecture_name` | structural_basis keyword + primary operation in `novel_component.ops_used`. |
| Format | lowercase words joined by underscores. |
| Prohibited | Known architecture names: transformer, CNN, GNN, LSTM, attention, convolution, and every other published architecture or family. |
| Collision with a prohibited name | Rename from the structural basis. Never keep the name. |

## Constraint Validation

| Check | Condition | Result |
|---|---|---|
| Hyperparameter range | Every numeric value in `hyperparameters` lies inside its `genome_constraints` range. | pass |
| Composition range | `composition.num_layers` lies inside its `genome_constraints` range. | pass |
| Out-of-range value | Any numeric value falls outside its range. | BLOCKED, naming the field and its bounds |
| Clamping | Any value moved to the nearest bound. | Prohibited. Out-of-range is BLOCKED, never clamped. |
| Missing proposal | Dispatch carries no proposal, or `required_operations` is empty. | BLOCKED |
| Fingerprint collision | Fingerprint equals a prior spec's fingerprint. | BLOCKED, naming the colliding spec. No op renaming or arrangement reshuffling to force a mismatch. |
