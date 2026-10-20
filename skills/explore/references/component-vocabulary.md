# Component Vocabulary

Per-domain catalog of abstract operation types. Proposals name operations from this vocabulary in `required_operations`; the names are abstract, never named architectures. The `When it applies` column names the structural signal that implies the operation.

## Mathematical

| Operation type | What it does | When it applies | Limitations |
|---|---|---|---|
| Frequency projection | Projects inputs onto a harmonic or Fourier basis | The group has known irreducible representations | Requires the basis to be known or learnable |
| Pointwise combination | Element-wise operation in a transformed basis | The task operation is a convolution or group homomorphism | Works only when the right basis is found |
| Learned basis functions | Learns the representation basis from data | The optimal basis is unknown but structurally constrained | Optimization stalls in a poor basis |
| Inverse mapping | Recovers the original domain from the transformed representation | The architecture uses a frequency or spectral representation | Adds parameters |
| Amplitude weighting | Per-channel scaling in the transformed domain | Some basis components carry more information than others | Minimal parameters; no effect when all components are equally informative |

## Graph

| Operation type | What it does | When it applies | Limitations |
|---|---|---|---|
| Injective aggregation | Aggregates a multiset without information loss (sum) | 1-WL expressiveness is required | Needs high dimension for faithfulness |
| Partitioned embedding | Divides the embedding dimension into groups that compute different statistics | Several structural statistics are informative | Partition boundaries are a design choice |
| Multi-statistic aggregation | Computes sum, max, and std across partitioned dimensions | A single aggregation statistic loses information | More parameters per layer |
| Structural probe | High-dimensional embedding that preserves structural properties | The task requires distinguishing fine-grained structure | Large embedding dimension |
| Cross-partition mixing | Learned linear combination across partition groups | Independent statistics need combining | Adds a mixing layer |

## Sequence

Extensible stub.

| Operation type | What it does | When it applies | Limitations |
|---|---|---|---|
| Positional encoding | Injects order information into each element | Output depends on element order | Fixed encodings bound the usable length |
| Recurrent state update | Carries a running summary across positions | Dependency range exceeds one step | Sequential computation limits parallelism |
| Pairwise interaction | Scores relations between all position pairs | Long-range dependencies determine the output | Cost grows quadratically with length |
| Windowed pooling | Aggregates a local window of positions | Decisive information is local | Loses dependencies beyond the window |

## Sequence Labeling

| Operation type | What it does | When it applies | Limitations |
|---|---|---|---|
| Token feature extraction | Produces per-token feature vectors from string properties (shape, prefix, suffix, case) | Always the first operation | Feature choice determines what the labeler can see |
| Corpus-trained embedding | Learns dense token representations from the unlabeled corpus (FastText, Word2Vec) | Vocabulary is large or tokens carry semantic similarity structure | Requires sufficient corpus size for meaningful embeddings |
| Corpus frequency features | Computes TF-IDF or frequency-rank features per token | Token rarity correlates with entity membership (e.g., artist names are rare) | Loses word identity; only captures distributional position |
| Layout feature injection | Appends document-layout signals (bbox position, font size, bold/italic) to token features | Layout features correlate with entity boundaries (e.g., bold = artist name) | Not available from all document parsers; adds feature dimensions |
| Sequential label decoding | Models label-to-label transitions via CRF or Viterbi | Adjacent labels are dependent (BIO constraints, multi-token spans) | Adds inference cost; no benefit when labels are conditionally independent |
| Per-token classification | Classifies each token independently (SVM, Random Forest) | Labels are conditionally independent given features, or sequence structure is weak | Ignores BIO transition constraints; may produce invalid sequences |
| Dictionary post-correction | Snaps predicted entity spans to a known-entity dictionary | A reference dictionary exists for at least one entity type | Cannot discover entities absent from the dictionary |

## Tabular

Extensible stub.

| Operation type | What it does | When it applies | Limitations |
|---|---|---|---|
| Per-feature embedding | Maps each column to its own embedding | Columns differ in type or scale | Parameters grow with column count |
| Feature interaction layer | Combines selected feature groups multiplicatively | Interaction groups determine the target | Needs the groups identified in analysis |
| Feature gating | Learned per-feature selection weights | A minimum feature set determines the target | Gate collapse removes informative features |
| Threshold partitioning | Splits feature space by learned thresholds | The target changes at discrete feature values | Hard splits block gradient flow |

## Vision

Extensible stub.

| Operation type | What it does | When it applies | Limitations |
|---|---|---|---|
| Local filtering | Applies shared local kernels across the grid | Translation invariance holds and information is local | Receptive field bounds global context |
| Spatial pooling | Reduces resolution while aggregating regions | The label survives small shifts | Discards fine position information |
| Patch embedding | Maps grid patches to vectors for set-style processing | Information is global and patch-decomposable | Patch size fixes the resolution floor |
| Equivariant transform | Applies group-equivariant filters | Rotation or scale invariance holds | Higher cost per layer |
