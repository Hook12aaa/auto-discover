# Divergence Rules

## Fingerprint Computation

Explore computes a partial fingerprint for each proposal. The full spec_class fingerprint exists only after propose-spec runs, because `layer_arrangement` is a genome spec field that a proposal does not carry.

| Component | Definition | Available at |
|---|---|---|
| `sorted_ops_tuple` | `required_operations` sorted alphabetically, as a tuple | Proposal |
| `composition_strategy` | `composition_strategy` copied verbatim | Proposal |
| `layer_arrangement` | The ordered layer arrangement of the genome spec | Genome spec only |

| Fingerprint | Value | Computed by |
|---|---|---|
| Partial | `(sorted_ops_tuple, composition_strategy)` | explore |
| Full (spec_class) | `(sorted_ops_tuple, composition_strategy, layer_arrangement)` | propose-spec |

## Collision Detection

Explore compares partial fingerprints only within the current proposal batch. Explore performs no tree-level collision detection.

| Comparison | Against | Rule |
|---|---|---|
| Proposal vs proposal | Partial fingerprints of the other proposals in the current batch | Reject the later proposal on exact partial-fingerprint match. |
| Cross-tree collision | Every prior spec in `experiment-tree.json` | Deferred to propose-spec. propose-spec compares the full `spec_class` fingerprint (including `layer_arrangement`) against every prior spec in the tree. Explore does not perform tree-level collision detection. |
| Shared operations only | Any | Not a rejection. `composition_strategy` must also match. |

## Mandatory Divergence

UNTRIED classes are research directions in `problem-analysis.json` with no matching spec class in the experiment tree.

| Tree state | Mandatory action |
|---|---|
| UNTRIED classes exist | At least one research agent slot targets an UNTRIED class |
| All EXPLORING, none UNTRIED | Refine the most promising class and fill one coverage slot for the least-explored class |
| All EXHAUSTED | Do not spawn agents; return to the orchestrator |
