# Findings Log Schema

Defines the structured research log written to `.auto-discover/research/round_N/findings.json`.

```json
{
  "round": "integer",
  "probes": [
    {
      "id": "string — probe_N",
      "question": "string — what property this tests",
      "script_path": "string",
      "result": "string — structured finding",
      "implication": "string — what this means for architecture design"
    }
  ],
  "searches": [
    {
      "query": "string — the search terms used",
      "source": "string — probe_N that motivated this search",
      "top_results": ["string — title + key finding"],
      "implication": "string — what this means for architecture design"
    }
  ],
  "prototypes": [
    {
      "id": "string — proto_N",
      "based_on": "string — which probes + searches motivated it",
      "script_path": "string",
      "accuracy": "float",
      "params": "integer",
      "succeeded": "boolean",
      "failure_diagnosis": "string | null — why it failed, if it did"
    }
  ],
  "genome_specs_produced": ["string — hash of each spec written to worktree"]
}
```

## Field Notes

| Field | Notes |
|---|---|
| `round` | Integer starting at 1. Increments each time the orchestrator dispatches research. |
| `probes[].id` | Format `probe_N` where N is a sequential integer within the round. |
| `probes[].question` | The property being tested, stated as a question. Not a specific mathematical structure name -- the question names what relationship is being probed. |
| `probes[].script_path` | Relative path to the probe script within `.auto-discover/research/round_N/`. |
| `probes[].result` | The structured JSON output the probe printed, recorded as a string. |
| `probes[].implication` | What the probe result means for architecture design. Derived from the result, not from prior knowledge. |
| `searches[].query` | The exact search terms passed to WebSearch. Derived from a probe finding. |
| `searches[].source` | The `probe_N` id whose result motivated this search. Every search traces to a probe. |
| `searches[].top_results` | The top 3 results from the search, each as a title and key finding string. |
| `searches[].implication` | What the search results mean for architecture design. |
| `prototypes[].id` | Format `proto_N` where N is a sequential integer within the round. |
| `prototypes[].based_on` | Comma-separated list of probe and search ids that motivated this prototype. |
| `prototypes[].script_path` | Relative path to the prototype script within `.auto-discover/research/round_N/`. |
| `prototypes[].accuracy` | Best accuracy achieved during prototype training. |
| `prototypes[].params` | Total trainable parameter count. |
| `prototypes[].succeeded` | True if accuracy exceeded chance after 10% of the mini-budget. |
| `prototypes[].failure_diagnosis` | Required when `succeeded` is false. States why the prototype failed -- what structural assumption was wrong, what capacity was insufficient, what the loss curve revealed. |
| `genome_specs_produced` | List of spec hashes (fingerprints) for genome specs written to worktrees this round. |
