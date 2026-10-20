# Pareto Computation

Objectives per node: `primary_metric` (direction from `metric_direction` in experiment-tree.json) and `params` (minimize).

## Dominance

Node A dominates node B when A is strictly better than B on `primary_metric` AND has fewer or equal `params`, or A has strictly fewer `params` AND a primary metric no worse than B's.

| Comparison of candidate vs a front point | Status |
|---|---|
| Candidate dominates the point | Candidate is Dominant over that point |
| Point dominates candidate | Candidate is Dominated by that point |
| Neither dominates (tie on both, or trade-off across objectives) | Neutral |

## Candidate Status Against the Front

| Comparison results across the whole front | Candidate status | Front effect |
|---|---|---|
| Dominates at least one point, dominated by none | Dominant | Add candidate, remove every point it dominates |
| Dominated by at least one point | Dominated | Front unchanged |
| Dominates no point, dominated by none | Neutral | Add candidate, remove nothing |

## Front Update

After evaluating a new node, recompute the front by testing every node with `review_verdict` in {KEEP, KEEP_WITH_CONCERNS} against every other such node. A node belongs to the front when no other tested node dominates it. The comparison runs as an executed script over the inline `pareto_front` plus the candidate.

| Output | Value |
|---|---|
| `status` | Dominant, Dominated, or Neutral |
| `front_updated` | true when the front membership changed |
| `points_removed` | node ids removed from the front by this candidate |

## History Tracking

After every round, append the current front to `pareto_history` using the `{round, front}` entry format defined in `experiment-tree-schema.md`.

| Rule | Value |
|---|---|
| Entries per round | Exactly one, including rounds where the front did not change |
| Entry shape | `{round, front}`; `front` is a copy of `pareto_front` |
| Mutation | Append-only |
