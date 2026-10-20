# Analysis Catalog

One section per domain type. Each row is one structural check. The `Output field` column names the `problem-analysis.json` entry the check populates. Entries written as `sp: <category>, "<text>"` become `structural_properties` items with that category; a check that fails to verify is recorded with `verified: false`.

## Mathematical

| Check | What to verify | How to verify | Output field |
|---|---|---|---|
| Group structure | Is the task a group operation? Associative? Commutative? Invertible? | Compose a script testing each property on small instances | sp: algebraic, "group operation verified" |
| Representation theory | What are the irreducible representations? | Derive from the group classification | sp: algebraic, "N irreducible representations" |
| Symmetries | What transformations preserve the task? | Test on toy inputs | sp: geometric, "translation/permutation invariance" |
| Information bounds | Minimum faithful representation dimension | Representation theory or a counting argument | sp: information_theoretic, "minimum dim = N" |
| Compositional structure | Does the task decompose as embed, operate, readout? | Analyze the mathematical formulation | sp: compositional, "functional decomposition" |
| Baseline failure mode | What structural gap does the baseline reveal? | Read `baseline_metrics.json`, compare to task requirements | `baseline_failure_analysis` fields |
| Theoretical constraints | Known expressiveness bounds or impossibility results | Mathematical argument | `theoretical_constraints` entries |

Grounding, experiment 01 (modular addition mod p, p in [5, 31]): the task is the cyclic group Z_p; the group-structure check verifies associativity, commutativity, and invertibility on every p in the declared range; the irreducible representations of Z_p are its p characters, which yields the frequency-basis research direction.

## Graph

| Check | What to verify | How to verify | Output field |
|---|---|---|---|
| Equivalence relation | What defines "same"? (isomorphism, WL-equivalence) | Read from the hypothesis | sp: algebraic, "equivalence = 1-WL" |
| Distinguishing invariants | What structural properties separate non-equivalent inputs? | Analyze the equivalence hierarchy | sp: algebraic, "invariants: degree, spectrum, subgraph counts" |
| Aggregation requirements | Does mean or max aggregation lose distinguishing information? | Test on known-separable pairs | sp: information_theoretic, "injective aggregation required" |
| Symmetry requirements | Is the output invariant to node ordering? | Read from the task definition | sp: geometric, "permutation invariance" |
| Compositional structure | Does local computation feed a global readout? | Analyze the task | sp: compositional, "neighborhood -> global" |
| Baseline failure mode | Why does the conventional approach fail? | Read baseline metrics | `baseline_failure_analysis` fields |
| Expressiveness bounds | Known WL hierarchy bounds | Mathematical argument | `theoretical_constraints` entries |

Grounding, experiment 02 (1-WL-distinguishable pairs vs mean-aggregation GCN): the aggregation check runs mean aggregation on a known-separable pair and records identical outputs, which verifies the information loss and feeds the injective-aggregation research direction.

## Sequence

Extensible stub. Rows are placeholders until an experiment grounds them.

| Check | What to verify | How to verify | Output field |
|---|---|---|---|
| Dependency range | Distance over which the output depends on earlier inputs | Perturb one position, measure output change by distance | sp: information_theoretic, "dependency range = N" |
| Order sensitivity | Does permuting the inputs change the output? | Test on shuffled toy sequences | sp: geometric, "order sensitivity" |
| Length variability | Does the task hold across input lengths? | Evaluate toy instances at several lengths | sp: compositional, "length generalization requirement" |
| Baseline failure mode | What structural gap does the baseline reveal? | Read baseline metrics | `baseline_failure_analysis` fields |

## Sequence Labeling

| Check | What to verify | How to verify | Output field |
|---|---|---|---|
| Label vocabulary | What entity types exist? How many? What BIO constraints apply? | Read from hypothesis label set | sp: information_theoretic, "N entity types, BIO-constrained" |
| Token context dependency | How far does the correct label depend on surrounding tokens? | Perturb tokens at varying distances in the training set, measure label agreement change | sp: information_theoretic, "context window = N tokens" |
| Layout signal strength | Do formatting features (bold, font size, position) predict entity boundaries? | Mutual information between layout features and BIO labels on the training set | sp: compositional, "layout features informative/uninformative" |
| Entity span length distribution | Are entities typically single-token or multi-token? What is the max? | Statistics over training labels | sp: compositional, "mean span length = N, max = M" |
| Label transition structure | Does the label at position i depend on the label at position i-1? | Compare per-token accuracy (independent) to CRF accuracy (Markov) on a toy subset | sp: geometric, "label dependencies: Markov/independent" |
| Baseline failure mode | What structural gap does the baseline reveal? Which entity types does it miss? | Read baseline metrics per entity type | `baseline_failure_analysis` fields |

## Tabular

Extensible stub. Rows are placeholders until an experiment grounds them.

| Check | What to verify | How to verify | Output field |
|---|---|---|---|
| Feature interactions | Which feature groups determine the target jointly? | Test target dependence on feature subsets | sp: compositional, "interaction groups" |
| Feature invariances | Does the target ignore column order or scale? | Permute and rescale columns on toy rows | sp: geometric, "column invariance" |
| Information bounds | Minimum feature set that determines the target | Ablation on toy instances | sp: information_theoretic, "minimum feature set" |
| Baseline failure mode | What structural gap does the baseline reveal? | Read baseline metrics | `baseline_failure_analysis` fields |

## Vision

Extensible stub. Rows are placeholders until an experiment grounds them.

| Check | What to verify | How to verify | Output field |
|---|---|---|---|
| Translation invariance | Does the label survive pixel-grid shifts? | Shift toy images, compare labels | sp: geometric, "translation invariance" |
| Scale and rotation | Does the label survive scaling or rotation? | Transform toy images, compare labels | sp: geometric, "scale/rotation invariance" |
| Locality | Is the decisive information local or global? | Mask regions, measure label change | sp: compositional, "local -> global" |
| Baseline failure mode | What structural gap does the baseline reveal? | Read baseline metrics | `baseline_failure_analysis` fields |
