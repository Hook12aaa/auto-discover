# Research Protocol

Prescribes how to research, not what to find.

| Phase | Protocol | Constraint |
|---|---|---|
| Probe | Scripts must be self-contained, print structured JSON, and test one property each | Max 50 lines per probe |
| Search | Search terms derive from probe findings, not from prior knowledge | Record every search query and top-3 results in findings log |
| Prototype | Self-contained Python file, train on a data subset | Max 100 lines, max 500 epochs |
| Learn | Record failure mode + diagnosis in findings log | Every failed prototype gets a "why it failed" entry |
| Diverge | New probes target different structural properties than successful prototypes | At least 2 different mathematical bases per round |

## Round 2+ Protocol

| Input | What to read | What to target |
|---|---|---|
| Experiment tree | Prior specs, accuracies, spec classes | Gaps: unexplored structural bases |
| Findings log | Prior probes, searches, failures | Failures: what broke and why -> new search queries |
| Review verdicts | Pareto-dominated, stale pathways | Stale: classes with diminishing returns |

## Anti-Content Rules

The research skill NEVER names specific structures to look for. These are violations:
- "Probe for group structure" -- names the structure
- "Search for Fourier properties" -- names the property
- "Check if the mapping is equivariant" -- names the property

These are correct:
- "Probe the input/output relationship for symmetries" -- names the phase, not the content
- "Search based on what the probes found" -- derives from findings
- "Build a prototype that exploits the structural property the probes revealed" -- references findings
