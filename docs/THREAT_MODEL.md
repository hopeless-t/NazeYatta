# Threat Model (v0.1)

NazeYatta assumes a worker may misunderstand, ignore, or strategically phrase inputs to reduce friction.

| Failure / attack | Mitigation direction |
|---|---|
| Worker underspecifies task | Action IR validation / missing-meaning review |
| Worker fabricates evidence | provenance + external verification |
| Policy is modified without authority | policy ownership + version/hash binding |
| LLM misses a hazard | deterministic mandatory policy lane |
| LLM invents hazard | candidate-only generative lane |
| State changes after preflight | fingerprints + stale detection |
| Observation failure becomes absence | explicit UNKNOWN semantics |
| Worker clears its own BLOCK | separate override authority/record |
| Prompt injection in third-party docs | instructions != policy |
| Gate failure | explicit fail-open/fail-closed policy semantics |

## Critical assumption

Preflight alone cannot force compliance. High-impact actions require an enforcement point the worker cannot bypass.
