# Domain Detection

Maps hypothesis signals to the `domain_type` value in `problem-analysis.json`.

| Signal in hypothesis | Domain type | Tiebreaker |
|---|---|---|
| Group, ring, field operations; modular arithmetic; algebraic structure keywords (homomorphism, cyclic group, permutation group) | `mathematical` | Wins over `sequence` and `tabular` when the inputs are discrete operands of an algebraic operation. |
| Graph inputs; node or edge features; adjacency; isomorphism; Weisfeiler-Leman; message passing | `graph` | Wins over `tabular`; see Multi-Domain Hypotheses for `mathematical`. |
| Sequential or temporal inputs; time dependencies; variable-length inputs; autoregressive targets | `sequence` | Loses to `mathematical` when the sequence encodes operands of an algebraic operation. |
| Tabular features; fixed columns; classification or regression on structured records | `tabular` | Loses to `graph` and `mathematical` on any match. |
| Image or pixel inputs; spatial structure; convolution; translation of a pixel grid | `vision` | Wins over `tabular` when features are a pixel grid. |
| Token sequence labeling; BIO/IOB tags; entity extraction; NER; span tagging; document layout; PDF text extraction | `sequence_labeling` | Wins over `sequence` when the target is per-token labels, not a sequence-to-sequence output. Wins over `tabular` when input is ordered tokens with positional context. |

## Detection Method

| Step | Action |
|---|---|
| 1 | Scan `thesis`, `null_hypothesis`, and `success_criteria` for the keywords in the Signal column. |
| 2 | Record every domain with at least one keyword match. |
| 3 | One matching domain: that domain is `domain_type`. |
| 4 | Several matching domains: apply Multi-Domain Hypotheses. |
| 5 | No matching domain: analyze-problem emits BLOCKED without writing `problem-analysis.json`, and the pipeline routes to BLOCKED_NEEDS_USER. |

## Multi-Domain Hypotheses

| Matched domains | Resolution |
|---|---|
| graph + tabular | `graph` |
| mathematical + sequence | `mathematical` |
| mathematical + tabular | `mathematical` |
| graph + mathematical | `graph` when the input is a graph object; `mathematical` when graphs appear only as an illustration of the algebraic operation |
| vision + tabular | `vision` |
| sequence_labeling + sequence | `sequence_labeling` |
| sequence_labeling + tabular | `sequence_labeling` |
| Any other pair | The domain whose keywords appear in `thesis`; the domain whose keywords appear in `success_criteria` breaks a remaining tie |

Specificity order, most specific first: graph, mathematical, sequence_labeling, vision, sequence, tabular.

## Worked Examples

| Hypothesis | Matched signals | Domain type |
|---|---|---|
| Experiment 01: modular addition (a + b) mod p for primes in [5, 31] | modular arithmetic, algebraic structure | `mathematical` |
| Experiment 02: distinguish graph pairs separable by 1-Weisfeiler-Leman | graph inputs, isomorphism, message passing | `graph` |
